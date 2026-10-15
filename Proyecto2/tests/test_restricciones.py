
import ast
import os
import sys
import unittest

from _utilidades import SRC

PROHIBIDOS = {"re", "ply", "lark", "antlr4", "markdown", "mistune", "markdown2",
              "commonmark", "markdown_it", "pyparsing", "parsimonious"}


def modulos_fuente():
    for nombre in sorted(os.listdir(SRC)):
        if nombre.endswith(".py"):
            yield nombre, os.path.join(SRC, nombre)


def arbol_de(ruta):
    with open(ruta, encoding="utf-8") as f:
        return ast.parse(f.read(), filename=ruta)


def importaciones(arbol):
    encontradas = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            for alias in nodo.names:
                encontradas.add(alias.name.split(".")[0])
        elif isinstance(nodo, ast.ImportFrom) and nodo.module and nodo.level == 0:
            encontradas.add(nodo.module.split(".")[0])
    return encontradas


def clases_y_metodos(arbol):
    clases = {}
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.ClassDef):
            clases[nodo.name] = {n.name for n in nodo.body if isinstance(n, ast.FunctionDef)}
    return clases


class PruebasRestricciones(unittest.TestCase):

    def test_python_3_10_o_superior(self):
        self.assertGreaterEqual(sys.version_info[:2], (3, 10))

    def test_sin_librerias_prohibidas(self):
        for nombre, ruta in modulos_fuente():
            usados = importaciones(arbol_de(ruta)) & PROHIBIDOS
            self.assertEqual(usados, set(), "%s importa %s" % (nombre, usados))

    def test_el_lexer_no_usa_re(self):
        with open(os.path.join(SRC, "analizador_lexico.py"), encoding="utf-8") as f:
            codigo = f.read()
        self.assertNotIn("import re", codigo)
        self.assertNotIn("re.compile", codigo)
        self.assertNotIn("re.match", codigo)
        self.assertNotIn("re.sub", codigo)

    def test_el_generador_html_no_usa_sustitucion_por_regex(self):
        with open(os.path.join(SRC, "generador_html.py"), encoding="utf-8") as f:
            codigo = f.read()
        self.assertNotIn("import re", codigo)
        self.assertNotIn("re.sub", codigo)

    def test_clases_requeridas_existen(self):
        clases = {}
        for _nombre, ruta in modulos_fuente():
            clases.update(clases_y_metodos(arbol_de(ruta)))
        for requerida in ("Token", "AnalizadorLexico", "NodoAST", "AnalizadorSintactico",
                          "GestorErrores", "GeneradorHTML"):
            self.assertIn(requerida, clases, "falta la clase %s" % requerida)
        # clase principal de la interfaz gráfica (se inspecciona sin importar tkinter)
        self.assertIn("AplicacionMarkdownCheck", clases)

    def test_analizador_lexico_expone_siguiente_token(self):
        ruta = os.path.join(SRC, "analizador_lexico.py")
        self.assertIn("siguiente_token", clases_y_metodos(arbol_de(ruta))["AnalizadorLexico"])

    def test_parser_tiene_una_funcion_por_no_terminal(self):
        ruta = os.path.join(SRC, "analizador_sintactico.py")
        metodos = clases_y_metodos(arbol_de(ruta))["AnalizadorSintactico"]
        for funcion in ("_documento", "_bloque", "_encabezado", "_parrafo", "_lista",
                        "_item_lista", "_sublista", "_cita", "_linea_cita", "_bloque_codigo",
                        "_regla_horizontal", "_en_linea", "_elemento_linea", "_codigo_inline"):
            self.assertIn(funcion, metodos, funcion)

    def test_negrita_y_cursiva_son_recursion_mutua_con_en_linea(self):
        ruta = os.path.join(SRC, "analizador_sintactico.py")
        arbol = arbol_de(ruta)
        llamadas = {}
        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.FunctionDef):
                llamadas[nodo.name] = {
                    n.func.attr for n in ast.walk(nodo)
                    if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
        self.assertIn("_elemento_linea", llamadas["_en_linea"])
        self.assertIn("_enfasis", llamadas["_elemento_linea"])
        self.assertIn("_en_linea", llamadas["_enfasis"])           # ciclo en_linea -> enfasis -> en_linea
        self.assertIn("_cita", llamadas["_elemento_cita"])         # cita anidada
        self.assertIn("_elemento_cita", llamadas["_cita"])

    def test_el_codigo_esta_comentado(self):
        for nombre, ruta in modulos_fuente():
            arbol = arbol_de(ruta)
            self.assertIsNotNone(ast.get_docstring(arbol), "%s sin docstring de módulo" % nombre)
            for nodo in ast.walk(arbol):
                # Las clases que solo agrupan constantes (sin métodos) quedan exentas
                if isinstance(nodo, ast.ClassDef) and any(
                        isinstance(n, ast.FunctionDef) for n in nodo.body):
                    self.assertIsNotNone(ast.get_docstring(nodo),
                                         "%s.%s sin docstring" % (nombre, nodo.name))


class PruebasInterfazGrafica(unittest.TestCase):
    """Pruebas de la GUI: se omiten si no hay Tkinter o pantalla disponible."""

    def setUp(self):
        try:
            import tkinter as tk
            self.raiz = tk.Tk()
        except Exception as error:                     # sin tkinter o sin display
            self.skipTest("Tkinter/pantalla no disponible: %s" % error)
        self.raiz.withdraw()
        from tkinter import messagebox
        self._originales = {n: getattr(messagebox, n) for n in ("showinfo", "showwarning", "showerror")}
        for nombre in self._originales:
            setattr(messagebox, nombre, lambda *a, **k: None)   # evita diálogos bloqueantes
        from interfaz_grafica import AplicacionMarkdownCheck
        self.app = AplicacionMarkdownCheck(self.raiz)

    def tearDown(self):
        if hasattr(self, "_originales"):
            from tkinter import messagebox
            for nombre, funcion in self._originales.items():
                setattr(messagebox, nombre, funcion)
        if hasattr(self, "raiz"):
            self.raiz.destroy()

    def test_paneles_requeridos(self):
        self.assertIsNotNone(self.app.editor)
        self.assertIsNotNone(self.app.tabla_tokens)
        self.assertIsNotNone(self.app.tabla_errores)
        self.assertIsNotNone(self.app.texto_dot)

    def test_reportes_deshabilitados_al_inicio(self):
        self.assertEqual(str(self.app.btn_r1.cget("state")), "disabled")

    def test_analisis_exitoso_llena_tokens_y_habilita_reportes(self):
        import tempfile
        from _utilidades import EJEMPLO_VALIDO
        with tempfile.TemporaryDirectory() as carpeta:
            self.app._carpeta_reportes = lambda: carpeta
            self.app.editor.insert("1.0", EJEMPLO_VALIDO)
            self.app.analizar()
            self.assertGreater(len(self.app.tabla_tokens.get_children()), 0)
            self.assertEqual(len(self.app.tabla_errores.get_children()), 0)
            self.assertEqual(str(self.app.btn_r1.cget("state")), "normal")
            self.assertIn("digraph", self.app.texto_dot.get("1.0", "end-1c"))

    def test_analisis_con_errores_llena_tabla_de_errores_y_no_habilita_reportes(self):
        self.app.editor.insert("1.0", "# T\n\n**roto\n\n>mal")
        self.app.analizar()
        self.assertEqual(len(self.app.tabla_errores.get_children()), 2)
        self.assertEqual(str(self.app.btn_r1.cget("state")), "disabled")


if __name__ == "__main__":
    unittest.main()