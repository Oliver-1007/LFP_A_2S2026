

from __future__ import annotations

from typing import List, Optional

from .modelos import Aula, Catedratico, Clase, Curso, ModeloHorario
from .tokens import Token, TipoToken



class InterpreteHorario:
    def __init__(self, tokens: List[Token]) -> None:
        # Los comentarios no aportan estructura; se descartan aqui.
        self.tokens = [t for t in tokens if t.tipo != TipoToken.COMENTARIO_LINEA]
        self.pos = 0
        self.modelo = ModeloHorario()

    # utilidades 

    def _actual(self) -> Optional[Token]:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def _avanzar(self) -> Optional[Token]:
        token = self._actual()
        if token is not None:
            self.pos += 1
        return token

    def _es_simbolo(self, simbolo: str) -> bool:
        t = self._actual()
        return t is not None and t.tipo == TipoToken.SIMBOLO and t.lexema == simbolo

    def _es_lexema(self, lexema: str) -> bool:
        t = self._actual()
        return t is not None and t.lexema == lexema

    def _consumir_simbolo(self, simbolo: str) -> bool:
        if self._es_simbolo(simbolo):
            self._avanzar()
            return True
        return False

    def _consumir_lexema(self, lexema: str) -> bool:
        if self._es_lexema(lexema):
            self._avanzar()
            return True
        return False

    @staticmethod
    def _quitar_comillas(lexema: str) -> str:
        if len(lexema) >= 2 and lexema[0] == '"' and lexema[-1] == '"':
            return lexema[1:-1]
        return lexema

    @staticmethod
    def _a_entero(valor: str) -> int:
        return int(valor) if valor.isdigit() else 0

    def _leer_atributos(self) -> dict:
        #Lee pares clave: valor separados por comas hasta encontrar ']'
        atributos: dict = {}
        while self._actual() is not None and not self._es_simbolo("]"):
            clave_tok = self._avanzar()
            if clave_tok is None:
                break
            self._consumir_simbolo(":")
            valor_tok = self._avanzar()
            if valor_tok is None:
                break
            # CADENA y CODIGO llegan entre comillas 
            # se despojan aqui para trabajar con el
            # valor semantico limpio en el resto del sistema.
            valor = self._quitar_comillas(valor_tok.lexema)
            atributos[clave_tok.lexema] = valor
            self._consumir_simbolo(",")
        return atributos

    # gramatica

    def interpretar(self) -> ModeloHorario:
        if not self._consumir_lexema("HORARIO"):
            return self.modelo
        self._consumir_simbolo("{")

        while self._actual() is not None and not self._es_simbolo("}"):
            actual = self._actual()
            if actual.lexema == "CURSOS":
                self._interpretar_seccion("CURSOS", self._interpretar_curso)
            elif actual.lexema == "CATEDRATICOS":
                self._interpretar_seccion("CATEDRATICOS", self._interpretar_catedratico)
            elif actual.lexema == "AULAS":
                self._interpretar_seccion("AULAS", self._interpretar_aula)
            elif actual.lexema == "CLASES":
                self._interpretar_seccion("CLASES", self._interpretar_clase)
            else:
                self._avanzar()  # token inesperado: se ignora y se continua

        self._consumir_simbolo("}")
        self._consumir_simbolo(";")
        return self.modelo

    def _interpretar_seccion(self, nombre_bloque: str, interpretar_elemento) -> None:
        self._consumir_lexema(nombre_bloque)
        self._consumir_simbolo("{")
        while self._actual() is not None and not self._es_simbolo("}"):
            interpretar_elemento()
        self._consumir_simbolo("}")
        self._consumir_simbolo(";")

    def _interpretar_curso(self) -> None:
        if not self._consumir_lexema("curso"):
            self._avanzar()
            return
        self._consumir_simbolo(":")
        nombre_tok = self._avanzar()
        nombre = self._quitar_comillas(nombre_tok.lexema) if nombre_tok else ""
        self._consumir_simbolo("[")
        atributos = self._leer_atributos()
        self._consumir_simbolo("]")
        self._consumir_simbolo(",")
        self.modelo.cursos.append(Curso(
            codigo=atributos.get("codigo", ""),
            nombre=nombre,
            creditos=self._a_entero(atributos.get("creditos", "")),
        ))

    def _interpretar_catedratico(self) -> None:
        if not self._consumir_lexema("catedratico"):
            self._avanzar()
            return
        self._consumir_simbolo(":")
        nombre_tok = self._avanzar()
        nombre = self._quitar_comillas(nombre_tok.lexema) if nombre_tok else ""
        self._consumir_simbolo("[")
        atributos = self._leer_atributos()
        self._consumir_simbolo("]")
        self._consumir_simbolo(",")
        self.modelo.catedraticos.append(Catedratico(
            codigo=atributos.get("codigo", ""),
            nombre=nombre,
            categoria=atributos.get("categoria", ""),
        ))

    def _interpretar_aula(self) -> None:
        if not self._consumir_lexema("aula"):
            self._avanzar()
            return
        self._consumir_simbolo(":")
        codigo_tok = self._avanzar()
        codigo = self._quitar_comillas(codigo_tok.lexema) if codigo_tok else ""
        self._consumir_simbolo("[")
        atributos = self._leer_atributos()
        self._consumir_simbolo("]")
        self._consumir_simbolo(",")
        self.modelo.aulas.append(Aula(
            codigo=codigo,
            capacidad=self._a_entero(atributos.get("capacidad", "")),
            edificio=atributos.get("edificio", ""),
        ))

    def _interpretar_clase(self) -> None:
        if not self._consumir_lexema("clase"):
            self._avanzar()
            return
        self._consumir_simbolo(":")
        curso_tok = self._avanzar()
        curso_codigo = self._quitar_comillas(curso_tok.lexema) if curso_tok else ""
        self._consumir_lexema("con")
        cat_tok = self._avanzar()
        catedratico_codigo = self._quitar_comillas(cat_tok.lexema) if cat_tok else ""
        self._consumir_lexema("en")
        aula_tok = self._avanzar()
        aula_codigo = self._quitar_comillas(aula_tok.lexema) if aula_tok else ""
        self._consumir_simbolo("[")
        atributos = self._leer_atributos()
        self._consumir_simbolo("]")
        self._consumir_simbolo(",")
        self.modelo.clases.append(Clase(
            curso_codigo=curso_codigo,
            catedratico_codigo=catedratico_codigo,
            aula_codigo=aula_codigo,
            dia=atributos.get("dia", ""),
            inicio=atributos.get("inicio", ""),
            fin=atributos.get("fin", ""),
            seccion=atributos.get("seccion", ""),
        ))
