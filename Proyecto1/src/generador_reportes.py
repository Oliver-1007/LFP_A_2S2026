
from __future__ import annotations

import html
import os
from typing import List

from .detector_choques import Choque
from .modelos import ModeloHorario, separar_hora
from .tokens import ErrorLexico

DIAS_SEMANA = ["LUNES", "MARTES", "MIERCOLES", "JUEVES", "VIERNES", "SABADO", "DOMINGO"]
CATEGORIAS_VALIDAS = {"TITULAR", "INTERINO", "AUXILIAR"}

CSS_BASE = """
:root {
    --color-fondo: #f4f6f8;
    --color-texto: #2c3e50;
    --color-primario: #2c3e50;
    --color-verde: #d4efdf;
    --color-verde-borde: #27ae60;
    --color-rojo: #fadbd8;
    --color-rojo-borde: #c0392b;
    --color-azul: #d6eaf8;
    --color-azul-borde: #2980b9;
    --color-naranja: #fdebd0;
    --color-naranja-borde: #e67e22;
}
* { box-sizing: border-box; }
body {
    font-family: "Segoe UI", Helvetica, Arial, sans-serif;
    background: var(--color-fondo);
    color: var(--color-texto);
    margin: 0;
    padding: 2rem;
}
h1 { border-bottom: 3px solid var(--color-primario); padding-bottom: .5rem; }
h2 { margin-top: 2rem; color: var(--color-primario); }
table {
    border-collapse: collapse;
    width: 100%;
    margin: 1rem 0 2rem 0;
    background: white;
    box-shadow: 0 1px 4px rgba(0,0,0,.1);
}
th, td {
    border: 1px solid #d5dbdb;
    padding: .5rem .75rem;
    text-align: left;
    vertical-align: top;
    font-size: .9rem;
}
th { background: var(--color-primario); color: white; }
tr:nth-child(even) td { background: #fbfcfc; }

.tabla-horario td.vacio { background: #fdfefe; }
.tabla-horario td.confirmado { background: var(--color-verde); border-left: 4px solid var(--color-verde-borde); }
.tabla-horario td.choque { background: var(--color-rojo); border-left: 4px solid var(--color-rojo-borde); font-weight: bold; }
.tabla-horario td.hora { font-weight: bold; background: #eaecee; white-space: nowrap; }

.nivel-baja { background: var(--color-azul); color: var(--color-azul-borde); font-weight: bold; }
.nivel-normal { background: var(--color-verde); color: var(--color-verde-borde); font-weight: bold; }
.nivel-alta { background: var(--color-naranja); color: var(--color-naranja-borde); font-weight: bold; }
.nivel-saturada { background: var(--color-rojo); color: var(--color-rojo-borde); font-weight: bold; }

.kpis { display: flex; flex-wrap: wrap; gap: 1rem; margin: 1.5rem 0; }
.kpi {
    background: white; border-radius: .5rem; padding: 1rem 1.5rem;
    box-shadow: 0 1px 4px rgba(0,0,0,.1); min-width: 140px; text-align: center;
}
.kpi-valor { display: block; font-size: 2rem; font-weight: bold; color: var(--color-primario); }
.kpi-etiqueta { display: block; font-size: .85rem; color: #7f8c8d; }
.kpi-alerta .kpi-valor { color: var(--color-rojo-borde); }

.tabla-ocupacion tr.ocupacion-alta td { background: var(--color-rojo); }
.barra { background: #eaecee; border-radius: 4px; height: 10px; width: 100%; overflow: hidden; display: inline-block; }
.barra-relleno { background: var(--color-azul-borde); height: 100%; }

.sin-errores { color: var(--color-verde-borde); font-weight: bold; }
footer { margin-top: 3rem; font-size: .8rem; color: #95a5a6; }
"""

class GeneradorReportes:
    """Genera los reportes HTML del proyecto a partir de un ModeloHorario
    y la lista de choques ya detectada."""

    def __init__(self, modelo: ModeloHorario, choques: List[Choque],
                 errores: List[ErrorLexico] | None = None) -> None:
        self.modelo = self.modelo_valido(modelo, errores)
        clases_validas = {id(clase) for clase in self.modelo.clases}
        self.choques = [
            choque for choque in choques
            if id(choque.clase_a) in clases_validas
            and id(choque.clase_b) in clases_validas
        ]
        self._choque_por_clase = self._indexar_choques()

    @staticmethod
    def _es_identificador_valido(valor: str) -> bool:
        return bool(valor.strip())

    @staticmethod
    def _es_hora_valida(valor: str) -> bool:
        if len(valor) != 5 or valor[2] != ":":
            return False
        for posicion in (0, 1, 3, 4):
            if valor[posicion] < "0" or valor[posicion] > "9":
                return False
        partes = separar_hora(valor)
        if partes is None:
            return False
        horas, minutos = (int(parte) for parte in partes)
        return 6 * 60 <= horas * 60 + minutos <= 21 * 60 and minutos <= 59

    @classmethod
    def modelo_valido(cls, modelo: ModeloHorario,
                      errores: List[ErrorLexico] | None = None) -> ModeloHorario:
        lineas_con_error = {error.linea for error in (errores or [])}

        def sin_error_en_registro(registro) -> bool:
            return registro.linea not in lineas_con_error

        cursos = [
            curso for curso in modelo.cursos
            if sin_error_en_registro(curso)
            and cls._es_identificador_valido(curso.codigo)
            and bool(curso.nombre.strip())
            and curso.creditos > 0
        ]
        catedraticos = [
            catedratico for catedratico in modelo.catedraticos
            if sin_error_en_registro(catedratico)
            and cls._es_identificador_valido(catedratico.codigo)
            and bool(catedratico.nombre.strip())
            and catedratico.categoria in CATEGORIAS_VALIDAS
        ]
        aulas = [
            aula for aula in modelo.aulas
            if sin_error_en_registro(aula)
            and cls._es_identificador_valido(aula.codigo)
            and aula.capacidad > 0
            and bool(aula.edificio.strip())
        ]

        codigos_cursos = {curso.codigo for curso in cursos}
        codigos_catedraticos = {catedratico.codigo for catedratico in catedraticos}
        codigos_aulas = {aula.codigo for aula in aulas}
        clases = [
            clase for clase in modelo.clases
            if sin_error_en_registro(clase)
            and clase.curso_codigo in codigos_cursos
            and clase.catedratico_codigo in codigos_catedraticos
            and clase.aula_codigo in codigos_aulas
            and clase.dia in DIAS_SEMANA
            and cls._es_hora_valida(clase.inicio)
            and cls._es_hora_valida(clase.fin)
            and clase.inicio < clase.fin
            and bool(clase.seccion.strip())
        ]
        return ModeloHorario(
            cursos=cursos,
            catedraticos=catedraticos,
            aulas=aulas,
            clases=clases,
        )

    def _indexar_choques(self) -> dict:
        indice: dict = {}
        for choque in self.choques:
            indice.setdefault(id(choque.clase_a), []).append(choque)
            indice.setdefault(id(choque.clase_b), []).append(choque)
        return indice

    # -- helpers de salida ---------------------------------------------------

    @staticmethod
    def _envolver_html(titulo: str, cuerpo: str) -> str:
        return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>{html.escape(titulo)} - HorarioScript</title>
<style>{CSS_BASE}</style>
</head>
<body>
<h1>{html.escape(titulo)}</h1>
{cuerpo}
<footer>Generado automaticamente por HorarioScript (analizador lexico de horarios academicos).</footer>
</body>
</html>
"""

    @staticmethod
    def _escribir(ruta: str, contenido: str) -> None:
        carpeta = os.path.dirname(ruta)
        if carpeta:
            os.makedirs(carpeta, exist_ok=True)
        with open(ruta, "w", encoding="utf-8") as archivo:
            archivo.write(contenido)

    # -- Reporte 1: Horario semanal por seccion ------------------------------

    def _clases_por_seccion(self) -> dict:
        secciones: dict = {}
        for clase in self.modelo.clases:
            secciones.setdefault(clase.seccion or "General", []).append(clase)
        return secciones

    def _celda_bloque(self, clases_celda: list) -> str:
        if not clases_celda:
            return "<td class='vacio'></td>"
        hay_choque = len(clases_celda) > 1 or any(
            id(c) in self._choque_por_clase for c in clases_celda
        )
        estado = "choque" if hay_choque else "confirmado"
        partes = []
        for clase in clases_celda:
            curso = self.modelo.buscar_curso(clase.curso_codigo)
            catedratico = self.modelo.buscar_catedratico(clase.catedratico_codigo)
            nombre_curso = curso.nombre if curso else clase.curso_codigo
            nombre_catedratico = catedratico.nombre if catedratico else clase.catedratico_codigo
            partes.append(
                f"<div><strong>{html.escape(nombre_curso)}</strong><br>"
                f"{html.escape(nombre_catedratico)}<br>Aula {html.escape(clase.aula_codigo)}</div>"
            )
        etiqueta_estado = "CHOQUE DE HORARIO" if estado == "choque" else "CONFIRMADO"
        marca = f"<div class='estado'>&#9888; {etiqueta_estado}</div>" if estado == "choque" else f"<div class='estado'>{etiqueta_estado}</div>"
        return f"<td class='{estado}'>{''.join(partes)}{marca}</td>"

    def _tabla_seccion(self, seccion: str, clases: list) -> str:
        bloques = sorted({(c.inicio, c.fin) for c in clases if c.inicio and c.fin})
        filas = []
        for inicio, fin in bloques:
            celdas = []
            for dia in DIAS_SEMANA:
                clases_celda = [
                    c for c in clases
                    if c.dia == dia and c.inicio == inicio and c.fin == fin
                ]
                celdas.append(self._celda_bloque(clases_celda))
            filas.append(f"<tr><td class='hora'>{inicio} - {fin}</td>{''.join(celdas)}</tr>")
        encabezado_dias = "".join(f"<th>{dia.title()}</th>" for dia in DIAS_SEMANA)
        filas_html = "".join(filas) if filas else (
            f"<tr><td colspan='{len(DIAS_SEMANA) + 1}'>Sin bloques horarios validos.</td></tr>"
        )
        return f"""
<h2>Seccion {html.escape(seccion)}</h2>
<table class="tabla-horario">
<tr><th>Bloque</th>{encabezado_dias}</tr>
{filas_html}
</table>
"""

    def generar_horario_semanal(self, ruta: str) -> str:
        secciones = self._clases_por_seccion()
        if secciones:
            cuerpo = "\n".join(
                self._tabla_seccion(seccion, clases)
                for seccion, clases in sorted(secciones.items())
            )
        else:
            cuerpo = "<p>No hay clases registradas en el archivo analizado.</p>"
        self._escribir(ruta, self._envolver_html("Horario Semanal por Seccion", cuerpo))
        return ruta

    # -- Reporte 2: Carga de catedraticos -------------------------------------

    @staticmethod
    def _nivel_carga(horas: float):
        if horas <= 4:
            return "BAJA", "baja"
        if horas <= 10:
            return "NORMAL", "normal"
        if horas <= 15:
            return "ALTA", "alta"
        return "SATURADA", "saturada"

    def generar_carga_catedraticos(self, ruta: str) -> str:
        filas = []
        for catedratico in self.modelo.catedraticos:
            clases_cat = [c for c in self.modelo.clases if c.catedratico_codigo == catedratico.codigo]
            horas = sum(c.duracion_minutos() for c in clases_cat) / 60
            cursos_distintos = len({c.curso_codigo for c in clases_cat})
            secciones_distintas = len({c.seccion for c in clases_cat if c.seccion})
            nivel, clase_css = self._nivel_carga(horas)
            filas.append(f"""
<tr>
<td>{html.escape(catedratico.nombre)}</td>
<td>{html.escape(catedratico.codigo)}</td>
<td>{html.escape(catedratico.categoria)}</td>
<td>{horas:.1f}</td>
<td>{cursos_distintos}</td>
<td>{secciones_distintas}</td>
<td class="nivel-{clase_css}">{nivel}</td>
</tr>
""")
        filas_html = "".join(filas) if filas else (
            "<tr><td colspan='7'>No hay catedraticos registrados.</td></tr>"
        )
        cuerpo = f"""
<table class="tabla-carga">
<tr>
<th>Catedratico</th><th>Codigo</th><th>Categoria</th><th>Horas/semana</th>
<th>Cursos</th><th>Secciones</th><th>Nivel de carga</th>
</tr>
{filas_html}
</table>
"""
        self._escribir(ruta, self._envolver_html("Carga de Catedraticos", cuerpo))
        return ruta

    # -- Reporte 3: Estadistico general del ciclo ----------------------------

    def _nombre_catedratico(self, codigo: str) -> str:
        catedratico = self.modelo.buscar_catedratico(codigo)
        return catedratico.nombre if catedratico else codigo

    def generar_estadistico(self, ruta: str) -> str:
        total_cursos = len(self.modelo.cursos)
        total_catedraticos = len(self.modelo.catedraticos)
        total_aulas = len(self.modelo.aulas)
        total_clases = len(self.modelo.clases)
        total_choques = len(self.choques)

        horas_por_catedratico = {}
        for catedratico in self.modelo.catedraticos:
            clases_cat = [c for c in self.modelo.clases if c.catedratico_codigo == catedratico.codigo]
            horas_por_catedratico[catedratico.codigo] = sum(c.duracion_minutos() for c in clases_cat) / 60

        if horas_por_catedratico:
            codigo_max, horas_max = max(horas_por_catedratico.items(), key=lambda item: item[1])
        else:
            codigo_max, horas_max = None, 0.0

        ocupacion_por_aula = {}
        for aula in self.modelo.aulas:
            clases_aula = [c for c in self.modelo.clases if c.aula_codigo == aula.codigo]
            porcentaje = (len(clases_aula) / total_clases * 100) if total_clases else 0.0
            ocupacion_por_aula[aula.codigo] = (len(clases_aula), porcentaje)

        if ocupacion_por_aula:
            codigo_aula_max, (_, porcentaje_aula_max) = max(
                ocupacion_por_aula.items(), key=lambda item: item[1][1]
            )
        else:
            codigo_aula_max, porcentaje_aula_max = None, 0.0

        promedio_horas = (
            sum(horas_por_catedratico.values()) / total_catedraticos
            if total_catedraticos else 0.0
        )

        filas_aulas = []
        for aula in self.modelo.aulas:
            cantidad, porcentaje = ocupacion_por_aula.get(aula.codigo, (0, 0.0))
            clase_resaltado = "ocupacion-alta" if porcentaje > 80 else ""
            filas_aulas.append(f"""
<tr class="{clase_resaltado}">
<td>{html.escape(aula.codigo)}</td>
<td>{cantidad}</td>
<td><div class="barra"><div class="barra-relleno" style="width:{min(porcentaje, 100):.1f}%"></div></div> {porcentaje:.1f}%</td>
</tr>
""")
        filas_aulas_html = "".join(filas_aulas) if filas_aulas else (
            "<tr><td colspan='3'>No hay aulas registradas.</td></tr>"
        )

        cuerpo = f"""
<div class="kpis">
<div class="kpi"><span class="kpi-valor">{total_cursos}</span><span class="kpi-etiqueta">Cursos</span></div>
<div class="kpi"><span class="kpi-valor">{total_catedraticos}</span><span class="kpi-etiqueta">Catedraticos</span></div>
<div class="kpi"><span class="kpi-valor">{total_aulas}</span><span class="kpi-etiqueta">Aulas</span></div>
<div class="kpi"><span class="kpi-valor">{total_clases}</span><span class="kpi-etiqueta">Clases</span></div>
<div class="kpi kpi-alerta"><span class="kpi-valor">{total_choques}</span><span class="kpi-etiqueta">Choques detectados</span></div>
</div>
<p><strong>Catedratico con mayor carga:</strong> {html.escape(self._nombre_catedratico(codigo_max) if codigo_max else 'N/A')} ({horas_max:.1f} h/semana)</p>
<p><strong>Aula con mayor ocupacion:</strong> {html.escape(codigo_aula_max or 'N/A')} ({porcentaje_aula_max:.1f}%)</p>
<p><strong>Promedio de horas semanales por catedratico:</strong> {promedio_horas:.1f} h</p>
<h2>Ocupacion por aula</h2>
<table class="tabla-ocupacion">
<tr><th>Aula</th><th>Clases asignadas</th><th>% Ocupacion</th></tr>
{filas_aulas_html}
</table>
"""
        self._escribir(ruta, self._envolver_html("Estadistico General del Ciclo", cuerpo))
        return ruta

    # -- Reporte adicional: errores lexicos -----------------------------------

    def generar_reporte_errores(self, errores: List[ErrorLexico], ruta: str) -> str:
        if errores:
            filas = "".join(f"""
<tr>
<td>{error.numero}</td>
<td>{html.escape(error.lexema)}</td>
<td>{error.tipo.name}</td>
<td>{html.escape(error.descripcion)}</td>
<td>{error.linea}</td>
<td>{error.columna}</td>
</tr>
""" for error in errores)
            cuerpo = f"""
<table class="tabla-errores">
<tr><th>#</th><th>Lexema</th><th>Tipo</th><th>Descripcion</th><th>Linea</th><th>Columna</th></tr>
{filas}
</table>
"""
        else:
            cuerpo = "<p class='sin-errores'>No se detectaron errores lexicos en el archivo analizado.</p>"
        self._escribir(ruta, self._envolver_html("Reporte de Errores Lexicos", cuerpo))
        return ruta

    # -- Generacion masiva -----------------------------------------------------

    def generar_todos(self, carpeta_salida: str, errores: List[ErrorLexico]) -> dict:
        os.makedirs(carpeta_salida, exist_ok=True)
        rutas = {
            "horario_semanal": self.generar_horario_semanal(
                os.path.join(carpeta_salida, "reporte_horario_semanal.html")
            ),
            "carga_catedraticos": self.generar_carga_catedraticos(
                os.path.join(carpeta_salida, "reporte_carga_catedraticos.html")
            ),
            "estadistico": self.generar_estadistico(
                os.path.join(carpeta_salida, "reporte_estadistico.html")
            ),
            "errores": self.generar_reporte_errores(
                errores, os.path.join(carpeta_salida, "reporte_errores.html")
            ),
        }
        return rutas
