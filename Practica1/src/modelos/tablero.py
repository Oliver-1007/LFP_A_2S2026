

class Tablero:

    DIFICULTADES_VALIDAS = ("Facil", "Media", "Dificil", "Experto")
    TAMAÑO = 9

    def __init__(self, id_sudoku: int, dificultad: str, cadena_tablero: str):
        self.id_sudoku = int(id_sudoku)
        self.dificultad = dificultad.strip()
        self.cadena_original = cadena_tablero.strip()
        self.matriz = self._construir_matriz(self.cadena_original)

    def _construir_matriz(self, cadena: str) -> list:
        if len(cadena) != self.TAMAÑO * self.TAMAÑO:
            raise ValueError(
                f"El tablero {getattr(self, 'id_sudoku', '?')} no tiene 81"
                f"caracteres (tiene {len(cadena)})."
            )

        matriz = []
        for fila in range(self.TAMAÑO):
            inicio = fila * self.TAMAÑO
            fin = inicio + self.TAMAÑO
            trozo = cadena[inicio:fin]
            if not trozo.isdigit():
                raise ValueError(
                    f"El tablero {getattr(self, 'id_sudoku', '?')} contiene"
                    "caracteres no numericos."
                )
            matriz.append([int(c) for c in trozo])
        return matriz

    def es_celda_fija(self, fila: int, columna: int) -> bool:
        return self.matriz[fila][columna] != 0

    def obtener_valor(self, fila: int, columna: int) -> int:
        return self.matriz[fila][columna]

    def __repr__(self) -> str:
        return f"Tablero(id={self.id_sudoku}, difucultad={self.dificultad})"
