"""Is there anything to 'federate' across games? Helper-function reuse in Franzen's 100 transcripts.

RubiQ's federated idea: clients train separate parts and share updates. The ARC-AGI-3
analogue is sharing model-written tools across the games of one Kaggle run. This measures
how much of the model's code-writing is helper functions that recur across games.

For every python tool call (<parameter=code> ... </parameter>) in each transcript:
  * parse with ast; collect every FunctionDef (any depth);
  * exact key   = ast.dump of the function with its own name and argument names blanked;
  * near key    = set of identifier-normalised tokens; near-duplicate if Jaccard >= 0.8;
  * generic     = the body has no integer literal > 9 and no single-letter colour string literal
                  (a crude proxy for 'not tied to one board's coordinates or colours').
Token cost of a definition = len(source)/4 (approximation; no tokenizer for this model here).

Usage: python helper_reuse.py TRANSCRIPT_DIR BENCHMARK_JSON
"""
from __future__ import annotations

import ast
import collections
import io
import json
import re
import sys
import tokenize
from pathlib import Path

CODE = re.compile(r"<parameter=code>\n?(.*?)</parameter>", re.S)


def functions(code: str):
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            src = ast.get_source_segment(code, node) or ""
            n = ast.parse(ast.unparse(node)).body[0]
            n.name = "_"
            for a in n.args.args + n.args.kwonlyargs:
                a.arg = "_"
            out.append((node.name, ast.dump(n, annotate_fields=False), src))
    return out


def norm_tokens(src: str) -> frozenset:
    toks = []
    try:
        for t in tokenize.generate_tokens(io.StringIO(src).readline):
            if t.type == tokenize.NAME:
                toks.append("ID" if t.string not in KEEP else t.string)
            elif t.type in (tokenize.OP, tokenize.NUMBER):
                toks.append(t.string)
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return frozenset()
    return frozenset(zip(toks, toks[1:]))  # token bigrams


KEEP = {"def", "return", "for", "in", "if", "else", "elif", "while", "range", "len", "and", "or", "not",
        "None", "True", "False", "import", "from", "lambda", "yield", "with", "as", "try", "except"}


def generic(src: str) -> bool:
    if re.search(r"\b(?:[1-9]\d+)\b", src):
        return False
    if re.search(r"""['"][A-Za-z]['"]""", src):
        return False
    return True


def main(tdir: str, bench: str) -> None:
    runs = json.load(open(bench))["game_runs"]
    tokens_by_run = {}
    for r in runs:
        m = re.search(r"tokens=(\d+)", r.get("solver_note") or "")
        p = re.search(r"_p(\d+)\.html", r["solver_analysis_html"]).group(1)
        tokens_by_run[f"{r['game_id']}_p{p}"] = int(m.group(1)) if m else 0
    defs = []   # (game, run, name, exact_key, src)
    calls = 0
    for f in sorted(Path(tdir).glob("*.txt")):
        run = f.stem
        game = run.split("-")[0]
        text = f.read_text(errors="replace")
        for code in CODE.findall(text):
            calls += 1
            for name, key, src in functions(code):
                defs.append((game, run, name, key, src))
    print(f"transcripts={len(list(Path(tdir).glob('*.txt')))} python calls={calls} function definitions={len(defs)}")
    total_def_tok = sum(len(d[4]) / 4 for d in defs)
    total_gen = sum(tokens_by_run.values())
    print(f"definition tokens (chars/4)={total_def_tok:,.0f}; all generated tokens (solver totals)={total_gen:,}; "
          f"share={total_def_tok / total_gen:.4f}")

    # within-run redefinitions (same exact key defined again in the same run)
    first_in_run = set()
    redefs = 0
    redef_tok = 0.0
    for g, run, name, key, src in defs:
        if (run, key) in first_in_run:
            redefs += 1
            redef_tok += len(src) / 4
        else:
            first_in_run.add((run, key))
    print(f"within-run exact redefinitions={redefs} tokens={redef_tok:,.0f} share_of_all_generated={redef_tok / total_gen:.4f}")

    # cross-game: unique (run, key) definitions; is the same exact key present in another GAME?
    uniq = {}
    for g, run, name, key, src in defs:
        uniq.setdefault((run, key), (g, name, src))
    games_by_key = collections.defaultdict(set)
    for (run, key), (g, name, src) in uniq.items():
        games_by_key[key].add(g)
    cross_exact = [(run, key) for (run, key), (g, n, s) in uniq.items() if len(games_by_key[key] - {g}) > 0]
    tok_cross_exact = sum(len(uniq[k][2]) / 4 for k in cross_exact)
    print(f"unique per-run definitions={len(uniq)}; exact duplicate in another game={len(cross_exact)} "
          f"({len(cross_exact) / len(uniq):.3f}); tokens={tok_cross_exact:,.0f} share_of_all_generated={tok_cross_exact / total_gen:.4f}")

    # near-duplicates across games (bigram Jaccard >= 0.8): every unique definition against all
    # definitions of other games, through an inverted index over bigrams.
    items = [(uniq[k][0], uniq[k][1], uniq[k][2], norm_tokens(uniq[k][2])) for k in uniq]
    index = collections.defaultdict(set)
    for i, (_, _, _, ts) in enumerate(items):
        for t in ts:
            index[t].add(i)
    near = 0
    near_tok = 0.0
    for i, (g, name, src, ts) in enumerate(items):
        if len(ts) < 5:
            continue
        cand = collections.Counter()
        for t in ts:
            for j in index[t]:
                if j != i and items[j][0] != g:
                    cand[j] += 1
        hit = False
        need = 0.8 * len(ts)          # Jaccard >= 0.8 implies |A & B| >= 0.8 |A|: exact pre-filter, no top-N cut
        for j, inter in cand.items():
            if inter < need:
                continue
            union = len(ts) + len(items[j][3]) - inter
            if union and inter / union >= 0.8:
                hit = True
                break
        if hit:
            near += 1
            near_tok += len(src) / 4
    print(f"near-duplicate (bigram Jaccard>=0.8) in another game={near} ({near / len(items):.3f}); "
          f"tokens={near_tok:,.0f} share_of_all_generated={near_tok / total_gen:.4f}")
    gen = sum(1 for _, _, s, _ in items if generic(s))
    print(f"generic by proxy={gen} ({gen / len(items):.3f})")
    names = collections.Counter(n for _, n, _, _ in items)
    print("most common helper names:", names.most_common(25))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
