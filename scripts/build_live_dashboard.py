"""Regenerate deliverables/PRISM_Live_Dashboard.html.

Reads live progress from the iteration-17 (Gemma) and iteration-19
(Qwen/Llama) caches, token meters, and the $9 spend guard, plus a static
detailed record of prior experiments, and writes one self-contained HTML
page with a 30-second meta-refresh. Safe to run at any time; every input
is optional (missing files render as 'not started').

Called automatically by crossfamily_transfer.py on every save (~200 calls);
can also be run by hand:  python scripts/build_live_dashboard.py
"""

import csv
import html
import json
import os
import time

ROOT = os.path.join(os.path.dirname(__file__), "..")
OUT_HTML = os.path.join(ROOT, "deliverables", "PRISM_Live_Dashboard.html")
CAP_USD = 9.00
TOTAL_CELLS = 3840


def cache_rows(path):
    if not os.path.exists(path):
        return 0
    with open(path, encoding="utf-8", errors="replace") as f:
        return max(0, sum(1 for _ in f) - 1)


def usage(path):
    if not os.path.exists(path):
        return {}
    try:
        return list(csv.DictReader(open(path)))[-1]
    except Exception:
        return {}


def report(path):
    if not os.path.exists(path):
        return None
    return open(path, encoding="utf-8", errors="replace").read()


def json_or_none(path):
    if not os.path.exists(path):
        return None
    try:
        return json.load(open(path))
    except Exception:
        return None


def experiment_s_data():
    it23 = os.path.join(ROOT, "experiments", "iteration-23-experiment-s",
                        "results")
    pilot = json_or_none(os.path.join(it23, "pilot_result.json"))
    preflight = json_or_none(os.path.join(it23, "preflight_result.json"))
    orderings = json_or_none(os.path.join(it23, "orderings.json"))
    lock = json_or_none(os.path.join(it23, "model_lock.json"))
    u = usage(os.path.join(it23, "token_usage.csv"))
    guard = json_or_none(os.path.join(it23, "spend_guard.json")) or {}
    main_done = cache_rows(os.path.join(it23, "answer_cache.csv"))
    n_searched = len(orderings.get("searched", [])) if orderings else 0
    main_target = 200 * 100  # (150 random + 50 guided) x 100 questions,
    # the searched arm's target grows as the online search runs
    main_target += n_searched * 100 if orderings else 0
    rep = report(os.path.join(it23, "experiment_s_report.txt"))
    pilot_passed = bool(pilot and pilot.get("passed"))
    preflight_pairs_done = 0
    if pilot_passed and not preflight:
        # pre-flight cells share the cache with the pilot; anything
        # cached beyond the pilot's fixed 200 is pre-flight progress
        preflight_pairs_done = max(0, main_done - 200)
    stages = [
        {"name": "1. Pilot", "done": bool(pilot),
         "detail": (f"accuracy {pilot['accuracy']:.2f} -> "
                    f"{'PASS' if pilot['passed'] else 'FAIL'}")
                   if pilot else "not started"},
        {"name": "2. Pre-flight", "done": bool(preflight),
         "detail": (preflight["h22_forecast_text"] if preflight
                    else (f"running: ~{preflight_pairs_done:,} / "
                         f"~4,400 cells cached"
                         if preflight_pairs_done else "not started")
                    if pilot_passed else "not started")},
        {"name": "3. Main landscape", "done": bool(rep),
         "detail": (f"{max(0, main_done - 201 - preflight.get('n_pairs_per_op', 22) * 4 * 2 * 25):,} "
                    f"/ {main_target:,} cells cached (stage-3 only; "
                    f"total cache incl. pilot+preflight: {main_done:,})"
                    if orderings and preflight else "not started")},
        {"name": "4. Analysis", "done": bool(rep),
         "detail": "STUDY COMPLETE" if rep else "pending stage 3"},
    ]
    return {
        "model": lock["model"] if lock else "not yet locked",
        "cap": guard.get("cap_usd", 10.0),
        "spend": guard.get("reported_usd", 0.0),
        "calls": u.get("calls", "0"),
        "stages": stages,
        "report": rep,
        "pilot_failed": bool(pilot and not pilot["passed"]),
    }


def experiment_t_data():
    it24 = os.path.join(ROOT, "experiments",
                        "iteration-24-prompt-optimizer-baselines", "results")
    summary = json_or_none(os.path.join(it24, "T_RESULTS_SUMMARY.json"))
    state = json_or_none(os.path.join(it24, "state.json")) or {}
    done = set(state.get("stages_done", []))
    u = usage(os.path.join(it24, "token_usage.csv"))
    guard = json_or_none(os.path.join(it24, "spend_guard.json")) or {}
    complete = bool(summary) and "C" in done
    if summary:
        a1 = summary["A1"]
        h25 = summary["H25"]
        h26 = summary["H26"]
        b = summary["B_search"]
        sweep = summary["A2_A3_sweep"]
        a1_detail = (f"orig train {a1['orig_train_acc']:.3f} -> best "
                     f"optimized {a1['best_opt_train_acc']:.3f} "
                     f"(round {a1['best_round']})")
        a23_detail = (f"orig-wording std {sweep['original_wording']['std']:.3f} "
                      f"vs opt-wording std "
                      f"{sweep['optimized_wording']['std']:.3f}; "
                      f"level lift +{sweep['paired_level_lift_mean']:.3f} "
                      f"CI [{sweep['paired_level_lift_ci'][0]:+.3f},"
                      f"{sweep['paired_level_lift_ci'][1]:+.3f}]")
        b_detail = (f"PRISM {b['prism_best'][0]:.3f} "
                    f"[{b['prism_best'][1]:.3f},{b['prism_best'][2]:.3f}] vs "
                    f"OPRO {b['opro_best'][0]:.3f} "
                    f"[{b['opro_best'][1]:.3f},{b['opro_best'][2]:.3f}] @ "
                    f"budget {b['budget']}")
        c_detail = (f"H25 (complementarity) {h25['verdict']} "
                    f"(ratio {h25['ratio']}); H26 (search) {h26['verdict']}")
    else:
        a1_detail = a23_detail = b_detail = c_detail = "not started"
    stages = [
        {"name": "A1. OPRO wording opt", "done": "A1" in done,
         "detail": a1_detail if "A1" in done else "running"},
        {"name": "A2/A3. Ordering sweeps", "done": "A3" in done,
         "detail": a23_detail if "A3" in done else
                   ("running" if "A1" in done else "queued")},
        {"name": "B. PRISM vs OPRO search", "done": "B" in done,
         "detail": b_detail if "B" in done else
                   ("running" if "A3" in done else "queued")},
        {"name": "C. Analysis", "done": "C" in done,
         "detail": c_detail if complete else "pending stage B"},
    ]
    return {
        "model": (summary["target_model"] if summary
                  else "meta-llama/llama-3.1-8b-instruct"),
        "optimizer": (summary["optimizer_model"] if summary
                      else "gemini-2.5-flash-lite"),
        "cap": guard.get("cap_usd", 5.0),
        "spend": guard.get("reported_usd", 0.0),
        "calls": u.get("calls", "0"),
        "stages": stages,
        "complete": complete,
        "report": (summary and complete and
                   "H25 (ordering-content complementarity): HOLDS -- after "
                   "OPRO rewrites all 8 module wordings (train "
                   f"{summary['A1']['orig_train_acc']:.3f}->"
                   f"{summary['A1']['best_opt_train_acc']:.3f}; held-out level "
                   f"lift +{summary['A2_A3_sweep']['paired_level_lift_mean']:.3f}"
                   ", CI excludes zero), ordering-driven std is undiminished "
                   f"(opt {summary['H25']['opt_std']:.3f} vs orig "
                   f"{summary['H25']['orig_std']:.3f}, ratio "
                   f"{summary['H25']['ratio']}). Ordering and content "
                   "optimization are complementary axes.\n"
                   "H26 (search vs generic LLM optimizer): statistical tie, "
                   "NOT falsified -- PRISM best-found @25 "
                   f"{summary['B_search']['prism_best'][0]:.3f} vs OPRO "
                   f"{summary['B_search']['opro_best'][0]:.3f} "
                   f"(diff {summary['B_search']['prism_minus_opro'][0]:+.3f}, "
                   "CI spans zero); PRISM converges faster early, OPRO edges "
                   "past by budget 25.") or "",
    }


def leg_data():
    legs = []
    it17 = os.path.join(ROOT, "experiments", "iteration-17", "results")
    u = usage(os.path.join(it17, "token_usage.csv"))
    legs.append({
        "name": "Gemma 4B-active (Exp. Q, It-17)",
        "model": "gemma-4-26b-a4b-it (Google API)",
        "done": cache_rows(os.path.join(it17, "gemma_answer_cache.csv")),
        "calls": u.get("calls", "0"),
        "cost": f"$0 billed (worst-case ${u.get('usd_worstcase', '?')})",
        "report": report(os.path.join(it17, "slm_transfer_report.txt")),
        "guarded": False,
    })
    it19 = os.path.join(ROOT, "experiments", "iteration-19-crossfamily",
                        "results")
    for leg, model in (("qwen", "qwen/qwen3-30b-a3b-instruct-2507 (3B active)"),
                       ("llama", "meta-llama/llama-3.2-3b-instruct")):
        u = usage(os.path.join(it19, f"{leg}_token_usage.csv"))
        legs.append({
            "name": f"{leg.capitalize()} leg (Exp. Q2, It-19)",
            "model": f"{model} (OpenRouter)",
            "done": cache_rows(os.path.join(it19,
                                            f"{leg}_answer_cache.csv")),
            "calls": u.get("calls", "0"),
            "cost": f"${float(u.get('usd_reported', 0) or 0):.2f} "
                    f"API-reported",
            "report": report(os.path.join(it19,
                                          f"{leg}_transfer_report.txt")),
            "guarded": True,
        })
    guard = {}
    gpath = os.path.join(it19, "spend_guard.json")
    if os.path.exists(gpath):
        guard = json.load(open(gpath))
    return legs, guard


PAST = [
    ("2-3", "A/B", "Do the historical toy results reproduce? How does "
     "hitting time scale?", "Reproduced with caveats; scaling consistent "
     "with O(n^3 log n) to n=16 for matched operators"),
    ("3", "C/D", "Does the mutation operator have to match the landscape "
     "type?", "Yes - 3/3 matches (swap-absolute, insert-precedence, "
     "inversion-adjacency); mismatch = 100% failure on plateau-rich "
     "landscapes; deceptive defeats everything"),
    ("4", "E", "Can a uniform operator portfolio replace landscape "
     "knowledge?", "Yes at 1.1-4.1x matched cost - default for unknown "
     "landscapes (D8)"),
    ("5-6", "F/G", "Deterministic v4 benchmarks + n=6/7 scale-up",
     "Exact ground truth (XOR 100%, parity 40% hit rate); n=6 720 "
     "enumerated, hit rate 0.90"),
    ("7", "I", "Does PRISM beat random on neural landscapes under "
     "distinct-eval budgets?", "NO - H10 falsified; PRISM = random; "
     "landscape locality governs (D12, D13)"),
    ("8", "J", "Do pre-search statistics predict outcomes?", "Yes - rho1 "
     "recovers matched operator 3/3; FDC separates 8/8 outcomes; "
     "pre-flight mandatory (D14)"),
    ("9", "K", "LLM flagship: 720 prompt orderings x 32 GSM8K, "
     "Flash-Lite", "Accuracy 6.3% - 96.9% by ordering alone; pre-flight "
     "predicted operator + outcome; ANSWER-last / COMPUTE-early"),
    ("10", "L", "Does aging evolution fix premature convergence?",
     "48% to 78%, but only to random's level on FDC=0 landscapes (D15)"),
    ("11", "M", "n=8 LLM (40,320 orderings)", "Ordering swings 0.10-1.00; "
     "sampled pre-flight correctly forecast 'random competitive' (D16)"),
    ("12", "N", "Can an encoding-matched surrogate beat the elitist EA?",
     "Yes - kendall n=7 needle: 13.5 vs 55.7 evals; random 0/15 (D17)"),
    ("14", "audit", "40-seed CIs + claims audit", "'3x faster' LLM claim "
     "RETRACTED at 40 seeds (D18); pre-flight reliability 94-99%"),
    ("15", "theory", "Aging-mode theory (Appendix B)", "Almost-sure record "
     "convergence with explicit geometric bound; numerically verified"),
    ("16", "O/P", "Transfer + SciML", "Cross-task transfer ZERO (r=-0.004); "
     "cross-size n6-n8 STRONG (rho 0.665, +17.5-pt warm start); SINDy "
     "pipeline ordering swings recovery error 0.1%-23.2% (D19)"),
    ("18", "R", "Transfer-guided evaluation policy", "Perfect n=8 ordering "
     "by budget 5 (random p=0.248); supporting evidence (D20)"),
    ("17", "Q", "Cross-MODEL transfer Flash-Lite to Gemma-4B",
     "ASYMMETRIC: bottom-avoidance decisive (0.150 vs 0.442, CI "
     "[+0.221,+0.372]); top-15 marginal (+0.123 [+0.008,+0.234]); rank + "
     "position structure do NOT transfer (Spearman 0.158 CI spans 0; "
     "r=0.064)"),
    ("19", "Q2", "Cross-FAMILY transfer (Qwen 3B-active, Llama-3.2-3B)",
     "REPLICATED - Gemma was the outlier: top-ordering advantage "
     "transfers on all 3 families; Llama structure r=0.582; new "
     "moderator = target capability ($0.66 of $9 cap)"),
    ("20", "suite", "SciML pipeline suite: 6 dynamical systems x 720 "
     "orderings", "Ordering effects universal (LV 0.00-1.00 by order "
     "alone); insert wins rho1 6/6; PRISM dominates random 4/6; "
     "near-zero Cayley-FDC under-calls precedence search (proposed D23)"),
    ("21", "H24", "NAS-Bench-201 within-slice search confirmation "
     "(pre-registered)", "13/18 forecasts correct; cifar100+ImageNet16 "
     "HIGH slices 6/6 decisive; misses one-sided (search under-called)"),
    ("22", "ablation", "rho1 vs walk-autocorrelation vs ruggedness as "
     "operator selector", "pair_rho1 best at every budget (0.925 mean "
     "pick accuracy at B=100 vs 0.848/0.915)"),
]

CSS = """
:root{--surface:#fcfcfb;--page:#f9f9f7;--ink:#0b0b0b;--ink2:#52514e;
--muted:#898781;--grid:#e1e0d9;--border:rgba(11,11,11,.10);
--blue:#2a78d6;--blue-track:#cde2fb;--good:#0ca30c;--warn:#fab219;
--crit:#d03b3b;--goodtext:#006300}
@media(prefers-color-scheme:dark){:root{--surface:#1a1a19;--page:#0d0d0d;
--ink:#fff;--ink2:#c3c2b7;--muted:#898781;--grid:#2c2c2a;
--border:rgba(255,255,255,.10);--blue:#3987e5;--blue-track:#104281;
--goodtext:#0ca30c}}
*{box-sizing:border-box;margin:0}
body{font:14px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif;
background:var(--page);color:var(--ink);padding:24px;max-width:1080px;
margin:0 auto}
h1{font-size:20px;margin-bottom:2px}
h2{font-size:15px;margin:28px 0 10px}
.sub{color:var(--ink2);font-size:12px;margin-bottom:20px}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));
gap:12px}
.tile{background:var(--surface);border:1px solid var(--border);
border-radius:10px;padding:14px 16px}
.tile .k{font-size:11px;color:var(--muted);text-transform:uppercase;
letter-spacing:.04em}
.tile .v{font-size:26px;font-weight:650;margin-top:2px}
.tile .d{font-size:12px;color:var(--ink2);margin-top:2px}
.card{background:var(--surface);border:1px solid var(--border);
border-radius:10px;padding:16px;margin-bottom:12px}
.card h3{font-size:14px;margin-bottom:2px}
.card .m{font-size:12px;color:var(--muted);margin-bottom:10px}
.bar{height:10px;border-radius:5px;background:var(--blue-track);
overflow:hidden;margin:6px 0 4px}
.bar>i{display:block;height:100%;border-radius:5px 0 0 5px;
background:var(--blue)}
.bar>i.full{border-radius:5px}
.stats{font-size:12px;color:var(--ink2)}
pre{background:var(--page);border:1px solid var(--grid);border-radius:8px;
padding:12px;font:12px/1.45 ui-monospace,Consolas,monospace;
overflow-x:auto;white-space:pre;color:var(--ink);margin-top:10px}
table{width:100%;border-collapse:collapse;background:var(--surface);
border:1px solid var(--border);border-radius:10px;overflow:hidden;
font-size:12.5px}
th{text-align:left;font-size:11px;color:var(--muted);
text-transform:uppercase;letter-spacing:.04em;padding:9px 12px;
border-bottom:1px solid var(--grid)}
td{padding:9px 12px;border-bottom:1px solid var(--grid);
vertical-align:top;color:var(--ink2)}
td:first-child,td:nth-child(2){white-space:nowrap;color:var(--ink);
font-variant-numeric:tabular-nums}
tr:last-child td{border-bottom:none}
.ok{color:var(--goodtext);font-weight:600}
.badge{display:inline-block;font-size:11px;font-weight:600;
padding:2px 8px;border-radius:99px;border:1px solid var(--border)}
.b-done{color:var(--goodtext)}
.b-run{color:var(--blue)}
.b-wait{color:var(--muted)}
.stage-row{display:flex;gap:10px;flex-wrap:wrap;margin:10px 0}
.stage{flex:1;min-width:160px;border:1px solid var(--border);
border-radius:8px;padding:8px 10px;font-size:12px}
.stage .name{font-weight:600;margin-bottom:3px}
.stage.done{border-color:var(--good);background:color-mix(in srgb,
var(--good) 10%,transparent)}
.stage.fail{border-color:var(--crit);background:color-mix(in srgb,
var(--crit) 10%,transparent)}
.wrap{overflow-x:auto}
footer{color:var(--muted);font-size:11px;margin-top:24px}
"""


def esc(s):
    return html.escape(str(s))


def build():
    legs, guard = leg_data()
    reported = sum((guard.get("reported_usd") or {}).values())
    key_delta = None
    if guard.get("key_usage_latest") is not None and \
            guard.get("key_usage_baseline") is not None:
        key_delta = guard["key_usage_latest"] - guard["key_usage_baseline"]
    total_done = sum(l["done"] for l in legs)
    total_cells = TOTAL_CELLS * len(legs)
    spend_pct = min(100.0, reported / CAP_USD * 100)
    spend_state = ("&#9679; ok", "ok") if reported < CAP_USD * .5 else (
        ("&#9650; nearing cap", "b-run") if reported < CAP_USD * .9
        else ("&#9632; AT CAP", "b-wait"))

    tiles = f"""
<div class="tiles">
 <div class="tile"><div class="k">Overall progress</div>
  <div class="v">{total_done:,} / {total_cells:,}</div>
  <div class="d">answer cells cached across {len(legs)} legs</div></div>
 <div class="tile"><div class="k">OpenRouter spend (hard cap $9)</div>
  <div class="v">${reported:.2f}</div>
  <div class="d"><span class="{spend_state[1]}">{spend_state[0]}</span>
   &nbsp;{spend_pct:.1f}% of cap{
       f" · key meter delta ${key_delta:.2f}" if key_delta is not None
       else ""}</div></div>
 <div class="tile"><div class="k">Cost guard</div>
  <div class="v">2 meters</div>
  <div class="d">per-call API-reported cost + independent key-usage
   endpoint; breach &rarr; clean pause</div></div>
 <div class="tile"><div class="k">Updated</div>
  <div class="v" style="font-size:16px">{time.strftime('%H:%M:%S')}</div>
  <div class="d">{time.strftime('%Y-%m-%d')} · page auto-refreshes
   every 30 s</div></div>
</div>"""

    cards = []
    for l in legs:
        pct = l["done"] / TOTAL_CELLS * 100
        state = ("DONE", "b-done") if l["report"] else (
            ("RUNNING", "b-run") if l["done"] else ("QUEUED", "b-wait"))
        rep = (f"<pre>{esc(l['report'])}</pre>" if l["report"] else "")
        cards.append(f"""
<div class="card"><h3>{esc(l['name'])} &nbsp;<span
  class="badge {state[1]}">{state[0]}</span></h3>
 <div class="m">{esc(l['model'])}</div>
 <div class="bar"><i class="{'full' if pct >= 100 else ''}"
  style="width:{pct:.1f}%"></i></div>
 <div class="stats">{l['done']:,} / {TOTAL_CELLS:,} cells
  ({pct:.1f}%) &nbsp;·&nbsp; {esc(l['calls'])} API calls
  &nbsp;·&nbsp; {esc(l['cost'])}</div>{rep}</div>""")

    es = experiment_s_data()
    es_pct = min(100.0, (es["spend"] / es["cap"] * 100) if es["cap"] else 0)
    es_state = ("FAILED PILOT", "b-wait") if es["pilot_failed"] else (
        ("DONE", "b-done") if es["report"] else
        ("RUNNING", "b-run") if es["spend"] > 0 else ("QUEUED", "b-wait"))
    es_stage_html = "".join(
        f'<div class="stage {"done" if s["done"] else ("fail" if es["pilot_failed"] and s["name"].startswith("1") else "")}">'
        f'<div class="name">{esc(s["name"])}</div>'
        f'<div>{esc(s["detail"])}</div></div>'
        for s in es["stages"])
    es_report_html = (f"<pre>{esc(es['report'])}</pre>" if es["report"]
                      else "")
    es_card = f"""
<div class="card"><h3>Experiment S — Benchmark #2 (MATH-500 hard-reasoning
  landscape) &nbsp;<span class="badge {es_state[1]}">{es_state[0]}</span></h3>
 <div class="m">{esc(es['model'])} · dedicated ${es['cap']:.2f} cap
  (independent of the leg cap above)</div>
 <div class="bar"><i class="{'full' if es_pct >= 100 else ''}"
  style="width:{es_pct:.1f}%"></i></div>
 <div class="stats">${es['spend']:.2f} / ${es['cap']:.2f} spent
  ({es_pct:.1f}%) &nbsp;·&nbsp; {esc(es['calls'])} API calls</div>
 <div class="stage-row">{es_stage_html}</div>{es_report_html}</div>"""

    et = experiment_t_data()
    et_pct = min(100.0, (et["spend"] / et["cap"] * 100) if et["cap"] else 0)
    et_state = ("DONE", "b-done") if et["complete"] else (
        ("RUNNING", "b-run") if et["spend"] > 0 else ("QUEUED", "b-wait"))
    et_stage_html = "".join(
        f'<div class="stage {"done" if s["done"] else ""}">'
        f'<div class="name">{esc(s["name"])}</div>'
        f'<div>{esc(s["detail"])}</div></div>'
        for s in et["stages"])
    et_report_html = (f"<pre>{esc(et['report'])}</pre>" if et["report"]
                      else "")
    et_card = f"""
<div class="card"><h3>Experiment T — Prompt-Optimizer Baselines
  (OPRO vs PRISM) &nbsp;<span class="badge {et_state[1]}">{et_state[0]}</span></h3>
 <div class="m">target {esc(et['model'])} · optimizer {esc(et['optimizer'])}
  · dedicated ${et['cap']:.2f} cap (hand-implemented OPRO, no library)</div>
 <div class="bar"><i class="{'full' if et_pct >= 100 else ''}"
  style="width:{et_pct:.1f}%"></i></div>
 <div class="stats">${et['spend']:.2f} / ${et['cap']:.2f} spent
  ({et_pct:.1f}%) &nbsp;·&nbsp; {esc(et['calls'])} API calls</div>
 <div class="stage-row">{et_stage_html}</div>{et_report_html}</div>"""

    past_rows = "\n".join(
        f"<tr><td>{esc(it)}</td><td>{esc(ex)}</td><td>{esc(q)}</td>"
        f"<td>{esc(res)}</td></tr>"
        for it, ex, q, res in PAST)

    page = f"""<!doctype html><html><head><meta charset="utf-8">
<meta http-equiv="refresh" content="30">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>PRISM Live Dashboard</title><style>{CSS}</style></head><body>
<h1>PRISM — Live Experiment Dashboard</h1>
<div class="sub">Cross-model instruction-ordering transfer
 (Experiments Q / Q2 · benchmark #1 of the top-5 program) ·
 design: 120 orderings &times; 32 GSM8K questions per model, identical
 modules and prompts; source landscape = Experiment K (Gemini
 Flash-Lite, all 720 orderings enumerated)</div>
{tiles}
<h2>Experiment T (Paper-B blocker: prompt-optimizer baselines, approved D27)</h2>
{et_card}
<h2>Experiment S (Benchmark #2, approved D25)</h2>
{es_card}
<h2>Legs (Benchmark #1, complete)</h2>
{''.join(cards)}
<h2>Prior experiments (full record, iterations 2&ndash;22)</h2>
<div class="wrap"><table>
<tr><th>It.</th><th>Exp.</th><th>Question</th><th>Result</th></tr>
{past_rows}
</table></div>
<footer>Generated by scripts/build_live_dashboard.py (invoked on every
 runner save, ~every 200 calls). Raw data:
 experiments/iteration-17/results/ and
 experiments/iteration-19-crossfamily/results/ (caches, token meters,
 spend_guard.json). Spend cap authorized 2026-07-12: $9.00 across both
 OpenRouter legs. Prediction ledger and archival protocol:
 claude prism benchmark recomendation/.</footer>
</body></html>"""
    os.makedirs(os.path.dirname(OUT_HTML), exist_ok=True)
    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write(page)
    print(f"dashboard -> {os.path.abspath(OUT_HTML)}")


if __name__ == "__main__":
    build()
