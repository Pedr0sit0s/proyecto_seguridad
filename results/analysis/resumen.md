# Resultados del experimento (regenerado)

Cifras de `analyze_final.py` sobre los `.jsonl` vigentes en `results/`. ASR = fraccion de ataques con efecto real. IC 95% por bootstrap sobre ataques.

## Ataques por defensa

| Modelo | Def. | n | ASR efectivo [IC95%] | ASR intento [IC95%] |
|---|---|---|---|---|
| gpt-4o-mini | D0 | 240 | 30.4% [13.3%, 47.5%] | 30.4% [14.2%, 46.7%] |
| gpt-4o-mini | D1 | 240 | 0.0% [0.0%, 0.0%] | 0.0% [0.0%, 0.0%] |
| gpt-4o-mini | D2 | 240 | 5.4% [1.7%, 10.0%] | 5.4% [1.7%, 10.0%] |
| gpt-4o-mini | D3 | 237 | 0.0% [0.0%, 0.0%] | 0.0% [0.0%, 0.0%] |
| gpt-4o-mini | D5 | 240 | 0.0% [0.0%, 0.0%] | 29.6% [13.8%, 46.7%] |
| gpt-4o-mini | D6 | 230 | 0.0% [0.0%, 0.0%] | 0.0% [0.0%, 0.0%] |
| gpt-4o-mini | D7 | 240 | 0.0% [0.0%, 0.0%] | 0.0% [0.0%, 0.0%] |
| gpt-6-luna | D0 | 120 | 35.8% [23.3%, 48.3%] | 35.8% [22.5%, 49.2%] |
| gpt-6-luna | D1 | 120 | 0.0% [0.0%, 0.0%] | 0.0% [0.0%, 0.0%] |
| gpt-6-luna | D2 | 120 | 20.0% [8.3%, 32.5%] | 20.0% [8.3%, 33.3%] |
| gpt-6-luna | D3 | 120 | 0.0% [0.0%, 0.0%] | 0.0% [0.0%, 0.0%] |
| gpt-6-luna | D5 | 120 | 0.0% [0.0%, 0.0%] | 29.2% [20.0%, 39.2%] |
| gpt-6-luna | D6 | 120 | 0.0% [0.0%, 0.0%] | 0.0% [0.0%, 0.0%] |
| gpt-6-luna | D7 | 120 | 0.0% [0.0%, 0.0%] | 0.0% [0.0%, 0.0%] |

## Casos legitimos y costo

| Modelo | Def. | n | OK % | Falsos positivos % | Violaciones | Tokens | Tokens (xD0) |
|---|---|---|---|---|---|---|---|
| gpt-4o-mini | D0 | 120 | 94.2% | 0.0% | 0 | 1525 | x1.0 |
| gpt-4o-mini | D1 | 120 | 96.7% | 0.0% | 0 | 3583 | x2.35 |
| gpt-4o-mini | D2 | 120 | 100.0% | 0.0% | 0 | 1838 | x1.21 |
| gpt-4o-mini | D3 | 120 | 66.7% | 30.0% | 0 | 1500 | x0.98 |
| gpt-4o-mini | D5 | 120 | 96.7% | 0.0% | 0 | 1524 | x1.0 |
| gpt-4o-mini | D6 | 120 | 69.2% | 30.8% | 0 | 3120 | x2.05 |
| gpt-4o-mini | D7 | 120 | 99.2% | 0.0% | 0 | 3662 | x2.4 |
| gpt-6-luna | D0 | 60 | 96.7% | 0.0% | 2 | 2219 | x1.0 |
| gpt-6-luna | D1 | 60 | 100.0% | 0.0% | 0 | 3962 | x1.79 |
| gpt-6-luna | D2 | 60 | 96.7% | 0.0% | 1 | 2676 | x1.21 |
| gpt-6-luna | D3 | 60 | 95.0% | 3.3% | 0 | 2314 | x1.04 |
| gpt-6-luna | D5 | 60 | 100.0% | 0.0% | 0 | 2152 | x0.97 |
| gpt-6-luna | D6 | 60 | 100.0% | 0.0% | 0 | 4366 | x1.97 |
| gpt-6-luna | D7 | 60 | 100.0% | 0.0% | 0 | 4024 | x1.81 |
