
import os
from datetime import datetime

class GeneradorReportes:
    ESTILO_CSS = """
        body { font-family: 'Segoe UI', Arial, sans-serif; margin: 40px; background-color: #f4f6f8; color: #1f2937; }
        h1 { color: #1e3a8a; }
        p.subtitulo { color: #6b7280; margin-top: -8px; }
        table { border-collapse: collapse; width: 100%; margin-top: 20px; background-color: #ffffff; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
        th, td { padding: 10px 14px; text-align: left; border-bottom: 1px solid #e5e7eb; }
        th { background-color: #1e3a8a; color: #ffffff; }
        tr:nth-child(even) { background-color: #f9fafb; }
        tr:hover { background-color: #eef2ff; }
        .exito-alto { color: #15803d; font-weight: bold; }
        .exito-medio { color: #b45309; font-weight: bold; }
        .exito-bajo { color: #b91c1c; font-weight: bold; }
        footer { margin-top: 24px; color: #9ca3af; font-size: 0.85em; }
        .badge { display: inline-block; padding: 2px 10px; border-radius: 12px; font-size: 0.85em; color: white; }
        .Facil { background-color: #22c55e; }
        .Media { background-color: #eab308; }
        .Dificil { background-color: #f97316; }
        .Experto { background-color: #dc2626; }
        .oro { background-color: #fde68a; }
        .plata { background-color: #e5e7eb; }
        .bronce { background-color: #fdba74; }
    """

    def __init__(self, carpeta_salida: str = "reportes"):
        self.carpeta_salida = carpeta_salida
        os.makedirs(self.carpeta_salida, exist_ok=True)

    def _clase_tasa_exito(self, tasa: float) -> str:
        if tasa >= 70:
            return "exito-alto"
        if tasa >= 40:
            return "exito-medio"
        return "exito-bajo"

    def _encabezado_html(self, titulo: str) -> str:
        fecha_generacion = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        return f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>{titulo} - Torneo Numerix</title>
    <style>{self.ESTILO_CSS}</style>
</head>
<body>
    <h1>{titulo}</h1>
    <p class="subtitulo">Torneo de Sudoku - Numerix Academy | Generado el {fecha_generacion}</p>
"""

    def _pie_html(self) -> str:
        return """
    <footer>Reporte generado automáticamente por LFP Numerix.</footer>
</body>
</html>
"""

    ## PRIMER REPORTE (SUDOKU)
    def generar_resumen_por_sudoku(self, resumen: list, nombre_archivo: str = "reporte1_resumen_por_sudoku.html") -> str:
        html = [self._encabezado_html("Reporte 1: Resumen por Sudoku")]
        html.append("""
    <table>
        <tr>
            <th>ID Sudoku</th>
            <th>Dificultad</th>
            <th>Cantidad de Intentos</th>
            <th>Tiempo Promedio (s)</th>
            <th>Tasa de Fallo</th>
        </tr>
""")
        for fila in resumen:
            clase_tasa = self._clase_tasa_exito(fila["tasa_exito"])
            html.append(
                f"""        <tr>
            <td>{fila['id_sudoku']}</td>
            <td><span class="badge {fila['dificultad']}">{fila['dificultad']}</span></td>
            <td>{fila['cantidad_intentos']}</td>
            <td>{fila['tiempo_promedio']:.2f}</td>
            <td class="{clase_tasa}">{fila['tasa_exito']:.2f}%</td>
        </tr>
"""
            )
        html.append("    </table>")
        html.append(self._pie_html())

        ruta = os.path.join(self.carpeta_salida, nombre_archivo)
        with open(ruta, "w", encoding="utf-8") as archivo:
            archivo.write("".join(html))
        return ruta


    ## SEGUNDO REPORTE (JUGADOR)
    def generar_rendimiento_por_jugador(self, rendimiento: list, nombre_archivo: str = "reporte2_rendimiento_por_jugador.html") -> str:
        html = [self._encabezado_html("Reporte 2: Rendimiento por Jugador")]
        html.append("""
    <table>
        <tr>
            <th>Carnet</th>
            <th>Nombre Completo</th>
            <th>Nivel</th>
            <th>Tableros Intentados</th>
            <th>Validez Promedio</th>
            <th>Tiempo Promedio (s)</th>
            <th>Resueltos Perfectamente</th>
        </tr>
""")
        for fila in rendimiento:
            html.append(
                f"""        <tr>
            <td>{fila['carnet']}</td>
            <td>{fila['nombre_completo']}</td>
            <td>{fila['nivel']}</td>
            <td>{fila['cantidad_tableros']}</td>
            <td>{fila['validez_promedio']:.2f}%</td>
            <td>{fila['tiempo_promedio']:.2f}</td>
            <td>{fila['resueltos_perfectos']}</td>
        </tr>
"""
            )
        html.append("    </table>")
        html.append(self._pie_html())

        ruta = os.path.join(self.carpeta_salida, nombre_archivo)
        with open(ruta, "w", encoding="utf-8") as archivo:
            archivo.write("".join(html))
        return ruta

    ## TERCER REPORTE (TOP 10 MEJORES TIEMPOS)
    def generar_top_mejores_tiempos(self, top: list, nombre_archivo: str = "reporte3_top_mejores_tiempos.html") -> str:
        html = [self._encabezado_html("Reporte 3: Top 10 Mejores Tiempos")]
        html.append("""
    <table>
        <tr>
            <th>Posición</th>
            <th>Carnet</th>
            <th>Nombre Completo</th>
            <th>ID Sudoku</th>
            <th>Dificultad</th>
            <th>Tiempo (s)</th>
        </tr>
""")
        medallas = {1: "oro", 2: "plata", 3: "bronce"}
        if not top:
            html.append('        <tr><td colspan="6">Aún no hay intentos resueltos correctamente.</td></tr>\n')
        for fila in top:
            clase_medalla = medallas.get(fila["posicion"], "")
            html.append(
                f"""        <tr class="{clase_medalla}">
            <td>{fila['posicion']}</td>
            <td>{fila['carnet']}</td>
            <td>{fila['nombre_completo']}</td>
            <td>{fila['id_sudoku']}</td>
            <td><span class="badge {fila['dificultad']}">{fila['dificultad']}</span></td>
            <td>{fila['tiempo_segundos']}</td>
        </tr>
"""
            )
        html.append("    </table>")
        html.append(self._pie_html())

        ruta = os.path.join(self.carpeta_salida, nombre_archivo)
        with open(ruta, "w", encoding="utf-8") as archivo:
            archivo.write("".join(html))
        return ruta