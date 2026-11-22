from tools import TOOL_SCHEMAS, ToolExecutor
from prompts import SYSTEM, REINFORCED_RULES, SANDWICH_REMINDER, CLASSIFIER_PROMPT, BLOCKED_REPLY, SPOTLIGHT_RULES
from defenses import DEFENSES
MAX_STEPS = 6

def mark(text):
    """Funcion que reemplaza espacios en blanco con el caracter: ^, para defensa spotlight"""
    return "^".join(text.split())

class Session:
    def __init__(self, client, model, defense=DEFENSES["D0"], system=SYSTEM, temperature=None, reasoning_effort=None):
        if defense.reinforced_prompt:
            system = system + "\n\n" + REINFORCED_RULES
        if defense.spotlighting:
            system = system + "\n\n" + SPOTLIGHT_RULES
        self.client = client
        self.model = model
        self.temperature = temperature
        self.history = [{"role": "system", "content": system}]
        self.executor = ToolExecutor(enforce_rules=defense.code_validation)
        #medicion de tokens por presupuesto, :(
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.llm_calls = 0
        self.defense = defense
        self.blocked = 0
        self.reasoning_effort = reasoning_effort

    def _is_injection(self, user_text):
        """Clasifica el mensaje del cliente. True si es malicioso y False si es un texto normal"""
        kwargs = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": CLASSIFIER_PROMPT},
                {"role": "user", "content": f"<mensaje>{user_text}</mensaje>"}
            ]
        }
        if self.temperature is not None:
            kwargs["temperature"] = 0

        if self.reasoning_effort is not None:
            kwargs["reasoning_effort"] = self.reasoning_effort
        
        resp = self.client.chat.completions.create(**kwargs)
        #Costo de tokens de clasificador, se suma al total
        self.llm_calls += 1
        usage = getattr(resp, "usage", None)
        if usage is not None:
            self.prompt_tokens += usage.prompt_tokens or 0
            self.completion_tokens += usage.completion_tokens or 0
        verdict = (resp.choices[0].message.content or "").strip().upper()
        return not verdict.startswith("SAFE")

    def send(self, user_text):
        """Envia mensaje del user y devuelve la respuesta de texto del agente"""
        #Defensa de filtracion y clasificacion de respuestas del usuaraio a traves de llamada adicional a modelo
        if self.defense.input_classifier and self._is_injection(user_text):
            self.blocked += 1
            return BLOCKED_REPLY

        if self.defense.spotlighting:
            user_text = mark(user_text)

        #Defensa Sandwich recordatorio del sistema desues de cada respuesta del usuario D1
        if self.defense.sandwich:
            user_text = user_text + "\n\n" + SANDWICH_REMINDER
        self.history.append({"role": "user", "content": user_text})
        msg = None
        for i in range(MAX_STEPS):
            kwargs = {"model": self.model, "messages": self.history, "tools": TOOL_SCHEMAS}
            if self.temperature is not None:
                kwargs["temperature"] = self.temperature
            if self.reasoning_effort is not None:
                kwargs["reasoning_effort"] = self.reasoning_effort
            resp = self.client.chat.completions.create(**kwargs)
            #Operacione spara calcular costo
            self.llm_calls += 1
            usage = getattr(resp, "usage", None)
            if usage is not None:
                self.prompt_tokens += usage.prompt_tokens or 0
                self.completion_tokens += usage.completion_tokens or 0

            msg = resp.choices[0].message
            if not msg.tool_calls:
                break
            #Agregar mensaje al historial de contexto de uso de herramientas
            self.history.append({
                "role": "assistant",
                "content": msg.content,
                "tool_calls": [
                    {"id": c.id, "type": "function", "function": {"name": c.function.name, "arguments": c.function.arguments}} for c in msg.tool_calls
                ]
            })
            #Ejecucion de tools
            for c in msg.tool_calls:
                result = self.executor.execute(c.function.name, c.function.arguments)
                self.history.append({"role": "tool", "tool_call_id": c.id, "content": result})
        answer = (msg.content if msg else None) or "(No hubo respuesta)"
        self.history.append({"role": "assistant", "content": answer})
        return answer