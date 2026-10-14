# MarkdownCheck

**Analizador léxico-sintáctico de Markdown a HTML**
Proyecto 2 — Lenguajes Formales y de Programación (LFP) · Universidad de San Carlos de Guatemala (USAC)

> **Autor:** `Oliver Jorge Raxtún Morales` · **Carnet:** `202400634` · **Sección:** `A` · **Semestre:** `Segundo Semestre / 2026`

---

## Descripción

MarkdownCheck lee un documento escrito en un subconjunto de Markdown, lo analiza con un **Autómata Finito Determinista (AFD)** escrito a mano y un **parser descendente recursivo** escrito a mano, construye un **árbol de derivación**, y a partir de él genera:

- **Reporte 1** — el documento traducido a HTML (`reporte1_documento.html`).
- **Reporte 2** — estadísticas del documento (`reporte2_estadisticas.html`).
- **Reporte 3** — tabla de contenido con enlaces al Reporte 1 (`reporte3_indice.html`).
- **`arbol.dot`** — árbol de derivación en formato Graphviz.

Además muestra la **tabla de tokens** y la **tabla de errores léxicos y sintácticos** en una interfaz gráfica (Tkinter). El análisis nunca se detiene ante el primer error: se recupera (modo pánico) y reporta todos los problemas en una sola pasada.

> **No se usan** librerías de parsing (`ply`, `lark`, `antlr4`...), ni de conversión Markdown (`markdown`, `mistune`...), ni el módulo `re` en la tokenización.

## Subconjunto de Markdown soportado

| Elemento | Sintaxis | HTML generado |
|---|---|---|
| Encabezados | `#` a `######` + espacio | `<h1>` … `<h6>` |
| Párrafos | texto; una línea en blanco separa bloques | `<p>` |
| Negrita | `**texto**` | `<strong>` |
| Cursiva | `*texto*` | `<em>` |
| Código en línea | `` `texto` `` | `<code>` |
| Listas no ordenadas | `-`, `*` o `+` + espacio; sublistas por indentación (2 espacios = 1 nivel), 3+ niveles | `<ul><li>` anidados |
| Citas | `>` (anidadas con `>>` o `> >`), 2+ niveles | `<blockquote>` anidados |
| Bloques de código | cercas ```` ``` ```` (contenido literal) | `<pre><code class="language-x">` |
| Regla horizontal | `---` | `<hr>` |

## Requisitos

| Requisito | Detalle |
|---|---|
| Python | **3.10 o superior** |
| Tkinter | Incluido con Python en Windows y macOS. En Linux: `sudo apt install python3-tk` |
| Graphviz *(opcional)* | Solo para convertir `arbol.dot` a imagen (`dot -Tpng arbol.dot -o arbol.png`). La aplicación funciona sin él |

**No hay dependencias externas** (`pip install` no es necesario).

## Instalación y ejecución

```bash
# 1. Clonar el repositorio
git clone https://github.com/Oliver-1007/LFP_A_2S2026/tree/main/Proyecto2
cd MarkdownCheck

# 2. Ejecutar la interfaz gráfica
python src/main.py

# 2b. O abrirla con un archivo ya cargado
python src/main.py examples/ejemplo_valido.md

# 2c. O ejecutar sin interfaz gráfica (genera reportes si no hay errores)
python src/main.py examples/ejemplo_valido.md --consola --salida reportes
```

En Windows puede usarse `py src/main.py`.

### Uso rápido de la interfaz

1. **Abrir .md** (o escribir/pegar texto en el editor).
2. **Analizar**.
3. Revisar las pestañas **Tokens**, **Errores** y **Árbol de derivación (DOT)**.
4. Si no hay errores, los reportes se generan en la carpeta `reportes/` y se habilitan los botones **Reporte 1 / 2 / 3** (se abren en el navegador).

## Estructura del repositorio

```
MarkdownCheck/
├── src/                       Código fuente
│   ├── main.py                Punto de entrada (GUI y modo consola)
│   ├── tokens.py              TipoToken y Token
│   ├── gestor_errores.py      TipoError, FaseError, ErrorAnalisis, GestorErrores
│   ├── analizador_lexico.py   AnalizadorLexico (AFD manual)
│   ├── nodo_ast.py            NodoAST (árbol de derivación)
│   ├── analizador_sintactico.py  AnalizadorSintactico (descendente recursivo)
│   ├── generador_html.py      GeneradorHTML (Reportes 1, 2 y 3)
│   ├── generador_dot.py       GeneradorDOT (Graphviz)
│   ├── procesador.py          Fachada: análisis + escritura de archivos
│   └── interfaz_grafica.py    AplicacionMarkdownCheck (Tkinter)
├── tests/                     Pruebas automatizadas (unittest, 156 pruebas)
├── examples/                  Documentos de entrada de ejemplo
│   ├── ejemplo_valido.md
│   └── ejemplo_con_errores.md
├── docs/                      Documentación
│   ├── manual_tecnico.md
│   ├── manual_usuario.md
│   ├── casos_de_prueba.md
│   └── img/                   Diagramas y capturas de pantalla
├── .gitignore
└── README.md
```

## Pruebas

```bash
# Toda la suite (desde la raíz del proyecto)
python -m unittest discover -s tests -v

# Tabla de casos de prueba (entrada / esperado / obtenido)
python tests/test_casos_prueba.py --tabla
```

Las pruebas de la interfaz gráfica se omiten automáticamente si el equipo no tiene pantalla o Tkinter.

## Documentación

| Documento | Contenido |
|---|---|
| [Manual técnico](docs/manual_tecnico.md) | Arquitectura, diagrama de clases, AFD, gramática, parser, recuperación de errores y decisiones de diseño |
| [Manual de usuario](docs/manual_usuario.md) | Guía paso a paso con capturas de pantalla |
| [Casos de prueba](docs/casos_de_prueba.md) | 18 casos con entrada, resultado esperado y resultado obtenido |

## Limitaciones conocidas

- Las citas contienen únicamente texto en línea (no listas ni encabezados dentro de una cita).
- Una línea en blanco termina la lista en curso; una lista con líneas en blanco entre ítems se trata como varias listas.
- El código en línea debe cerrarse en la misma línea donde se abre.
- No hay secuencias de escape (`\*`).
- No se implementó el alcance opcional (listas ordenadas, enlaces, imágenes, tablas, tachado, listas de tareas, vista previa en vivo, resaltado de sintaxis).


## Licencia

Proyecto académico desarrollado para el curso de Lenguajes Formales y de Programación, USAC.
