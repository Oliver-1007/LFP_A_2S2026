

import os
import sys

from src.gestion.gestor_torneo import GestorTorneo
from src.reportes.generador_reportes import GeneradorReportes

RUTA_REPORTES = "reportes"

def limpiar_pantalla():
    os.system("cls" if os.name == "nt" else "clear")

def mostrar_menu():
    print("""
    ==========================================
           TORNEO DE SUDOKU - NUMERIX
    ==========================================
    1. Cargar archivo de sudoku
    2. Cargar archivo de jugadores
    3. Cargar archivo de intentos
    4. Validar y calificar intentos
    5. Generar Reporte: Resumen por Sudoku
    6. Generar Reporte: Rendimiento por jugador
    7. Generar Reporte: Top 10 mejores tiempos
    8. Salir
    ------------------------------------------
    """)

def pedir_ruta(mensaje: str, ruta_por_defecto: str) -> str:
    entrada = input(f"{mensaje} [Enter para usar '{ruta_por_defecto}']: ").strip()
    return entrada if entrada else ruta_por_defecto


def mostrar_resultado_carga(entidad: str, cantidad: int, errores: list):
    print(f"\n{cantidad} registro(s) de {entidad} cargado(s) correctamente.")
    if errores:
        print(f"Se encontraron {len(errores)} error(es):")
        for error in errores[:10]:
            print(f"  - {error}")
        if len(errores) > 10:
            print(f"  ... y {len(errores) - 10} error(es) más.")

def opcion_cargar_sudokus(gestor: GestorTorneo):
    ruta = pedir_ruta("Ruta del archivo de sudokus", os.path.join("data", "sudokus.lfp"))
    cantidad, errores = gestor.cargar_sudokus(ruta)
    mostrar_resultado_carga("sudokus", cantidad, errores)


def opcion_cargar_jugadores(gestor: GestorTorneo):
    ruta = pedir_ruta("Ruta del archivo de jugadores", os.path.join("data", "jugadores.lfp"))
    cantidad, errores = gestor.cargar_jugadores(ruta)
    mostrar_resultado_carga("jugadores", cantidad, errores)


def opcion_cargar_intentos(gestor: GestorTorneo):
    ruta = pedir_ruta("Ruta del archivo de intentos", os.path.join("data", "intentos.lfp"))
    cantidad, errores = gestor.cargar_intentos(ruta)
    mostrar_resultado_carga("intentos", cantidad, errores)

def opcion_validar_intentos(gestor: GestorTorneo):
    if not gestor.sudokus_cargados or not gestor.intentos_cargados:
        print("\nDebe cargar primero los sudokus y los intentos (opciones 1 y 3).")
        return
    cantidad, errores = gestor.validar_intentos()
    print(f"\n{cantidad} intento(s) validado(s) correctamente.")
    if errores:
        print(f"Se encontraron {len(errores)} error(es):")
        for error in errores[:10]:
            print(f"  - {error}")


def opcion_reporte_resumen_sudoku(gestor: GestorTorneo, generador: GeneradorReportes):
    if not gestor.intentos_validados:
        print("\nDebe validar los intentos primero (opción 4).")
        return
    resumen = gestor.calcular_resumen_por_sudoku()
    ruta = generador.generar_resumen_por_sudoku(resumen)
    print(f"\nReporte generado exitosamente: {ruta}")


def opcion_reporte_rendimiento_jugador(gestor: GestorTorneo, generador: GeneradorReportes):
    if not gestor.intentos_validados:
        print("\nDebe validar los intentos primero (opción 4).")
        return
    rendimiento = gestor.calcular_rendimiento_por_jugador()
    ruta = generador.generar_rendimiento_por_jugador(rendimiento)
    print(f"\nReporte generado exitosamente: {ruta}")


def opcion_reporte_top_tiempos(gestor: GestorTorneo, generador: GeneradorReportes):
    if not gestor.intentos_validados:
        print("\nDebe validar los intentos primero (opción 4).")
        return
    top = gestor.calcular_top_mejores_tiempos()
    ruta = generador.generar_top_mejores_tiempos(top)
    print(f"\nReporte generado exitosamente: {ruta}")


def main():
    gestor = GestorTorneo()
    generador = GeneradorReportes(carpeta_salida=RUTA_REPORTES)

    acciones = {
        "1": lambda: opcion_cargar_sudokus(gestor),
        "2": lambda: opcion_cargar_jugadores(gestor),
        "3": lambda: opcion_cargar_intentos(gestor),
        "4": lambda: opcion_validar_intentos(gestor),
        "5": lambda: opcion_reporte_resumen_sudoku(gestor, generador),
        "6": lambda: opcion_reporte_rendimiento_jugador(gestor, generador),
        "7": lambda: opcion_reporte_top_tiempos(gestor, generador),
    }

    while True:
        mostrar_menu()
        opcion = input("Seleccione una opción: ").strip()

        if opcion == "8":
            print("\n¡Gracias por usar LFP Numerix! Hasta la próxima.")
            sys.exit(0)
        elif opcion in acciones:
            acciones[opcion]()
        else:
            print("\nOpción inválida. Intente nuevamente.")

        input("\nPresione Enter para continuar...")
        limpiar_pantalla()


if __name__ == "__main__":
    main()
