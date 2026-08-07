

class Jugador:
    NIVELES_VALIDOS = ("Principiante", "Intermedio", "Experto")

    def __init__(self, carnet: int, nombre: str, apellido: str, nivel: str):
        self.carnet = int(carnet)
        self.nombre = nombre.strip()
        self.apellido = apellido.strip()
        self.nivel = nivel.strip()

    def nombre_completo(self) -> str:
        return f"{self.nombre} {self.apellido}"

    def __repr__(self) -> str:
        return f"Jugador(carnet={self.carnet}, nombre='{self.nombre_completo}')"