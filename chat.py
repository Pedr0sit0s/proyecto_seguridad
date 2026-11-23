import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from tools import TOOL_SCHEMAS, ToolExecutor
from bot import Session

load_dotenv()

MODEL = os.getenv("MODEL", "gpt-4o-mini")
client = OpenAI(
    base_url = os.getenv("BASE_URL"),
    api_key = os.getenv("LLM_API_KEY"),
)

session = Session(client, MODEL)

while True:
    user = input("tu> ")
    if user.strip().lower() == "salir":
        break
    n0 = len(session.executor.calls)
    print(session.send(user))
    #Debugging proceso para analizar mejor
    for c in session.executor.calls[n0:]:
        print(f"[Debugg] llamada: {c['name']} {c['args']}, -> {c['result']}")
    if session.executor.orders:
        print(f"[Debug] pedidos: {session.executor.orders}")