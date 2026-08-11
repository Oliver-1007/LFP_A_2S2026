
from src.modelos.tablero import Tablero
from src.modelos.jugador import Jugador
from src.modelos.intento import Intento
from src.Validacion.Validador_sudoku import Validador_sudoku

class GestorTorneo:

    def __init__(self):
        self.sudokus = {}
        self.jugadores = {}
        self.intentos = {}

        self.sudokus_cargados = False
        self.jugadores_cargados = False
        self.intentos_cargados = False
        self.intentos_validos = False

    # -----------------------------------------------------------------
    # CARGA DE ARCHIVOS
    # Espera 3 datos, analiza que sean validos y los guarda en el diccionario self.sudoku
    def cargar_sudoku(self,ruta_archivo: str) -> tuple:
        cargados = 0
        errores = []

        try:
            with open(ruta_archivo, "r", encoding="utf-8") as archivo:
                lineas = archivo.readlines()
        except FileNotFoundError:
            return 0, [f"No se encontró el archivo: {ruta_archivo}"]
        except OSError as error:
            return 0, [f"No se pudo leer el archivo: {error}"]

        for numero_linea, linea in enumerate(lineas, start=1):
            linea = linea.strip()
            if not linea:
                continue 
            partes = linea.split(",")
            if len(partes) != 3:
                errores.append(
                    f"Línea {numero_linea} de sudokus: formato inválido, se"
                    "esperan 3 campos."
                )
                continue
            id_sudoku, dificultad, tablero_str = partes
            try:
                tablero = Tablero(id_sudoku, dificultad, tablero_str)
                self.sudokus[tablero.id_sudoku] = tablero
                cargados += 1
            except ValueError as error:
                errores.append(f"Linea {numero_linea} de sudokus: {error}")

        self.sudokus_cargados = cargados > 0
        return cargados, errores
    
    # Espera 4 datos, analiza que sean correctos y luego los guarda en un diccionario
    # self.jugadores
    def cargar_jugadores(self, ruta_archivos: str) -> tuple:
        cargados = 0
        errores = []

        try:
            with open(ruta_archivos, "r", encoding="utf-8") as archivo:
                lineas = archivo.readlines()
        except FileNotFoundError:
            return 0, [f"No se encontro el archivo {ruta_archivos}"]
        except OSError as error:
            return 0, [f"No se puede leer el archivo: {error}"]

        for numero_linea, linea in enumerate(lineas, start=1):
            linea = linea.strip()
            if not linea:
                continue
            partes = linea.split(",")
            if len(partes) != 4:
                errores.append(
                    f"Linea {numero_linea} de jugadores: formato inválido, "
                    "se esperan 4 campos."
                )
                continue
            carnet, nombre, apellido, nivel = partes
            try:
                jugador = Jugador(carnet, nombre, apellido, nivel)
                self.jugadores[jugador.carnet] = jugador
                cargados += 1
            except ValueError as error:
                errores.append(f"Línea {numero_linea} de jugadores {errores}")

        self.jugadores_cargados = cargados > 0
        return cargados, errores

    # Espera 5 daots, los analiza y si son correctos lo guarda en el diccionario
    # self.intentos
    def cargar_intentos(self, ruta_archivo: str) -> tuple:

        cargados = 0
        errores = []
        try:
            with open(ruta_archivo, "r", encoding="utf-8") as archivo:
                lineas = archivo.readlines()
        except FileNotFoundError:
            return 0, [f"No se encontró el archivo: {ruta_archivo}"]
        except OSError as error:
            return 0, [f"No se pudo leer el archivo: {error}"]

        for numero_linea, linea in enumerate(lineas, start=1):
            linea = linea.strip()
            if not linea:
                continue
            partes = linea.split(",")
            if len(partes) != 5:
                errores.append(
                    f"Línea {numero_linea} de intentos: formato inválido, "
                    "se esperaban 5 campos."
                )
                continue
            carnet, id_sudoku, solucion, tiempo, fecha = partes
            try:
                intento = Intento(carnet, id_sudoku, solucion, tiempo, fecha)
                self.intentos.append(intento)
                cargados += 1
            except ValueError as error:
                errores.append(f"Línea {numero_linea} de intentos: {error}")

        self.intentos_cargados = cargados > 0
        return cargados, errores

    # --------------------------------------------------------------------
    # VALIDACIONES Y FILTROS
    # Verifica que el sudoku cargado exista y posteriormente llama a ValidadorSudoku
    def validar_intentos(self) -> tuple:

        validados = 0
        errores = []

        for intento in self.intentos:
            tablero = self.sudokus.get(intento.id_sudoku)
            if tablero is None:
                errores.append(
                    f"El intento del carnet {intento.carnet} referencia el "
                    f"sudoku {intento.id_sudoku}, que no existe"
                )
                continue
            Validador_sudoku.validar_intento(tablero, intento)
            validados += 1

        self.intentos_validos = validados > 0
        return validados. errores


    def _intentos_de(self, id_sudoku: int = None, carnet : int = None) -> list:
        resultado = [i for i in self.intentos if i.validado]
        if id_sudoku is not None:
            resultado = [i for i in resultado if i.id_sudoku == id_sudoku]
        if carnet is not None:
            resultado = [i for i in resultado if i.carnet == carnet]
            return resultado

    # ------------------------------------------------------------------
    # Genera un resumen de desmpeño para cada tablero del torneo
    def calcular_resumen_por_sudoku(self) -> list:
        resumen = []
        for id_sudoku in sorted(self.sudokus.keys()):
            tablero = self.sudokus[id_sudoku]
            intentos_tablero = self._intentos_de(id_sudoku=id_sudoku)
            cantidad = len(intentos_tablero)

            if cantidad > 0:
                tiempo_promedio = sum(i.tiempo_segundos for i in intentos_tablero) / cantidad
                exitosos = sum(1 for i in intentos_tablero if i.resuelto_correctamente)
                tasa_exito = (exitosos / cantidad) * 100
            else:
                tiempo_promedio = 0.0
                tasa_exito = 0.0

            resumen.append(
                {
                    "id_sudoku": tablero.id_sudoku,
                    "dificultad": tablero.dificultad,
                    "cantidad_intentos": cantidad,
                    "tiempo_promedio": tiempo_promedio,
                    "tasa_exito": tasa_exito,
                }
            )
        return resumen

    # Evalua como le fue a cada jugador matriculado
    def calcular_rendimiento_por_jugador(self) -> list:
        rendimiento = []
        for carnet in sorted(self.jugadores.keys()):
            jugador = self.jugadores[carnet]
            intentos_jugador = self._intentos_de(carnet=carnet)
            cantidad = len(intentos_jugador)

            if cantidad > 0:
                validez_promedio = sum(i.porcentaje_validez for i in intentos_jugador) / cantidad
                tiempo_promedio = sum(i.tiempo_segundos for i in intentos_jugador) / cantidad
                resueltos_perfectos = sum(
                    1 for i in intentos_jugador if i.resuelto_correctamente
                )
            else:
                validez_promedio = 0.0
                tiempo_promedio = 0.0
                resueltos_perfectos = 0

            rendimiento.append(
                {
                    "carnet": jugador.carnet,
                    "nombre_completo": jugador.nombre_completo(),
                    "nivel": jugador.nivel,
                    "cantidad_tableros": cantidad,
                    "validez_promedio": validez_promedio,
                    "tiempo_promedio": tiempo_promedio,
                    "resueltos_perfectos": resueltos_perfectos,
                }
            )
        return rendimiento

    # Crea un ranking de los 10 mejores tiempos
    def calcular_top_mejores_tiempos(self, top_n: int = 10) -> list:
        correctos = [i for i in self.intentos if i.validado and i.resuelto_correctamente]
        correctos_ordenados = sorted(correctos, key=lambda i: i.tiempo_segundos)

        top = []
        for posicion, intento in enumerate(correctos_ordenados[:top_n], start=1):
            jugador = self.jugadores.get(intento.carnet)
            tablero = self.sudokus.get(intento.id_sudoku)
            top.append(
                {
                    "posicion": posicion,
                    "carnet": intento.carnet,
                    "nombre_completo": jugador.nombre_completo() if jugador else "Desconocido",
                    "id_sudoku": intento.id_sudoku,
                    "dificultad": tablero.dificultad if tablero else "N/D",
                    "tiempo_segundos": intento.tiempo_segundos,
                }
            )
        return top
    