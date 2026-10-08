
EPSILON = "ε"


## Nodo de un árbol de derivación.
class NodoAST:
    def __init__(self, tipo, token=None, **atributos):
        self.tipo = tipo
        self.token = token
        self.hijos = []
        self.atributos = atributos

    # Constructores
    @classmethod
    def hoja(cls, token):
        """Hoja terminal a partir de un token."""
        return cls(token.tipo, token)

    @classmethod
    def epsilon(cls):
        """Hoja ε (producción vacía)."""
        return cls(EPSILON)

    # Consulta
    @property
    def es_terminal(self):
        return self.token is not None or self.tipo == EPSILON

    @property
    def es_epsilon(self):
        return self.tipo == EPSILON

    def agregar(self, hijo):
        self.hijos.append(hijo)
        return hijo

    ## Primer hijo directo del tipo indicado.
    def buscar(self, tipo):
        for hijo in self.hijos:
            if hijo.tipo == tipo:
                return hijo
        return None

    ## Todos los hijos directos del tipo indicado.
    def buscar_todos(self, tipo):
        return [h for h in self.hijos if h.tipo == tipo]

    def elementos_cadena(self):
        nodo = self
        while nodo is not None:
            hijos = nodo.hijos
            cola = None
            if len(hijos) >= 2 and hijos[-1].tipo == self.tipo:
                cola = hijos[-1]
                visibles = hijos[:-1]
            else:
                visibles = hijos
            for hijo in visibles:
                if not hijo.es_epsilon:
                    yield hijo
            nodo = cola

    def __repr__(self):
        return "NodoAST(%s, hijos=%d)" % (self.tipo, len(self.hijos))