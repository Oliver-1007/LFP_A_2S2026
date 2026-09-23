
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.analizador_lexico import AnalizadorLexico
from src.detector_choques import detectar_choques
from src.interprete import InterpreteHorario

CARPETA_EJEMPLOS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ejemplos")

def probar_archivo(ruta: str) -> None:
    with open(ruta, "r", encoding="utf-8") as archivo:
        contenido = archivo.read()

    analizador = AnalizadorLexico(contenido)
    tokens = analizador.analizar()
    errores = analizador.gestor_errores.errores

    interprete = InterpreteHorario(tokens)
    modelo = interprete.interpretar()
    choques = detectar_choques(modelo.clases)

    print("=" * 70)
    print(f"Archivo: {os.path.basename(ruta)}")
    print(f"  Tokens reconocidos : {len(tokens)}")
    print(f"  Errores lexicos    : {len(errores)}")
    for error in errores:
        print(f"    - [{error.numero}] {error.tipo.name}: {error.descripcion}")
    print(f"  Cursos={len(modelo.cursos)} Catedraticos={len(modelo.catedraticos)} "
          f"Aulas={len(modelo.aulas)} Clases={len(modelo.clases)}")
    print(f"  Choques de horario  : {len(choques)}")
    for choque in choques:
        print(
            f"    - {choque.tipo} ({choque.recurso}): "
            f"{choque.clase_a.curso_codigo} vs {choque.clase_b.curso_codigo} "
            f"[{choque.clase_a.dia} {choque.clase_a.inicio}-{choque.clase_a.fin}]"
        )


def main() -> None:
    for nombre_archivo in sorted(os.listdir(CARPETA_EJEMPLOS)):
        if nombre_archivo.endswith(".hor"):
            probar_archivo(os.path.join(CARPETA_EJEMPLOS, nombre_archivo))


if __name__ == "__main__":
    main()
