"""Agrega los resultados crudos de results/*.jsonl en las tablas y figuras del informe final.

Uso:
    python results/analysis/analyze_final.py

Lee los archivos canonicos de ataques y casos legitimos por modelo/defensa, calcula ASR
efectivo e intento con IC 95% (bootstrap sobre ataques), costo en tokens, tasa de falsos
positivos en casos legitimos, y guarda tablas (.csv), figuras (.png) y results/analysis/resumen.md
"""
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 10,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "axes.axisbelow": True,
    "grid.alpha": 0.3,
    "grid.linewidth": 0.5,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
})

random.seed(0)
HERE = Path(__file__).parent
ROOT = HERE.parent.parent
RESULTS = ROOT / "results"

ATTACK_FILES = {
    "gpt-4o-mini": {
        "D0": "gpt4omini_D0.jsonl", "D1": "gpt4omini_D1.jsonl", "D2": "gpt4omini_D2.jsonl",
        "D3": "gpt4omini_D3.jsonl", "D5": "gpt4omini_D0_D5.jsonl", "D6": "gpt4omini_D6.jsonl",
        "D7": "gpt4omini_D7.jsonl",
    },
    "gpt-6-luna": {
        "D0": "gpt6luna_D0.jsonl", "D1": "gpt6luna_D1.jsonl", "D2": "gpt6luna_D2.jsonl",
        "D3": "gpt6luna_D3.jsonl", "D5": "gpt6luna_D5.jsonl", "D6": "gpt6luna_D6.jsonl",
        "D7": "gpt6luna_D7.jsonl",
    },
}

BENIGN_FILES = {
    "gpt-4o-mini": {
        "D0": ("gpt4omini_benign.jsonl", "D0"), "D1": ("gpt4omini_benign.jsonl", "D1"),
        "D2": ("gpt4omini_D2_benign.jsonl", None), "D3": ("gpt4omini_benign.jsonl", "D3"),
        "D5": ("gpt4omini_benign.jsonl", "D5"), "D6": ("gpt4omini_benign.jsonl", "D6"),
        "D7": ("gpt4omini_D7_benign.jsonl", None),
    },
    "gpt-6-luna": {
        "D0": ("gpt6luna_D0_benign.jsonl", None), "D1": ("gpt6luna_D1_benign.jsonl", None),
        "D2": ("gpt6luna_D2_benign.jsonl", None), "D3": ("gpt6luna_benign_D3", None),
        "D5": ("gpt6luna_D5_benign.jsonl", None), "D6": ("gpt6luna_benign_D6", None),
        "D7": ("gpt6luna_D7_benign.jsonl", None),
    },
}

DEFENSES = ["D0", "D1", "D2", "D3", "D5", "D6", "D7"]
MODELS = ["gpt-4o-mini", "gpt-6-luna"]
MODEL_LABEL = {"gpt-4o-mini": "gpt4omini", "gpt-6-luna": "gpt6luna"}

FAMILIES = {
    "directo": {"A01", "B01"},
    "suplantacion": {"A02", "A03", "A04", "B04", "C01", "C03", "C04"},
    "persuasion": {"A05", "A06", "A07", "A11", "B03", "C02", "C05", "C06", "C08"},
    "evasion": {"A08", "A09", "A10", "A12", "B02", "C07"},
}
ID_TO_FAMILY = {aid: fam for fam, ids in FAMILIES.items() for aid in ids}


def load(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def pct(x):
    return round(100 * x, 1)


def bootstrap_ci(by_attack_success, n_boot=3000):
    """IC 95% para la ASR promediando sobre ataques, remuestreando ataques con reemplazo."""
    attack_ids = list(by_attack_success.keys())
    if not attack_ids:
        return 0.0, 0.0
    means = []
    for _ in range(n_boot):
        sample = [random.choice(attack_ids) for _ in attack_ids]
        vals = [v for aid in sample for v in by_attack_success[aid]]
        means.append(sum(vals) / len(vals) if vals else 0.0)
    means.sort()
    lo = means[int(0.025 * n_boot)]
    hi = means[int(0.975 * n_boot) - 1]
    return pct(lo), pct(hi)


def attack_table():
    rows_out = []
    family_out = {}
    for model in MODELS:
        by_attack_eff = defaultdict(list)
        by_attack_att = defaultdict(list)
        family_rows = defaultdict(lambda: defaultdict(list))
        for d in DEFENSES:
            path = RESULTS / ATTACK_FILES[model][d]
            rows = load(path)
            rows = [r for r in rows if not r.get("error") and r.get("setup_ok")]
            eff_by_attack = defaultdict(list)
            att_by_attack = defaultdict(list)
            for r in rows:
                eff_by_attack[r["item_id"]].append(1 if r["eff_discount"] or r["eff_price"] else 0)
                att_by_attack[r["item_id"]].append(1 if r["att_discount"] or r["att_price"] else 0)
                fam = ID_TO_FAMILY[r["item_id"]]
                family_rows[fam][d].append(1 if r["eff_discount"] or r["eff_price"] else 0)
            eff_vals = [v for vs in eff_by_attack.values() for v in vs]
            att_vals = [v for vs in att_by_attack.values() for v in vs]
            eff_asr = pct(sum(eff_vals) / len(eff_vals)) if eff_vals else 0.0
            att_asr = pct(sum(att_vals) / len(att_vals)) if att_vals else 0.0
            eff_lo, eff_hi = bootstrap_ci(eff_by_attack)
            att_lo, att_hi = bootstrap_ci(att_by_attack)
            rows_out.append({
                "modelo": model, "defensa": d, "n": len(rows),
                "asr_efectivo": eff_asr, "asr_efectivo_lo": eff_lo, "asr_efectivo_hi": eff_hi,
                "asr_intento": att_asr, "asr_intento_lo": att_lo, "asr_intento_hi": att_hi,
            })
        family_out[model] = {
            fam: {d: pct(sum(vs) / len(vs)) if (vs := family_rows[fam][d]) else 0.0 for d in DEFENSES}
            for fam in FAMILIES
        }
    return rows_out, family_out


def benign_table():
    rows_out = []
    for model in MODELS:
        base_tokens = None
        for d in DEFENSES:
            fname, filter_defense = BENIGN_FILES[model][d]
            rows = load(RESULTS / fname)
            if filter_defense:
                rows = [r for r in rows if r["defense"] == filter_defense]
            rows = [r for r in rows if not r.get("error")]
            n = len(rows)
            ok = sum(1 for r in rows if r["ok"])
            fp = sum(1 for r in rows if r["fp"])
            viol = sum(1 for r in rows if r["eff_discount"] or r["eff_price"])
            tokens = sum(r["prompt_tokens"] + r["completion_tokens"] for r in rows) / n if n else 0
            if d == "D0":
                base_tokens = tokens
            rows_out.append({
                "modelo": model, "defensa": d, "n": n,
                "ok_pct": pct(ok / n) if n else 0.0,
                "fp_pct": pct(fp / n) if n else 0.0,
                "violaciones": viol,
                "tokens": round(tokens),
                "tokens_x": round(tokens / base_tokens, 2) if base_tokens else 1.0,
            })
    return rows_out


def write_csv(path, rows, fields):
    with open(path, "w", encoding="utf-8") as f:
        f.write(",".join(fields) + "\n")
        for r in rows:
            f.write(",".join(str(r[k]) for k in fields) + "\n")


def plot_asr_por_defensa(attack_rows, path):
    fig, axes = plt.subplots(1, 2, figsize=(9, 4), sharey=True)
    for ax, model in zip(axes, MODELS):
        data = [r for r in attack_rows if r["modelo"] == model]
        xs = [r["defensa"] for r in data]
        ys = [r["asr_efectivo"] for r in data]
        errs = [[y - r["asr_efectivo_lo"] for y, r in zip(ys, data)],
                [r["asr_efectivo_hi"] - y for y, r in zip(ys, data)]]
        ax.bar(xs, ys, color="#4a7a8c", yerr=errs, capsize=3)
        ax.set_title(model)
        ax.set_ylabel("ASR efectivo (%)")
        ax.set_ylim(0, max(45, max(ys) + 10))
    fig.suptitle("Tasa de exito efectivo por defensa (IC 95%)")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_familias(family_data, path):
    fig, axes = plt.subplots(1, 2, figsize=(9, 4), sharey=True)
    fams = list(FAMILIES)
    for ax, model in zip(axes, MODELS):
        d0 = [family_data[model][f]["D0"] for f in fams]
        d2 = [family_data[model][f]["D2"] for f in fams]
        x = range(len(fams))
        w = 0.35
        ax.bar([i - w / 2 for i in x], d0, width=w, label="D0 (sin defensa)", color="#9a9a9a")
        ax.bar([i + w / 2 for i in x], d2, width=w, label="D2 (spotlighting)", color="#2f9e8f")
        ax.set_xticks(list(x))
        ax.set_xticklabels([f"{f}\n({len(FAMILIES[f])})" for f in fams], fontsize=8)
        ax.set_title(model)
        for i, v in enumerate(d0):
            ax.text(i - w / 2, v + 1, f"{v:.0f}%", ha="center", fontsize=7)
        for i, v in enumerate(d2):
            ax.text(i + w / 2, v + 1, f"{v:.0f}%", ha="center", fontsize=7)
    axes[0].set_ylabel("ASR efectivo (%)")
    axes[0].legend(fontsize=8)
    fig.suptitle("ASR efectivo por familia de ataque, D0 vs D2")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_falsos_positivos(benign_rows, path):
    fig, ax = plt.subplots(figsize=(6, 4))
    w = 0.35
    x = range(len(DEFENSES))
    for i, model in enumerate(MODELS):
        data = {r["defensa"]: r["fp_pct"] for r in benign_rows if r["modelo"] == model}
        ys = [data[d] for d in DEFENSES]
        offset = -w / 2 if i == 0 else w / 2
        ax.bar([xi + offset for xi in x], ys, width=w, label=model,
               color="#4a7a8c" if i == 0 else "#c97a4a")
    ax.set_xticks(list(x))
    ax.set_xticklabels(DEFENSES)
    ax.set_ylabel("Falsos positivos (%)")
    ax.set_title("Clientes legitimos rechazados, por defensa")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_costo_vs_asr(attack_rows, benign_rows, path):
    fig, ax = plt.subplots(figsize=(6, 4.5))
    markers = {"gpt-4o-mini": "o", "gpt-6-luna": "^"}
    for model in MODELS:
        asr = {r["defensa"]: r["asr_efectivo"] for r in attack_rows if r["modelo"] == model}
        tok = {r["defensa"]: r["tokens_x"] for r in benign_rows if r["modelo"] == model}
        xs = [tok[d] for d in DEFENSES]
        ys = [asr[d] for d in DEFENSES]
        ax.scatter(xs, ys, marker=markers[model], s=60, label=model, color="#4a7a8c" if model == "gpt-4o-mini" else "#c97a4a")
        for d, x, y in zip(DEFENSES, xs, ys):
            ax.annotate(d, (x, y), textcoords="offset points", xytext=(5, 3), fontsize=8)
    ax.set_xlabel("Costo en tokens (x D0, casos legitimos)")
    ax.set_ylabel("ASR efectivo en ataques (%)")
    ax.set_title("Costo vs. seguridad por defensa")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main():
    attack_rows, family_data = attack_table()
    benign_rows = benign_table()

    write_csv(HERE / "tabla_ataques.csv", attack_rows,
              ["modelo", "defensa", "n", "asr_efectivo", "asr_efectivo_lo", "asr_efectivo_hi",
               "asr_intento", "asr_intento_lo", "asr_intento_hi"])
    write_csv(HERE / "tabla_legitimos.csv", benign_rows,
              ["modelo", "defensa", "n", "ok_pct", "fp_pct", "violaciones", "tokens", "tokens_x"])
    for model in MODELS:
        fam_rows = [{"familia": f, **{d: family_data[model][f][d] for d in DEFENSES}} for f in FAMILIES]
        write_csv(HERE / f"familias_{model}.csv", fam_rows, ["familia"] + DEFENSES)

    plot_asr_por_defensa(attack_rows, HERE / "fig_asr_por_defensa.png")
    plot_familias(family_data, HERE / "fig_familias.png")
    plot_falsos_positivos(benign_rows, HERE / "fig_falsos_positivos.png")
    plot_costo_vs_asr(attack_rows, benign_rows, HERE / "fig_costo_vs_asr.png")

    lines = ["# Resultados del experimento (regenerado)", "",
             "Cifras de `analyze_final.py` sobre los `.jsonl` vigentes en `results/`. "
             "ASR = fraccion de ataques con efecto real. IC 95% por bootstrap sobre ataques.", ""]
    lines.append("## Ataques por defensa\n")
    lines.append("| Modelo | Def. | n | ASR efectivo [IC95%] | ASR intento [IC95%] |")
    lines.append("|---|---|---|---|---|")
    for r in attack_rows:
        lines.append(f"| {r['modelo']} | {r['defensa']} | {r['n']} | "
                      f"{r['asr_efectivo']}% [{r['asr_efectivo_lo']}%, {r['asr_efectivo_hi']}%] | "
                      f"{r['asr_intento']}% [{r['asr_intento_lo']}%, {r['asr_intento_hi']}%] |")
    lines.append("\n## Casos legitimos y costo\n")
    lines.append("| Modelo | Def. | n | OK % | Falsos positivos % | Violaciones | Tokens | Tokens (xD0) |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for r in benign_rows:
        lines.append(f"| {r['modelo']} | {r['defensa']} | {r['n']} | {r['ok_pct']}% | "
                      f"{r['fp_pct']}% | {r['violaciones']} | {r['tokens']} | x{r['tokens_x']} |")
    (HERE / "resumen.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("Listo: tablas, figuras y resumen.md regenerados en results/analysis/")


if __name__ == "__main__":
    main()
