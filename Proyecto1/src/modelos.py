
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


def separar_hora(hora: str):
    """Separa manualmente una hora en sus componentes antes de validarla."""
    horas = ""
    minutos = ""
    encontro_separador = False

    for caracter in hora:
        if caracter == ":":
            if encontro_separador:
                return None
            encontro_separador = True
        elif encontro_separador:
            minutos += caracter
        else:
            horas += caracter

    if not encontro_separador or not horas or not minutos:
        return None
    return horas, minutos


@dataclass
class Curso:
    codigo: str
    nombre: str
    creditos: int = 0
    linea: int = 0


@dataclass
class Catedratico:
    codigo: str
    nombre: str
    categoria: str = ""
    linea: int = 0


@dataclass
class Aula:
    codigo: str
    capacidad: int = 0
    edificio: str = ""
    linea: int = 0


@dataclass
class Clase:
    curso_codigo: str
    catedratico_codigo: str
    aula_codigo: str
    dia: str = ""
    inicio: str = ""
    fin: str = ""
    seccion: str = ""
    linea: int = 0

    ## Duracion de la clase en minutos, o 0 si inicio/fin son invalidos
    def duracion_minutos(self) -> int:
        inicio = self._a_minutos(self.inicio)
        fin = self._a_minutos(self.fin)
        if inicio is None or fin is None or fin <= inicio:
            return 0
        return fin - inicio

    @staticmethod
    def _a_minutos(hora: str):
        partes = separar_hora(hora)
        if partes is None:
            return None
        h, m = partes
        if not (h.isdigit() and m.isdigit()):
            return None
        return int(h) * 60 + int(m)

## Contenedor con toda la informacion semantica de un archivo .hor
@dataclass
class ModeloHorario:
    
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
