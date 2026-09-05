
from __future__ import annotations

import os
import time
import tkinter as tk
import webbrowser
from tkinter import filedialog, messagebox, ttk

from .analizador_lexico import AnalizadorLexico
from .detector_choques import detectar_choques
from .generador_dot import guardar_dot
from .generador_reportes import GeneradorReportes
from .interprete import InterpreteHorario
from .tokens import TipoToken

class AplicacionHorarioScript(tk.Tk):

    def __init__(self) -> None:
        super().__init__()
        self.title("HorarioScript - Analizador Lexico de Horarios Academicos")
        self.geometry("1150x720")
        self.minsize(950, 600)

        self.ruta_archivo_actual: str | None = None
        self.tokens = []
        self.errores = []
        self.modelo = None
        self.choques = []
        self.tiempo_analisis_ms = 0.0

        self._construir_menu()
        self._construir_layout()


    def _construir_menu(self) -> None:
        barra_menu = tk.Menu(self)

        menu_archivo = tk.Menu(barra_menu, tearoff=0)
        menu_archivo.add_command(label="Abrir archivo .hor...", command=self.cargar_archivo)
        menu_archivo.add_separator()
        menu_archivo.add_command(label="Salir", command=self.destroy)
        barra_menu.add_cascade(label="Archivo", menu=menu_archivo)

        menu_analisis = tk.Menu(barra_menu, tearoff=0)
        menu_analisis.add_command(label="Analizar", command=self.analizar)
        menu_analisis.add_command(label="Generar reportes HTML", command=self.generar_reportes)
        menu_analisis.add_command(label="Generar diagrama DOT", command=self.generar_dot)
        barra_menu.add_cascade(label="Analisis", menu=menu_analisis)

        self.config(menu=barra_menu)

    def _construir_layout(self) -> None:
        contenedor_superior = ttk.Frame(self, padding=8)
        contenedor_superior.pack(fill="x")

        ttk.Button(contenedor_superior, text="Cargar archivo .hor", command=self.cargar_archivo).pack(side="left", padx=4)
        ttk.Button(contenedor_superior, text="Analizar", command=self.analizar).pack(side="left", padx=4)
        ttk.Button(contenedor_superior, text="Generar reportes HTML", command=self.generar_reportes).pack(side="left", padx=4)
        ttk.Button(contenedor_superior, text="Generar diagrama DOT", command=self.generar_dot).pack(side="left", padx=4)

        self.etiqueta_archivo = ttk.Label(contenedor_superior, text="Ningun archivo cargado")
        self.etiqueta_archivo.pack(side="left", padx=16)

        panel_principal = ttk.PanedWindow(self, orient="horizontal")
        panel_principal.pack(fill="both", expand=True, padx=8, pady=4)

        # -- Panel izquierdo: contenido del archivo .hor --------------------
        marco_texto = ttk.Frame(panel_principal)
        ttk.Label(marco_texto, text="Contenido del archivo .hor").grid(
            row=0, column=0, columnspan=2, sticky="w"
        )
        self.area_texto = tk.Text(marco_texto, wrap="none", undo=True)
        scroll_y_texto = ttk.Scrollbar(marco_texto, orient="vertical", command=self.area_texto.yview)
        scroll_x_texto = ttk.Scrollbar(marco_texto, orient="horizontal", command=self.area_texto.xview)
        self.area_texto.configure(yscrollcommand=scroll_y_texto.set, xscrollcommand=scroll_x_texto.set)
        self.area_texto.grid(row=1, column=0, sticky="nsew")
        scroll_y_texto.grid(row=1, column=1, sticky="ns")
        scroll_x_texto.grid(row=2, column=0, sticky="ew")
        marco_texto.rowconfigure(1, weight=1)
        marco_texto.columnconfigure(0, weight=1)
        panel_principal.add(marco_texto, weight=1)

        # -- Panel derecho: pestanas con resultados --------------------------
        self.notebook = ttk.Notebook(panel_principal)
        panel_principal.add(self.notebook, weight=2)

        self._pestaña_tokens()
        self._pestaña_errores()
        self._pestaña_choques()
        self._pestaña_resumen()

        self.barra_estado = ttk.Label(self, text="Listo.", relief="sunken", anchor="w")
        self.barra_estado.pack(fill="x", side="bottom")

    def _pestaña_tokens(self) -> None:
        marco = ttk.Frame(self.notebook)
        columnas = ("numero", "lexema", "tipo", "linea", "columna")
        self.tabla_tokens = ttk.Treeview(marco, columns=columnas, show="headings")
        titulos = {"numero": "#", "lexema": "Lexema", "tipo": "Tipo de token", "linea": "Linea", "columna": "Columna"}
        anchos = {"numero": 50, "lexema": 220, "tipo": 230, "linea": 60, "columna": 70}
        for columna in columnas:
            self.tabla_tokens.heading(columna, text=titulos[columna])
            self.tabla_tokens.column(columna, width=anchos[columna], anchor="w")
        scroll = ttk.Scrollbar(marco, orient="vertical", command=self.tabla_tokens.yview)
        self.tabla_tokens.configure(yscrollcommand=scroll.set)
        self.tabla_tokens.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.notebook.add(marco, text="Tabla de tokens")

    def _pestaña_errores(self) -> None:
        marco = ttk.Frame(self.notebook)
        columnas = ("numero", "lexema", "tipo", "descripcion", "linea", "columna")
        self.tabla_errores = ttk.Treeview(marco, columns=columnas, show="headings")
        titulos = {
            "numero": "#", "lexema": "Lexema invalido", "tipo": "Tipo de error",
            "descripcion": "Descripcion", "linea": "Linea", "columna": "Columna",
        }
        anchos = {"numero": 50, "lexema": 150, "tipo": 180, "descripcion": 340, "linea": 60, "columna": 70}
        for columna in columnas:
            self.tabla_errores.heading(columna, text=titulos[columna])
            self.tabla_errores.column(columna, width=anchos[columna], anchor="w")
        scroll = ttk.Scrollbar(marco, orient="vertical", command=self.tabla_errores.yview)
        self.tabla_errores.configure(yscrollcommand=scroll.set)
        self.tabla_errores.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.notebook.add(marco, text="Tabla de errores")

    def _pestaña_choques(self) -> None:
        marco = ttk.Frame(self.notebook)
        columnas = ("tipo", "recurso", "clase_a", "clase_b")
        self.tabla_choques = ttk.Treeview(marco, columns=columnas, show="headings")
        titulos = {
            "tipo": "Tipo de choque", "recurso": "Recurso en conflicto",
            "clase_a": "Clase A", "clase_b": "Clase B",
        }
        anchos = {"tipo": 120, "recurso": 140, "clase_a": 260, "clase_b": 260}
        for columna in columnas:
            self.tabla_choques.heading(columna, text=titulos[columna])
            self.tabla_choques.column(columna, width=anchos[columna], anchor="w")
        scroll = ttk.Scrollbar(marco, orient="vertical", command=self.tabla_choques.yview)
        self.tabla_choques.configure(yscrollcommand=scroll.set)
        self.tabla_choques.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.notebook.add(marco, text="Choques de horario")

    def _pestaña_resumen(self) -> None:
        marco = ttk.Frame(self.notebook, padding=12)
        self.texto_resumen = tk.Text(marco, wrap="word", state="disabled", height=30)
        self.texto_resumen.pack(fill="both", expand=True)
        self.notebook.add(marco, text="Resumen")



    def cargar_archivo(self) -> None:
        ruta = filedialog.askopenfilename(
            title="Seleccionar archivo .hor",
            filetypes=[("Archivos HorarioScript", "*.hor"), ("Todos los archivos", "*.*")],
        )
        if not ruta:
            return
        try:
            with open(ruta, "r", encoding="utf-8") as archivo:
                contenido = archivo.read()
        except OSError as error:
            messagebox.showerror("Error al abrir archivo", str(error))
            return

        self.ruta_archivo_actual = ruta
        self.area_texto.delete("1.0", "end")
        self.area_texto.insert("1.0", contenido)
        self.etiqueta_archivo.configure(text=os.path.basename(ruta))
        self.barra_estado.configure(text=f"Archivo cargado: {ruta}")

    def analizar(self) -> None:
        contenido = self.area_texto.get("1.0", "end-1c")
        if not contenido.strip():
            messagebox.showwarning("Sin contenido", "Carga o escribe un archivo .hor antes de analizar.")
            return

        inicio = time.perf_counter()
        analizador = AnalizadorLexico(contenido)
        self.tokens = analizador.analizar()
        self.errores = analizador.gestor_errores.errores

        interprete = InterpreteHorario(self.tokens)
        self.modelo = interprete.interpretar()
        self.choques = detectar_choques(self.modelo.clases)
        self.tiempo_analisis_ms = (time.perf_counter() - inicio) * 1000

        self._refrescar_tabla_tokens()
        self._refrescar_tabla_errores()
        self._refrescar_tabla_choques()
        self._refrescar_resumen()

        self.barra_estado.configure(
            text=(
                f"Analisis completo: {len(self.tokens)} tokens, "
                f"{len(self.errores)} errores, {len(self.choques)} choques "
                f"({self.tiempo_analisis_ms:.2f} ms)."
            )
        )

    def _refrescar_tabla_tokens(self) -> None:
        self.tabla_tokens.delete(*self.tabla_tokens.get_children())
        for token in self.tokens:
            self.tabla_tokens.insert("", "end", values=token.como_fila())

    def _refrescar_tabla_errores(self) -> None:
        self.tabla_errores.delete(*self.tabla_errores.get_children())
        for error in self.errores:
            self.tabla_errores.insert("", "end", values=error.como_fila())

    def _refrescar_tabla_choques(self) -> None:
        self.tabla_choques.delete(*self.tabla_choques.get_children())
        for choque in self.choques:
            descripcion_a = f"{choque.clase_a.curso_codigo} ({choque.clase_a.dia} {choque.clase_a.inicio}-{choque.clase_a.fin})"
            descripcion_b = f"{choque.clase_b.curso_codigo} ({choque.clase_b.dia} {choque.clase_b.inicio}-{choque.clase_b.fin})"
            self.tabla_choques.insert("", "end", values=(choque.tipo, choque.recurso, descripcion_a, descripcion_b))

    def _refrescar_resumen(self) -> None:
        conteo_tokens: dict = {}
        for token in self.tokens:
            conteo_tokens[token.tipo] = conteo_tokens.get(token.tipo, 0) + 1

        conteo_errores: dict = {}
        for error in self.errores:
            conteo_errores[error.tipo] = conteo_errores.get(error.tipo, 0) + 1

        lineas = []
        lineas.append(f"Archivo analizado: {self.ruta_archivo_actual or '(sin guardar)'}")
        lineas.append(f"Tiempo de analisis: {self.tiempo_analisis_ms:.2f} ms")
        lineas.append("")
        lineas.append(f"Total de tokens: {len(self.tokens)}")
        for tipo in TipoToken:
            cantidad = conteo_tokens.get(tipo, 0)
            if cantidad:
                lineas.append(f"  - {tipo.name}: {cantidad}")
        lineas.append("")
        lineas.append(f"Total de errores lexicos: {len(self.errores)}")
        for tipo, cantidad in conteo_errores.items():
            lineas.append(f"  - {tipo.name}: {cantidad}")
        lineas.append("")
        if self.modelo is not None:
            lineas.append(f"Cursos: {len(self.modelo.cursos)}")
            lineas.append(f"Catedraticos: {len(self.modelo.catedraticos)}")
            lineas.append(f"Aulas: {len(self.modelo.aulas)}")
            lineas.append(f"Clases: {len(self.modelo.clases)}")
        lineas.append(f"Choques de horario detectados: {len(self.choques)}")

        self.texto_resumen.configure(state="normal")
        self.texto_resumen.delete("1.0", "end")
        self.texto_resumen.insert("1.0", "\n".join(lineas))
        self.texto_resumen.configure(state="disabled")

    def _carpeta_salida(self) -> str:
        base = os.path.dirname(self.ruta_archivo_actual) if self.ruta_archivo_actual else os.getcwd()
        return os.path.join(base, "reportes_horarioscript")

    def generar_reportes(self) -> None:
        if self.modelo is None:
            messagebox.showwarning("Analisis requerido", "Ejecuta el analisis antes de generar los reportes.")
            return
        carpeta = self._carpeta_salida()
        generador = GeneradorReportes(self.modelo, self.choques)
        rutas = generador.generar_todos(carpeta, self.errores)
        mensaje = "\n".join(rutas.values())
        respuesta = messagebox.askyesno(
            "Reportes generados",
            f"Se generaron los siguientes reportes:\n\n{mensaje}\n\n¿Deseas abrir el reporte de horario semanal?",
        )
        if respuesta:
            webbrowser.open(f"file://{os.path.abspath(rutas['horario_semanal'])}")
        self.barra_estado.configure(text=f"Reportes generados en: {carpeta}")

    def generar_dot(self) -> None:
        if self.modelo is None:
            messagebox.showwarning("Analisis requerido", "Ejecuta el analisis antes de generar el diagrama DOT.")
            return
        carpeta = self._carpeta_salida()
        os.makedirs(carpeta, exist_ok=True)
        ruta = os.path.join(carpeta, "jerarquia_horario.dot")
        guardar_dot(self.modelo, ruta)
        messagebox.showinfo(
            "Diagrama DOT generado",
            f"Se genero el archivo:\n{ruta}\n\n"
            "Puedes renderizarlo con Graphviz, por ejemplo:\n"
            "dot -Tpng jerarquia_horario.dot -o jerarquia_horario.png",
        )
        self.barra_estado.configure(text=f"Diagrama DOT generado en: {ruta}")


def iniciar_aplicacion() -> None:
    app = AplicacionHorarioScript()
    app.mainloop()