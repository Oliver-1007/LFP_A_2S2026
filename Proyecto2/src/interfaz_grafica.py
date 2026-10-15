
import os
import shutil
import subprocess
import tkinter as tk
import webbrowser
from tkinter import filedialog, messagebox, ttk

from procesador import ProcesadorMarkdown
from vista_previa import VistaPrevia


class AplicacionMarkdownCheck:
    """Ventana principal de la aplicación."""

    TITULO = "MarkdownCheck — Analizador Léxico-Sintáctico de Markdown a HTML"
    RETARDO_VISTA_MS = 300

    def __init__(self, raiz, archivo_inicial=None):
        self.raiz = raiz
        self.procesador = ProcesadorMarkdown()
        self.resultado = None
        self.ruta_archivo = None
        self.rutas_reportes = {}
        self._temporizador_vista = None
        self.vista_en_vivo = tk.BooleanVar(value=True)

        raiz.title(self.TITULO)
        raiz.geometry("1500x760")
        raiz.minsize(980, 560)

        self._crear_estilos()
        self._crear_barra_herramientas()
        self._crear_paneles()
        self._crear_barra_estado()
        self._actualizar_botones()

        if archivo_inicial:
            self._cargar_archivo(archivo_inicial)


    # Construcción de la interfaz
    def _crear_estilos(self):
        estilo = ttk.Style()
        try:
            estilo.theme_use("clam")
        except tk.TclError:
            pass
        estilo.configure("Treeview", rowheight=22)
        estilo.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"))
        estilo.configure("Principal.TButton", font=("Segoe UI", 9, "bold"))

    def _crear_barra_herramientas(self):
        barra = ttk.Frame(self.raiz, padding=(8, 6))
        barra.pack(side=tk.TOP, fill=tk.X)

        ttk.Button(barra, text="Abrir .md", command=self.abrir_archivo).pack(side=tk.LEFT, padx=2)
        ttk.Button(barra, text="Guardar", command=self.guardar_archivo).pack(side=tk.LEFT, padx=2)
        ttk.Separator(barra, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=8)
        self.btn_analizar = ttk.Button(barra, text="Analizar", style="Principal.TButton",
                                       command=self.analizar)
        self.btn_analizar.pack(side=tk.LEFT, padx=2)
        ttk.Separator(barra, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=8)

        self.btn_r1 = ttk.Button(barra, text="Reporte 1: Documento",
                                 command=lambda: self.abrir_reporte("reporte1"))
        self.btn_r2 = ttk.Button(barra, text="Reporte 2: Estadísticas",
                                 command=lambda: self.abrir_reporte("reporte2"))
        self.btn_r3 = ttk.Button(barra, text="Reporte 3: Índice",
                                 command=lambda: self.abrir_reporte("reporte3"))
        for boton in (self.btn_r1, self.btn_r2, self.btn_r3):
            boton.pack(side=tk.LEFT, padx=2)
        ttk.Separator(barra, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=8)
        ttk.Checkbutton(barra, text="Vista previa en vivo", variable=self.vista_en_vivo,
                        command=self._alternar_vista_en_vivo).pack(side=tk.LEFT, padx=2)
        self.btn_dot = ttk.Button(barra, text="Exportar árbol (.dot)", command=self.exportar_dot)
        self.btn_dot.pack(side=tk.LEFT, padx=2)
        self.btn_tablas = ttk.Button(barra, text="Exportar tablas (HTML)", command=self.exportar_tablas)
        self.btn_tablas.pack(side=tk.LEFT, padx=2)
        ttk.Button(barra, text="Limpiar", command=self.limpiar).pack(side=tk.RIGHT, padx=2)

    def _crear_paneles(self):
        divisor = ttk.PanedWindow(self.raiz, orient=tk.HORIZONTAL)
        divisor.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 4))

        # Panel izquierdo: editor
        marco_editor = ttk.LabelFrame(divisor, text=" Editor Markdown ", padding=4)
        divisor.add(marco_editor, weight=1)

        self.editor = tk.Text(marco_editor, wrap=tk.NONE, undo=True, font=("Consolas", 11),
                              tabs=("1c",), padx=6, pady=4)
        barra_v = ttk.Scrollbar(marco_editor, orient=tk.VERTICAL, command=self.editor.yview)
        barra_h = ttk.Scrollbar(marco_editor, orient=tk.HORIZONTAL, command=self.editor.xview)
        self.editor.configure(yscrollcommand=barra_v.set, xscrollcommand=barra_h.set)
        barra_v.pack(side=tk.RIGHT, fill=tk.Y)
        barra_h.pack(side=tk.BOTTOM, fill=tk.X)
        self.editor.pack(fill=tk.BOTH, expand=True)
        self.editor.tag_configure("resaltado", background="#fff3a3")
        self.editor.tag_configure("error", background="#ffb3b3")
        self.editor.bind("<<Modified>>", self._al_modificar_editor)

        # Panel derecho: pestañas
        self.pestanas = ttk.Notebook(divisor)
        divisor.add(self.pestanas, weight=2)

        self.tabla_tokens = self._crear_tabla(
            "Tokens",
            [("num", "N°", 55), ("lexema", "Lexema", 330), ("tipo", "Tipo de token", 150),
             ("linea", "Línea", 60), ("columna", "Columna", 70)])
        self.tabla_tokens.bind("<<TreeviewSelect>>", self._seleccionar_token)

        self.tabla_errores = self._crear_tabla(
            "Errores",
            [("num", "N°", 45), ("lexema", "Lexema", 90), ("tipo", "Tipo de error", 185),
             ("fase", "Fase", 80), ("descripcion", "Descripción", 400),
             ("linea", "Línea", 55), ("columna", "Columna", 65)])
        self.tabla_errores.bind("<<TreeviewSelect>>", self._seleccionar_error)
        self.tabla_errores.tag_configure("lexico", background="#ffe9e9")
        self.tabla_errores.tag_configure("sintactico", background="#fff1d6")

        self.marco_vista = ttk.Frame(self.pestanas)
        self.pestanas.add(self.marco_vista, text="Vista previa")
        self.texto_vista = tk.Text(self.marco_vista, borderwidth=0, highlightthickness=0)
        vista_v = ttk.Scrollbar(self.marco_vista, orient=tk.VERTICAL, command=self.texto_vista.yview)
        self.texto_vista.configure(yscrollcommand=vista_v.set)
        vista_v.pack(side=tk.RIGHT, fill=tk.Y)
        self.texto_vista.pack(fill=tk.BOTH, expand=True)
        self.vista = VistaPrevia(self.texto_vista)

        marco_dot = ttk.Frame(self.pestanas)
        self.pestanas.add(marco_dot, text="Árbol de derivación (DOT)")
        self.texto_dot = tk.Text(marco_dot, wrap=tk.NONE, font=("Consolas", 10), state=tk.DISABLED)
        dot_v = ttk.Scrollbar(marco_dot, orient=tk.VERTICAL, command=self.texto_dot.yview)
        dot_h = ttk.Scrollbar(marco_dot, orient=tk.HORIZONTAL, command=self.texto_dot.xview)
        self.texto_dot.configure(yscrollcommand=dot_v.set, xscrollcommand=dot_h.set)
        dot_v.pack(side=tk.RIGHT, fill=tk.Y)
        dot_h.pack(side=tk.BOTTOM, fill=tk.X)
        self.texto_dot.pack(fill=tk.BOTH, expand=True)

    ## Crea una pestaña con un Treeview con scroll y devuelve el Treeview
    def _crear_tabla(self, titulo, columnas):
        marco = ttk.Frame(self.pestanas)
        self.pestanas.add(marco, text=titulo)
        arbol = ttk.Treeview(marco, columns=[c[0] for c in columnas], show="headings",
                             selectmode="browse")
        for clave, texto, ancho in columnas:
            arbol.heading(clave, text=texto)
            arbol.column(clave, width=ancho, minwidth=40, anchor=tk.W, stretch=(clave in ("lexema", "descripcion")))
        barra_v = ttk.Scrollbar(marco, orient=tk.VERTICAL, command=arbol.yview)
        barra_h = ttk.Scrollbar(marco, orient=tk.HORIZONTAL, command=arbol.xview)
        arbol.configure(yscrollcommand=barra_v.set, xscrollcommand=barra_h.set)
        barra_v.pack(side=tk.RIGHT, fill=tk.Y)
        barra_h.pack(side=tk.BOTTOM, fill=tk.X)
        arbol.pack(fill=tk.BOTH, expand=True)
        return arbol

    def _crear_barra_estado(self):
        self.estado = tk.StringVar(value="Listo. Abra un archivo .md o escriba texto y pulse «Analizar».")
        ttk.Label(self.raiz, textvariable=self.estado, relief=tk.SUNKEN, anchor=tk.W,
                  padding=(8, 3)).pack(side=tk.BOTTOM, fill=tk.X)

    ## Los reportes solo están disponibles tras un análisis exitoso
    def _actualizar_botones(self):
        hay_reportes = bool(self.rutas_reportes)
        for boton in (self.btn_r1, self.btn_r2, self.btn_r3):
            boton.configure(state=tk.NORMAL if hay_reportes else tk.DISABLED)
        hay_resultado = self.resultado is not None
        self.btn_dot.configure(state=tk.NORMAL if hay_resultado else tk.DISABLED)
        self.btn_tablas.configure(state=tk.NORMAL if hay_resultado else tk.DISABLED)


    # Archivos
    def abrir_archivo(self):
        ruta = filedialog.askopenfilename(
            title="Abrir documento Markdown",
            filetypes=[("Markdown", "*.md *.markdown"), ("Texto", "*.txt"), ("Todos", "*.*")])
        if ruta:
            self._cargar_archivo(ruta)

    def _cargar_archivo(self, ruta):
        try:
            with open(ruta, "r", encoding="utf-8-sig") as archivo:
                contenido = archivo.read()
        except (OSError, UnicodeDecodeError) as error:
            messagebox.showerror("Error al abrir", "No se pudo leer el archivo:\n%s" % error)
            return
        self.ruta_archivo = ruta
        self.editor.delete("1.0", tk.END)
        self.editor.insert("1.0", contenido)
        self.editor.edit_reset()
        self.raiz.title("%s — %s" % (os.path.basename(ruta), self.TITULO))
        self._limpiar_resultados()
        self.estado.set("Archivo cargado: %s" % ruta)

    def guardar_archivo(self):
        ruta = self.ruta_archivo or filedialog.asksaveasfilename(
            title="Guardar documento", defaultextension=".md",
            filetypes=[("Markdown", "*.md"), ("Todos", "*.*")])
        if not ruta:
            return
        try:
            with open(ruta, "w", encoding="utf-8") as archivo:
                archivo.write(self.editor.get("1.0", "end-1c"))
        except OSError as error:
            messagebox.showerror("Error al guardar", str(error))
            return
        self.ruta_archivo = ruta
        self.raiz.title("%s — %s" % (os.path.basename(ruta), self.TITULO))
        self.estado.set("Guardado en %s" % ruta)

    def _carpeta_reportes(self):
        base = os.path.dirname(self.ruta_archivo) if self.ruta_archivo else os.getcwd()
        return os.path.join(base, "reportes")


    # Análisis
    def analizar(self):
        texto = self.editor.get("1.0", "end-1c")
        nombre = os.path.basename(self.ruta_archivo) if self.ruta_archivo else "documento.md"

        self._limpiar_resultados()
        self.resultado = self.procesador.analizar(texto, nombre)
        self._mostrar_tokens()
        self._mostrar_errores()
        self._mostrar_dot()
        self.vista.renderizar(self.resultado.arbol, not self.resultado.exito)

        total_tokens = len(self.resultado.tokens_visibles)
        total_errores = self.resultado.gestor.cantidad()

        if self.resultado.exito:
            try:
                self.rutas_reportes = self.procesador.generar_reportes(
                    self.resultado, self._carpeta_reportes())
                self.procesador.guardar_dot(self.resultado,
                                            os.path.join(self._carpeta_reportes(), "arbol.dot"))
            except OSError as error:
                messagebox.showerror("Error al generar reportes", str(error))
                self.rutas_reportes = {}
            self.pestanas.select(0)
            self.estado.set("✓ Análisis exitoso — %d tokens, 0 errores. Reportes generados en: %s"
                            % (total_tokens, self._carpeta_reportes()))
            if self.rutas_reportes:
                messagebox.showinfo(
                    "Análisis completado",
                    "El documento no contiene errores.\n\nSe generaron los 3 reportes HTML y "
                    "arbol.dot en:\n%s" % self._carpeta_reportes())
        else:
            self.pestanas.select(1)
            self.estado.set("✗ Se encontraron %d error(es) — %d tokens. Los reportes solo se generan "
                            "si el análisis no tiene errores." % (total_errores, total_tokens))
            messagebox.showwarning(
                "Errores encontrados",
                "Se detectaron %d error(es) léxicos/sintácticos.\nRevise la pestaña «Errores»; al "
                "seleccionar una fila se marca la posición en el editor." % total_errores)
        self._actualizar_botones()

    def _limpiar_resultados(self):
        self.resultado = None
        self.rutas_reportes = {}
        for tabla in (self.tabla_tokens, self.tabla_errores):
            tabla.delete(*tabla.get_children())
        self.texto_dot.configure(state=tk.NORMAL)
        self.texto_dot.delete("1.0", tk.END)
        self.texto_dot.configure(state=tk.DISABLED)
        self.editor.tag_remove("resaltado", "1.0", tk.END)
        self.editor.tag_remove("error", "1.0", tk.END)
        self._actualizar_botones()

    def limpiar(self):
        if self.editor.get("1.0", "end-1c").strip() and not messagebox.askyesno(
                "Limpiar", "¿Borrar el contenido del editor y los resultados?"):
            return
        self.editor.delete("1.0", tk.END)
        self.ruta_archivo = None
        self.raiz.title(self.TITULO)
        self._limpiar_resultados()
        self.vista.limpiar()
        self.estado.set("Listo.")

    # vista previa en vivo
    def _al_modificar_editor(self, _evento=None):
        if not self.editor.edit_modified():
            return
        self.editor.edit_modified(False)
        if not self.vista_en_vivo.get():
            return
        if self._temporizador_vista is not None:
            self.raiz.after_cancel(self._temporizador_vista)
        self._temporizador_vista = self.raiz.after(self.RETARDO_VISTA_MS,
                                                   self._actualizar_vista_previa)

    ## Analiza el texto actual y redibuja la vista previa
    def _actualizar_vista_previa(self):
        self._temporizador_vista = None
        texto = self.editor.get("1.0", "end-1c")
        try:
            resultado = self.procesador.analizar(texto)
            self.vista.renderizar(resultado.arbol, not resultado.exito)
        except Exception as error:
            self.estado.set("No se pudo actualizar la vista previa: %s" % error)

    def _alternar_vista_en_vivo(self):
        if self.vista_en_vivo.get():
            self._actualizar_vista_previa()
            self.pestanas.select(self.marco_vista)
            self.estado.set("Vista previa en vivo activada.")
        else:
            if self._temporizador_vista is not None:
                self.raiz.after_cancel(self._temporizador_vista)
                self._temporizador_vista = None
            self.estado.set("Vista previa en vivo desactivada: se actualiza solo al pulsar «Analizar».")

    # tablas
    def _mostrar_tokens(self):
        for numero, token in enumerate(self.resultado.tokens_visibles, 1):
            self.tabla_tokens.insert(
                "", tk.END, iid=str(numero - 1),
                values=(numero, token.lexema_visible(), token.tipo, token.linea, token.columna))

    def _mostrar_errores(self):
        for numero, error in enumerate(self.resultado.errores, 1):
            etiqueta = "lexico" if error.fase == "Léxico" else "sintactico"
            self.tabla_errores.insert(
                "", tk.END, iid=str(numero - 1), tags=(etiqueta,),
                values=(numero, error.lexema_visible(), error.tipo, error.fase,
                        error.descripcion, error.linea, error.columna))

    def _mostrar_dot(self):
        codigo = self.procesador.codigo_dot(self.resultado)
        self.texto_dot.configure(state=tk.NORMAL)
        self.texto_dot.insert("1.0", codigo)
        self.texto_dot.configure(state=tk.DISABLED)

    # resaltado en editor
    def _seleccionar_token(self, _evento):
        seleccion = self.tabla_tokens.selection()
        if not seleccion or self.resultado is None:
            return
        token = self.resultado.tokens_visibles[int(seleccion[0])]
        longitud = len(token.lexema) if "\n" not in token.lexema else 0
        self._resaltar("resaltado", token.linea, token.columna, longitud)

    def _seleccionar_error(self, _evento):
        seleccion = self.tabla_errores.selection()
        if not seleccion or self.resultado is None:
            return
        error = self.resultado.errores[int(seleccion[0])]
        self._resaltar("error", error.linea, error.columna, max(1, min(len(error.lexema), 3)))

    def _resaltar(self, etiqueta, linea, columna, longitud):
        self.editor.tag_remove("resaltado", "1.0", tk.END)
        self.editor.tag_remove("error", "1.0", tk.END)
        inicio = "%d.%d" % (linea, max(0, columna - 1))
        fin = "%d.%d" % (linea, max(0, columna - 1) + longitud) if longitud else "%d.end" % linea
        self.editor.tag_add(etiqueta, inicio, fin)
        self.editor.see(inicio)


    # Reportes y exportaciones
    def abrir_reporte(self, clave):
        ruta = self.rutas_reportes.get(clave)
        if not ruta or not os.path.exists(ruta):
            messagebox.showinfo("Reporte no disponible", "Analice un documento sin errores primero.")
            return
        webbrowser.open("file://" + os.path.abspath(ruta).replace("\\", "/"))

    def exportar_dot(self):
        if self.resultado is None:
            return
        ruta = filedialog.asksaveasfilename(
            title="Exportar árbol de derivación", defaultextension=".dot", initialfile="arbol.dot",
            filetypes=[("Graphviz DOT", "*.dot"), ("Todos", "*.*")])
        if not ruta:
            return
        try:
            self.procesador.guardar_dot(self.resultado, ruta)
        except OSError as error:
            messagebox.showerror("Error al exportar", str(error))
            return
        mensaje = "Árbol guardado en:\n%s" % ruta
        dot = shutil.which("dot")
        if dot:                                    # render opcional si Graphviz está instalado
            png = os.path.splitext(ruta)[0] + ".png"
            try:
                subprocess.run([dot, "-Tpng", ruta, "-o", png], check=True, timeout=60)
                mensaje += "\n\nImagen generada:\n%s" % png
            except (subprocess.SubprocessError, OSError):
                pass
        messagebox.showinfo("Exportación completada", mensaje)

    def exportar_tablas(self):
        if self.resultado is None:
            return
        ruta = filedialog.asksaveasfilename(
            title="Exportar tablas de tokens y errores", defaultextension=".html",
            initialfile="tablas_analisis.html", filetypes=[("HTML", "*.html"), ("Todos", "*.*")])
        if not ruta:
            return
        try:
            self.procesador.guardar_tablas(self.resultado, ruta)
        except OSError as error:
            messagebox.showerror("Error al exportar", str(error))
            return
        messagebox.showinfo("Exportación completada", "Tablas guardadas en:\n%s" % ruta)
