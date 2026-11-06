import json,glob,os,re,sys,statistics as st,collections
out=sys.argv[1]
log_path=os.path.join(out,"arcaid3-probe-first-dfranzen-m2.log")
log=open(log_path).read() if os.path.exists(log_path) else ""
# log may be JSON list of {stream_name,data,time}
txt=log
try:
    j=json.loads(log); txt="".join(e.get("data","") for e in j)
except Exception: pass
print("=== PF / guard / error log lines")
for l in txt.splitlines():
    if re.search(r"ARC3_PF_|ARCAID3|Traceback|Error|error:|benchmark:|mean score|total actions|total tokens|duration|wallclock|won:|runs:", l): print(l[:220])
bj=os.path.join(out,"benchmark.json")
if not os.path.exists(bj): print("no benchmark.json"); sys.exit()
b=json.load(open(bj)); runs=b["game_runs"]
tot_lv=sum(g["number_of_levels"] for g in runs); lc=sum(g["levels_completed"] for g in runs)
ratios=[]; deaths=0; acts=0
for g in runs:
    base=g["base_actions_per_level"]; apl=g["actions_per_level"]; k=g["levels_completed"]
    for i in range(k):
        if base[i]: ratios.append(apl[i]/base[i])
    acts+=sum(apl)
    resets=sum(1 for h in g.get("history") or [] if isinstance(h.get("action"),dict) and str(h["action"].get("id")).startswith("RESET"))
    deaths+=max(0,resets-1)   # first RESET of a game starts it
print(f"\n=== benchmark: games {len(runs)} levels cleared {lc}/{tot_lv} actions {acts} mean score {st.mean(g['final_score'] for g in runs):.2f}")
for g in runs: print(f"  {g['game_id'][:4]} {g['levels_completed']}/{g['number_of_levels']} score={g['final_score']:.1f} acts={g['actions_per_level']} base={g['base_actions_per_level']} state={g.get('state')}")
print(f"median a/h on cleared levels {st.median(ratios):.2f} (n={len(ratios)}, >0.93: {sum(r>0.93 for r in ratios)}) | deaths (RESET beyond the first) {deaths}")
# request logs
cls=collections.Counter(); tok=collections.Counter(); trunc=0; resp=0; comp=0; prompt=0; cached=0
for f in glob.glob(os.path.join(out,"*_p0_requests.jsonl")):
    prev=0
    for line in open(f):
        try:r=json.loads(line)
        except: continue
        if r.get("event")!="response": continue
        u=r.get("usage") or {}; a=r.get("action") or 0; ct=u.get("completion_tokens",0)
        resp+=1; comp+=ct; prompt+=u.get("prompt_tokens",0); cached+=(u.get("prompt_tokens_details") or {}).get("cached_tokens",0)
        if r.get("finish_reason")=="length": trunc+=1
        k="acted" if a>prev else "no-action"; cls[k]+=1; tok[k]+=ct; prev=a
if resp:
    print(f"responses {resp}: no-action {cls['no-action']} ({cls['no-action']/resp:.0%}) | no-action token share {tok['no-action']/max(1,comp):.0%} | truncated (finish=length) {trunc} | completion tokens {comp} | cache hit {cached/max(1,prompt):.3f} | tokens/action {comp/max(1,acts):.0f}")
    # requests sent with the cap: look for max_tokens in request payloads
    capped=0
    for f in glob.glob(os.path.join(out,"*_p0_requests.jsonl")):
        for line in open(f):
            if '"max_tokens": 4096' in line: capped+=1
    print("request lines containing max_tokens 4096:",capped)
else: print("no request logs found")
print("start",b.get("start_time"),"end",b.get("end_time"))
