# LFP Numerix — Torneo de Sudoku: Validación y Análisis de Partidas

Práctica 1 del curso **Lenguajes Formales y de Programación**
Universidad de San Carlos de Guatemala — Facultad de Ingeniería

Sistema de consola en Python (POO) que valida los intentos de resolución
de un torneo de Sudoku organizado por *Numerix Academy*, calcula métricas
de desempeño y genera reportes analíticos en formato HTML.

## Descripción

El programa lee tres archivos delimitados por comas (`.lfp`): tableros de
Sudoku, jugadores inscritos e intentos de resolución. Reconstruye cada
tablero como una matriz de 9x9, valida las reglas del Sudoku (filas,
columnas y cajas de 3x3, respetando las pistas originales) y calcula el
porcentaje de validez de cada intento. Con esa información genera tres
reportes HTML: resumen por sudoku, rendimiento por jugador y el top 10 de
mejores tiempos.

## Estructura del proyecto

```
Practica1/
├── main.py
├── src/
│   ├── modelos/
│   │   ├── tablero.py
│   │   ├── jugador.py
│   │   └── intento.py
│   ├── validacion/
│   │   └── validador_sudoku.py
│   ├── gestion/
│   │   └── gestor_torneo.py
│   └── reportes/
│       └── generador_reportes.py
├── data/
│   ├── sudokus.lfp
│   ├── jugadores.lfp
│   └── intentos.lfp
└── reportes/
```

## Requisitos

- Python 3.x (no requiere librerías externas, solo la biblioteca estándar)

## Ejecución

Desde la carpeta `Practica1`:

```bash
python3 main.py
```

Se mostrará el menú interactivo:

```
==========================================
     TORNEO DE SUDOKU - NUMERIX
==========================================
1. Cargar archivo de sudokus
2. Cargar archivo de jugadores
3. Cargar archivo de intentos
4. Validar y calificar intentos
5. Generar Reporte: Resumen por Sudoku
6. Generar Reporte: Rendimiento por Jugador
7. Generar Reporte: Top 10 Mejores Tiempos
8. Salir
------------------------------------------
Seleccione una opción:
```

### Flujo de uso recomendado

1. **Opción 1** — Cargar `data/sudokus.lfp` (Enter usa la ruta por defecto).
2. **Opción 2** — Cargar `data/jugadores.lfp`.
3. **Opción 3** — Cargar `data/intentos.lfp`.
4. **Opción 4** — Validar y calificar todos los intentos cargados.
5. **Opciones 5, 6 y 7** — Generar los reportes HTML, que se guardan en la
   carpeta `reportes/` y pueden abrirse con cualquier navegador.
8. **Opción 8** — Salir del programa.

Cada opción de carga permite indicar una ruta distinta a un archivo
propio; si se presiona Enter sin escribir nada, se usa la ruta de ejemplo
incluida en `data/`.

## Formato de los archivos de entrada

**sudokus.lfp** — `id_sudoku,dificultad,tablero` (81 dígitos, 0 = celda vacía)
**jugadores.lfp** — `carnet,nombre,apellido,nivel`
**intentos.lfp** — `carnet,id_sudoku,solucion,tiempo_segundos,fecha`

## Mecánica de validación

- Las celdas que eran pistas fijas (≠0) en el tablero original deben
  mantenerse sin cambios en la solución; de lo contrario esa celda se
  marca como inválida.
- Se validan las 9 filas, 9 columnas y 9 cajas de 3x3 (27 unidades en
  total), verificando que cada una contenga los dígitos del 1 al 9 sin
  repetirse.
- **Porcentaje de validez** = (unidades válidas / 27) × 100.
- Un intento se considera **resuelto correctamente** solo si el
  porcentaje de validez es 100% y todas las pistas originales se
  respetaron.

## Reportes generados

| Archivo | Contenido |
|---|---|
| `reporte1_resumen_por_sudoku.html` | Intentos recibidos, tiempo promedio y tasa de éxito por tablero |
| `reporte2_rendimiento_por_jugador.html` | Tableros intentados, validez promedio, tiempo promedio y resueltos perfectos por jugador |
| `reporte3_top_mejores_tiempos.html` | Top 10 de los mejores tiempos entre intentos resueltos al 100% |

## Datos de ejemplo incluidos

La carpeta `data/` incluye archivos de ejemplo listos para probar el
sistema de principio a fin: 3 tableros, 4 jugadores y 8 intentos (con
casos correctos, con pistas modificadas y con filas/celdas inválidas)
para poder observar los distintos escenarios de calificación.

## Autor

Oliver Jorge Raxtún Morales — Carné 202400634
Ingeniería en Ciencias y Sistemas, USAC