



from __future__ import annotations

from .modelos import ModeloHorario


#Convierte un codigo (p. ej. 'LFP-0796') en un identificador DOT
#valido, envolviendolo entre comillas para evitar caracteres especiales
def _id_valido(texto: str) -> str:
    escapado = texto.replace('"', '\\"')
    return f'"{escapado}"'


# Construye el codigo DOT con la jerarquia HORARIO -> secciones ->
# elementos, y las relaciones clase -> (curso, catedratico, aula)
def generar_dot_jerarquia(modelo: ModeloHorario) -> str:
    lineas = []
    lineas.append("digraph HorarioScript {")
    lineas.append('    rankdir=LR;')
    lineas.append('    node [shape=box, style="rounded,filled", fontname="Helvetica"];')
    lineas.append('    "HORARIO" [shape=doublecircle, fillcolor="#2c3e50", fontcolor=white];')

    # Nodo raiz -> secciones
    for seccion in ("CURSOS", "CATEDRATICOS", "AULAS", "CLASES"):
        lineas.append(f'    "{seccion}" [fillcolor="#34495e", fontcolor=white];')
        lineas.append(f'    "HORARIO" -> "{seccion}";')

    # Cursos
    for curso in modelo.cursos:
        nodo = _id_valido(f"curso:{curso.codigo}")
        lineas.append(f'    {nodo} [label="{curso.codigo}\\n{curso.nombre}", fillcolor="#aed6f1"];')
        lineas.append(f'    "CURSOS" -> {nodo};')

    # Catedraticos
    for catedratico in modelo.catedraticos:
        nodo = _id_valido(f"catedratico:{catedratico.codigo}")
        lineas.append(
            f'    {nodo} [label="{catedratico.codigo}\\n{catedratico.nombre}\\n({catedratico.categoria})", '
            f'fillcolor="#a9dfbf"];'
        )
        lineas.append(f'    "CATEDRATICOS" -> {nodo};')

    # Aulas
    for aula in modelo.aulas:
        nodo = _id_valido(f"aula:{aula.codigo}")
        lineas.append(
            f'    {nodo} [label="{aula.codigo}\\ncap. {aula.capacidad}\\n{aula.edificio}", '
            f'fillcolor="#f9e79f"];'
        )
        lineas.append(f'    "AULAS" -> {nodo};')

    # Clases y sus relaciones curso-catedratico-aula
    for indice, clase in enumerate(modelo.clases, start=1):
        nodo_clase = _id_valido(f"clase:{indice}")
        etiqueta = f"{clase.seccion or 'S/N'}\\n{clase.dia} {clase.inicio}-{clase.fin}"
        lineas.append(f'    {nodo_clase} [label="{etiqueta}", shape=ellipse, fillcolor="#f5b7b1"];')
        lineas.append(f'    "CLASES" -> {nodo_clase};')

        nodo_curso = _id_valido(f"curso:{clase.curso_codigo}")
        nodo_catedratico = _id_valido(f"catedratico:{clase.catedratico_codigo}")
        nodo_aula = _id_valido(f"aula:{clase.aula_codigo}")
        lineas.append(f'    {nodo_clase} -> {nodo_curso} [label="dicta", style=dashed];')
        lineas.append(f'    {nodo_clase} -> {nodo_catedratico} [label="con", style=dashed];')
        lineas.append(f'    {nodo_clase} -> {nodo_aula} [label="en", style=dashed];')

    lineas.append("}")
    return "\n".join(lineas)


def guardar_dot(modelo: ModeloHorario, ruta_salida: str) -> str:
    """Genera el codigo DOT y lo guarda en ruta_salida. Retorna la ruta."""
    contenido = generar_dot_jerarquia(modelo)
    with open(ruta_salida, "w", encoding="utf-8") as archivo:
        archivo.write(contenido)
    return ruta_salida
