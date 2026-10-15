
import tkinter as tk
import tkinter.font as tkfont

from tokens import TipoToken as T


## Dibuja un árbol de derivación en un widget Text de solo lectura
class VistaPrevia:

    TAMANOS_ENCABEZADO = {1: 24, 2: 20, 3: 17, 4: 15, 5: 13, 6: 12}
    TAMANO_BASE = 11
    SANGRIA_LISTA = 22
    VINETAS = ("•", "◦", "▪")

    def __init__(self, widget):
        self.widget = widget
        self._familia = self._elegir_familia(("Segoe UI", "Helvetica", "Arial", "DejaVu Sans"))
        self._mono = self._elegir_familia(("Consolas", "Menlo", "DejaVu Sans Mono", "Courier New"))
        self._configurar_etiquetas()

    # configuración
    def _elegir_familia(self, candidatas):
        disponibles = set(tkfont.families(self.widget))
        for nombre in candidatas:
            if nombre in disponibles:
                return nombre
        return tkfont.nametofont("TkDefaultFont").actual("family")

    def _configurar_etiquetas(self):
        w = self.widget
        w.configure(font=(self._familia, self.TAMANO_BASE), wrap=tk.WORD, padx=14, pady=10,
                    state=tk.DISABLED, cursor="arrow")
        w.tag_configure("bloque", spacing1=3, spacing3=7)
        w.tag_configure("encabezado", spacing1=12, spacing3=6)
        w.tag_configure("codigo_en_linea", background="#eff1f3")
        w.tag_configure("bloque_codigo", background="#0d1117", foreground="#e6edf3",
                        lmargin1=14, lmargin2=14, rmargin=14, spacing1=0, spacing3=0)
        w.tag_configure("barra_cita", foreground="#c4cad1")
        w.tag_configure("regla", foreground="#c4cad1", spacing1=6, spacing3=10)
        w.tag_configure("estado_ok", foreground="#1a7f37", background="#dafbe1",
                        font=(self._familia, 9), spacing3=8)
        w.tag_configure("estado_error", foreground="#a40e26", background="#ffe9e9",
                        font=(self._familia, 9), spacing3=8)
        w.tag_configure("vacio", foreground="#8b949e", font=(self._familia, 10, "italic"))

    ## Etiqueta de fuente para una combinación de estilo
    def _fuente(self, tamano, negrita, cursiva, monoespaciada):
        nombre = "f_%d_%d_%d_%d" % (tamano, negrita, cursiva, monoespaciada)
        if nombre not in self.widget.tag_names():
            estilos = ("bold " if negrita else "") + ("italic" if cursiva else "")
            familia = self._mono if monoespaciada else self._familia
            self.widget.tag_configure(nombre, font=(familia, tamano, estilos.strip() or "normal"))
        return nombre

    ## Etiqueta de margen izquierdo (listas y citas), creada bajo demanda
    def _margen(self, clave, izquierda, resto=None, color=None):
        nombre = "m_%s_%d_%d" % (clave, izquierda, resto if resto is not None else izquierda)
        if nombre not in self.widget.tag_names():
            opciones = {"lmargin1": izquierda,
                        "lmargin2": resto if resto is not None else izquierda}
            if color:
                opciones["foreground"] = color
            self.widget.tag_configure(nombre, **opciones)
        return nombre

    # API
    def limpiar(self):
        self.widget.configure(state=tk.NORMAL)
        self.widget.delete("1.0", tk.END)
        self.widget.configure(state=tk.DISABLED)

    ## Redibuja la vista previa completa a partir del árbol de derivación
    def renderizar(self, arbol, hay_errores=False):
        posicion = self.widget.yview()[0]
        self.widget.configure(state=tk.NORMAL)
        self.widget.delete("1.0", tk.END)

        if hay_errores:
            self.widget.insert(tk.END, "El documento tiene errores: vista previa parcial \n",
                               ("estado_error",))
        else:
            self.widget.insert(tk.END, "Análisis completado sin errores \n", ("estado_ok",))

        hubo_bloques = False
        for elemento in arbol.elementos_cadena():
            if elemento.tipo != "<bloque>":
                continue
            hubo_bloques = True
            self._bloque(elemento.hijos[0])
        if not hubo_bloques:
            self.widget.insert(tk.END, "El documento está vacío.", ("vacio",))

        self.widget.configure(state=tk.DISABLED)
        self.widget.yview_moveto(posicion)

    # bloques
    def _bloque(self, bloque):
        tipo = bloque.tipo
        if tipo == "<encabezado>":
            nivel = bloque.atributos["nivel"]
            self._en_linea(bloque.buscar("<en_linea>"), ("encabezado",),
                           self.TAMANOS_ENCABEZADO[nivel], negrita=True)
            self.widget.insert(tk.END, "\n", ("encabezado",))
        elif tipo == "<parrafo>":
            self._en_linea(bloque.buscar("<en_linea>"), ("bloque",), self.TAMANO_BASE)
            self.widget.insert(tk.END, "\n", ("bloque",))
        elif tipo == "<lista>":
            self._lista(bloque, 0)
        elif tipo == "<cita>":
            self._cita(bloque)
        elif tipo == "<bloque_codigo>":
            self._bloque_codigo(bloque)
        elif tipo == "<regla_horizontal>":
            self.widget.insert(tk.END, "─" * 64 + "\n", ("regla",))

    def _lista(self, lista, profundidad):
        izquierda = self.SANGRIA_LISTA * (profundidad + 1)
        margen = self._margen("lista", izquierda - 14, izquierda)
        base = (margen, "bloque")
        fuente = self._fuente(self.TAMANO_BASE, False, False, False)
        vineta = self.VINETAS[profundidad % len(self.VINETAS)]
        for item in lista.elementos_cadena():
            self.widget.insert(tk.END, vineta + "  ", base + (fuente,))
            self._en_linea(item.buscar("<en_linea>"), base, self.TAMANO_BASE)
            self.widget.insert(tk.END, "\n", base)
            for sublista in item.buscar_todos("<sublista>"):
                self._lista(sublista.buscar("<lista>"), profundidad + 1)

    def _cita(self, cita):
        nivel = cita.atributos["nivel"]
        margen = self._margen("cita", 10 + 18 * (nivel - 1), 10 + 18 * (nivel - 1), "#57606a")
        fuente = self._fuente(self.TAMANO_BASE, False, False, False)
        for elemento in cita.elementos_cadena():
            hijo = elemento.hijos[0]
            if hijo.tipo == "<linea_cita>":
                self.widget.insert(tk.END, "┃ " * nivel, ("barra_cita", margen, "bloque", fuente))
                self._en_linea(hijo.buscar("<en_linea>"), (margen, "bloque"), self.TAMANO_BASE)
                self.widget.insert(tk.END, "\n", (margen, "bloque"))
            else:
                self._cita(hijo)

    def _bloque_codigo(self, bloque):
        fuente = self._fuente(10, False, False, True)
        etiquetas = (fuente, "bloque_codigo")
        contenido = bloque.atributos["contenido"]
        self.widget.insert(tk.END, " \n", etiquetas)
        for linea in contenido.split("\n") if contenido else [""]:
            self.widget.insert(tk.END, linea + "\n", etiquetas)
        self.widget.insert(tk.END, " \n", etiquetas)
        self.widget.insert(tk.END, "\n", ("bloque",))

    # en línea
    def _en_linea(self, en_linea, etiquetas, tamano, negrita=False, cursiva=False):
        for elemento in en_linea.elementos_cadena():
            hijo = elemento.hijos[0]
            if hijo.tipo == "<negrita>":
                self._en_linea(hijo.buscar("<en_linea>"), etiquetas, tamano, True, cursiva)
            elif hijo.tipo == "<cursiva>":
                self._en_linea(hijo.buscar("<en_linea>"), etiquetas, tamano, negrita, True)
            elif hijo.tipo == "<codigo_inline>":
                estilo = self._fuente(max(tamano - 1, 9), negrita, cursiva, True)
                self.widget.insert(tk.END, hijo.atributos["contenido"],
                                   etiquetas + (estilo, "codigo_en_linea"))
            elif hijo.tipo == T.SALTO_LINEA:
                self.widget.insert(tk.END, " ", etiquetas + (self._fuente(tamano, negrita, cursiva, False),))
            else:
                # Cada fragmento lleva una sola etiqueta de fuente (evita conflictos de prioridad)
                estilo = self._fuente(tamano, negrita, cursiva, False)
                self.widget.insert(tk.END, hijo.token.lexema, etiquetas + (estilo,))
