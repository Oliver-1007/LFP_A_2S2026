
import os

from gestor_errores import GestorErrores
from analizador_lexico import AnalizadorLexico
from analizador_sintactico import AnalizadorSintactico
from generador_html import GeneradorHTML
from generador_dot import GeneradorDOT


## Resultado completo de analizar un documento
class ResultadoAnalisis:

    def __init__(self, texto, nombre_archivo, tokens, gestor, arbol):
        self.texto = texto
        self.nombre_archivo = nombre_archivo
        self.tokens = tokens
        self.gestor = gestor
        self.arbol = arbol

    @property
    def exito(self):
        return not self.gestor.hay_errores()

    ## Tokens que aparecen en la tabla
    @property
    def tokens_visibles(self):
        return [t for t in self.tokens if not t.sintetico]

    @property
    def errores(self):
        return self.gestor.ordenados()


## Ejecuta el análisis y escribe los archivos de salida
class ProcesadorMarkdown:

    def analizar(self, texto, nombre_archivo="documento.md"):
        gestor = GestorErrores()
        lexico = AnalizadorLexico(texto, gestor)
        sintactico = AnalizadorSintactico(lexico, gestor)
        arbol = sintactico.analizar()
        return ResultadoAnalisis(texto, nombre_archivo, sintactico.tokens, gestor, arbol)

    @staticmethod
    def codigo_dot(resultado):
        return GeneradorDOT().generar(resultado.arbol)

    ## Genera los tres reportes en HTML solo si el analisis fue exitoso
    ## Devuelve un diccionario {clave: ruta}; vacio si hubo errores
    def generar_reportes(self, resultado, carpeta):
        if not resultado.exito:
            return {}
        os.makedirs(carpeta, exist_ok=True)
        generador = GeneradorHTML(resultado.arbol, resultado.nombre_archivo)
        contenidos = {
            "reporte1": (GeneradorHTML.ARCHIVO_R1, generador.generar_reporte1()),
            "reporte2": (GeneradorHTML.ARCHIVO_R2, generador.generar_reporte2()),
            "reporte3": (GeneradorHTML.ARCHIVO_R3, generador.generar_reporte3()),
        }
        rutas = {}
        for clave, (nombre, html) in contenidos.items():
            ruta = os.path.join(carpeta, nombre)
            self._escribir(ruta, html)
            rutas[clave] = ruta
        return rutas

    def guardar_dot(self, resultado, ruta):
        self._escribir(ruta, self.codigo_dot(resultado))
        return ruta

    def guardar_tablas(self, resultado, ruta):
        html = GeneradorHTML.generar_tablas(resultado.tokens, resultado.errores, resultado.nombre_archivo)
        self._escribir(ruta, html)
        return ruta

    @staticmethod
    def _escribir(ruta, contenido):
        with open(ruta, "w", encoding="utf-8") as archivo:
            archivo.write(contenido)
