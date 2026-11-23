import os
from dotenv import load_dotenv
from openai import OpenAI
from tools import TOOL_SCHEMAS

load_dotenv()
client = OpenAI(base_url=os.getenv("BASE_URL"), api_key=os.getenv("LLM_API_KEY"))
for temp in (0.7, None):
    kw = {"model": "gpt-6-luna",
          "messages": [{"role": "user", "content": "Muestrame el menu"}],
          "tools": TOOL_SCHEMAS, "reasoning_effort": "none"}
    if temp is not None:
        kw["temperature"] = temp
    try:
        r = client.chat.completions.create(**kw)
        m = r.choices[0].message
        print(temp, "OK", [c.function.name for c in (m.tool_calls or [])], (m.content or "")[:60])
    except Exception as e:
        print(temp, "ERROR", type(e).__name__, str(e)[:200])