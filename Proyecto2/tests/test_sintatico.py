
import unittest

from _utilidades import (T, analizar, tipos_error, recorrer, contar_nodos, EJEMPLO_VALIDO)
from analizador_sintactico import AnalizadorSintactico
from gestor_errores import GestorErrores, TipoError, FaseError
from nodo_ast import EPSILON
from tokens import Token


def bloques(resultado):
    """Contenido de cada <bloque> de la raíz."""
    return [e.hijos[0] for e in resultado.arbol.elementos_cadena() if e.tipo == "<bloque>"]


def buscar_nodos(resultado, tipo):
    return [n for n in recorrer(resultado.arbol) if n.tipo == tipo]


class LexicoFalso:
    """Lexer de prueba que entrega una secuencia fija de tokens."""

    def __init__(self, tokens):
        self._tokens = list(tokens) + [Token(T.FIN, "", 99, 1)]
        self._i = 0

    def siguiente_token(self):
        token = self._tokens[min(self._i, len(self._tokens) - 1)]
        self._i += 1
        return token


class PruebasEstructuraDelArbol(unittest.TestCase):

    def test_raiz_es_documento_y_termina_en_epsilon(self):
        r = analizar("# T")
        self.assertEqual(r.arbol.tipo, "<documento>")
        ultimo = r.arbol
        while ultimo.hijos and ultimo.hijos[-1].tipo == "<documento>":
            ultimo = ultimo.hijos[-1]
        self.assertEqual(ultimo.hijos[-1].tipo, EPSILON)

    def test_documento_vacio(self):
        r = analizar("")
        self.assertEqual([h.tipo for h in r.arbol.hijos], [EPSILON])

    def test_tipos_de_bloque_del_ejemplo(self):
        r = analizar(EJEMPLO_VALIDO)
        self.assertEqual([b.tipo for b in bloques(r)],
                         ["<encabezado>", "<parrafo>", "<encabezado>", "<lista>",
                          "<cita>", "<bloque_codigo>", "<regla_horizontal>", "<parrafo>"])
        self.assertTrue(r.exito)

    def test_hojas_son_terminales_y_nodos_internos_no(self):
        r = analizar(EJEMPLO_VALIDO)
        for nodo in recorrer(r.arbol):
            if nodo.hijos:
                self.assertFalse(nodo.es_terminal, nodo.tipo)
            elif nodo.tipo.startswith("<"):
                self.fail("no terminal sin hijos: %s" % nodo.tipo)

    def test_las_hojas_terminales_conservan_su_token(self):
        r = analizar("# Hola")
        for nodo in recorrer(r.arbol):
            if nodo.es_terminal and not nodo.es_epsilon:
                self.assertIsNotNone(nodo.token)

    def test_cada_token_visible_queda_en_el_arbol(self):
        r = analizar(EJEMPLO_VALIDO)
        en_arbol = [n.token for n in recorrer(r.arbol) if n.token is not None]
        sin_fin = [t for t in r.tokens if t.tipo != T.FIN]
        self.assertEqual(len(en_arbol), len(sin_fin))

    def test_encabezado_guarda_su_nivel(self):
        r = analizar("### Sub")
        self.assertEqual(bloques(r)[0].atributos["nivel"], 3)

    def test_bloque_codigo_guarda_lenguaje_y_contenido(self):
        r = analizar("```python\nx = 1\n```")
        b = bloques(r)[0]
        self.assertEqual(b.atributos["lenguaje"], "python")
        self.assertEqual(b.atributos["contenido"], "x = 1")


class PruebasListas(unittest.TestCase):

    def test_lista_con_tres_niveles(self):
        r = analizar("- a\n  - b\n    - c")
        self.assertEqual(len(buscar_nodos(r, "<sublista>")), 2)
        self.assertEqual(len(buscar_nodos(r, "<item_lista>")), 3)
        self.assertTrue(r.exito)

    def test_items_hermanos_forman_una_sola_lista(self):
        r = analizar("- a\n- b\n- c")
        self.assertEqual(len(bloques(r)), 1)
        self.assertEqual(len(list(bloques(r)[0].elementos_cadena())), 3)

    def test_lista_separada_por_linea_en_blanco_son_dos_bloques(self):
        r = analizar("- a\n\n- b")
        self.assertEqual([b.tipo for b in bloques(r)], ["<lista>", "<lista>"])

    def test_sublistas_hermanas_en_un_mismo_nivel(self):
        r = analizar("- a\n  - b\n  - c\n- d")
        sub = buscar_nodos(r, "<sublista>")[0]
        self.assertEqual(len(list(sub.buscar("<lista>").elementos_cadena())), 2)

    def test_lista_no_ordenada_con_marcadores_mixtos(self):
        r = analizar("- a\n* b\n+ c")
        self.assertEqual(len(buscar_nodos(r, "<item_lista>")), 3)
        self.assertTrue(r.exito)


class PruebasCitas(unittest.TestCase):

    def test_cita_simple(self):
        r = analizar("> hola")
        self.assertEqual(len(buscar_nodos(r, "<cita>")), 1)
        self.assertEqual(len(buscar_nodos(r, "<linea_cita>")), 1)

    def test_cita_anidada_dos_niveles(self):
        r = analizar("> uno\n>> dos")
        citas = buscar_nodos(r, "<cita>")
        self.assertEqual({c.atributos["nivel"] for c in citas}, {1, 2})
        self.assertTrue(r.exito)

    def test_cita_anidada_tres_niveles_y_regreso(self):
        r = analizar("> a\n>> b\n>>> c\n> d")
        niveles = [c.atributos["nivel"] for c in buscar_nodos(r, "<cita>")]
        self.assertEqual(max(niveles), 3)
        self.assertEqual(len(buscar_nodos(r, "<linea_cita>")), 4)
        self.assertEqual(len(bloques(r)), 1)

    def test_cita_que_inicia_en_nivel_profundo_crea_niveles_intermedios(self):
        r = analizar(">>> directo")
        self.assertEqual(max(c.atributos["nivel"] for c in buscar_nodos(r, "<cita>")), 3)


class PruebasEnLineaRecursivo(unittest.TestCase):

    def test_negrita_contiene_cursiva(self):
        r = analizar("**a *b* c**")
        negrita = buscar_nodos(r, "<negrita>")[0]
        interior = [n for n in recorrer(negrita) if n.tipo == "<cursiva>"]
        self.assertEqual(len(interior), 1)

    def test_cursiva_contiene_negrita(self):
        r = analizar("*a **b** c*")
        cursiva = buscar_nodos(r, "<cursiva>")[0]
        self.assertEqual(len([n for n in recorrer(cursiva) if n.tipo == "<negrita>"]), 1)

    def test_codigo_inline_dentro_de_negrita(self):
        r = analizar("**usa `x`**")
        self.assertEqual(len(buscar_nodos(r, "<codigo_inline>")), 1)
        self.assertTrue(r.exito)

    def test_parrafo_de_varias_lineas_es_un_solo_bloque(self):
        r = analizar("linea uno\nlinea dos\nlinea tres")
        self.assertEqual([b.tipo for b in bloques(r)], ["<parrafo>"])

    def test_negrita_puede_cruzar_lineas_dentro_de_un_parrafo(self):
        r = analizar("**abre\ncierra** fin")
        self.assertTrue(r.exito)
        self.assertEqual(len(buscar_nodos(r, "<negrita>")), 1)

    def test_parrafo_seguido_de_encabezado_sin_linea_en_blanco(self):
        r = analizar("texto\n## Titulo")
        self.assertEqual([b.tipo for b in bloques(r)], ["<parrafo>", "<encabezado>"])


class PruebasRecuperacionDeErrores(unittest.TestCase):

    def test_token_inesperado_modo_panico_y_continua(self):
        tokens = [Token(T.DEDENT, "", 1, 1),
                  Token(T.TEXTO, "hola", 2, 1), Token(T.NUEVA_LINEA, "\n", 2, 5)]
        gestor = GestorErrores()
        arbol = AnalizadorSintactico(LexicoFalso(tokens), gestor).analizar()
        errores = gestor.ordenados()
        self.assertEqual([e.tipo for e in errores], [TipoError.TOKEN_INESPERADO])
        self.assertEqual(errores[0].fase, FaseError.SINTACTICO)
        self.assertEqual((errores[0].linea, errores[0].columna), (1, 1))
        # después del error el parser reconoce el párrafo siguiente
        tipos = [n.tipo for n in recorrer(arbol)]
        self.assertIn("<parrafo>", tipos)

    def test_varios_tokens_inesperados_se_reportan_todos(self):
        tokens = [Token(T.DEDENT, "", 1, 1), Token(T.INDENT, "", 2, 1),
                  Token(T.DEDENT, "", 3, 1)]
        gestor = GestorErrores()
        AnalizadorSintactico(LexicoFalso(tokens), gestor).analizar()
        self.assertEqual(gestor.cantidad(), 3)

    def test_el_parser_siempre_termina_con_entradas_raras(self):
        entradas = ["**", "*", "`", "```", ">", ">>", "- ", "#", "# ", "*****",
                    "- a\n        - b", "> > > > >", "`a\n`b", "***\n***"]
        for entrada in entradas:
            r = analizar(entrada)
            self.assertEqual(r.arbol.tipo, "<documento>", repr(entrada))

    def test_arbol_grande_no_desborda_la_recursion(self):
        texto = "\n".join(("- item **x**\n  - sub" if i % 3 else "# H%d\n\ntexto" % i)
                          for i in range(3000))
        r = analizar(texto)
        self.assertTrue(r.exito)
        self.assertGreater(contar_nodos(r.arbol), 10000)


if __name__ == "__main__":
    unittest.main()
