
import unittest

from _utilidades import T, analizar, tipos_error, tokens_de, FaseError, TipoError
from gestor_errores import GestorErrores


def unico_error(testcase, texto, tipo):
    """Verifica que haya exactamente un error del tipo indicado y lo devuelve."""
    r = analizar(texto)
    testcase.assertEqual(tipos_error(r), [tipo], repr(texto))
    return r.errores[0]


class PruebasErroresLexicos(unittest.TestCase):

    def test_negrita_sin_cerrar(self):
        e = unico_error(self, "Hola **mundo sin cerrar", TipoError.NEGRITA_SIN_CERRAR)
        self.assertEqual(e.fase, FaseError.LEXICO)
        self.assertEqual((e.linea, e.columna), (1, 6))
        self.assertEqual(e.descripcion, "Negrita sin cerrar iniciada en línea 1, columna 6")

    def test_cursiva_sin_cerrar(self):
        e = unico_error(self, "Texto *cursiva abierta", TipoError.CURSIVA_SIN_CERRAR)
        self.assertEqual(e.fase, FaseError.LEXICO)
        self.assertEqual((e.linea, e.columna), (1, 7))
        self.assertEqual(e.descripcion, "Cursiva sin cerrar iniciada en línea 1, columna 7")

    def test_codigo_inline_sin_cerrar(self):
        e = unico_error(self, "Un `codigo sin cerrar", TipoError.CODIGO_INLINE_SIN_CERRAR)
        self.assertEqual(e.fase, FaseError.LEXICO)
        self.assertEqual((e.linea, e.columna), (1, 4))
        self.assertEqual(e.descripcion, "Código en línea sin cerrar iniciado en línea 1, columna 4")

    def test_bloque_codigo_sin_cerrar(self):
        e = unico_error(self, "texto\n\n```python\nx = 1\ny = 2", TipoError.BLOQUE_CODIGO_SIN_CERRAR)
        self.assertEqual(e.fase, FaseError.LEXICO)
        self.assertEqual(e.linea, 3)
        self.assertEqual(e.descripcion, "Bloque de código sin cerrar iniciado en línea 3")

    def test_encabezado_invalido_mas_de_seis(self):
        e = unico_error(self, "####### Demasiados", TipoError.ENCABEZADO_INVALIDO)
        self.assertEqual(e.fase, FaseError.LEXICO)
        self.assertEqual((e.linea, e.columna), (1, 1))
        self.assertEqual(e.descripcion, "Encabezado inválido en línea 1: máximo 6 niveles")

    def test_seis_numerales_es_valido(self):
        self.assertTrue(analizar("###### Seis").exito)

    def test_negrita_sin_cerrar_se_reporta_en_la_posicion_de_apertura(self):
        e = unico_error(self, "# T\n\nlinea\ncon **negrita", TipoError.NEGRITA_SIN_CERRAR)
        self.assertEqual((e.linea, e.columna), (4, 5))

    def test_delimitador_abierto_en_item_de_lista(self):
        e = unico_error(self, "- item *abierto\n- otro", TipoError.CURSIVA_SIN_CERRAR)
        self.assertEqual((e.linea, e.columna), (1, 8))

    def test_delimitador_abierto_en_encabezado(self):
        e = unico_error(self, "## Titulo **roto", TipoError.NEGRITA_SIN_CERRAR)
        self.assertEqual((e.linea, e.columna), (1, 11))

    def test_delimitador_abierto_en_cita(self):
        e = unico_error(self, "> cita *rota", TipoError.CURSIVA_SIN_CERRAR)
        self.assertEqual((e.linea, e.columna), (1, 8))

    def test_el_delimitador_abierto_no_se_propaga_al_siguiente_bloque(self):
        r = analizar("**abierta\n\nparrafo limpio con **cierre**")
        self.assertEqual(tipos_error(r), [TipoError.NEGRITA_SIN_CERRAR])

    def test_negrita_que_cruza_lineas_en_parrafo_no_es_error(self):
        self.assertTrue(analizar("**abre\ncierra**").exito)

    def test_asteriscos_entrelazados(self):
        r = analizar("**a *b** c*")
        self.assertIn(TipoError.CURSIVA_SIN_CERRAR, tipos_error(r))
        self.assertFalse(r.exito)


class PruebasErroresSintacticos(unittest.TestCase):

    def test_indentacion_invalida_salto_de_dos_niveles(self):
        e = unico_error(self, "- a\n    - b\n- c", TipoError.INDENTACION_INVALIDA)
        self.assertEqual(e.fase, FaseError.SINTACTICO)
        self.assertEqual((e.linea, e.columna), (2, 5))
        self.assertEqual(e.descripcion, "Indentación inválida en línea 2, columna 5")

    def test_indentacion_invalida_de_cero_a_cuatro_espacios(self):
        r = analizar("- uno\n    - dos")
        self.assertEqual(tipos_error(r), [TipoError.INDENTACION_INVALIDA])

    def test_indentacion_valida_de_un_nivel_a_la_vez(self):
        self.assertTrue(analizar("- a\n  - b\n    - c\n      - d").exito)

    def test_indentacion_invalida_en_tercer_nivel(self):
        r = analizar("- a\n  - b\n        - c")
        self.assertEqual(tipos_error(r), [TipoError.INDENTACION_INVALIDA])
        self.assertEqual((r.errores[0].linea, r.errores[0].columna), (3, 9))

    def test_primer_item_con_indentacion_excesiva(self):
        r = analizar("        - suelto")
        self.assertEqual(tipos_error(r), [TipoError.INDENTACION_INVALIDA])

    def test_cita_mal_formada_sin_espacio(self):
        e = unico_error(self, ">sin espacio", TipoError.CITA_MAL_FORMADA)
        self.assertEqual(e.fase, FaseError.SINTACTICO)
        self.assertEqual((e.linea, e.columna), (1, 1))
        self.assertEqual(e.descripcion, "Cita mal formada en línea 1, columna 1")

    def test_cita_mal_formada_en_segundo_nivel(self):
        e = unico_error(self, ">>mal", TipoError.CITA_MAL_FORMADA)
        self.assertEqual((e.linea, e.columna), (1, 2))

    def test_citas_bien_formadas(self):
        for entrada in ("> a", ">> a", "> > a", ">>> a", ">", "> a\n>> b"):
            self.assertTrue(analizar(entrada).exito, entrada)


class PruebasRecuperacion(unittest.TestCase):

    def test_acumula_todos_los_errores_en_una_sola_pasada(self):
        texto = ("####### malo\n\n"
                 "Hola **negrita\n\n"
                 "y *cursiva\n\n"
                 "y `codigo\n\n"
                 "- a\n    - b\n\n"
                 ">cita\n\n"
                 "```\nsin cerrar")
        r = analizar(texto)
        self.assertEqual(
            sorted(tipos_error(r)),
            sorted([TipoError.ENCABEZADO_INVALIDO, TipoError.NEGRITA_SIN_CERRAR,
                    TipoError.CURSIVA_SIN_CERRAR, TipoError.CODIGO_INLINE_SIN_CERRAR,
                    TipoError.INDENTACION_INVALIDA, TipoError.CITA_MAL_FORMADA,
                    TipoError.BLOQUE_CODIGO_SIN_CERRAR]))

    def test_errores_ordenados_por_posicion(self):
        r = analizar("# T\n\n**a\n\n>b\n\n*c")
        posiciones = [(e.linea, e.columna) for e in r.errores]
        self.assertEqual(posiciones, sorted(posiciones))

    def test_el_analisis_continua_despues_del_error(self):
        r = analizar("**roto\n\n# Titulo valido\n\n- item")
        self.assertIn(T.NUMERAL, [t.tipo for t in r.tokens_visibles])
        self.assertIn(T.VINETA, [t.tipo for t in r.tokens_visibles])

    def test_no_se_generan_reportes_si_hay_errores(self):
        import tempfile
        from procesador import ProcesadorMarkdown
        r = analizar("**roto")
        with tempfile.TemporaryDirectory() as carpeta:
            self.assertEqual(ProcesadorMarkdown().generar_reportes(r, carpeta), {})

    def test_el_arbol_se_construye_aun_con_errores(self):
        r = analizar("**roto\n\n- a\n    - b")
        self.assertEqual(r.arbol.tipo, "<documento>")
        self.assertGreater(len(r.arbol.hijos), 1)

    def test_gestor_ignora_duplicados_exactos(self):
        g = GestorErrores()
        g.registrar_lexico(TipoError.NEGRITA_SIN_CERRAR, "**", "x", 1, 1)
        g.registrar_lexico(TipoError.NEGRITA_SIN_CERRAR, "**", "x", 1, 1)
        self.assertEqual(g.cantidad(), 1)

    def test_gestor_limpiar(self):
        g = GestorErrores()
        g.registrar_sintactico(TipoError.CITA_MAL_FORMADA, ">", "x", 1, 1)
        g.limpiar()
        self.assertFalse(g.hay_errores())


if __name__ == "__main__":
    unittest.main()
