
from nodo_ast import EPSILON

## Convierte un árbol de derivación en texto DOT
class GeneradorDOT:

    COLOR_RAIZ = "#2E75B6"
    COLOR_NO_TERMINAL = "#D6EAF8"
    COLOR_TERMINAL = "#F9E79F"
    COLOR_EPSILON = "#E5E8E8"
    MAX_LEXEMA = 28

    def generar(self, arbol):
        """Devuelve el contenido completo del archivo arbol.dot."""
        lineas = [
            "digraph ArbolDerivacion {",
            "  rankdir=TB;",
            '  node [shape=box, style=filled, fontname="Arial"];',
            '  edge [color="#566573"];',
        ]
        aristas = []
        contador = 0
        # Recorrido en preorden iterativo (los árboles de listas/documentos son profundos)
        pila = [(arbol, None)]
        while pila:
            nodo, id_padre = pila.pop()
            id_nodo = "n%d" % contador
            contador += 1
            lineas.append("  %s" % self._declarar(id_nodo, nodo, id_padre is None))
            if id_padre is not None:
                aristas.append("  %s -> %s;" % (id_padre, id_nodo))
            for hijo in reversed(nodo.hijos):
                pila.append((hijo, id_nodo))
        lineas.extend(aristas)
        lineas.append("}")
        return "\n".join(lineas) + "\n"

    # nodos
    def _declarar(self, id_nodo, nodo, es_raiz):
        etiqueta = self._etiqueta(nodo)
        if es_raiz:
            return '%s [label="%s", fillcolor="%s", fontcolor=white];' % (
                id_nodo, etiqueta, self.COLOR_RAIZ)
        if nodo.tipo == EPSILON:
            color = self.COLOR_EPSILON
        elif nodo.es_terminal:
            color = self.COLOR_TERMINAL
        else:
            color = self.COLOR_NO_TERMINAL
        return '%s [label="%s", fillcolor="%s"];' % (id_nodo, etiqueta, color)

    ## Etiqueta del nodo; los terminales muestran su tipo y su lexema
    def _etiqueta(self, nodo):
        if nodo.token is None:
            return self._escapar(nodo.tipo)
        token = nodo.token
        texto = token.lexema
        if token.sintetico:
            texto = "(cierre implícito)"
        elif token.tipo in ("INDENT", "DEDENT"):
            texto = ""
        elif token.tipo in ("NUEVA_LINEA", "SALTO_LINEA", "SALTO_PARRAFO"):
            # Se muestra el carácter de salto como texto literal \n dentro de la etiqueta
            return self._escapar(token.tipo) + "\\n" + "\\\\n"
        if len(texto) > self.MAX_LEXEMA:
            texto = texto[:self.MAX_LEXEMA - 1] + "…"
        if texto:
            return self._escapar(token.tipo) + "\\n" + self._escapar(texto)
        return self._escapar(token.tipo)

    ## Escapa caracteres especiales de una cadena DOT entre comillas
    @staticmethod
    def _escapar(texto):
        salida = []
        for c in texto:
            if c == "\\":
                salida.append("\\\\")
            elif c == '"':
                salida.append('\\"')
            elif c == "\n":
                salida.append("↵")
            elif c == "\t":
                salida.append(" ")
            else:
                salida.append(c)
        return "".join(salida)
