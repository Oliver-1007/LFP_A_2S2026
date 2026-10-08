

from __future__ import annotations

from typing import List, Optional

from .gestor_errores import GestorErrores
from .tokens import Token, TipoToken, TipoError


# Palabras reservadas

PALABRAS_BLOQUE = {"HORARIO", "CURSOS", "CATEDRATICOS", "AULAS", "CLASES"}
PALABRAS_ELEMENTO = {"curso", "catedratico", "aula", "clase"}
PALABRAS_RELACION = {"con", "en"}
PALABRAS_ATRIBUTO = {
    "codigo", "creditos", "categoria", "capacidad", "edificio",
    "dia", "inicio", "fin", "seccion",
}
DIAS_VALIDOS = {"LUNES", "MARTES", "MIERCOLES", "JUEVES", "VIERNES", "SABADO", "DOMINGO"}
CATEGORIAS_VALIDAS = {"TITULAR", "INTERINO", "AUXILIAR"}

SIMBOLOS_VALIDOS = set("{}[]:,;")
ESPACIOS_EN_BLANCO = {" ", "\t", "\r", "\n"}

HORA_MIN_INSTITUCIONAL = 6 * 60       # 06:00
HORA_MAX_INSTITUCIONAL = 21 * 60      # 21:00


class AnalizadorLexico:
    def __init__(self, texto: str) -> None:
        self.texto = texto
        self.longitud = len(texto)
        self.pos = 0
        self.linea = 1
        self.columna = 1
        self.gestor_errores = GestorErrores()
        self.contexto_esperado: Optional[str] = None

    # Utilidades de bajo nivel sobre el buffer de entrada

    def _actual(self) -> Optional[str]:
        if self.pos < self.longitud:
            return self.texto[self.pos]
        return None

    def _adelante(self, offset: int = 1) -> Optional[str]:
        idx = self.pos + offset
        if idx < self.longitud:
            return self.texto[idx]
        return None

    ## Consume el caracter actual, actualiza linea/columna y lo retorna
    def _avanzar(self) -> str:
        c = self.texto[self.pos]
        self.pos += 1
        if c == "\n":
            self.linea += 1
            self.columna = 1
        else:
            self.columna += 1
        return c

    def _saltar_espacios(self) -> None:
        while self._actual() is not None and self._actual() in ESPACIOS_EN_BLANCO:
            self._avanzar()

    def _registrar_error(self, lexema: str, tipo: TipoError, descripcion: str,
                          linea: int, columna: int) -> None:
        self.gestor_errores.agregar(lexema, tipo, descripcion, linea, columna)

    # Logica 

    def siguiente_token(self) -> Optional[Token]:
        while True:
            self._saltar_espacios()
            if self.pos >= self.longitud:
                return None

            c = self._actual()
            linea_i, columna_i = self.linea, self.columna

            if c == "#":
                if self._adelante() == "#":
                    return self._leer_comentario(linea_i, columna_i)
                self._avanzar()
                self._registrar_error(
                    c, TipoError.CARACTER_NO_RECONOCIDO,
                    f"Caracter no reconocido: '{c}' en linea {linea_i}, columna {columna_i}",
                    linea_i, columna_i,
                )
                continue

            if c == '"':
                token = self._leer_cadena(linea_i, columna_i)
                if token is None:
                    continue
                return token

            if c.isdigit():
                token = self._leer_numero(linea_i, columna_i)
                if token is None:
                    continue
                return token

            if c.isalpha():
                token = self._leer_palabra(linea_i, columna_i)
                if token is None:
                    continue
                return token

            if c in SIMBOLOS_VALIDOS:
                self._avanzar()
                return Token(TipoToken.SIMBOLO, c, linea_i, columna_i)

            # Cualquier otro caracter no pertenece al alfabeto del lenguaje.
            self._avanzar()
            self._registrar_error(
                c, TipoError.CARACTER_NO_RECONOCIDO,
                f"Caracter no reconocido: '{c}' en linea {linea_i}, columna {columna_i}",
                linea_i, columna_i,
            )
            continue

    def analizar(self) -> List[Token]:
        tokens: List[Token] = []
        numero = 0
        while True:
            token = self.siguiente_token()
            if token is None:
                break
            numero += 1
            token.numero = numero
            tokens.append(token)
        return tokens

    # -- Subautomatas ---------------------------------------------------------

    def _leer_comentario(self, linea_i: int, columna_i: int) -> Token:
        """Consume '##' y todo lo que sigue hasta '\\n' o EOF."""
        letras = [self._avanzar(), self._avanzar()]  # '#', '#'
        while self._actual() is not None and self._actual() != "\n":
            letras.append(self._avanzar())
        lexema = "".join(letras)
        return Token(TipoToken.COMENTARIO_LINEA, lexema, linea_i, columna_i)

    def _leer_cadena(self, linea_i: int, columna_i: int) -> Optional[Token]:
        caracteres = [self._avanzar()]  # comilla de apertura
        while True:
            c = self._actual()
            if c is None or c == "\n":
                lexema = "".join(caracteres)
                self._registrar_error(
                    lexema, TipoError.CADENA_SIN_CERRAR,
                    f"Cadena sin cerrar iniciada en linea {linea_i}, columna {columna_i}",
                    linea_i, columna_i,
                )
                return None
            caracteres.append(self._avanzar())
            if c == '"':
                lexema = "".join(caracteres)
                return self._clasificar_literal_entre_comillas(lexema, linea_i, columna_i)

    def _forma_de_codigo(self, interior: str) -> bool:
        posicion_guion = -1
        cantidad_guiones = 0
        
        # Buscar la posición y cantidad exacta de guiones
        for indice in range(len(interior)):
            if interior[indice] == "-":
                cantidad_guiones += 1
                if posicion_guion == -1:
                    posicion_guion = indice
                    
        # Un código debe tener obligatoriamente un solo guion
        if cantidad_guiones != 1:
            return False

        prefijo = interior[:posicion_guion]
        sufijo = interior[posicion_guion + 1:]
        
        if not (1 <= len(prefijo) <= 3):
            return False
            
        # Debe iniciar obligatoriamente con una letra
        if not prefijo[0].isalpha():
            return False
         
        #El resto puede ser alfanumérico
        for caracter in prefijo:
            if not caracter.isalnum():
                return False
                
        # El sufijo debe contener al menos un dígito
        if len(sufijo) == 0:
            return False
            
        # El sufijo debe ser exclusivamente numérico
        for caracter in sufijo:
            if not caracter.isdigit():
                return False
                
        return True

    def _clasificar_literal_entre_comillas(self, lexema: str, linea_i: int, columna_i: int) -> Optional[Token]:
        interior = lexema[1:-1] if len(lexema) >= 2 else ""

        # Verificación directa de formato válido
        if self._forma_de_codigo(interior):
            return Token(TipoToken.CODIGO, lexema, linea_i, columna_i)

        # Buscar si el interior tiene un guion
        contiene_guion = False
        for caracter in interior:
            if caracter == "-":
                contiene_guion = True
                break
                
        # Si no tiene guion, es simplemente un texto libre 
        if not contiene_guion:
            return Token(TipoToken.CADENA, lexema, linea_i, columna_i)

        # Si tiene guion pero no cumplió _forma_de_codigo, aplicamos una regla
        # básica: si contiene espacios asume que es una CADENA normal (ej. "Curso - 1").
        tiene_espacios = False
        for caracter in interior:
            if caracter == " ":
                tiene_espacios = True
                break

        if not tiene_espacios:
            self._registrar_error(
                lexema, TipoError.CODIGO_MAL_FORMADO,
                f"Codigo mal formado: '{lexema}' en linea {linea_i}, columna {columna_i}",
                linea_i, columna_i,
            )
            return None
            
        # Si tiene guion pero también espacios, es una CADENA regular válida
        return Token(TipoToken.CADENA, lexema, linea_i, columna_i)

    def _leer_digitos(self) -> str:
        digitos = []
        while self._actual() is not None and self._actual().isdigit():
            digitos.append(self._avanzar())
        return "".join(digitos)

    def _leer_numero(self, linea_i: int, columna_i: int) -> Optional[Token]:
        parte_entera = self._leer_digitos()

        siguiente = self._actual()
        if siguiente == ":":
            self._avanzar()
            minutos_str = self._leer_digitos()
            lexema = f"{parte_entera}:{minutos_str}"
            return self._validar_hora(lexema, parte_entera, minutos_str, linea_i, columna_i)

        if siguiente == "-":
            self._avanzar()
            digitos_str = self._leer_digitos()
            sufijo_invalido = self._leer_continuacion_codigo()
            lexema = f"{parte_entera}-{digitos_str}"
            if sufijo_invalido:
                lexema += sufijo_invalido
            return self._validar_codigo(lexema, digitos_str, linea_i, columna_i)

        return Token(TipoToken.ENTERO, parte_entera, linea_i, columna_i)

    def _validar_hora(self, lexema: str, horas_str: str, minutos_str: str,
                       linea_i: int, columna_i: int) -> Optional[Token]:
        formato_valido = len(horas_str) == 2 and len(minutos_str) == 2
        if formato_valido:
            horas, minutos = int(horas_str), int(minutos_str)
            total_minutos = horas * 60 + minutos
            dentro_de_rango = (
                0 <= minutos <= 59
                and HORA_MIN_INSTITUCIONAL <= total_minutos <= HORA_MAX_INSTITUCIONAL
            )
        else:
            dentro_de_rango = False

        if not formato_valido or not dentro_de_rango:
            self._registrar_error(
                lexema, TipoError.HORA_FUERA_DE_RANGO,
                f"Hora fuera de rango en linea {linea_i}, columna {columna_i}",
                linea_i, columna_i,
            )
            return None
        return Token(TipoToken.HORA, lexema, linea_i, columna_i)

    ##Subautomata alfabetico: consume letras y decide entre CODIGO,
    ##palabra reservada, DIA o CATEGORIA
    def _leer_palabra(self, linea_i: int, columna_i: int) -> Optional[Token]:
        
        letras = []
        while self._actual() is not None and self._actual().isalpha():
            letras.append(self._avanzar())
        palabra = "".join(letras)

        if self._actual() == "-":
            self._avanzar()
            digitos_str = self._leer_digitos()
            sufijo_invalido = self._leer_continuacion_codigo()
            lexema = f"{palabra}-{digitos_str}"
            if sufijo_invalido:
                lexema += sufijo_invalido
            return self._validar_codigo(lexema, digitos_str, linea_i, columna_i)

        return self._clasificar_palabra(palabra, linea_i, columna_i)

    def _validar_codigo(self, lexema: str, digitos_str: str,
                         linea_i: int, columna_i: int) -> Optional[Token]:
        posicion_guion = -1
        for indice in range(len(lexema)):
            if lexema[indice] == "-":
                posicion_guion = indice
                break
        prefijo = lexema[:posicion_guion] if posicion_guion >= 0 else ""
        sufijo = lexema[posicion_guion + 1:] if posicion_guion >= 0 else ""
        prefijo_valido = len(prefijo) > 0 and prefijo[0].isalpha()
        for caracter in prefijo:
            prefijo_valido = prefijo_valido and caracter.isalnum()
        sufijo_valido = len(sufijo) > 0
        for caracter in sufijo:
            sufijo_valido = sufijo_valido and caracter.isdigit()
        if not prefijo_valido or not sufijo_valido or not digitos_str:
            self._registrar_error(
                lexema, TipoError.CODIGO_MAL_FORMADO,
                f"Codigo mal formado: '{lexema}' en linea {linea_i}, columna {columna_i}",
                linea_i, columna_i,
            )
            return None
        return Token(TipoToken.CODIGO, lexema, linea_i, columna_i)

    def _leer_continuacion_codigo(self) -> str:
        """Consume letras, digitos o guiones pegados al candidato actual."""
        caracteres = []
        while self._actual() is not None:
            caracter = self._actual()
            if not (caracter.isalnum() or caracter == "-"):
                break
            caracteres.append(self._avanzar())
        return "".join(caracteres)

    def _clasificar_palabra(self, palabra: str, linea_i: int, columna_i: int) -> Optional[Token]:
        resultado: Optional[Token] = None
        nuevo_contexto: Optional[str] = None

        if palabra in PALABRAS_BLOQUE:
            resultado = Token(TipoToken.PALABRA_RESERVADA_BLOQUE, palabra, linea_i, columna_i)
        elif palabra in PALABRAS_ELEMENTO:
            resultado = Token(TipoToken.PALABRA_RESERVADA_ELEMENTO, palabra, linea_i, columna_i)
        elif palabra in PALABRAS_RELACION:
            resultado = Token(TipoToken.PALABRA_RESERVADA_RELACION, palabra, linea_i, columna_i)
        elif palabra in PALABRAS_ATRIBUTO:
            resultado = Token(TipoToken.PALABRA_RESERVADA_ATRIBUTO, palabra, linea_i, columna_i)
            if palabra == "dia":
                nuevo_contexto = "DIA"
            elif palabra == "categoria":
                nuevo_contexto = "CATEGORIA"
        elif palabra in DIAS_VALIDOS:
            resultado = Token(TipoToken.DIA, palabra, linea_i, columna_i)
        elif palabra in CATEGORIAS_VALIDAS:
            resultado = Token(TipoToken.CATEGORIA, palabra, linea_i, columna_i)
        else:
            if self.contexto_esperado == "DIA":
                self._registrar_error(
                    palabra, TipoError.DIA_NO_RECONOCIDO,
                    f"Dia no reconocido: '{palabra}' en linea {linea_i}, columna {columna_i}",
                    linea_i, columna_i,
                )
            elif self.contexto_esperado == "CATEGORIA":
                self._registrar_error(
                    palabra, TipoError.CATEGORIA_NO_RECONOCIDA,
                    f"Categoria no reconocida: '{palabra}' en linea {linea_i}, columna {columna_i}",
                    linea_i, columna_i,
                )
            elif palabra.isupper():
                # Fuera de contexto explicito, una palabra completamente en
                # mayusculas que no coincide con ninguna palabra de bloque ni
                # enumeracion es, con alta probabilidad, un dia mal escrito.
                self._registrar_error(
                    palabra, TipoError.DIA_NO_RECONOCIDO,
                    f"Dia no reconocido: '{palabra}' en linea {linea_i}, columna {columna_i}",
                    linea_i, columna_i,
                )
            else:
                self._registrar_error(
                    palabra, TipoError.PALABRA_NO_RECONOCIDA,
                    f"Palabra no reconocida: '{palabra}' en linea {linea_i}, columna {columna_i}",
                    linea_i, columna_i,
                )
        self.contexto_esperado = nuevo_contexto
        return resultado
