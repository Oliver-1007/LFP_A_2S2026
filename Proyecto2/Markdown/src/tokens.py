
class TipoToken:
    """Catálogo de tipos de token reconocidos por el AFD léxico."""

    # Tokens de bloque 
    NUMERAL = "NUMERAL" 
    VINETA = "VIÑETA"
    INDENT = "INDENT"
    DEDENT = "DEDENT"
    CITA = "CITA"
    CERCA_CODIGO = "CERCA_CODIGO"
    LENGUAJE = "LENGUAJE_CODIGO"
    REGLA_HORIZONTAL = "REGLA_HORIZONTAL"
    SALTO_PARRAFO = "SALTO_PARRAFO"

    # Tokens en línea
    NEGRITA = "NEGRITA"
    CURSIVA = "CURSIVA"
    CODIGO_INLINE = "CODIGO_INLINE"
    TEXTO = "TEXTO"
    TEXTO_LITERAL = "TEXTO_LITERAL"

    # Tokens de control de línea
    SALTO_LINEA = "SALTO_LINEA"
    NUEVA_LINEA = "NUEVA_LINEA"
    FIN = "FIN"


class Token:
    """
    Unidad léxica producida por AnalizadorLexico.

    Atributos:
        tipo      -- uno de los valores de TipoToken.
        lexema    -- texto exacto reconocido en la entrada.
        linea     -- número de línea (base 1).
        columna   -- número de columna (base 1).
        nivel     -- nivel asociado (NUMERAL: 1-6, CITA: nivel de anidamiento).
        sintetico -- True si el lexer lo insertó para recuperarse de un error
                     (p. ej. cierre implícito de una negrita sin cerrar).
        error     -- (linea, columna) si el token exhibe un problema que el
                     parser debe reportar (indentación inválida, cita mal formada).
    """

    __slots__ = ("tipo", "lexema", "linea", "columna", "nivel", "sintetico", "error")

    def __init__(self, tipo, lexema, linea, columna, nivel=0, sintetico=False, error=None):
        self.tipo = tipo
        self.lexema = lexema
        self.linea = linea
        self.columna = columna
        self.nivel = nivel
        self.sintetico = sintetico
        self.error = error

    def lexema_visible(self, maximo=60):
        """Representación del lexema apta para tablas (sin saltos de línea reales)."""
        if self.tipo in (TipoToken.INDENT, TipoToken.DEDENT):
            return "(virtual)"
        if self.tipo == TipoToken.FIN:
            return "EOF"
        texto = self.lexema.replace("\n", "\\n")
        if len(texto) > maximo:
            texto = texto[:maximo - 1] + "…"
        return texto

    def __repr__(self):
        return "Token(%s, %r, %d:%d)" % (self.tipo, self.lexema, self.linea, self.columna)