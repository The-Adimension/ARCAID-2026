"""Re-runnable checks behind rows-2026-10-01-addendum.jsonl.

Offline part (repo files only):  RHAE form test on every stored game run.
Online part (Kaggle API, GET only): submissions, kernel code identity, Change A
counters, runtime identity. Needs Kaggle credentials (a kaggle.json or a proxy
that injects them). Optional: --leaderboard <public leaderboard CSV>.

Replays nothing, starts no engine, loads no pickle, submits nothing.
Run from the repo root:
    python corpus/verify_addendum_2026-10-01.py [--offline] [--leaderboard path.csv]
"""

from __future__ import annotations

import argparse
import csv
import glob
import hashlib
import json
import re
import urllib.request

API = "https://www.kaggle.com/api/v1"
COMP = "arc-prize-2026-arc-agi-3"
FORMS = {
    "memo_min(r^2,1.15)": lambda q: min(q * q, 1.15),
    "lineage_min(r,1.15)^2": lambda q: min(q, 1.15) ** 2,
    "cap_1.0": lambda q: min(q, 1.0) ** 2,
}


def get(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=120) as r:
        return r.read()


def get_json(path: str):
    return json.loads(get(API + path))


def code_cells(nb: dict) -> list[str]:
    return ["".join(c["source"]) if isinstance(c["source"], list) else c["source"]
            for c in nb["cells"] if c["cell_type"] == "code"]


def code_hash(cells: list[str]) -> str:
    return hashlib.sha256("\n#--\n".join(cells).encode()).hexdigest()[:16]


def flat(o, p=""):
    out = {}
    if isinstance(o, dict):
        for k, v in o.items():
            out.update(flat(v, f"{p}.{k}" if p else k))
    elif isinstance(o, list) and any(isinstance(x, (dict, list)) for x in o):
        for i, v in enumerate(o):
            out.update(flat(v, f"{p}[{i}]"))
    else:
        out[p] = o
    return out


def game_score(run: dict, form) -> float:
    h, a, done = run["base_actions_per_level"], run["actions_per_level"], run["levels_completed"]
    n = len(h)
    total_w = n * (n + 1) / 2
    tot = comp = 0.0
    for i in range(n):
        if i < done and a[i] > 0:
            tot += (i + 1) * form(h[i] / a[i])
            comp += i + 1
    return 100 * min(tot / total_w, comp / total_w)


def rhae_form_test() -> dict:
    files = sorted(glob.glob("submissions/*/outputs/benchmark.json") + glob.glob("experiments/*/outputs/benchmark.json"))
    runs = [r for p in files for r in json.load(open(p))["game_runs"]
            if r.get("final_score") is not None and r.get("base_actions_per_level")]
    match = {k: sum(abs(game_score(r, f) - r["final_score"]) < 1e-6 for r in runs) for k, f in FORMS.items()}
    sj_ok = sj_tot = 0
    for p in files:
        s = p.replace("benchmark.json", "score.json")
        try:
            games = json.load(open(s))["games"]
        except FileNotFoundError:
            continue
        by: dict = {}
        for r in json.load(open(p))["game_runs"]:
            by.setdefault(r["game_id"], []).append(r["final_score"])
        for g, v in games.items():
            sj_tot += 1
            sj_ok += g in by and abs(sum(by[g]) / len(by[g]) - v["score"]) < 1e-6
    return {"game_runs": len(runs), "final_score_reproduced": match,
            "score_json_equals_final_score": f"{sj_ok}/{sj_tot}"}


def kaggle_checks() -> dict:
    out: dict = {}
    subs = {s["ref"]: s for s in get_json(f"/competitions/submissions/list/{COMP}?page=1")}
    idx = {int(r["submission_ref"]): r for r in csv.DictReader(open("submissions/index.csv"))}
    out["submissions"] = {
        "kaggle": len(subs), "index_csv": len(idx),
        "score_mismatches": [k for k in idx if k not in subs or subs[k]["publicScore"] != idx[k]["public_score"]],
        "private_nonempty": sum(1 for s in subs.values() if s["privateScore"]),
        "has_4_19": any(s["publicScore"] == "4.19" for s in subs.values()),
        "latest": max(s["date"] for s in subs.values()),
    }

    def pulled(user, slug):
        j = get_json(f"/kernels/pull?userName={user}&kernelSlug={slug}")
        md = j["metadata"]
        return code_hash(code_cells(json.loads(j["blob"]["source"]))), {
            k: md.get(k) for k in ("currentVersionNumber", "datasetDataSources", "modelDataSources",
                                   "machineShape", "dockerImage")}
    out["kernels"] = {f"{u}/{s}": pulled(u, s) for u, s in (
        ("habanwer", "taaf-flashnext-sheetu12b-0922"),
        ("scottlegrand", "taaf-flashnext-sheetu12b-0922"),
        ("habanwer", "taaf-flashnext-sheetu12b-reasoning-notes"),
        ("habanwer", "duck-v3-wmreason"))}

    def run_output(slug):
        j = get_json(f"/kernels/output?userName=habanwer&kernelSlug={slug}")
        text = "".join(e.get("data", "") for e in json.loads(j["log"]))
        counters = [l for l in text.splitlines() if re.search(r"ARC3_WMREASON_(READY|FINAL)", l)]
        files = {f["fileName"]: f["url"] for f in j["files"]}
        ids = sorted({re.search(r"/kf/(\d+)/", u).group(1) for u in files.values()})
        return counters, files, ids
    c_rn, f_rn, id_rn = run_output("taaf-flashnext-sheetu12b-reasoning-notes")
    c_b, f_b, id_b = run_output("taaf-flashnext-sheetu12b-0922")
    c_w, _, id_w = run_output("duck-v3-wmreason")
    out["change_a_counters"] = {"3.90": c_rn, "4.17_base": c_b, "3.03": c_w}
    out["output_script_version_ids"] = {"3.90": id_rn, "4.17": id_b, "3.03": id_w}

    diffs = {}
    for name in ("vllm-server-identity.json", "taaf_setup_env.json", "vllm-setup-provenance.json"):
        a = flat(json.loads(get(f_rn[name])))
        b = flat(json.loads(get(f_b[name])))
        keys = set(a) | set(b)
        diffs[name] = {
            "fields": len(keys),
            "differ": sorted(k for k in keys if a.get(k) != b.get(k)
                             and not re.search(r"pid|pgid|sid|ticks|boot|epoch|seconds|meminfo|mem_available|free_bytes|created|permission|gpu_rows|disk|log_tail|_sha256_at_preflight|preflight_sha256", k)),
        }
    out["runtime_3.90_vs_4.17"] = diffs
    return out


def leaderboard(path: str) -> dict:
    rows = list(csv.DictReader(open(path, encoding="utf-8-sig")))
    pick = lambda user: next(({k: r[k] for k in ("Rank", "TeamName", "Score", "SubmissionCount", "LastSubmissionDate")}
                              for r in rows if user in r["TeamMemberUserNames"].split(",")), None)
    return {"sha256_16": hashlib.sha256(open(path, "rb").read()).hexdigest()[:16], "teams": len(rows),
            "habanwer": pick("habanwer"), "scottlegrand": pick("scottlegrand"),
            "latest_submission_in_file": max(r["LastSubmissionDate"] for r in rows)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--leaderboard")
    args = ap.parse_args()
    out = {"rhae_form_test": rhae_form_test()}
    if not args.offline:
        out["kaggle"] = kaggle_checks()
    if args.leaderboard:
        out["leaderboard"] = leaderboard(args.leaderboard)
    print(json.dumps(out, indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
