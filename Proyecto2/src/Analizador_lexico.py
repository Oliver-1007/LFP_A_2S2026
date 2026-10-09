
from collections import deque

from tokens import Token, TipoToken as T
from gestor_errores import TipoError


## Clases de línea que distingue el AFD de inicio de línea
class TipoLinea:

    VACIA = "VACIA"
    NUMERAL = "NUMERAL"
    NUMERAL_INVALIDO = "NUMERAL_INVALIDO"
    VINETA = "VINETA"
    CITA = "CITA"
    CERCA = "CERCA"
    REGLA = "REGLA"
    TEXTO = "TEXTO"


class ClasificacionLinea:
    """Resultado de reconocer el inicio de una línea."""

    __slots__ = ("tipo", "indentacion", "columna", "inicio", "lexema", "nivel", "error_col")

    def __init__(self, tipo, indentacion=0, columna=1, inicio=0, lexema="", nivel=0, error_col=None):
        self.tipo = tipo
        self.indentacion = indentacion
        self.columna = columna
        self.inicio = inicio
        self.lexema = lexema
        self.nivel = nivel
        self.error_col = error_col


## Convierte el texto Markdown en tokens mediante siguiente_token()
class AnalizadorLexico:

    Q_INDENT = "Q_INDENT"
    Q_HASH = "Q_HASH"
    Q_GUION = "Q_GUION"
    Q_BULLET = "Q_BULLET"
    Q_TICK = "Q_TICK"

    Q_TEXTO = "Q_TEXTO"
    Q_ASTERISCO = "Q_ASTERISCO"
    Q_CODIGO = "Q_CODIGO"

    def __init__(self, texto, gestor_errores):
        self._gestor = gestor_errores
        texto = texto.replace("\ufeff", "").replace("\r\n", "\n").replace("\r", "\n")
        lineas = texto.split("\n")
        if lineas and lineas[-1] == "":
            lineas.pop()
        self._lineas = lineas
        self._idx = 0
        self._cola = deque()
        self._niveles = []
        self._pila_enfasis = []
        self._fin_emitido = False
        self._token_fin = None


    # Devuelve el siguiente token; tras el final devuelve siempre FIN
    def siguiente_token(self):
        while not self._cola:
            if self._idx < len(self._lineas):
                self._procesar_linea()
            elif not self._fin_emitido:
                self._finalizar()
            else:
                return self._token_fin
        return self._cola.popleft()

    ## Conveniencia: devuelve la lista completa de tokens
    def tokenizar(self):
        tokens = []
        while True:
            token = self.siguiente_token()
            tokens.append(token)
            if token.tipo == T.FIN:
                return tokens

    # Utilidades internas
    def _emitir(self, tipo, lexema, linea, columna, nivel=0, sintetico=False, error=None):
        token = Token(tipo, lexema, linea, columna, nivel, sintetico, error)
        self._cola.append(token)
        return token

    def _finalizar(self):
        ultima = len(self._lineas) + 1
        self._cerrar_indentacion(ultima, 1)
        self._token_fin = self._emitir(T.FIN, "", ultima, 1)
        self._fin_emitido = True

    @staticmethod
    def _resto_vacio(linea, i):
        """True si desde i solo hay espacios o tabuladores."""
        while i < len(linea):
            if linea[i] not in " \t":
                return False
            i += 1
        return True

    @staticmethod
    def _es_cierre_cerca(linea):
        """Una línea cierra un bloque de código si solo contiene 3+ acentos graves."""
        cantidad = 0
        for c in linea:
            if c == "`":
                cantidad += 1
            elif c not in " \t":
                return False
        return cantidad >= 3


    # AFD 1: reconocimiento del inicio de línea
    def _clasificar(self, linea):
        n = len(linea)
        i = 0
        indentacion = 0
        cantidad = 0
        columna = 1
        marca = 0
        estado = self.Q_INDENT

        while True:
            c = linea[i] if i < n else "" 

            if estado == self.Q_INDENT:
                if c == " ":
                    indentacion += 1
                    i += 1
                elif c == "\t":
                    indentacion += 2
                    i += 1
                elif c == "":
                    return ClasificacionLinea(TipoLinea.VACIA, indentacion, i + 1, i)
                else:
                    columna = i + 1
                    marca = i
                    if c == "#":
                        estado = self.Q_HASH
                    elif c == ">":
                        return self._reconocer_cita(linea, i, indentacion)
                    elif c == "-":
                        estado = self.Q_GUION
                    elif c == "*" or c == "+":
                        estado = self.Q_BULLET
                    elif c == "`":
                        estado = self.Q_TICK
                    else:
                        return ClasificacionLinea(TipoLinea.TEXTO, indentacion, columna, i)

            elif estado == self.Q_HASH:
                if c == "#":
                    cantidad += 1
                    i += 1
                else:
                    lexema = "#" * cantidad
                    if cantidad > 6:
                        return ClasificacionLinea(TipoLinea.NUMERAL_INVALIDO, indentacion,
                                                  columna, marca, lexema, cantidad)
                    if c == " " or c == "\t":
                        j = i
                        while j < n and linea[j] in " \t":
                            j += 1
                        return ClasificacionLinea(TipoLinea.NUMERAL, indentacion,
                                                  columna, j, lexema, cantidad)
                    # '#sinespacio' => texto plano
                    return ClasificacionLinea(TipoLinea.TEXTO, indentacion, columna, marca)

            elif estado == self.Q_GUION:
                if c == "-":
                    cantidad += 1
                    i += 1
                else:
                    if cantidad == 1 and (c == " " or c == "\t"):
                        j = i
                        while j < n and linea[j] in " \t":
                            j += 1
                        return ClasificacionLinea(TipoLinea.VINETA, indentacion, columna, j, "-")
                    if cantidad >= 3 and self._resto_vacio(linea, i):
                        return ClasificacionLinea(TipoLinea.REGLA, indentacion, columna, marca,
                                                  "-" * cantidad)
                    return ClasificacionLinea(TipoLinea.TEXTO, indentacion, columna, marca)

            elif estado == self.Q_BULLET:
                # c es '*' o '+' (aún no consumido): solo es viñeta si le sigue un espacio
                siguiente = linea[i + 1] if i + 1 < n else ""
                if siguiente == " " or siguiente == "\t":
                    j = i + 1
                    while j < n and linea[j] in " \t":
                        j += 1
                    return ClasificacionLinea(TipoLinea.VINETA, indentacion, columna, j, c)
                return ClasificacionLinea(TipoLinea.TEXTO, indentacion, columna, marca)

            elif estado == self.Q_TICK:
                if c == "`":
                    cantidad += 1
                    i += 1
                else:
                    if cantidad >= 3:
                        return ClasificacionLinea(TipoLinea.CERCA, indentacion, columna, i, "`" * cantidad)
                    return ClasificacionLinea(TipoLinea.TEXTO, indentacion, columna, marca)

    def _reconocer_cita(self, linea, i, indentacion):
        n = len(linea)
        niveles = 0
        j = i
        ultimo = i
        error_col = None
        while True:
            niveles += 1
            ultimo = j
            j += 1
            siguiente = linea[j] if j < n else ""
            if siguiente == ">":
                continue
            if siguiente == " " or siguiente == "\t":
                k = j
                while k < n and linea[k] in " \t":
                    k += 1
                if k < n and linea[k] == ">":
                    j = k                # notación '> >'
                    continue
                j = k
                break
            if siguiente == "":
                break
            error_col = ultimo + 1
            break
        return ClasificacionLinea(TipoLinea.CITA, indentacion, i + 1, j,
                                  linea[i:ultimo + 1], niveles, error_col)


    # Procesamiento por línea
    def _procesar_linea(self):
        linea = self._lineas[self._idx]
        num = self._idx + 1
        clase = self._clasificar(linea)
        tipo = clase.tipo

        # Línea en blanco -> un único SALTO_PARRAFO
        if tipo == TipoLinea.VACIA:
            self._cerrar_indentacion(num, 1)
            self._emitir(T.SALTO_PARRAFO, "\n", num, 1)
            self._idx += 1
            while (self._idx < len(self._lineas)
                   and self._clasificar(self._lineas[self._idx]).tipo == TipoLinea.VACIA):
                self._idx += 1
            return

        # Toda línea que no sea viñeta termina la lista en curso
        if tipo != TipoLinea.VINETA:
            self._cerrar_indentacion(num, clase.columna)

        if tipo == TipoLinea.CERCA:
            self._procesar_bloque_codigo(clase, linea, num)
            return

        if tipo == TipoLinea.REGLA:
            self._emitir(T.REGLA_HORIZONTAL, clase.lexema, num, clase.columna)
            self._idx += 1
            return

        # Marcadores de línea (seguidos de contenido en línea)
        if tipo == TipoLinea.NUMERAL:
            self._emitir(T.NUMERAL, clase.lexema, num, clase.columna, nivel=clase.nivel)
        elif tipo == TipoLinea.NUMERAL_INVALIDO:
            self._gestor.registrar_lexico(
                TipoError.ENCABEZADO_INVALIDO, clase.lexema,
                "Encabezado inválido en línea %d: máximo 6 niveles" % num,
                num, clase.columna)
        elif tipo == TipoLinea.CITA:
            error = (num, clase.error_col) if clase.error_col else None
            self._emitir(T.CITA, clase.lexema, num, clase.columna, nivel=clase.nivel, error=error)
        elif tipo == TipoLinea.VINETA:
            self._procesar_indentacion(clase, num)

        self._procesar_contenido(clase, linea, num)

    ## Escanea el contenido en línea y emite el token de fin de línea
    def _procesar_contenido(self, clase, linea, num):
        self._escanear(linea, num, clase.inicio)

        es_texto = clase.tipo in (TipoLinea.TEXTO, TipoLinea.NUMERAL_INVALIDO)
        continua = False
        if es_texto and self._idx + 1 < len(self._lineas):
            siguiente = self._clasificar(self._lineas[self._idx + 1]).tipo
            continua = siguiente in (TipoLinea.TEXTO, TipoLinea.NUMERAL_INVALIDO)

        col_fin = len(linea) + 1
        if continua:
            # El párrafo sigue en la línea siguiente: los énfasis pueden continuar
            self._emitir(T.SALTO_LINEA, "\n", num, col_fin)
        else:
            # Fin del bloque: los delimitadores abiertos quedan sin cerrar
            self._cerrar_enfasis(num, col_fin)
            self._emitir(T.NUEVA_LINEA, "\n", num, col_fin)
        self._idx += 1


    # Indentación 
    def _procesar_indentacion(self, clase, num):
        """Genera INDENT/DEDENT y la VIÑETA, marcando saltos de indentación inválidos."""
        nivel = clase.indentacion // 2
        col = clase.columna
        invalido = False

        if not self._niveles:
            self._niveles = [nivel]
            if nivel > 1:
                invalido = True
        elif nivel < self._niveles[0]:
            while len(self._niveles) > 1:
                self._niveles.pop()
                self._emitir(T.DEDENT, "", num, col)
            self._niveles[0] = nivel
            invalido = True
        elif nivel > self._niveles[-1]:
            if nivel - self._niveles[-1] > 1:
                invalido = True
            self._niveles.append(nivel)
            self._emitir(T.INDENT, "", num, col)
        elif nivel < self._niveles[-1]:
            while len(self._niveles) > 1 and self._niveles[-1] > nivel:
                self._niveles.pop()
                self._emitir(T.DEDENT, "", num, col)
            if self._niveles[-1] < nivel:
                invalido = True
                self._niveles.append(nivel)
                self._emitir(T.INDENT, "", num, col)

        error = (num, col) if invalido else None
        self._emitir(T.VINETA, clase.lexema, num, col, error=error)

    def _cerrar_indentacion(self, num, col):
        """Emite los DEDENT pendientes y reinicia el estado de lista."""
        while len(self._niveles) > 1:
            self._niveles.pop()
            self._emitir(T.DEDENT, "", num, col)
        self._niveles = []


    # AFD 2: contenido en línea
    def _escanear(self, linea, num, desde):
        """Tokeniza TEXTO, NEGRITA, CURSIVA y CODIGO_INLINE desde el índice `desde`."""
        fin = len(linea)
        while fin > desde and linea[fin - 1] in " \t":
            fin -= 1
        i = desde
        while i < fin:
            c = linea[i]
            if c == "*":
                estado = self.Q_ASTERISCO
            elif c == "`":
                estado = self.Q_CODIGO
            else:
                estado = self.Q_TEXTO

            if estado == self.Q_TEXTO:
                j = i
                while j < fin and linea[j] != "*" and linea[j] != "`":
                    j += 1
                self._emitir(T.TEXTO, linea[i:j], num, i + 1)
                i = j
            elif estado == self.Q_ASTERISCO:
                i = self._reconocer_asteriscos(linea, num, i, fin)
            else:
                i = self._reconocer_codigo(linea, num, i, fin)

    ## Maximal munch: '**' es NEGRITA antes que dos CURSIVA. '***' se separa según el contexto
    def _reconocer_asteriscos(self, linea, num, i, fin):
        k = 0
        while i + k < fin and linea[i + k] == "*":
            k += 1
        tope = self._pila_enfasis[-1][0] if self._pila_enfasis else None
        if k >= 3 and tope == T.CURSIVA:
            tipo, ancho = T.CURSIVA, 1
        elif k >= 2:
            tipo, ancho = T.NEGRITA, 2
        else:
            tipo, ancho = T.CURSIVA, 1
        self._delimitador(tipo, "*" * ancho, num, i + 1)
        return i + ancho

    ## Abre o cierra un énfasis manteniendo un anidamiento correcto
    def _delimitador(self, tipo, lexema, num, col):
        pila = self._pila_enfasis
        posicion = None
        for idx in range(len(pila) - 1, -1, -1):
            if pila[idx][0] == tipo:
                posicion = idx
                break
        if posicion is None:
            pila.append((tipo, num, col))
            self._emitir(tipo, lexema, num, col)
        else:
            while len(pila) - 1 > posicion:
                self._reportar_sin_cerrar(pila.pop(), num, col)
            pila.pop()
            self._emitir(tipo, lexema, num, col)

    ## Registra el error de un delimitador sin cierre e inserta su cierre sintético
    def _reportar_sin_cerrar(self, apertura, num, col):
        tipo, linea_ap, col_ap = apertura
        if tipo == T.NEGRITA:
            self._gestor.registrar_lexico(
                TipoError.NEGRITA_SIN_CERRAR, "**",
                "Negrita sin cerrar iniciada en línea %d, columna %d" % (linea_ap, col_ap),
                linea_ap, col_ap)
        else:
            self._gestor.registrar_lexico(
                TipoError.CURSIVA_SIN_CERRAR, "*",
                "Cursiva sin cerrar iniciada en línea %d, columna %d" % (linea_ap, col_ap),
                linea_ap, col_ap)
        self._emitir(tipo, "", num, col, sintetico=True)

    ## Al terminar un bloque, todo delimitador aún abierto es un error léxico
    def _cerrar_enfasis(self, num, col):
        while self._pila_enfasis:
            self._reportar_sin_cerrar(self._pila_enfasis.pop(), num, col)

    ## Código en línea: el contenido entre acentos graves es literal
    def _reconocer_codigo(self, linea, num, i, fin):
        j = i + 1
        while j < fin and linea[j] != "`":
            j += 1
        self._emitir(T.CODIGO_INLINE, "`", num, i + 1)
        if j > i + 1:
            self._emitir(T.TEXTO_LITERAL, linea[i + 1:j], num, i + 2)
        if j < fin:
            self._emitir(T.CODIGO_INLINE, "`", num, j + 1)
            return j + 1
        self._gestor.registrar_lexico(
            TipoError.CODIGO_INLINE_SIN_CERRAR, "`",
            "Código en línea sin cerrar iniciado en línea %d, columna %d" % (num, i + 1),
            num, i + 1)
        self._emitir(T.CODIGO_INLINE, "", num, fin + 1, sintetico=True)
        return fin


    ## Consume desde la cerca de apertura hasta la de cierre sin tokenizar el interior
    def _procesar_bloque_codigo(self, clase, linea, num):
        self._emitir(T.CERCA_CODIGO, clase.lexema, num, clase.columna)

        info = linea[clase.inicio:].strip()
        if info:
            col_info = clase.inicio + 1
            while col_info <= len(linea) and linea[col_info - 1] in " \t":
                col_info += 1
            self._emitir(T.LENGUAJE, info, num, col_info)

        contenido = []
        j = self._idx + 1
        cerrado = False
        while j < len(self._lineas):
            if self._es_cierre_cerca(self._lineas[j]):
                cerrado = True
                break
            contenido.append(self._lineas[j])
            j += 1

        if contenido:
            self._emitir(T.TEXTO_LITERAL, "\n".join(contenido), num + 1, 1)

        if cerrado:
            cierre = self._lineas[j]
            col = 1
            while cierre[col - 1] in " \t":
                col += 1
            self._emitir(T.CERCA_CODIGO, cierre.strip(), j + 1, col)
            self._idx = j + 1
        else:
            self._gestor.registrar_lexico(
                TipoError.BLOQUE_CODIGO_SIN_CERRAR, clase.lexema,
                "Bloque de código sin cerrar iniciado en línea %d" % num,
                num, clase.columna)
            self._emitir(T.CERCA_CODIGO, "", len(self._lineas), 1, sintetico=True)
            self._idx = len(self._lineas)