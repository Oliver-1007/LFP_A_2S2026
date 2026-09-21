

from __future__ import annotations

from typing import List

from .tokens import ErrorLexico, TipoError

class GestorErrores:
    def __init__(self) -> None:
        self._errores: List[ErrorLexico] = []
        self._contador = 0

    def agregar(self, lexema: str, tipo: TipoError, descripcion: str,
                linea: int, columna: int) -> ErrorLexico:
        """Registra un nuevo error lexico y le asigna un numero secuencial."""
        self._contador += 1
        error = ErrorLexico(
            numero=self._contador,
            lexema=lexema,
            tipo=tipo,
            descripcion=descripcion,
            linea=linea,
            columna=columna,
        )
        self._errores.append(error)
        return error

    @property
    def errores(self) -> List[ErrorLexico]:
        """Lista de errores en el orden en que fueron detectados."""
        return list(self._errores)

    def hay_errores(self) -> bool:
        return len(self._errores) > 0

    def total_errores(self) -> int:
        return len(self._errores)

    def conteo_por_tipo(self) -> dict:
        """Devuelve cuantos errores hay de cada TipoError (para estadisticas)."""
        conteo = {tipo: 0 for tipo in TipoError}
        for error in self._errores:
            conteo[error.tipo] += 1
        return conteo

    def reiniciar(self) -> None:
        """Limpia el estado del gestor para volver a analizar otro archivo."""
        self._errores.clear()
        self._contador = 0
