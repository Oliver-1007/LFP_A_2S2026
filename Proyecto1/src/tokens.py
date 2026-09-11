

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto



class TipoToken(Enum):

    # Palabras reservadas que delimitan las 5 secciones principales
    PALABRA_RESERVADA_BLOQUE = auto()
    # Palabras reservadas que introducen un elemento dentro de una seccion
    PALABRA_RESERVADA_ELEMENTO = auto()
    # Palabras reservadas de relacion (con, en)
    PALABRA_RESERVADA_RELACION = auto()
    # Palabras reservadas que nombran un atributo (codigo, dia, etc)
    PALABRA_RESERVADA_ATRIBUTO = auto()
    # Codigos alfanumericos con guion (LFP-0796, DOC-001, A-101)
    CODIGO = auto()
    # Literales de texto entre comillas dobles
    CADENA = auto()
    # Literales de hora en formato HH:MM
    HORA = auto()
    # Literales numericos enteros
    ENTERO = auto()
    # Enumeracion de dias (LUNES..SABADO)
    DIA = auto()
    # Enumeracion de categoria de catedratico
    CATEGORIA = auto()
    # Caracteres de puntuacion con significado sintactico
    SIMBOLO = auto()
    # Comentario de linea que inicia con ##
    COMENTARIO_LINEA = auto()


class TipoError(Enum):

    CARACTER_NO_RECONOCIDO = auto()
    CADENA_SIN_CERRAR = auto()
    HORA_FUERA_DE_RANGO = auto()
    DIA_NO_RECONOCIDO = auto()
    CODIGO_MAL_FORMADO = auto()
    CATEGORIA_NO_RECONOCIDA = auto()
    PALABRA_NO_RECONOCIDA = auto()


@dataclass
class Token:

    tipo: TipoToken
    lexema: str
    linea: int
    columna: int
    numero: int = 0  # Se asigna al construir la tabla de tokens completa.

    def como_fila(self) -> tuple:
        """Devuelve la tupla (numero, lexema, tipo, linea, columna)
        lista para poblar la tabla de tokens de la interfaz grafica."""
        return (self.numero, self.lexema, self.tipo.name, self.linea, self.columna)


@dataclass
class ErrorLexico:

    numero: int
    lexema: str
    tipo: TipoError
    descripcion: str
    linea: int
    columna: int

    def como_fila(self) -> tuple:

        return (self.numero, self.lexema, self.tipo.name, self.descripcion, self.linea, self.columna)
