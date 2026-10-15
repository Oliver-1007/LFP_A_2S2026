
import unittest

from _utilidades import analizar, html_de, tipos_error, EJEMPLO_VALIDO

# Cada caso: (id, nombre, entrada, errores_esperados, fragmentos_html_esperados)
CASOS = [
    ("CP-01", "Documento válido con todos los elementos obligatorios", EJEMPLO_VALIDO, [],
     ["<h1", "<h2", "<strong>", "<em>", "<code>Python</code>", "<ul>", "<blockquote>",
      "<pre><code", "<hr>"]),

    ("CP-02", "Listas con 3 niveles de anidamiento",
     "- uno\n  - dos\n    - tres\n      - cuatro", [],
     ["<li>uno", "<li>dos", "<li>tres", "<li>cuatro"]),

    ("CP-03", "Citas anidadas (>> y > >)", "> nivel 1\n>> nivel 2\n> > nivel 2 bis", [],
     ["<blockquote>", "<p>nivel 1</p>", "<p>nivel 2</p>", "<p>nivel 2 bis</p>"]),

    ("CP-04", "Negrita sin cerrar", "Texto con **negrita abierta", ["NEGRITA_SIN_CERRAR"], []),

    ("CP-05", "Cursiva sin cerrar", "Texto con *cursiva abierta", ["CURSIVA_SIN_CERRAR"], []),

    ("CP-06", "Código en línea sin cerrar", "Texto con `codigo abierto",
     ["CODIGO_INLINE_SIN_CERRAR"], []),

    ("CP-07", "Encabezado inválido (7 numerales)", "####### Demasiado profundo",
     ["ENCABEZADO_INVALIDO"], []),

    ("CP-08", "Bloque de código sin cerrar", "```python\nprint('hola')\n",
     ["BLOQUE_CODIGO_SIN_CERRAR"], []),

    ("CP-09", "Indentación inconsistente (salto de 0 a 4 espacios)",
     "- raíz\n    - salto inválido", ["INDENTACION_INVALIDA"], []),

    ("CP-10", "Cita mal formada (sin espacio tras >)", ">sin espacio",
     ["CITA_MAL_FORMADA"], []),

    ("CP-11", "Caso borde: documento vacío", "", [], []),

    ("CP-12", "Caso borde: '#sinespacio' es texto, no encabezado", "#sinespacio", [],
     ["<p>#sinespacio</p>"]),

    ("CP-13", "Caso borde: Markdown dentro de un bloque de código permanece literal",
     "```\n# no es titulo\n**no negrita**\n```", [],
     ["# no es titulo\n**no negrita**"]),

    ("CP-14", "Caso borde: asterisco como viñeta y como cursiva",
     "* viñeta\n\n*cursiva*", [], ["<li>viñeta</li>", "<em>cursiva</em>"]),

    ("CP-15", "Caso borde: negrita y cursiva simultáneas", "***ambas***", [],
     ["<strong><em>ambas</em></strong>"]),

    ("CP-16", "Caso borde: caracteres HTML se escapan", "a < b & c", [],
     ["a &lt; b &amp; c"]),

    ("CP-17", "Caso borde: múltiples errores en una sola pasada",
     "####### a\n\n**b\n\n>c", ["CITA_MAL_FORMADA", "ENCABEZADO_INVALIDO", "NEGRITA_SIN_CERRAR"], []),

    ("CP-18", "Caso borde: regla horizontal entre párrafos", "uno\n\n---\n\ndos", [],
     ["<p>uno</p>", "<hr>", "<p>dos</p>"]),
]


def ejecutar(entrada):
    """Devuelve (errores_obtenidos, html_o_None)."""
    r = analizar(entrada)
    errores = sorted(tipos_error(r))
    return errores, (html_de(r) if r.exito else None)


class PruebasCasosDePrueba(unittest.TestCase):

    def test_hay_al_menos_diez_casos(self):
        self.assertGreaterEqual(len(CASOS), 10)

    def test_casos_individuales(self):
        for ident, nombre, entrada, errores, fragmentos in CASOS:
            with self.subTest(caso=ident, nombre=nombre):
                obtenidos, html = ejecutar(entrada)
                self.assertEqual(obtenidos, sorted(errores))
                if not errores:
                    for fragmento in fragmentos:
                        self.assertIn(fragmento, html)

    def test_reconocimiento_de_al_menos_90_por_ciento_de_los_elementos(self):
        html = html_de(analizar(EJEMPLO_VALIDO))
        elementos = [
            "<h1", "<h2", "<p>", "<strong>teoría sólida</strong>", "<em>práctica de código</em>",
            "<code>Python</code>", "<ul>", "<li>Análisis léxico", "<li>Autómatas finitos",
            "<li>Expresiones regulares", "<li>Análisis sintáctico",
            "<li>Gramáticas libres de contexto", "<li>Recursión por la izquierda",
            "<li>Recursión por la derecha", "<li>Generación de código", "<blockquote>",
            "<pre><code class=\"language-python\">", "<hr>", "Fin del documento.",
        ]
        reconocidos = sum(1 for e in elementos if e in html)
        self.assertGreaterEqual(reconocidos / float(len(elementos)), 0.90)

    def test_ejemplo_valido_sin_errores(self):
        self.assertTrue(analizar(EJEMPLO_VALIDO).exito)


def imprimir_tabla():
    """Imprime entrada / esperado / obtenido de cada caso."""
    aprobados = 0
    for ident, nombre, entrada, errores, fragmentos in CASOS:
        obtenidos, html = ejecutar(entrada)
        ok = obtenidos == sorted(errores) and (
            bool(errores) or all(f in html for f in fragmentos))
        aprobados += ok
        print("=" * 72)
        print("%s  %s  [%s]" % (ident, nombre, "APROBADO" if ok else "FALLIDO"))
        vista = entrada if len(entrada) < 120 else entrada[:117] + "..."
        print("  Entrada  : %r" % vista)
        print("  Esperado : errores=%s%s" % (sorted(errores) or "ninguno",
                                              "" if errores else " | HTML contiene %s" % fragmentos[:3]))
        print("  Obtenido : errores=%s" % (obtenidos or "ninguno"))
    print("=" * 72)
    print("Resultado: %d/%d casos aprobados" % (aprobados, len(CASOS)))


if __name__ == "__main__":
    import sys
    if "--tabla" in sys.argv:
        imprimir_tabla()
    else:
        unittest.main()
