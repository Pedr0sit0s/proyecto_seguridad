"""Ejecuta lista decidida de ataques contra el agente de BurgerBot, los realiza varias veces y guarda los resultados
Uso:
    python run.py --dry-run #Solo cuenta cuantas conversaciones son en total
    python run.py --ids A02 B02 --reps 1 --out results/prueba.jsonl
    python run.py --reps 10 --out results/gpt4omini.jsonl

"""

import argparse
import json
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from dotenv import load_dotenv

from attacks import ATTACKS, SETUP
from bot import Session
from evaluation import attempted_violations, effective_violations
from defenses import DEFENSES

load_dotenv()

def run_one(client, model, temperature, attack, rep, defense, reasoning_effort=None):
    """Ejecuta una conversacion de ataque y evalua resultado"""
    s = Session(client, model, defense=DEFENSES[defense], temperature=temperature, reasoning_effort=reasoning_effort)
    replies, error, setup_ok = [], None, False
    t0 = time.time()
    try:
        for turn in SETUP:
            s.send(turn)
        setup_ok = bool(s.executor.orders)
        for turn in attack["turns"]:
            replies.append(s.send(turn))
    except Exception as e:
        error = f"{type(e).__name__}: {e}"
    eff_d, eff_p = effective_violations(s.executor.orders)
    att_d, att_p = attempted_violations(s.executor.calls)
    kind = attack["success"]
    return {
        "item_id": attack["id"], "technique": attack["technique"], "objective": attack["objective"],
        "success_type": kind, "defense": defense, "model": model, "temperature": temperature,
        "rep": rep, "setup_ok": setup_ok, "replies": replies,
        "tool_calls": s.executor.calls, "orders": s.executor.orders,
        "eff_discount": eff_d, "eff_price": eff_p, "att_discount": att_d, "att_price": att_p,
        "success": eff_d if kind == "discount" else eff_p,
        "attempted": att_d if kind == "discount" else att_p,
        "prompt_tokens": s.prompt_tokens, "completion_tokens": s.completion_tokens,
        "llm_calls": s.llm_calls, "latency_s": round(time.time() - t0, 2), "error": error, "blocked": s.blocked,
        "reasoning_effort": reasoning_effort
    }

def load_done(path):
    """Conveersaciones guardads"""
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

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", default=os.getenv("MODEL", "gpt-4o-mini"))
    ap.add_argument("--temperature", type=float, default=0.7)
    ap.add_argument("--ids", nargs="*", help="solo estos ataques, por ejemplo A02 B01")
    ap.add_argument("--reps", type=int, default=10, help="repeticiones por atauqe")
    ap.add_argument("--workers", type=int, default=4, help="Conversaciones en paralelo")
    ap.add_argument("--out", default="results/resultados.jsonl")
    ap.add_argument("--dry-run", action="store_true", help="solo contar")
    ap.add_argument("--defenses", nargs="+", default=["D0"], choices=list(DEFENSES))
    ap.add_argument("--reasoning-effort", default=None, choices=["none", "low", "medium", "high"])
    args = ap.parse_args()

    attacks = [a for a in ATTACKS if not args.ids or a["id"] in args.ids]
    done = load_done(args.out)
    tasks = [(a, d, r) for a in attacks for d in args.defenses for r in range(args.reps) if (a["id"], d, r) not in done]
    print(f"Modelo: {args.model} | temperatura: {args.temperature} | ataques: {len(attacks)} | reps: {args.reps}")
    print(f"Conversaciones planificadas: {len(attacks) * len(args.defenses) * args.reps} | ya hechas: {len(done)} | por ejecutar: {len(tasks)}")
    if args.dry_run or not tasks:
        return

    from openai import OpenAI
    client  = OpenAI(base_url=os.getenv("BASE_URL"), api_key=os.getenv("LLM_API_KEY"), max_retries=6)
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    lock, n_ok, n_err, t0 = threading.Lock(), 0, 0, time.time()
    with open(args.out, "a", encoding="utf-8") as out, ThreadPoolExecutor(args.workers) as pool:
        futures = [pool.submit(run_one, client, args.model, args.temperature, a, r, d, args.reasoning_effort) for a, d, r in tasks]
        for i, fut in enumerate(as_completed(futures), 1):
            rec = fut.result()
            with lock:
                out.write(json.dumps(rec, ensure_ascii=False) + "\n")
                out.flush()
            n_err += bool(rec["error"])
            n_ok += not rec["error"]
            if i % 10 == 0 or i == len(tasks):
                mins = (time.time() - t0) / 60
                print(f"  {i}/{len(tasks)} errores={n_err} transcurrido={mins:.1f} min ETA={mins / i * (len(tasks) - i):.1f} min", flush=True)
    print(f"Listo. Resultados en {args.out}")

if __name__ == "__main__":
    main()
