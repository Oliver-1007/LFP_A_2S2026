
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class Curso:
    codigo: str
    nombre: str
    creditos: int = 0


@dataclass
class Catedratico:
    codigo: str
    nombre: str
    categoria: str = ""


@dataclass
class Aula:
    codigo: str
    capacidad: int = 0
    edificio: str = ""


@dataclass
class Clase:
    curso_codigo: str
    catedratico_codigo: str
    aula_codigo: str
    dia: str = ""
    inicio: str = ""
    fin: str = ""
    seccion: str = ""

    def duracion_minutos(self) -> int:
        """Duracion de la clase en minutos, o 0 si inicio/fin son invalidos."""
        inicio = self._a_minutos(self.inicio)
        fin = self._a_minutos(self.fin)
        if inicio is None or fin is None or fin <= inicio:
            return 0
        return fin - inicio

    @staticmethod
    def _a_minutos(hora: str):
        partes = hora.split(":")
        if len(partes) != 2:
            return None
        h, m = partes
        if not (h.isdigit() and m.isdigit()):
            return None
        return int(h) * 60 + int(m)


@dataclass
class ModeloHorario:
    """Contenedor con toda la informacion semantica de un archivo .hor."""

    cursos: List[Curso] = field(default_factory=list)
    catedraticos: List[Catedratico] = field(default_factory=list)
    aulas: List[Aula] = field(default_factory=list)
    clases: List[Clase] = field(default_factory=list)

    def buscar_curso(self, codigo: str) -> Curso | None:
        return next((c for c in self.cursos if c.codigo == codigo), None)

    def buscar_catedratico(self, codigo: str) -> Catedratico | None:
        return next((c for c in self.catedraticos if c.codigo == codigo), None)

    def buscar_aula(self, codigo: str) -> Aula | None:
        return next((a for a in self.aulas if a.codigo == codigo), None)