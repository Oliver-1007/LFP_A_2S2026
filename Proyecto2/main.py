
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from procesador import ProcesadorMarkdown


## Modo sin interfaz: analiza el archivo, imprime errores y genera los archivos.
def ejecutar_consola(ruta, carpeta_salida):
    with open(ruta, "r", encoding="utf-8-sig") as archivo:
        texto = archivo.read()

    procesador = ProcesadorMarkdown()
    resultado = procesador.analizar(texto, os.path.basename(ruta))

    print("Tokens reconocidos: %d" % len(resultado.tokens_visibles))
    if resultado.exito:
        rutas = procesador.generar_reportes(resultado, carpeta_salida)
        procesador.guardar_dot(resultado, os.path.join(carpeta_salida, "arbol.dot"))
        print("Análisis completado sin errores. Archivos generados en: %s" % carpeta_salida)
        for ruta_reporte in rutas.values():
            print("  - %s" % ruta_reporte)
        print("  - %s" % os.path.join(carpeta_salida, "arbol.dot"))
        return 0

    print("Se encontraron %d error(es):" % resultado.gestor.cantidad())
    for numero, error in enumerate(resultado.errores, 1):
        print("  %2d. [%s] %s (línea %d, columna %d): %s"
              % (numero, error.fase, error.tipo, error.linea, error.columna, error.descripcion))
    return 1


def ejecutar_grafica(archivo_inicial):
    import tkinter as tk
    from interfaz_grafica import AplicacionMarkdownCheck

    raiz = tk.Tk()
    AplicacionMarkdownCheck(raiz, archivo_inicial)
    raiz.mainloop()
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="MarkdownCheck: analizador léxico-sintáctico de Markdown a HTML")
    parser.add_argument("archivo", nargs="?", help="documento .md a analizar")
    parser.add_argument("--consola", action="store_true",
                        help="ejecuta sin interfaz gráfica (requiere 'archivo')")
    parser.add_argument("--salida", default="reportes",
                        help="carpeta de salida en modo consola (por defecto: reportes)")
    args = parser.parse_args(argv)

    if args.consola:
        if not args.archivo:
            parser.error("el modo --consola requiere indicar un archivo .md")
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        return ejecutar_consola(args.archivo, args.salida)
    return ejecutar_grafica(args.archivo)


if __name__ == "__main__":
    sys.exit(main())
