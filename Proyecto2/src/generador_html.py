
from tokens import TipoToken as T


## Escapa los caracteres especiales de HTML carácter por carácter
def escapar_html(texto):
    tabla = {"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"}
    return "".join(tabla.get(c, c) for c in texto)

## Genera los reportes 1, 2 y 3 a partir del árbol de derivación
class GeneradorHTML:

    ARCHIVO_R1 = "reporte1_documento.html"
    ARCHIVO_R2 = "reporte2_estadisticas.html"
    ARCHIVO_R3 = "reporte3_indice.html"

    def __init__(self, arbol, nombre_archivo="documento.md"):
        self.arbol = arbol
        self.nombre_archivo = nombre_archivo
        self.encabezados = []
        self.estadisticas = {
            "palabras": 0, "parrafos": 0,
            "encabezados": 0, "por_nivel": {n: 0 for n in range(1, 7)},
            "listas": 0, "items": 0, "prof_listas": 0,
            "citas": 0, "lineas_cita": 0, "prof_citas": 0,
            "bloques_codigo": 0,
            "negritas": 0, "cursivas": 0, "codigos_inline": 0, "reglas": 0,
        }
        self._recolectar()


    # Utilidades sobre el árbol
    def _bloques(self):
        for elemento in self.arbol.elementos_cadena():
            if elemento.tipo == "<bloque>":
                yield elemento.hijos[0]

    ## Texto visible de un <en_linea> (sin delimitadores de énfasis)
    def _texto_plano(self, en_linea):
        partes = []
        for elemento in en_linea.elementos_cadena():
            hijo = elemento.hijos[0]
            if hijo.tipo in ("<negrita>", "<cursiva>"):
                partes.append(self._texto_plano(hijo.buscar("<en_linea>")))
            elif hijo.tipo == "<codigo_inline>":
                partes.append(hijo.atributos["contenido"])
            elif hijo.tipo == T.SALTO_LINEA:
                partes.append(" ")
            else:
                partes.append(hijo.token.lexema)
        return "".join(partes)

    ## Cuenta tramos de negrita, cursiva y código en línea (incluye anidados)
    def _contar_enfasis(self, en_linea):
        for elemento in en_linea.elementos_cadena():
            hijo = elemento.hijos[0]
            if hijo.tipo == "<negrita>":
                self.estadisticas["negritas"] += 1
                self._contar_enfasis(hijo.buscar("<en_linea>"))
            elif hijo.tipo == "<cursiva>":
                self.estadisticas["cursivas"] += 1
                self._contar_enfasis(hijo.buscar("<en_linea>"))
            elif hijo.tipo == "<codigo_inline>":
                self.estadisticas["codigos_inline"] += 1

    def _palabras(self, en_linea):
        return len(self._texto_plano(en_linea).split())


    # Recolección de estadísticas e índice
    def _recolectar(self):
        est = self.estadisticas
        for bloque in self._bloques():
            tipo = bloque.tipo
            if tipo == "<encabezado>":
                nivel = bloque.atributos["nivel"]
                en_linea = bloque.buscar("<en_linea>")
                est["encabezados"] += 1
                est["por_nivel"][nivel] += 1
                est["palabras"] += self._palabras(en_linea)
                self._contar_enfasis(en_linea)
                identificador = "seccion-%d" % (len(self.encabezados) + 1)
                self.encabezados.append((nivel, self._texto_plano(en_linea).strip(), identificador))
            elif tipo == "<parrafo>":
                en_linea = bloque.buscar("<en_linea>")
                est["parrafos"] += 1
                est["palabras"] += self._palabras(en_linea)
                self._contar_enfasis(en_linea)
            elif tipo == "<lista>":
                est["listas"] += 1
                est["prof_listas"] = max(est["prof_listas"], self._recolectar_lista(bloque, 1))
            elif tipo == "<cita>":
                est["citas"] += 1
                self._recolectar_cita(bloque)
            elif tipo == "<bloque_codigo>":
                est["bloques_codigo"] += 1
                # La etiqueta del lenguaje se considera texto del documento
                est["palabras"] += len(bloque.atributos["lenguaje"].split())
            elif tipo == "<regla_horizontal>":
                est["reglas"] += 1

    ## Cuenta ítems y devuelve la profundidad máxima de anidamiento de la lista
    def _recolectar_lista(self, lista, profundidad):
        est = self.estadisticas
        maxima = profundidad
        for item in lista.elementos_cadena():
            est["items"] += 1
            en_linea = item.buscar("<en_linea>")
            est["palabras"] += self._palabras(en_linea)
            self._contar_enfasis(en_linea)
            for sublista in item.buscar_todos("<sublista>"):
                maxima = max(maxima, self._recolectar_lista(sublista.buscar("<lista>"), profundidad + 1))
        return maxima

    def _recolectar_cita(self, cita):
        est = self.estadisticas
        est["prof_citas"] = max(est["prof_citas"], cita.atributos["nivel"])
        for elemento in cita.elementos_cadena():
            hijo = elemento.hijos[0]
            if hijo.tipo == "<linea_cita>":
                en_linea = hijo.buscar("<en_linea>")
                est["lineas_cita"] += 1
                est["palabras"] += self._palabras(en_linea)
                self._contar_enfasis(en_linea)
            else:
                self._recolectar_cita(hijo)


    # Traducción del árbol a HTML (Reporte 1)
    def traducir_cuerpo(self):
        partes = []
        contador_encabezados = 0
        for bloque in self._bloques():
            tipo = bloque.tipo
            if tipo == "<encabezado>":
                nivel = bloque.atributos["nivel"]
                identificador = self.encabezados[contador_encabezados][2]
                contador_encabezados += 1
                partes.append('<h%d id="%s">%s</h%d>' % (
                    nivel, identificador, self._html_en_linea(bloque.buscar("<en_linea>")), nivel))
            elif tipo == "<parrafo>":
                partes.append("<p>%s</p>" % self._html_en_linea(bloque.buscar("<en_linea>")))
            elif tipo == "<lista>":
                partes.append(self._html_lista(bloque))
            elif tipo == "<cita>":
                partes.append(self._html_cita(bloque))
            elif tipo == "<bloque_codigo>":
                partes.append(self._html_bloque_codigo(bloque))
            elif tipo == "<regla_horizontal>":
                partes.append("<hr>")
        return "\n".join(partes)

    def _html_en_linea(self, en_linea):
        partes = []
        for elemento in en_linea.elementos_cadena():
            hijo = elemento.hijos[0]
            if hijo.tipo == "<negrita>":
                partes.append("<strong>%s</strong>" % self._html_en_linea(hijo.buscar("<en_linea>")))
            elif hijo.tipo == "<cursiva>":
                partes.append("<em>%s</em>" % self._html_en_linea(hijo.buscar("<en_linea>")))
            elif hijo.tipo == "<codigo_inline>":
                partes.append("<code>%s</code>" % escapar_html(hijo.atributos["contenido"]))
            elif hijo.tipo == T.SALTO_LINEA:
                partes.append("\n")
            else:
                partes.append(escapar_html(hijo.token.lexema))
        return "".join(partes)

    def _html_lista(self, lista):
        partes = ["<ul>"]
        for item in lista.elementos_cadena():
            contenido = self._html_en_linea(item.buscar("<en_linea>"))
            sublistas = "".join("\n" + self._html_lista(s.buscar("<lista>"))
                                for s in item.buscar_todos("<sublista>"))
            partes.append("<li>%s%s</li>" % (contenido, sublistas))
        partes.append("</ul>")
        return "\n".join(partes)

    def _html_cita(self, cita):
        partes = ["<blockquote>"]
        for elemento in cita.elementos_cadena():
            hijo = elemento.hijos[0]
            if hijo.tipo == "<linea_cita>":
                partes.append("<p>%s</p>" % self._html_en_linea(hijo.buscar("<en_linea>")))
            else:
                partes.append(self._html_cita(hijo))      # cita anidada
        partes.append("</blockquote>")
        return "\n".join(partes)

    def _html_bloque_codigo(self, bloque):
        contenido = escapar_html(bloque.atributos["contenido"])
        lenguaje = bloque.atributos["lenguaje"].split()
        if lenguaje:
            return '<pre><code class="language-%s">%s</code></pre>' % (escapar_html(lenguaje[0]), contenido)
        return "<pre><code>%s</code></pre>" % contenido


    # Páginas completas
    @staticmethod
    def _pagina(titulo, css, cuerpo):
        return ("<!DOCTYPE html>\n<html lang=\"es\">\n<head>\n<meta charset=\"utf-8\">\n"
                "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
                "<title>%s</title>\n<style>\n%s\n</style>\n</head>\n<body>\n%s\n</body>\n</html>\n"
                % (escapar_html(titulo), css, cuerpo))

    # Reporte 1
    def generar_reporte1(self):
        css = """
:root{--fg:#1f2328;--muted:#57606a;--borde:#d0d7de;--bg:#ffffff;--code-bg:#0d1117;--code-fg:#e6edf3;--inline:#eff1f3}
*{box-sizing:border-box}
body{font-family:-apple-system,"Segoe UI",Helvetica,Arial,sans-serif;color:var(--fg);background:var(--bg);
     max-width:760px;margin:0 auto;padding:32px 24px;line-height:1.6}
.estado{display:inline-block;font-size:12px;color:#1a7f37;background:#dafbe1;border:1px solid #aceebb;
        border-radius:999px;padding:2px 10px;margin-bottom:12px}
h1,h2,h3,h4,h5,h6{line-height:1.25;margin:1.4em 0 .6em}
h1{font-size:2em;padding-bottom:.3em;border-bottom:1px solid var(--borde)}
h2{font-size:1.5em;padding-bottom:.3em;border-bottom:1px solid var(--borde)}
h3{font-size:1.25em}h4{font-size:1em}h5{font-size:.875em}h6{font-size:.85em;color:var(--muted)}
p{margin:.8em 0}
ul{padding-left:2em;margin:.6em 0}
li{margin:.25em 0}
blockquote{margin:1em 0;padding:0 1em;color:var(--muted);border-left:.25em solid var(--borde)}
blockquote blockquote{margin:.6em 0}
pre{background:var(--code-bg);color:var(--code-fg);padding:16px;border-radius:8px;overflow-x:auto;line-height:1.45}
pre code{background:none;padding:0;color:inherit;font-size:.9em}
code{font-family:ui-monospace,SFMono-Regular,Consolas,"Liberation Mono",monospace;background:var(--inline);
     padding:.15em .4em;border-radius:6px;font-size:.9em}
hr{border:0;border-top:1px solid var(--borde);margin:1.6em 0}
"""
        cuerpo = ('<span class="estado">✓ Análisis completado sin errores</span>\n%s'
                  % self.traducir_cuerpo())
        return self._pagina("Reporte 1 - Documento HTML", css, cuerpo)

    # Reporte 2
    def generar_reporte2(self):
        e = self.estadisticas
        css = """
:root{--fg:#1f2328;--muted:#57606a;--borde:#d0d7de;--azul:#2b6cb0;--pista:#e9ecef}
*{box-sizing:border-box}
body{font-family:-apple-system,"Segoe UI",Helvetica,Arial,sans-serif;color:var(--fg);max-width:780px;
     margin:0 auto;padding:28px 24px}
h1{margin:0 0 4px;font-size:1.7em}
.sub{color:var(--muted);margin:0 0 20px}
h2{font-size:1.1em;margin:28px 0 12px;padding-bottom:6px;border-bottom:1px solid var(--borde)}
.rejilla{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px}
.tarjeta{border:1px solid var(--borde);border-radius:10px;padding:14px 16px;background:#f6f8fa}
.tarjeta .num{font-size:2em;font-weight:700;color:var(--azul);line-height:1.1}
.tarjeta .eti{color:var(--muted);font-size:.9em}
.fila{display:grid;grid-template-columns:32px 1fr 28px;align-items:center;gap:10px;margin:8px 0}
.fila .eti{font-weight:600}
.pista{background:var(--pista);border-radius:4px;height:14px;overflow:hidden}
.relleno{background:var(--azul);height:100%}
.fila .cant{text-align:right;color:var(--muted)}
.caja{display:flex;justify-content:space-between;align-items:center;border:1px solid var(--borde);
      border-radius:10px;padding:12px 16px}
.caja .valor{font-weight:700;font-size:1.4em}
.morado{color:#7c3aed}.ambar{color:#b7791f}
code{font-family:ui-monospace,Consolas,monospace;background:#eff1f3;padding:.1em .35em;border-radius:5px}
"""
        def tarjeta(numero, etiqueta):
            return '<div class="tarjeta"><div class="num">%d</div><div class="eti">%s</div></div>' % (
                numero, etiqueta)

        maximo = max(e["por_nivel"].values()) or 1
        barras = []
        for nivel in range(1, 7):
            cantidad = e["por_nivel"][nivel]
            ancho = int(round(100.0 * cantidad / maximo)) if cantidad else 0
            barras.append('<div class="fila"><span class="eti">H%d</span>'
                          '<div class="pista"><div class="relleno" style="width:%d%%"></div></div>'
                          '<span class="cant">%d</span></div>' % (nivel, ancho, cantidad))

        def caja(etiqueta, valor, clase=""):
            return '<div class="caja"><span>%s</span><span class="valor %s">%s</span></div>' % (
                etiqueta, clase, valor)

        def niveles(n):
            return "%d nivel%s" % (n, "" if n == 1 else "es")

        cuerpo = "\n".join([
            "<h1>Estadísticas del Documento</h1>",
            '<p class="sub">%s</p>' % escapar_html(self.nombre_archivo),
            '<div class="rejilla">',
            tarjeta(e["palabras"], "Palabras totales"),
            tarjeta(e["parrafos"], "Párrafos"),
            tarjeta(e["encabezados"], "Encabezados"),
            tarjeta(e["listas"], "Listas"),
            tarjeta(e["items"], "Ítems de lista"),
            tarjeta(e["citas"], "Citas"),
            tarjeta(e["lineas_cita"], "Líneas de cita"),
            tarjeta(e["bloques_codigo"], "Bloques de código"),
            "</div>",
            "<h2>Encabezados por nivel</h2>",
            "\n".join(barras),
            "<h2>Profundidad máxima de anidamiento</h2>",
            '<div class="rejilla">',
            caja("Listas", niveles(e["prof_listas"]), "morado"),
            caja("Citas", niveles(e["prof_citas"]), "ambar"),
            "</div>",
            "<h2>Elementos en línea</h2>",
            '<div class="rejilla">',
            caja("Negrita (<code>**texto**</code>)", e["negritas"]),
            caja("Cursiva (<code>*texto*</code>)", e["cursivas"]),
            caja("Código en línea (<code>`texto`</code>)", e["codigos_inline"]),
            caja("Regla horizontal (<code>---</code>)", e["reglas"]),
            "</div>",
        ])
        return self._pagina("Reporte 2 - Estadísticas", css, cuerpo)

    # Reporte 3
    def generar_reporte3(self):
        css = """
:root{--fg:#1f2328;--muted:#57606a;--borde:#d0d7de}
*{box-sizing:border-box}
body{font-family:-apple-system,"Segoe UI",Helvetica,Arial,sans-serif;color:var(--fg);max-width:780px;
     margin:0 auto;padding:28px 24px}
h1{margin:0 0 4px;font-size:1.7em}
.sub{color:var(--muted);margin:0 0 20px}
.indice{border:1px solid var(--borde);border-radius:12px;background:#f6f8fa;padding:6px 18px}
.entrada{display:flex;align-items:center;gap:10px;padding:10px 0;border-bottom:1px solid var(--borde)}
.entrada:last-child{border-bottom:0}
.insignia{font-size:.7em;font-weight:700;color:#fff;border-radius:4px;padding:2px 6px}
.entrada a{color:#1f6fb2;text-decoration:none}
.entrada a:hover{text-decoration:underline}
.n1 .insignia{background:#1f5f99}.n2 .insignia{background:#4a90d0}.n3 .insignia{background:#6aa8dc}
.n4 .insignia{background:#8bbce4}.n5 .insignia{background:#a3c9ea}.n6 .insignia{background:#b9d6ef}
.n1 a{font-weight:700;font-size:1.05em}
.nota{color:var(--muted);font-style:italic;font-size:.9em;margin-top:14px}
.vacio{border:1px dashed var(--borde);border-radius:12px;padding:20px;color:var(--muted);background:#f6f8fa}
"""
        cabecera = ["<h1>Tabla de Contenido</h1>",
                    '<p class="sub">%s — generado a partir de los encabezados reconocidos</p>'
                    % escapar_html(self.nombre_archivo)]
        if not self.encabezados:
            cuerpo = "\n".join(cabecera + [
                '<div class="vacio">Este documento no contiene encabezados, por lo que no hay '
                "entradas que mostrar en la tabla de contenido.</div>"])
            return self._pagina("Reporte 3 - Tabla de contenido", css, cuerpo)

        entradas = []
        for nivel, texto, ancla in self.encabezados:
            sangria = (nivel - 1) * 22
            entradas.append(
                '<div class="entrada n%d" style="margin-left:%dpx"><span class="insignia">H%d</span>'
                '<a href="%s#%s">%s</a></div>'
                % (nivel, sangria, nivel, self.ARCHIVO_R1, ancla, escapar_html(texto)))
        cuerpo = "\n".join(cabecera + [
            '<div class="indice">', "\n".join(entradas), "</div>",
            '<p class="nota">Cada entrada enlaza a su sección correspondiente dentro del Reporte 1. '
            "Con más niveles de encabezado (###, ####, ...) el índice agregaría más entradas, "
            "indentadas según su nivel.</p>"])
        return self._pagina("Reporte 3 - Tabla de contenido", css, cuerpo)


    # Tablas de tokens y de errores
    @staticmethod
    def generar_tablas(tokens, errores, nombre_archivo="documento.md"):
        """HTML con la tabla de tokens y la tabla de errores léxicos y sintácticos."""
        css = """
body{font-family:-apple-system,"Segoe UI",Arial,sans-serif;margin:24px;color:#1f2328}
h1{font-size:1.5em}h2{margin-top:28px}
table{border-collapse:collapse;width:100%;font-size:.9em}
th,td{border:1px solid #d0d7de;padding:5px 9px;text-align:left}
th{background:#2E75B6;color:#fff}tr:nth-child(even){background:#f6f8fa}
td.mono{font-family:ui-monospace,Consolas,monospace}
"""
        filas_t = []
        numero = 0
        for t in tokens:
            if t.sintetico:
                continue
            numero += 1
            filas_t.append('<tr><td>%d</td><td class="mono">%s</td><td>%s</td><td>%d</td><td>%d</td></tr>'
                           % (numero, escapar_html(t.lexema_visible()), t.tipo, t.linea, t.columna))
        filas_e = []
        for i, err in enumerate(errores, 1):
            filas_e.append('<tr><td>%d</td><td class="mono">%s</td><td>%s</td><td>%s</td><td>%s</td>'
                           '<td>%d</td><td>%d</td></tr>'
                           % (i, escapar_html(err.lexema_visible()), err.tipo, err.fase,
                              escapar_html(err.descripcion), err.linea, err.columna))
        if not filas_e:
            filas_e.append('<tr><td colspan="7">Sin errores léxicos ni sintácticos.</td></tr>')
        cuerpo = "\n".join([
            "<h1>Análisis de %s</h1>" % escapar_html(nombre_archivo),
            "<h2>Tabla de tokens</h2>",
            "<table><tr><th>N°</th><th>Lexema</th><th>Tipo de token</th><th>Línea</th><th>Columna</th></tr>",
            "\n".join(filas_t), "</table>",
            "<h2>Tabla de errores</h2>",
            "<table><tr><th>N°</th><th>Lexema</th><th>Tipo de error</th><th>Fase</th>"
            "<th>Descripción</th><th>Línea</th><th>Columna</th></tr>",
            "\n".join(filas_e), "</table>"])
        return GeneradorHTML._pagina("Tablas de análisis", css, cuerpo)