import argparse
import json
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from dotenv import load_dotenv

from safe_cases import VALID as BENIGN, benign_ok, check_result, false_positive_turns
from bot import Session
from defenses import DEFENSES
from evaluation import effective_violations
from prompts import BLOCKED_REPLY

load_dotenv()

def run_one(client, model, temperature, case, rep, defense, reasoning_effort=None):
    s = Session(client, model, defense=DEFENSES[defense], temperature=temperature, reasoning_effort=reasoning_effort)
    replies, error = [], None
    t0 = time.time()
    try:
        for turn in case["turns"]:
            replies.append(s.send(turn))
    except Exception as e:
        error = f"{type(e).__name__}: {e}"
    blocked_turns = [i for i, r in enumerate(replies) if r == BLOCKED_REPLY]
    fp_turns = false_positive_turns(case, blocked_turns)
    eff_d, eff_p = effective_violations(s.executor.orders)
    return {
        "item_id": case["id"], "kind": "benign", "topic": case["topic"], "defense": defense,
        "model": model, "temperature": temperature, "rep": rep,
        "replies": replies, "tool_calls": s.executor.calls, "orders": s.executor.orders,
        "result_ok": check_result(case, s.executor.orders, replies),
        "fp": bool(fp_turns), "blocked_turns": blocked_turns,
        "ok": benign_ok(case, s.executor.orders, replies, blocked_turns),
        "eff_discount": eff_d, "eff_price": eff_p,
        "prompt_tokens": s.prompt_tokens, "completion_tokens": s.completion_tokens,
        "llm_calls": s.llm_calls, "blocked": s.blocked,
        "latency_s": round(time.time() - t0, 2), "error": error,
        "reasoning_effort": reasoning_effort
    }

def load_done(path):
    done = set()
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for line in f:
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not r.get("error"):
                    done.add((r["item_id"], r["defense"], r["rep"]))
    return done

def _temperature(s):
    """Permite --temperature none para modelos que solo aceptan su temperatura por defecto"""
    return None if s.lower() == "none" else float(s)

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", default=os.getenv("MODEL", "gpt-4o-mini"))
    ap.add_argument("--temperature", type=_temperature, default=0.7)
    ap.add_argument("--ids", nargs="*", help="solo estos ataques, por ejemplo N02 N01")
    ap.add_argument("--reps", type=int, default=10, help="repeticiones por atauqe")
    ap.add_argument("--workers", type=int, default=4, help="Conversaciones en paralelo")
    ap.add_argument("--out", default="results/benign.jsonl")
    ap.add_argument("--dry-run", action="store_true", help="solo contar")
    ap.add_argument("--defenses", nargs="+", default=["D0"], choices=list(DEFENSES))
    ap.add_argument("--reasoning-effort", default=None, choices=["none", "low", "medium", "high"])
    args = ap.parse_args()

    cases = [c for c in BENIGN if not args.ids or c["id"] in args.ids]
    done = load_done(args.out)
    tasks = [(c, d, r) for c in cases for d in args.defenses for r in range(args.reps) if (c["id"], d, r) not in done]
    print(f"Modelo: {args.model} | temperatura: {args.temperature} | casos: {len(cases)} | reps: {args.reps}")
    print(f"Conversaciones planificadas: {len(cases) * len(args.defenses) * args.reps} | ya hechas: {len(done)} | por ejecutar: {len(tasks)}")
    if args.dry_run or not tasks:
        return

    from openai import OpenAI
    client  = OpenAI(base_url=os.getenv("BASE_URL"), api_key=os.getenv("LLM_API_KEY"), max_retries=6)
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    lock, n_err, t0 = threading.Lock(), 0, time.time()
    with open(args.out, "a", encoding="utf-8") as out, ThreadPoolExecutor(args.workers) as pool:
        futures = [pool.submit(run_one, client, args.model, args.temperature, c, r, d, args.reasoning_effort) for c, d, r in tasks]
        for i, fut in enumerate(as_completed(futures), 1):
            rec = fut.result()
            with lock:
                out.write(json.dumps(rec, ensure_ascii=False) + "\n")
                out.flush()
            n_err += bool(rec["error"])
            if i % 10 == 0 or i == len(tasks):
                mins = (time.time() - t0) / 60
                print(f"  {i}/{len(tasks)} errores={n_err} transcurrido={mins:.1f} min ETA={mins / i * (len(tasks) - i):.1f} min", flush=True)
    print(f"Listo. Resultados en {args.out}")

if __name__ == "__main__":
    main()