
class TipoError:
    """Tipos de error definidos en la sección 4.9 del enunciado."""

    NEGRITA_SIN_CERRAR = "NEGRITA_SIN_CERRAR"
    CURSIVA_SIN_CERRAR = "CURSIVA_SIN_CERRAR"
    CODIGO_INLINE_SIN_CERRAR = "CODIGO_INLINE_SIN_CERRAR"
    BLOQUE_CODIGO_SIN_CERRAR = "BLOQUE_CODIGO_SIN_CERRAR"
    ENCABEZADO_INVALIDO = "ENCABEZADO_INVALIDO"
    INDENTACION_INVALIDA = "INDENTACION_INVALIDA"
    CITA_MAL_FORMADA = "CITA_MAL_FORMADA"

    TOKEN_INESPERADO = "TOKEN_INESPERADO"


class FaseError:
    LEXICO = "Léxico"
    SINTACTICO = "Sintáctico"


## Un error individual con su posición exacta
class ErrorAnalisis:

    __slots__ = ("tipo", "fase", "lexema", "descripcion", "linea", "columna")

    def __init__(self, tipo, fase, lexema, descripcion, linea, columna):
        self.tipo = tipo
        self.fase = fase
        self.lexema = lexema
        self.descripcion = descripcion
        self.linea = linea
        self.columna = columna

    def lexema_visible(self, maximo=40):
        texto = self.lexema.replace("\n", "\\n")
        if len(texto) > maximo:
            texto = texto[:maximo - 1] + "…"
        return texto

    def __repr__(self):
        return "Error(%s, %d:%d)" % (self.tipo, self.linea, self.columna)


class GestorErrores:
    """Colección de errores del análisis."""

    def __init__(self):
        self._errores = []
        self._vistos = set()

    # registro
    def registrar(self, tipo, fase, lexema, descripcion, linea, columna):
        """Registra un error (ignora duplicados exactos de tipo y posición)."""
        clave = (tipo, linea, columna)
        if clave in self._vistos:
            return
        self._vistos.add(clave)
        self._errores.append(ErrorAnalisis(tipo, fase, lexema, descripcion, linea, columna))

    def registrar_lexico(self, tipo, lexema, descripcion, linea, columna):
        self.registrar(tipo, FaseError.LEXICO, lexema, descripcion, linea, columna)

    def registrar_sintactico(self, tipo, lexema, descripcion, linea, columna):
        self.registrar(tipo, FaseError.SINTACTICO, lexema, descripcion, linea, columna)

    # consulta
    def hay_errores(self):
        return len(self._errores) > 0

    def cantidad(self):
        return len(self._errores)

    ## Errores ordenados por posición en el documento (línea, columna)
    def ordenados(self):
        return sorted(self._errores, key=lambda e: (e.linea, e.columna))

    def limpiar(self):
        self._errores = []
        self._vistos = set()