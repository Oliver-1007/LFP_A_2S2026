
from tokens import TipoToken as T
from gestor_errores import TipoError
from nodo_ast import NodoAST


## Parser descendente recursivo que construye el árbol de derivación
class AnalizadorSintactico:

    INICIO_BLOQUE = (T.NUMERAL, T.VINETA, T.CITA, T.CERCA_CODIGO, T.REGLA_HORIZONTAL,
                     T.TEXTO, T.NEGRITA, T.CURSIVA, T.CODIGO_INLINE)

    def __init__(self, lexico, gestor_errores):
        self._lexico = lexico
        self._gestor = gestor_errores
        self._buffer = []
        self._pos = 0
        self._pila_enfasis = []


    ## Manejo de tokens
    @property
    def tokens(self):
        """Todos los tokens consumidos del lexer (incluye los sintéticos)."""
        return list(self._buffer)

    def _mirar(self, k=0):
        while len(self._buffer) <= self._pos + k:
            self._buffer.append(self._lexico.siguiente_token())
        return self._buffer[self._pos + k]

    @property
    def _actual(self):
        return self._mirar(0)

    def _avanzar(self):
        token = self._actual
        if token.tipo != T.FIN:
            self._pos += 1
        return token


    ## Punto de entrada
    def analizar(self):
        return self._documento()


    ## Errores
    ## Modo pánico: reporta el token inesperado y lo descarta
    def _token_inesperado(self, token):
        lexema = token.lexema if token.lexema else token.tipo
        self._gestor.registrar_sintactico(
            TipoError.TOKEN_INESPERADO, lexema,
            "Token inesperado %s (%s) en línea %d, columna %d"
            % (repr(lexema.replace("\n", "\\n")), token.tipo, token.linea, token.columna),
            token.linea, token.columna)
        self._avanzar()

    ## Consume NUEVA_LINEA y lo agrega al nodo
    def _fin_de_linea(self, nodo):
        if self._actual.tipo == T.NUEVA_LINEA:
            nodo.agregar(NodoAST.hoja(self._avanzar()))
        else:
            t = self._actual
            self._gestor.registrar_sintactico(
                TipoError.TOKEN_INESPERADO, t.lexema or t.tipo,
                "Se esperaba fin de línea y se encontró %s en línea %d, columna %d"
                % (t.tipo, t.linea, t.columna), t.linea, t.columna)


    # <documento> y <bloque>
    def _documento(self):
        raiz = NodoAST("<documento>")
        nodo = raiz
        while True:
            t = self._actual
            if t.tipo == T.FIN:
                nodo.agregar(NodoAST.epsilon())
                break
            if t.tipo == T.SALTO_PARRAFO:
                nodo.agregar(NodoAST.hoja(self._avanzar()))
            elif t.tipo in self.INICIO_BLOQUE:
                nodo.agregar(self._bloque())
            else:
                self._token_inesperado(t)
                continue
            siguiente = NodoAST("<documento>")
            nodo.agregar(siguiente)
            nodo = siguiente
        return raiz

    def _bloque(self):
        nodo = NodoAST("<bloque>")
        tipo = self._actual.tipo
        if tipo == T.NUMERAL:
            nodo.agregar(self._encabezado())
        elif tipo == T.VINETA:
            nodo.agregar(self._lista())
        elif tipo == T.CITA:
            nodo.agregar(self._cita(1))
        elif tipo == T.CERCA_CODIGO:
            nodo.agregar(self._bloque_codigo())
        elif tipo == T.REGLA_HORIZONTAL:
            nodo.agregar(self._regla_horizontal())
        else:
            nodo.agregar(self._parrafo())
        return nodo


    # Bloques
    def _encabezado(self):
        marca = self._avanzar()
        nodo = NodoAST("<encabezado>", nivel=marca.nivel)
        nodo.agregar(NodoAST.hoja(marca))
        nodo.agregar(self._en_linea())
        self._fin_de_linea(nodo)
        return nodo

    def _parrafo(self):
        nodo = NodoAST("<parrafo>")
        nodo.agregar(self._en_linea())
        self._fin_de_linea(nodo)
        return nodo

    def _regla_horizontal(self):
        nodo = NodoAST("<regla_horizontal>")
        nodo.agregar(NodoAST.hoja(self._avanzar()))
        return nodo

    def _bloque_codigo(self):
        nodo = NodoAST("<bloque_codigo>", lenguaje="", contenido="")
        nodo.agregar(NodoAST.hoja(self._avanzar()))
        if self._actual.tipo == T.LENGUAJE:
            t = self._avanzar()
            nodo.atributos["lenguaje"] = t.lexema
            nodo.agregar(NodoAST.hoja(t))
        if self._actual.tipo == T.TEXTO_LITERAL:
            t = self._avanzar()
            nodo.atributos["contenido"] = t.lexema
            nodo.agregar(NodoAST.hoja(t))
        if self._actual.tipo == T.CERCA_CODIGO:
            nodo.agregar(NodoAST.hoja(self._avanzar()))
        return nodo

    # listas
    def _lista(self):
        """<lista> ::= <item_lista> <lista> | <item_lista>"""
        raiz = NodoAST("<lista>")
        nodo = raiz
        while True:
            nodo.agregar(self._item_lista())
            if self._actual.tipo == T.VINETA:
                siguiente = NodoAST("<lista>")
                nodo.agregar(siguiente)
                nodo = siguiente
            else:
                break
        return raiz

    ## <item_lista> ::= VIÑETA <en_linea> NUEVA_LINEA <sublista>*
    def _item_lista(self):
        marca = self._avanzar()
        if marca.error is not None:
            self._gestor.registrar_sintactico(
                TipoError.INDENTACION_INVALIDA, marca.lexema,
                "Indentación inválida en línea %d, columna %d" % (marca.linea, marca.columna),
                marca.linea, marca.columna)
        nodo = NodoAST("<item_lista>")
        nodo.agregar(NodoAST.hoja(marca))
        nodo.agregar(self._en_linea())
        self._fin_de_linea(nodo)
        while self._actual.tipo == T.INDENT:
            nodo.agregar(self._sublista())
        return nodo

    ## <sublista> ::= INDENT <lista> DEDENT
    def _sublista(self):
        nodo = NodoAST("<sublista>")
        nodo.agregar(NodoAST.hoja(self._avanzar()))
        nodo.agregar(self._lista())
        if self._actual.tipo == T.DEDENT:
            nodo.agregar(NodoAST.hoja(self._avanzar()))
        return nodo

    ## citas
    ## <cita> ::= <elemento_cita> <cita> | <elemento_cita>  (nivel = profundidad actual)
    def _cita(self, nivel):
        raiz = NodoAST("<cita>", nivel=nivel)
        nodo = raiz
        while True:
            nodo.agregar(self._elemento_cita(nivel))
            t = self._actual
            if t.tipo == T.CITA and t.nivel >= nivel:
                siguiente = NodoAST("<cita>", nivel=nivel)
                nodo.agregar(siguiente)
                nodo = siguiente
            else:
                break
        return raiz

    ## <elemento_cita> ::= <linea_cita> | <cita> más profunda
    def _elemento_cita(self, nivel):
        nodo = NodoAST("<elemento_cita>")
        if self._actual.nivel == nivel:
            nodo.agregar(self._linea_cita())
        else:
            nodo.agregar(self._cita(nivel + 1))
        return nodo

    ## <linea_cita> ::= CITA <en_linea> NUEVA_LINEA
    def _linea_cita(self):
        marca = self._avanzar()
        if marca.error is not None:
            linea, columna = marca.error
            self._gestor.registrar_sintactico(
                TipoError.CITA_MAL_FORMADA, ">",
                "Cita mal formada en línea %d, columna %d" % (linea, columna),
                linea, columna)
        nodo = NodoAST("<linea_cita>", nivel=marca.nivel)
        nodo.agregar(NodoAST.hoja(marca))
        nodo.agregar(self._en_linea())
        self._fin_de_linea(nodo)
        return nodo


    ## Contenido en línea (recursión mutua en_linea / negrita / cursiva)
    def _es_elemento_linea(self, token):
        if token.tipo in (T.TEXTO, T.SALTO_LINEA, T.CODIGO_INLINE):
            return True
        if token.tipo in (T.NEGRITA, T.CURSIVA):
            # Si cierra el énfasis actual, termina <en_linea>
            return not (self._pila_enfasis and self._pila_enfasis[-1] == token.tipo)
        return False

    ## <en_linea> ::= <elemento_linea> <en_linea> | ε
    def _en_linea(self):
        raiz = NodoAST("<en_linea>")
        nodo = raiz
        while self._es_elemento_linea(self._actual):
            nodo.agregar(self._elemento_linea())
            siguiente = NodoAST("<en_linea>")
            nodo.agregar(siguiente)
            nodo = siguiente
        nodo.agregar(NodoAST.epsilon())
        return raiz

    def _elemento_linea(self):
        nodo = NodoAST("<elemento_linea>")
        tipo = self._actual.tipo
        if tipo == T.NEGRITA:
            nodo.agregar(self._enfasis("<negrita>", T.NEGRITA))
        elif tipo == T.CURSIVA:
            nodo.agregar(self._enfasis("<cursiva>", T.CURSIVA))
        elif tipo == T.CODIGO_INLINE:
            nodo.agregar(self._codigo_inline())
        else:
            nodo.agregar(NodoAST.hoja(self._avanzar()))
        return nodo

    ## <negrita> ::= NEGRITA <en_linea> NEGRITA   (idem <cursiva>)
    def _enfasis(self, nombre, tipo_delimitador):
        nodo = NodoAST(nombre)
        nodo.agregar(NodoAST.hoja(self._avanzar()))
        self._pila_enfasis.append(tipo_delimitador)
        nodo.agregar(self._en_linea())
        self._pila_enfasis.pop()
        if self._actual.tipo == tipo_delimitador:
            nodo.agregar(NodoAST.hoja(self._avanzar()))
        return nodo

    ## <codigo_inline> ::= CODIGO_INLINE [TEXTO_LITERAL] CODIGO_INLINE
    def _codigo_inline(self):
        nodo = NodoAST("<codigo_inline>", contenido="")
        nodo.agregar(NodoAST.hoja(self._avanzar()))
        if self._actual.tipo == T.TEXTO_LITERAL:
            t = self._avanzar()
            nodo.atributos["contenido"] = t.lexema
            nodo.agregar(NodoAST.hoja(t))
        if self._actual.tipo == T.CODIGO_INLINE:
            nodo.agregar(NodoAST.hoja(self._avanzar()))
        return nodo
