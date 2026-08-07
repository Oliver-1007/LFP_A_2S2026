
from src.modelos.tablero import Tablero
from src.modelos.intento import Intento

class Validador_sudoku:
    TAMAÑO = 9
    TAMAÑO_CAJA = 3
    TOTAL_UNIDADES = 27

    @staticmethod
    def _es_grupo_valido(valores: list) -> bool:
        """
        Funcion que verifica que cada fila, columna o caja contenga unicamente
        los numeros del 1 al 9 sin repetirse, returna true o false.
        """
        return sorted(valores) == list(range(1,10))

    @classmethod
    def _obtener_filas(cls, matriz: list) -> list:
        return [matriz[f] for f in range(cls.TAMAÑO)]

    @classmethod
    def _obtener_columnas(cls, matriz: list) -> list:
        return [[matriz[f][c] for f in range(cls.TAMAÑO)]
                                for c in range(cls.TAMAÑO)]

    @classmethod
    def _obtener_cajas(cls, matriz: list) -> list:
        """
        FUNCION PARA OBTENER CAJAS DE 3X3 DE UNA MATRIZ DE 9X9
        El primer par de bucles te posiciona en la esquina superior izquierda de cada caja
        El segundo par de bucles toma los datos com matriz de 3x3 partiendo de su esquina correspondiente
        """
        cajas = []
        for bloque_fila in range(0, cls.TAMAÑO, cls.TAMAÑO_CAJA):
            for bloque_columna in range(0, cls.TAMAÑO, cls.TAMAÑO_CAJA):
                caja = [
                    matriz[f][c]
                    for f in range(bloque_fila, bloque_fila+ cls.TAMAÑO_CAJA)
                    for c in range(bloque_columna, bloque_columna + cls.TAMAÑO_CAJA)
                ]
                cajas.append(caja)
        return cajas

    @classmethod
    def _verificar_pistas(cls, tablero: Tablero, intento: Intento) -> bool:
        """
        FUNCION BOLEANA QUE VERIFICA SI EL JUGADOR MODIFICO ALGUN NUMERO 
        INICIAL RETORNANDO TRUE O FALSE
        """
        for fila in range(cls.TAMAÑO):
            for columna in range (cls.TAMAÑO):
                if tablero.es_celda_fija(fila,columna):
                    valor_original = tablero.obtener_valor(fila,columna)
                    valor_porpuesto = intento.matriz_solucion[fila][columna]
                    if valor_original != valor_porpuesto:
                        return False
        return True

    @classmethod
    def validar_intento(cls, tablero: Tablero, intento: Intento) -> None:
        matriz_solucion = intento.matriz_solucion #VERIFICA QUE SEAN 81 CARACTERES CORRECTOS

        filas = cls._obtener_filas(matriz_solucion)
        columnas = cls._obtener_columnas(matriz_solucion)
        cajas = cls._obtener_cajas(matriz_solucion)

        filas_validas = sum(1 for f in filas if cls._es_grupo_valido(f))
        columnas_validas = sum(1 for c in columnas if cls._es_grupo_valido(c))
        cajas_validas = sum(1 for cj in cajas if cls._es_grupo_valido(cj))

        total_validas = filas_validas + columnas_validas + cajas_validas
        porcentaje = (total_validas / cls.TOTAL_UNIDADES) * 100

        pistas_ok = cls._verificar_pistas(tablero, intento)

        intento.filas_validas = filas_validas
        intento.columnas_validas = columnas_validas
        intento.cajas_validas = cajas_validas
        intento.porcentaje_validez = porcentaje
        intento.pistas_respetadas = pistas_ok  # True o False
        intento.resuelto_correctamente = (porcentaje == 100) and pistas_ok
        intento.valido = True