# HorarioScript — Analizador Léxico para Horarios Académicos

Proyecto del curso **Lenguajes Formales y de Programación** (USAC), segundo
semestre 2026. Implementa, en Python, un analizador léxico con interfaz
gráfica (Tkinter) capaz de leer, interpretar y reportar horarios académicos
a partir de archivos de texto con extensión `.hor`, escritos en el
mini-lenguaje **HorarioScript**.

## Contenido del repositorio

```
horarioscript/
├── src/                        Código fuente
│   ├── tokens.py                Token, ErrorLexico, TipoToken, TipoError
│   ├── gestor_errores.py        GestorErrores (modo pánico)
│   ├── analizador_lexico.py     AnalizadorLexico (AFD manual)
│   ├── modelos.py                Curso, Catedratico, Aula, Clase, ModeloHorario
│   ├── interprete.py             InterpreteHorario (tokens -> modelo semántico)
│   ├── detector_choques.py      Detección de choques de horario
│   ├── generador_dot.py          Código DOT (Graphviz) de la jerarquía del horario
│   ├── generador_reportes.py    Generador de los 3 reportes HTML + reporte de errores
│   └── gui_app.py                Interfaz gráfica en Tkinter
├── ejemplos/                    Archivos .hor de ejemplo
│   ├── horario_valido.hor
│   ├── horario_con_choque.hor
│   └── horario_con_errores.hor
├── tests/
│   └── test_manual.py           Script de verificación rápida (sin GUI)
├── docs/                        Documentación del proyecto
│   ├── MANUAL_TECNICO.md
│   ├── MANUAL_USUARIO.md
│   ├──CASOS_PRUEBA.md
|   ├── diagramas/  
|   └── imagenes/  
├── main.py                      Punto de entrada de la aplicación
├── .gitignore
└── README.md
```

## Requisitos

- Python 3.10 o superior (no requiere librerías externas; usa solo la
  biblioteca estándar: `tkinter`, `dataclasses`, `enum`, `html`, `os`,
  `time`, `webbrowser`, `itertools`).
- [Graphviz](https://graphviz.org/) (opcional) para renderizar el archivo
  `.dot` generado por la aplicación como imagen (`dot -Tpng archivo.dot -o
  archivo.png`).

## Ejecución

```bash
git clone <https://github.com/Oliver-1007/LFP_A_2S2026>
cd Proyecto1
python main.py
```

Esto abre la interfaz gráfica de HorarioScript. Desde ahí puedes:

1. **Cargar archivo .hor** — abre un archivo de la carpeta `ejemplos/` o
   uno propio.
2. **Analizar** — ejecuta el AFD, llena la tabla de tokens, la tabla de
   errores y detecta choques de horario.
3. **Generar reportes HTML** — crea, en una carpeta `reportes_horarioscript/`
   junto al archivo analizado, los 3 reportes obligatorios más el reporte
   de errores.
4. **Generar diagrama DOT** — crea el archivo `.dot` con la jerarquía
   curso-catedrático-aula, listo para renderizar con Graphviz.

También puedes ejecutar una verificación rápida por consola (sin abrir la
GUI) sobre los archivos de `ejemplos/`:

```bash
python -m tests.test_manual
```

## El lenguaje HorarioScript (resumen)

Un archivo `.hor` describe un bloque `HORARIO { ... };` con cuatro
secciones: `CURSOS`, `CATEDRATICOS`, `AULAS` y `CLASES`. Ejemplo mínimo:

```
## Horario Lenguajes Formales - Segundo Semestre 2026
HORARIO {
CURSOS {
curso: "Lenguajes Formales y de Programacion" [codigo: "LFP-0796", creditos: 4],
};
CATEDRATICOS {
catedratico: "Otto Rodriguez" [codigo: "DOC-001", categoria: TITULAR],
};
AULAS {
aula: "A-101" [capacidad: 40, edificio: "T-3"],
};
CLASES {
clase: "LFP-0796" con "DOC-001" en "A-101" [dia: LUNES, inicio: 07:00, fin: 08:40, seccion: "N"],
};
};
```

El detalle completo de la gramática léxica, los 12 tipos de token, los 7
tipos de error y las decisiones de diseño para resolver las ambigüedades
del lenguaje están documentados en [`docs/MANUAL_TECNICO.md`](docs/MANUAL_TECNICO.md).

## Documentación

- **Manual Técnico**: [`docs/MANUAL_TECNICO.md`](docs/MANUAL_TECNICO.md) —
  arquitectura, diagrama de clases, diagrama del AFD, tabla de
  transiciones, algoritmo de tokenización, lógica de choques de horario y
  justificación de decisiones de diseño.
- **Manual de Usuario**: [`docs/MANUAL_USUARIO.md`](docs/MANUAL_USUARIO.md) —
  guía paso a paso de uso de la aplicación.
- **Casos de Prueba**: [`docs/CASOS_PRUEBA.md`](docs/CASOS_PRUEBA.md) —
  casos ejecutados con entrada, resultado esperado y resultado obtenido.

## Autor

Oliver Jorge Raxtún Morales — Carné 202400634 — Facultad de Ingeniería,
Universidad de San Carlos de Guatemala.