


class Automata:
    """AFD que reconoce identificadores."""

    def __init__(self):
        self.estados = {"A", "B", "C", "E"}
        self.alfabeto = {"L", "D", "_"}
        self.estado_inicial = "A"
        self.estados_finales = {"B", "C"}

        self.delta = {
            ("A", "L"): "B", ("A", "D"): "E", ("A", "_"): "B",
            ("B", "L"): "C", ("B", "D"): "C", ("B", "_"): "C",
            ("C", "L"): "C", ("C", "D"): "C", ("C", "_"): "C",
            ("E", "L"): "E", ("E", "D"): "E", ("E", "_"): "E",
        }

    def _clasificar(self, caracter: str):
        if caracter.isalpha():
            return "L"
        if caracter.isdigit():
            return "D"
        if caracter == "_":
            return "_"
        return None 

    def reconoce(self, cadena: str):
        estado_actual = self.estado_inicial
        recorrido = [estado_actual]

        if cadena == "":
            return False,

        for caracter in cadena:
            simbolo = self._clasificar(caracter)
            if simbolo is None:
                recorrido.append(f"ERROR: '{caracter}' no pertenece al alfabeto")
                return False, recorrido
            estado_actual = self.delta[(estado_actual, simbolo)]
            recorrido.append(estado_actual)

        aceptado = estado_actual in self.estados_finales
        return aceptado, recorrido


def validar():
    afd = Automata()

    casos = [
        ("x", True),
        ("_contador", True),
        ("nombre_2", True),
        ("2variable", False),
        ("precio$", False),
    ]

    print(f"{'Cadena':<15}{'Esperado':<12}{'Obtenido':<12}Recorrido de estados")
    print("-" * 70)
    for cadena, esperado in casos:
        aceptado, recorrido = afd.reconoce(cadena)
        estado = "OK" if aceptado == esperado else "FALLO"
        print(f"{cadena:<15}{str(esperado):<12}{str(aceptado):<12}{' -> '.join(recorrido)}  [{estado}]")


if __name__ == "__main__":
    validar()
