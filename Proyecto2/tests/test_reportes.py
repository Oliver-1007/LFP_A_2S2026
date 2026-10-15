
import os
import tempfile
import unittest

from _utilidades import (T, analizar, html_de, generador, contar_nodos, GeneradorDOT,
                         EJEMPLO_VALIDO)
from procesador import ProcesadorMarkdown
from generador_html import GeneradorHTML, escapar_html


class PruebasReporte1(unittest.TestCase):
    """Traducción del árbol a HTML semántico."""

    def test_encabezados_h1_a_h6(self):
        for nivel in range(1, 7):
            html = html_de(analizar("%s Titulo" % ("#" * nivel)))
            self.assertIn("<h%d id=\"seccion-1\">Titulo</h%d>" % (nivel, nivel), html)

    def test_parrafo(self):
        self.assertEqual(html_de(analizar("Hola mundo")), "<p>Hola mundo</p>")

    def test_negrita_cursiva_y_codigo(self):
        html = html_de(analizar("**a** *b* `c`"))
        self.assertEqual(html, "<p><strong>a</strong> <em>b</em> <code>c</code></p>")

    def test_cursiva_dentro_de_negrita(self):
        html = html_de(analizar("**fuerte *suave* fin**"))
        self.assertIn("<strong>fuerte <em>suave</em> fin</strong>", html)

    def test_negrita_y_cursiva_simultaneas(self):
        self.assertIn("<strong><em>x</em></strong>", html_de(analizar("***x***")))

    def test_lista_anidada_preserva_jerarquia(self):
        html = html_de(analizar("- a\n  - b\n    - c\n- d"))
        self.assertEqual(
            html,
            "<ul>\n<li>a\n<ul>\n<li>b\n<ul>\n<li>c</li>\n</ul></li>\n</ul></li>\n<li>d</li>\n</ul>")

    def test_cita_anidada_misma_profundidad(self):
        html = html_de(analizar("> uno\n>> dos"))
        self.assertEqual(html.count("<blockquote>"), 2)
        self.assertEqual(html.count("</blockquote>"), 2)
        self.assertLess(html.index("<p>uno</p>"), html.index("<p>dos</p>"))
        # la segunda cita está dentro de la primera
        self.assertLess(html.index("<blockquote>", 1), html.index("</blockquote>"))

    def test_cita_tres_niveles(self):
        html = html_de(analizar(">>> hondo"))
        self.assertEqual(html.count("<blockquote>"), 3)

    def test_bloque_de_codigo_con_lenguaje_y_contenido_literal(self):
        html = html_de(analizar("```python\nx = **no** & <b>\n```"))
        self.assertEqual(
            html, '<pre><code class="language-python">x = **no** &amp; &lt;b&gt;</code></pre>')

    def test_bloque_de_codigo_sin_lenguaje(self):
        self.assertEqual(html_de(analizar("```\nabc\n```")), "<pre><code>abc</code></pre>")

    def test_regla_horizontal(self):
        self.assertEqual(html_de(analizar("---")), "<hr>")

    def test_escape_de_html_en_texto_y_codigo_inline(self):
        html = html_de(analizar("a < b & c > d `<x>`"))
        self.assertIn("a &lt; b &amp; c &gt; d", html)
        self.assertIn("<code>&lt;x&gt;</code>", html)

    def test_escapar_html_directo(self):
        self.assertEqual(escapar_html("<a href=\"x\">&'</a>"),
                         "&lt;a href=&quot;x&quot;&gt;&amp;&#39;&lt;/a&gt;")

    def test_parrafo_multilinea_conserva_el_salto(self):
        self.assertEqual(html_de(analizar("uno\ndos")), "<p>uno\ndos</p>")

    def test_ejemplo_completo_de_la_seccion_4_7(self):
        html = html_de(analizar(EJEMPLO_VALIDO))
        esperados = [
            "<h1 id=\"seccion-1\">Proyecto de Lenguajes Formales</h1>",
            "<strong>teoría sólida</strong>",
            "<em>práctica de código</em>",
            "<code>Python</code>",
            "<h2 id=\"seccion-2\">Contenido del curso</h2>",
            "<li>Análisis léxico\n<ul>",
            "<li>Recursión por la izquierda</li>",
            "<blockquote>",
            "<pre><code class=\"language-python\">def hola():",
            "<hr>",
            "<p>Fin del documento.</p>",
        ]
        for esperado in esperados:
            self.assertIn(esperado, html)
        self.assertEqual(html.count("<ul>"), 4)   # raíz + 3 sublistas
        self.assertEqual(html.count("<blockquote>"), 2)

    def test_pagina_completa_con_css_embebido_y_sin_recursos_externos(self):
        pagina = generador(analizar(EJEMPLO_VALIDO)).generar_reporte1()
        self.assertTrue(pagina.startswith("<!DOCTYPE html>"))
        self.assertIn("<style>", pagina)
        self.assertIn("Análisis completado sin errores", pagina)
        self.assertNotIn("http://", pagina)
        self.assertNotIn("https://", pagina)
        self.assertNotIn("<link", pagina)


class PruebasReporte2(unittest.TestCase):
    """Estadísticas del documento (valores de la imagen 2 del enunciado)."""

    def setUp(self):
        self.g = generador(analizar(EJEMPLO_VALIDO), "ejemplo_valido.md")
        self.e = self.g.estadisticas

    def test_totales_del_ejemplo(self):
        self.assertEqual(self.e["palabras"], 67)
        self.assertEqual(self.e["parrafos"], 2)
        self.assertEqual(self.e["encabezados"], 2)
        self.assertEqual(self.e["items"], 8)
        self.assertEqual(self.e["lineas_cita"], 2)
        self.assertEqual(self.e["bloques_codigo"], 1)

    def test_encabezados_por_nivel(self):
        self.assertEqual(self.e["por_nivel"], {1: 1, 2: 1, 3: 0, 4: 0, 5: 0, 6: 0})

    def test_profundidades(self):
        self.assertEqual(self.e["prof_listas"], 3)
        self.assertEqual(self.e["prof_citas"], 2)

    def test_cantidad_de_listas_y_citas(self):
        self.assertEqual(self.e["listas"], 1)
        self.assertEqual(self.e["citas"], 1)

    def test_elementos_en_linea(self):
        self.assertEqual(self.e["negritas"], 1)
        self.assertEqual(self.e["cursivas"], 1)
        self.assertEqual(self.e["codigos_inline"], 1)
        self.assertEqual(self.e["reglas"], 1)

    def test_conteo_de_enfasis_anidados_y_en_listas_y_citas(self):
        e = generador(analizar("- **a** *b*\n\n> `c` **d *e***")).estadisticas
        self.assertEqual((e["negritas"], e["cursivas"], e["codigos_inline"]), (2, 2, 1))

    def test_documento_vacio_tiene_todo_en_cero(self):
        e = generador(analizar("")).estadisticas
        self.assertEqual((e["palabras"], e["parrafos"], e["encabezados"], e["prof_listas"],
                          e["prof_citas"]), (0, 0, 0, 0, 0))

    def test_listas_planas_tienen_profundidad_uno(self):
        self.assertEqual(generador(analizar("- a\n- b")).estadisticas["prof_listas"], 1)

    def test_pagina_contiene_las_secciones_del_reporte(self):
        pagina = self.g.generar_reporte2()
        for texto in ("Estadísticas del Documento", "ejemplo_valido.md", "Palabras totales",
                      "Encabezados por nivel", "Profundidad máxima de anidamiento",
                      "3 niveles", "2 niveles", "Elementos en línea", "Regla horizontal"):
            self.assertIn(texto, pagina)
        for nivel in range(1, 7):
            self.assertIn(">H%d<" % nivel, pagina)

    def test_barras_proporcionales_al_maximo(self):
        pagina = self.g.generar_reporte2()
        self.assertEqual(pagina.count("width:100%"), 2)     # H1 y H2
        self.assertEqual(pagina.count("width:0%"), 4)       # H3 a H6


class PruebasReporte3(unittest.TestCase):
    """Tabla de contenido con enlaces internos hacia el Reporte 1."""

    def test_entradas_con_enlaces_al_reporte_1(self):
        pagina = generador(analizar(EJEMPLO_VALIDO), "ejemplo_valido.md").generar_reporte3()
        self.assertIn("Tabla de Contenido", pagina)
        self.assertIn('href="reporte1_documento.html#seccion-1"', pagina)
        self.assertIn('href="reporte1_documento.html#seccion-2"', pagina)
        self.assertIn("Proyecto de Lenguajes Formales", pagina)
        self.assertIn("Contenido del curso", pagina)

    def test_las_anclas_existen_en_el_reporte_1(self):
        g = generador(analizar("# A\n\n## B\n\n### C\n\n## D"))
        r1 = g.generar_reporte1()
        for _nivel, _texto, ancla in g.encabezados:
            self.assertIn('id="%s"' % ancla, r1)
            self.assertIn("#%s" % ancla, g.generar_reporte3())

    def test_indentacion_refleja_el_nivel(self):
        pagina = generador(analizar("# A\n\n## B\n\n### C")).generar_reporte3()
        self.assertIn("margin-left:0px", pagina)
        self.assertIn("margin-left:22px", pagina)
        self.assertIn("margin-left:44px", pagina)

    def test_insignias_por_nivel(self):
        pagina = generador(analizar("# A\n\n#### B")).generar_reporte3()
        self.assertIn(">H1<", pagina)
        self.assertIn(">H4<", pagina)

    def test_documento_sin_encabezados_lo_indica_explicitamente(self):
        pagina = generador(analizar("solo texto")).generar_reporte3()
        self.assertIn("no contiene encabezados", pagina)
        self.assertNotIn("<a href", pagina)

    def test_el_texto_del_indice_ignora_delimitadores_de_enfasis(self):
        g = generador(analizar("# Hola **mundo**"))
        self.assertEqual(g.encabezados[0][1], "Hola mundo")

    def test_texto_del_indice_escapado(self):
        pagina = generador(analizar("# a <b> & c")).generar_reporte3()
        self.assertIn("a &lt;b&gt; &amp; c", pagina)


class PruebasGraphviz(unittest.TestCase):
    """arbol.dot: árbol de derivación real."""

    def setUp(self):
        self.r = analizar(EJEMPLO_VALIDO)
        self.dot = GeneradorDOT().generar(self.r.arbol)

    def test_estructura_basica(self):
        self.assertTrue(self.dot.startswith("digraph ArbolDerivacion {"))
        self.assertTrue(self.dot.strip().endswith("}"))
        self.assertEqual(self.dot.count("{"), self.dot.count("}"))
        self.assertIn("rankdir=TB;", self.dot)

    def test_nodo_raiz_es_documento_y_tiene_color_propio(self):
        self.assertIn('n0 [label="<documento>", fillcolor="#2E75B6", fontcolor=white];', self.dot)

    def test_un_nodo_por_cada_nodo_del_arbol_y_aristas_n_menos_uno(self):
        total = contar_nodos(self.r.arbol)
        declarados = [l for l in self.dot.splitlines() if "[label=" in l]
        aristas = [l for l in self.dot.splitlines() if "->" in l]
        self.assertEqual(len(declarados), total)
        self.assertEqual(len(aristas), total - 1)

    def test_terminales_y_no_terminales_tienen_colores_distintos(self):
        self.assertIn('fillcolor="#F9E79F"', self.dot)     # terminales
        self.assertIn('fillcolor="#D6EAF8"', self.dot)     # no terminales
        for linea in self.dot.splitlines():
            if 'label="<' in linea and "n0 " not in linea:
                self.assertIn("#D6EAF8", linea)
            if 'label="NUMERAL' in linea or 'label="TEXTO' in linea:
                self.assertIn("#F9E79F", linea)

    def test_contiene_las_producciones_del_ejemplo(self):
        for simbolo in ("<bloque>", "<encabezado>", "<parrafo>", "<lista>", "<item_lista>",
                        "<sublista>", "<cita>", "<bloque_codigo>", "<regla_horizontal>",
                        "<en_linea>", "<negrita>", "<cursiva>", "<codigo_inline>",
                        "NUMERAL", "TEXTO", "VIÑETA", "INDENT", "DEDENT", "CITA",
                        "CERCA_CODIGO", "REGLA_HORIZONTAL", "NEGRITA", "CURSIVA"):
            self.assertIn(simbolo, self.dot, simbolo)

    def test_todas_las_aristas_referencian_nodos_declarados(self):
        ids = {l.split()[0] for l in self.dot.splitlines() if "[label=" in l}
        for linea in self.dot.splitlines():
            if "->" in linea:
                origen, _, destino = linea.strip().rstrip(";").partition(" -> ")
                self.assertIn(origen, ids)
                self.assertIn(destino, ids)

    def test_comillas_y_barras_se_escapan(self):
        dot = GeneradorDOT().generar(analizar('texto "citado" y \\ barra').arbol)
        self.assertIn('\\"citado\\"', dot)
        self.assertIn("\\\\ barra", dot)

    def test_arbol_con_errores_tambien_se_genera(self):
        dot = GeneradorDOT().generar(analizar("**roto").arbol)
        self.assertIn("cierre implícito", dot)

    def test_valido_con_graphviz_si_esta_instalado(self):
        import shutil
        import subprocess
        ejecutable = shutil.which("dot")
        if not ejecutable:
            self.skipTest("Graphviz no está instalado")
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = os.path.join(carpeta, "arbol.dot")
            with open(ruta, "w", encoding="utf-8") as f:
                f.write(self.dot)
            resultado = subprocess.run([ejecutable, "-Tsvg", ruta, "-o", os.path.join(carpeta, "a.svg")],
                                       capture_output=True)
            self.assertEqual(resultado.returncode, 0, resultado.stderr)


class PruebasArchivosDeSalida(unittest.TestCase):

    def test_genera_tres_reportes_y_dot_en_disco(self):
        p = ProcesadorMarkdown()
        r = p.analizar(EJEMPLO_VALIDO, "ejemplo_valido.md")
        with tempfile.TemporaryDirectory() as carpeta:
            rutas = p.generar_reportes(r, os.path.join(carpeta, "reportes"))
            self.assertEqual(sorted(rutas), ["reporte1", "reporte2", "reporte3"])
            for ruta in rutas.values():
                self.assertTrue(os.path.isfile(ruta))
                with open(ruta, encoding="utf-8") as f:
                    self.assertIn("<!DOCTYPE html>", f.read())
            self.assertEqual(os.path.basename(rutas["reporte1"]), "reporte1_documento.html")
            self.assertEqual(os.path.basename(rutas["reporte2"]), "reporte2_estadisticas.html")
            self.assertEqual(os.path.basename(rutas["reporte3"]), "reporte3_indice.html")
            ruta_dot = p.guardar_dot(r, os.path.join(carpeta, "arbol.dot"))
            with open(ruta_dot, encoding="utf-8") as f:
                self.assertIn("digraph", f.read())

    def test_exportar_tablas_de_tokens_y_errores(self):
        p = ProcesadorMarkdown()
        r = p.analizar("# T\n\n**roto", "x.md")
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = p.guardar_tablas(r, os.path.join(carpeta, "tablas.html"))
            with open(ruta, encoding="utf-8") as f:
                contenido = f.read()
        self.assertIn("Tabla de tokens", contenido)
        self.assertIn("Tabla de errores", contenido)
        self.assertIn("NEGRITA_SIN_CERRAR", contenido)

    def test_tabla_de_tokens_numera_sin_sinteticos(self):
        r = analizar("**roto")
        contenido = GeneradorHTML.generar_tablas(r.tokens, r.errores)
        self.assertEqual(contenido.count("<tr><td>"), len(r.tokens_visibles) + 1)


if __name__ == "__main__":
    unittest.main()
