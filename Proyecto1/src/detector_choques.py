



from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import List, Optional

from .modelos import Clase


#Representa un choque de horario detectado entre dos clases
@dataclass
class Choque:

    clase_a: Clase
    clase_b: Clase
    tipo: str      # 'CATEDRATICO', 'AULA' o 'AMBOS'
    recurso: str   # codigo del catedratico y/o del aula en conflicto


def _a_minutos(hora: str) -> Optional[int]:
    partes = hora.split(":")
    if len(partes) != 2:
        return None
    h, m = partes
    if not (h.isdigit() and m.isdigit()):
        return None
    return int(h) * 60 + int(m)


def _se_traslapan(clase_a: Clase, clase_b: Clase) -> bool:
    if not clase_a.dia or clase_a.dia != clase_b.dia:
        return False
    ini_a, fin_a = _a_minutos(clase_a.inicio), _a_minutos(clase_a.fin)
    ini_b, fin_b = _a_minutos(clase_b.inicio), _a_minutos(clase_b.fin)
    if None in (ini_a, fin_a, ini_b, fin_b):
        return False
    return ini_a < fin_b and ini_b < fin_a


#Recorre todos los pares de clases y reporta los choques encontrados
def detectar_choques(clases: List[Clase]) -> List[Choque]:
    choques: List[Choque] = []
    for clase_a, clase_b in combinations(clases, 2):
        if not _se_traslapan(clase_a, clase_b):
            continue

        mismo_catedratico = (
            clase_a.catedratico_codigo != ""
            and clase_a.catedratico_codigo == clase_b.catedratico_codigo
        )
        misma_aula = (
            clase_a.aula_codigo != ""
            and clase_a.aula_codigo == clase_b.aula_codigo
        )

        if mismo_catedratico and misma_aula:
            choques.append(Choque(clase_a, clase_b, "AMBOS", clase_a.catedratico_codigo))
        elif mismo_catedratico:
            choques.append(Choque(clase_a, clase_b, "CATEDRATICO", clase_a.catedratico_codigo))
        elif misma_aula:
            choques.append(Choque(clase_a, clase_b, "AULA", clase_a.aula_codigo))

    return choques


def clases_en_choque(choques: List[Choque]) -> set:
    """Devuelve el conjunto (id de objeto) de clases involucradas en al
    menos un choque, util para resaltar celdas en el reporte semanal."""
    resultado = set()
    for choque in choques:
        resultado.add(id(choque.clase_a))
        resultado.add(id(choque.clase_b))
    return resultado
