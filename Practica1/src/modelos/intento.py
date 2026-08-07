

class Intento:
    TANAÑO = 9

    def __init__(self, carnet: int,id_sudoku: int,solucion: str,tiempo_segundos: int,fecha: str,):
        self.carnet = int(carnet)
        self.id_sudoku = int(id_sudoku)
        self.solucion = solucion.strip()
        self.tiempo_segundos = int(tiempo_segundos)
        self.fecha = fecha.strip()
        self.matriz_solucion = self._sconstruir_matriz(self.solucion)

        self.filas_validas = 0
        self.columnas_validas = 0
        self.cajas_validas = 0
        self.porcentaje_validez = 0.0
        self.pistas_respetadas = True
        self.resuelto_correctamente = False
        self.valido = False

    def _construir_matriz(self, cadena: str) -> list:
        if len(cadena) != self.TAMAÑO * self.TAMAÑO:
            raise ValueError(
                f"El intento de carnet {getattr(self, 'carnet', '?')} para "
                f"el sudoku {getattr(self, '?')} no tiene 81 "
                f"caracteres (tiene{len(cadena)})."
            )
        matriz = []
        for fila in range(self.TAMAÑO):
            inicio = fila * self.TAMAÑO
            fin = inicio + self.TAMAÑO
            trozo = cadena[inicio: fin]
            if not trozo.isdigit():
                raise ValueError(
                    f"El intento del carnet {getattr(self, 'carnet', '?')} "
                    "contiene caracteres no numéricos."
                )
            matriz.append([int(c) for c in trozo])
        return matriz

    def __repr__(self) -> str:
        return (
            f"Intento(carnet={self.carnet}, id_sudoku={self.id_sudoku}, "
            f"validez={self.porcentaje_validez:.2f}%)"
        )
        