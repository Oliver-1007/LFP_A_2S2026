

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto



class TipoToken(Enum):

    PALABRA_RESERVADA_BLOQUE = auto()

    PALABRA_RESERVADA_ELEMENTO = auto()

    PALABRA_RESERVADA_RELACION = auto()

    PALABRA_RESERVADA_ATRIBUTO = auto()

    CODIGO = auto()

    CADENA = auto()

    HORA = auto()

    ENTERO = auto()

    DIA = auto()

    CATEGORIA = auto()

    SIMBOLO = auto()

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
    """Representa un token reconocido por el analizador lexico."""

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
    """Representa un error lexico detectado durante el analisis."""

    numero: int
    lexema: str
    tipo: TipoError
    descripcion: str
    linea: int
    columna: int

    def como_fila(self) -> tuple:
        """Devuelve la tupla (numero, lexema, tipo, descripcion, linea, columna)
        lista para poblar la tabla de errores de la interfaz grafica."""
        return (self.numero, self.lexema, self.tipo.name, self.descripcion, self.linea, self.columna)
