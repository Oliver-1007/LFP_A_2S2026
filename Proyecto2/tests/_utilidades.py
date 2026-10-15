
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(RAIZ, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from procesador import ProcesadorMarkdown
from generador_html import GeneradorHTML
from generador_dot import GeneradorDOT
from tokens import TipoToken as T
from gestor_errores import TipoError, FaseError

# Documento de ejemplo de la sección 4.7 del enunciado (con la sintaxis real
# de Markdown, ya que el PDF original muestra los acentos graves alterados).
EJEMPLO_VALIDO = """# Proyecto de Lenguajes Formales

Este curso combina **teoría sólida** y *práctica de código*, con ejemplos en `Python`.
## Contenido del curso

- Análisis léxico
   - Autómatas finitos
   - Expresiones regulares
- Análisis sintáctico
   - Gramáticas libres de contexto
     - Recursión por la izquierda
     - Recursión por la derecha
- Generación de código

> El análisis sintáctico es donde la teoría se encuentra con la práctica.
>> Y donde más se aprende, según los estudiantes.

```python
def hola():
    print("Hola LFP")
```

---

Fin del documento.
"""


def analizar(texto, nombre="prueba.md"):
    """Ejecuta léxico + sintáctico y devuelve el ResultadoAnalisis."""
    return ProcesadorMarkdown().analizar(texto, nombre)


def tipos_token(resultado, tecnicos=False):
    """Lista de tipos de token visibles (por defecto sin NUEVA_LINEA/SALTO_LINEA/FIN)."""
    ocultos = () if tecnicos else (T.NUEVA_LINEA, T.SALTO_LINEA, T.FIN)
    return [t.tipo for t in resultado.tokens_visibles if t.tipo not in ocultos]


def tokens_de(resultado, tipo):
    return [t for t in resultado.tokens_visibles if t.tipo == tipo]


def tipos_error(resultado):
    return [e.tipo for e in resultado.errores]


def html_de(resultado):
    """Cuerpo HTML (Reporte 1 sin envoltorio) generado desde el árbol."""
    return GeneradorHTML(resultado.arbol).traducir_cuerpo()


def generador(resultado, nombre="prueba.md"):
    return GeneradorHTML(resultado.arbol, nombre)


def contar_nodos(arbol):
    """Cuenta los nodos de un árbol sin recursión."""
    pila = [arbol]
    total = 0
    while pila:
        nodo = pila.pop()
        total += 1
        pila.extend(nodo.hijos)
    return total


def recorrer(arbol):
    """Recorrido iterativo en preorden."""
    pila = [arbol]
    while pila:
        nodo = pila.pop()
        yield nodo
        pila.extend(reversed(nodo.hijos))