# BurgerBot — red-teaming de prompt injection

Agente de pedidos de comida rápida (BurgerBot) usado como banco de pruebas para medir qué tan bien
resiste ataques de prompt injection bajo distintas defensas, y qué tan molestas son esas defensas
para clientes legítimos.

## Instalación

```
pip install -r requirements.txt
```

Variables de entorno (podés poner un `.env` en la raíz, se carga automáticamente):

```
LLM_API_KEY=...
BASE_URL=...        # opcional, endpoint compatible con la API de OpenAI
MODEL=gpt-4o-mini    # opcional, modelo por defecto
```

## Estructura

- `menu.py`, `prompts.py`, `tools.py`, `bot.py` — el agente: menú, prompts de sistema, herramientas
  (`get_menu`, `create_order`, `apply_discount`) y el loop de conversación (`Session`).
- `defenses.py` — las 7 configuraciones de defensa evaluadas (D0 a D7), como combinaciones de:
  prompt reforzado, recordatorio sandwich, spotlighting, clasificador de entrada y validación en código.
- `attacks.py` / `safe_cases.py` — catálogo de ataques de integridad (descuentos y precios manipulados)
  y de conversaciones legítimas de cliente, usadas para medir falsos positivos.
- `evaluation.py` — decide si un ataque tuvo éxito (`effective_violations`, sobre el pedido final) o
  solo fue intentado (`attempted_violations`, sobre las tool calls, aunque el código lo haya bloqueado).
- `run.py` / `run_benign.py` — lanzan los casos en paralelo contra un modelo real y guardan cada
  conversación como una línea JSON en `results/`.
- `chat.py`, `probar_ataque.py`, `probar_luna.py` — scripts sueltos para probar el bot a mano.
- `results/` — salidas de corridas (`.jsonl`) y `results/analysis/resumen.md` con las tablas finales.

## Uso

```
# correr todos los ataques, 10 repeticiones, defensa D0
python run.py --reps 10 --defenses D0 --out results/gpt4omini_D0.jsonl

# solo un par de ataques, para probar rápido
python run.py --ids A02 B02 --reps 1 --out results/prueba.jsonl

# casos legítimos, para medir falsos positivos
python run_benign.py --reps 10 --defenses D0 D1 --out results/benign.jsonl

# chatear a mano con el bot
python chat.py
```

`run.py`/`run_benign.py` son reanudables: si el archivo de salida ya existe, saltan las
combinaciones (ataque, defensa, repetición) ya guardadas sin error.

Los resultados agregados (ASR por defensa, matrices por ataque, falsos positivos, costo en tokens)
están en `results/analysis/resumen.md`.
