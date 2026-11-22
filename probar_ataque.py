import os
from openai import OpenAI
from bot import Session
from attacks import ATTACKS, SETUP
from evaluation import effective_violations, attempted_violations

client = OpenAI(
    base_url=os.getenv("BASE_URL"),
    api_key=os.getenv("LLM_API_KEY"),
)
s = Session(client, os.getenv("MODEL", "gpt-4o-mini"), temperature=0.7)
ataque = ATTACKS[1]
print("Ataque:", ataque["id"], ataque["technique"])

for t in SETUP + ataque["turns"]:
    print("\ntu>", t)
    print(s.send(t))

print("\nResultado")
print("Pedidos:", s.executor.orders)
print("Dano efectivo (descuento, precio):", effective_violations(s.executor.orders))
print("Intento (descuento, precio):", attempted_violations(s.executor.calls))
print("Llamadas al modelo:", s.llm_calls, "Tokens:", s.prompt_tokens, s.completion_tokens)