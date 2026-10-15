# -*- coding: utf-8 -*-

import unittest

from _utilidades import (T, analizar, tipos_token, tokens_de, tipos_error, EJEMPLO_VALIDO)
from analizador_lexico import AnalizadorLexico
from gestor_errores import GestorErrores


class PruebasEncabezados(unittest.TestCase):

    def test_niveles_1_a_6(self):
        for nivel in range(1, 7):
            r = analizar("%s Título" % ("#" * nivel))
            numerales = tokens_de(r, T.NUMERAL)
            self.assertEqual(len(numerales), 1)
            self.assertEqual(numerales[0].nivel, nivel)
            self.assertEqual(numerales[0].lexema, "#" * nivel)
            self.assertTrue(r.exito)

    def test_numeral_sin_espacio_es_texto(self):
        r = analizar("#sinespacio")
        self.assertEqual(tipos_token(r), [T.TEXTO])
        self.assertTrue(r.exito)

    def test_numeral_en_medio_de_linea_es_texto(self):
        r = analizar("hola # mundo")
        self.assertEqual(tipos_token(r), [T.TEXTO])


class PruebasMarcadoresDeBloque(unittest.TestCase):

    def test_tres_tipos_de_vineta(self):
        r = analizar("- uno\n* dos\n+ tres")
        vinetas = tokens_de(r, T.VINETA)
        self.assertEqual([v.lexema for v in vinetas], ["-", "*", "+"])
        self.assertTrue(r.exito)

    def test_vineta_asterisco_no_es_cursiva(self):
        r = analizar("* item")
        self.assertEqual(tipos_token(r), [T.VINETA, T.TEXTO])

    def test_asterisco_sin_espacio_es_cursiva(self):
        r = analizar("*enfasis*")
        self.assertEqual(tipos_token(r), [T.CURSIVA, T.TEXTO, T.CURSIVA])

    def test_guion_sin_espacio_es_texto(self):
        r = analizar("-Generación")
        self.assertEqual(tipos_token(r), [T.TEXTO])

    def test_regla_horizontal(self):
        for linea in ("---", "-----", "---   "):
            r = analizar(linea)
            self.assertEqual(tipos_token(r), [T.REGLA_HORIZONTAL], linea)

    def test_dos_guiones_no_son_regla(self):
        r = analizar("--")
        self.assertEqual(tipos_token(r), [T.TEXTO])

    def test_guiones_con_texto_no_son_regla(self):
        r = analizar("--- hola")
        self.assertNotIn(T.REGLA_HORIZONTAL, tipos_token(r))

    def test_salto_de_parrafo_unico_para_varias_lineas_en_blanco(self):
        r = analizar("uno\n\n\n   \ndos")
        self.assertEqual(tipos_token(r).count(T.SALTO_PARRAFO), 1)

    def test_cita_niveles_y_equivalencia_de_notaciones(self):
        for entrada in (">> texto", "> > texto"):
            r = analizar(entrada)
            citas = tokens_de(r, T.CITA)
            self.assertEqual(len(citas), 1, entrada)
            self.assertEqual(citas[0].nivel, 2, entrada)
            self.assertTrue(r.exito, entrada)

    def test_cita_nivel_tres(self):
        r = analizar(">>> profundo")
        self.assertEqual(tokens_de(r, T.CITA)[0].nivel, 3)


class PruebasEnLinea(unittest.TestCase):

    def test_maximal_munch_negrita(self):
        r = analizar("**fuerte**")
        self.assertEqual(tipos_token(r), [T.NEGRITA, T.TEXTO, T.NEGRITA])
        self.assertEqual(tokens_de(r, T.NEGRITA)[0].lexema, "**")

    def test_negrita_y_cursiva_combinadas(self):
        r = analizar("***ambas***")
        self.assertEqual(tipos_token(r),
                         [T.NEGRITA, T.CURSIVA, T.TEXTO, T.CURSIVA, T.NEGRITA])
        self.assertTrue(r.exito)

    def test_cursiva_dentro_de_negrita(self):
        r = analizar("**a *b* c**")
        self.assertEqual(tipos_token(r).count(T.NEGRITA), 2)
        self.assertEqual(tipos_token(r).count(T.CURSIVA), 2)
        self.assertTrue(r.exito)

    def test_codigo_inline_es_literal(self):
        r = analizar("`**no** *tokenizar*`")
        self.assertEqual(tipos_token(r), [T.CODIGO_INLINE, T.TEXTO_LITERAL, T.CODIGO_INLINE])
        self.assertEqual(tokens_de(r, T.TEXTO_LITERAL)[0].lexema, "**no** *tokenizar*")

    def test_texto_plano_conserva_lexema(self):
        r = analizar("Lenguajes Formales")
        self.assertEqual(tokens_de(r, T.TEXTO)[0].lexema, "Lenguajes Formales")


class PruebasBloqueCodigo(unittest.TestCase):

    def test_contenido_literal_sin_tokenizar(self):
        texto = "```python\n# no encabezado\n**no negrita**\n- no viñeta\n> no cita\n```"
        r = analizar(texto)
        self.assertEqual(tipos_token(r),
                         [T.CERCA_CODIGO, T.LENGUAJE, T.TEXTO_LITERAL, T.CERCA_CODIGO])
        self.assertEqual(tokens_de(r, T.TEXTO_LITERAL)[0].lexema,
                         "# no encabezado\n**no negrita**\n- no viñeta\n> no cita")
        self.assertTrue(r.exito)

    def test_lenguaje_capturado(self):
        r = analizar("```python\nx = 1\n```")
        self.assertEqual(tokens_de(r, T.LENGUAJE)[0].lexema, "python")

    def test_bloque_sin_lenguaje(self):
        r = analizar("```\ntexto\n```")
        self.assertEqual(tipos_token(r), [T.CERCA_CODIGO, T.TEXTO_LITERAL, T.CERCA_CODIGO])

    def test_bloque_vacio(self):
        r = analizar("```\n```")
        self.assertEqual(tipos_token(r), [T.CERCA_CODIGO, T.CERCA_CODIGO])
        self.assertTrue(r.exito)

    def test_se_conservan_lineas_en_blanco_e_indentacion(self):
        r = analizar("```\na\n\n    b\n```")
        self.assertEqual(tokens_de(r, T.TEXTO_LITERAL)[0].lexema, "a\n\n    b")


class PruebasIndentacion(unittest.TestCase):

    def test_lista_tres_niveles_indent_dedent(self):
        texto = "- a\n  - b\n    - c\n- d"
        r = analizar(texto)
        secuencia = [t for t in tipos_token(r) if t in (T.INDENT, T.DEDENT)]
        self.assertEqual(secuencia, [T.INDENT, T.INDENT, T.DEDENT, T.DEDENT])
        self.assertTrue(r.exito)

    def test_indent_dedent_balanceados_al_final(self):
        r = analizar("- a\n  - b\n    - c")
        tipos = tipos_token(r)
        self.assertEqual(tipos.count(T.INDENT), tipos.count(T.DEDENT))

    def test_dedent_multiple_en_una_sola_linea(self):
        r = analizar("- a\n  - b\n    - c\n- d")
        dedents = [t for t in r.tokens_visibles if t.tipo == T.DEDENT]
        self.assertEqual([d.linea for d in dedents], [4, 4])

    def test_tabulador_equivale_a_un_nivel(self):
        r = analizar("- a\n\t- b")
        self.assertEqual(tipos_token(r).count(T.INDENT), 1)
        self.assertTrue(r.exito)

    def test_tres_espacios_como_en_el_ejemplo_son_validos(self):
        r = analizar("- a\n   - b\n     - c")
        self.assertTrue(r.exito)

    def test_linea_en_blanco_termina_la_lista(self):
        r = analizar("- a\n  - b\n\n- c")
        tipos = tipos_token(r)
        self.assertEqual(tipos.count(T.INDENT), tipos.count(T.DEDENT))


class PruebasPosiciones(unittest.TestCase):

    def test_linea_y_columna_exactas(self):
        r = analizar("# Hola\n\nUn **dato** aquí")
        numeral = tokens_de(r, T.NUMERAL)[0]
        self.assertEqual((numeral.linea, numeral.columna), (1, 1))
        self.assertEqual(tokens_de(r, T.TEXTO)[0].columna, 3)
        negritas = tokens_de(r, T.NEGRITA)
        self.assertEqual((negritas[0].linea, negritas[0].columna), (3, 4))
        self.assertEqual((negritas[1].linea, negritas[1].columna), (3, 10))

    def test_columna_de_vineta_indentada(self):
        r = analizar("- a\n  - b")
        vinetas = tokens_de(r, T.VINETA)
        self.assertEqual((vinetas[1].linea, vinetas[1].columna), (2, 3))

    def test_tokens_ordenados_por_posicion(self):
        r = analizar(EJEMPLO_VALIDO)
        posiciones = [(t.linea, t.columna) for t in r.tokens]
        self.assertEqual(posiciones, sorted(posiciones))


class PruebasFlujoDeTokens(unittest.TestCase):

    def test_siempre_termina_en_fin_y_lo_repite(self):
        lexico = AnalizadorLexico("hola", GestorErrores())
        tokens = lexico.tokenizar()
        self.assertEqual(tokens[-1].tipo, T.FIN)
        self.assertEqual(lexico.siguiente_token().tipo, T.FIN)
        self.assertEqual(lexico.siguiente_token().tipo, T.FIN)

    def test_entrada_vacia(self):
        r = analizar("")
        self.assertEqual(tipos_token(r, tecnicos=True), [T.FIN])
        self.assertTrue(r.exito)

    def test_saltos_de_linea_windows_y_mac(self):
        base = tipos_token(analizar("# A\n\ntexto"))
        self.assertEqual(tipos_token(analizar("# A\r\n\r\ntexto")), base)
        self.assertEqual(tipos_token(analizar("# A\r\rtexto")), base)

    def test_archivo_sin_salto_de_linea_final(self):
        self.assertEqual(tipos_token(analizar("# T")), [T.NUMERAL, T.TEXTO])

    def test_bom_se_ignora(self):
        self.assertEqual(tipos_token(analizar("\ufeff# T")), [T.NUMERAL, T.TEXTO])

    def test_no_se_usa_modulo_re_en_el_flujo(self):
        # El lexer debe seguir produciendo tokens para entradas inusuales sin fallar
        for entrada in ("\t\t", "\x0c", "* * *", "` ` `", "> > >", "####", "#"):
            self.assertTrue(analizar(entrada).tokens)

    def test_tokens_sinteticos_no_aparecen_en_la_tabla(self):
        r = analizar("**sin cerrar")
        self.assertTrue(any(t.sintetico for t in r.tokens))
        self.assertFalse(any(t.sintetico for t in r.tokens_visibles))
        self.assertIn("NEGRITA_SIN_CERRAR", tipos_error(r))


if __name__ == "__main__":
    unittest.main()
