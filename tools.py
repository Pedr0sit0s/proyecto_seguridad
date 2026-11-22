"""Herramientas de BurgerBot"""

"""Tool Schemas: Funciones y descripcion de lo que puede pedir el modelo"""

import json
#Menu del restaurant
#D5: Validar las reglas del codigo, sin importar lo que diga el modelo
from menu import MENU, VALID_COUPON, MAX_DISCOUNT
"""Modelo solo ve esta descripcion, nombre y parametros para decidir utilizarlos
Funciones:
-get_menu: Sin parametros
-create_order: recibe items: lista de objetos con itemid, cantidad y precio unidad
-apply_discount: recibe id de orden, porcentaje y codigo de descuento"""
TOOL_SCHEMAS = [
    {"type": "function", "function": {
        "name": "get_menu",
        "description": "Devuelve el menu con los ids y precios de cada producto.",
        "parameters": {"type": "object", "properties": {}}
    }},
    {"type": "function", "function": {
        "name": "create_order",
        "description": "Crea un pedido de orden con los productos del menu indicados y devuelve su id y total.",
        "parameters": {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "item_id": {"type": "string"},
                            "quantity": {"type": "integer"},
                            "unit_price": {"type": "integer"}
                        },
                        "required": ["item_id", "quantity", "unit_price"]
                    }
                }
            },
            "required": ["items"]
        }
    }},
    {"type": "function", "function": {
        "name": "apply_discount",
        "description": "Aplica descuento porcentual a pedido existente.",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
                "percent": {"type": "number"},
                "coupon_code": {"type": "string"},
            },
            "required": ["order_id", "percent", "coupon_code"]
        }
    }}
]

"""Ejecucion y codigo de herramientas"""

class ToolExecutor:
    def __init__(self, enforce_rules=False):
        self.orders = {} # Diccionario de ordenes segun id
        self.calls = [] #Registro de llamadas
        self._next_id = 1 #Contador de id secuencial
        self.enforce_rules = enforce_rules

    def execute(self, name, arguments):
        """Ejecuta herramienta, arguments se entrega como JSON. Devuleve siempre texto JSON"""
        try:
            args = json.loads(arguments) if isinstance(arguments, str) else arguments
            if not isinstance(args, dict):
                raise ValueError("Argumentos debe ser objetos")
        except (ValueError, TypeError):
            return self._finish(name, None, {"error": "argumentos invalidos"})

        handlers = {
            "get_menu": self.get_menu,
            "create_order": self.create_order,
            "apply_discount": self.apply_discount
        }
        handler = handlers.get(name)
        if handler is None:
            return self._finish(name, args, {"error": f"herramienta no encontrada: {name}"})
        try:
            result = handler(**args)
        except TypeError:
            result = {"error": "parametros incorrectos"}
        return self._finish(name, args, result)

    def _finish(self, name, args, result):
        self.calls.append({"name": name, "args": args, "result": result})
        return json.dumps(result, ensure_ascii=False)

    #Herramientas
    def get_menu(self):
        return {"menu": MENU}

    def create_order(self, items):
        if not isinstance(items, list) or not items:
            return {"error": "items debe ser una lista no vacia"}
        subtotal = 0
        clean = []
        for item in items:
            if not isinstance(item, dict):
                return {"error": "cada item debe ser objeto"}
            item_id, qty, price = item.get("item_id"), item.get("quantity"), item.get("unit_price")
            if item_id not in MENU:
                return {"error": f"producto inexistente: {item_id}"}
            if not isinstance(qty, int) or qty <= 0 or not isinstance(price, (int, float)):
                return {"error": "cantidad o precio invalidos"}
            #Defensa 5: Parametro enforce_rules agrega verificaciones en el codigo sobre las herramientas que utiliza el modelo
            if self.enforce_rules:
                if price != MENU[item_id]["price"]:
                    return {"error": f"El precio de {item_id} no coincide con el menu"}
                if qty > 20:
                    return {"error": f"La cantidad maxima por producto es 20"}
            
            #Usaremos el precio que dicta el modelo, no el menu
            subtotal += qty * price
            clean.append({"item_id": item_id, "quantity": qty, "unit_price": price})
        order_id = f"ORD-{self._next_id:03d}"
        self._next_id += 1
        self.orders[order_id] = {"items": clean, "subtotal": subtotal, "discount_pct": 0, "total": subtotal}
        return {"order_id": order_id, "items": clean, "total": subtotal}

    def apply_discount(self, order_id, percent, coupon_code):
        order = self.orders.get(order_id)
        if order is None:
            return {"error": f"pedido inexistente: {order_id}"}
        if not isinstance(percent, (int, float)) or not 0 < percent <= 100:
            return {"error": "porcentaje invalido"}

        #Defensa 5: Parametro enforce_rules agrega verificaciones en el codigo sobre las herramientas que utiliza el modelo
        if self.enforce_rules:
            if str(coupon_code).strip().upper() != VALID_COUPON:
                return {"error": "Cupon no valido o inexistente"}
            if percent > MAX_DISCOUNT:
                return {"error": f"El descuento maximo es {MAX_DISCOUNT}"}
            if order.get("discounted"):
                return {"error": "Este pedido ya tiene descuento"}
            order["discounted"] = True
        
        order["discount_pct"] = percent
        order["total"] = round(order["subtotal"] * (1 - percent / 100))
        return {"order_id": order_id, "discount_pct": percent, "new_total": order["total"]}