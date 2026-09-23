
from pathlib import Path
from tempfile import TemporaryDirectory

from src.analizador_lexico import AnalizadorLexico
from src.detector_choques import detectar_choques
from src.generador_reportes import GeneradorReportes
from src.interprete import InterpreteHorario
from src.tokens import TipoError


RAIZ = Path(__file__).resolve().parents[1]


def analizar(nombre: str):
    contenido = (RAIZ / "examples" / nombre).read_text(encoding="utf-8")
    analizador = AnalizadorLexico(contenido)
    tokens = analizador.analizar()
    modelo = InterpreteHorario(tokens).interpretar()
    return analizador, modelo


def test_ejemplos_principales():
    analizador, modelo = analizar("horario_valido.hor")
    assert not analizador.gestor_errores.errores
    assert len(modelo.cursos) == 2
    assert len(modelo.catedraticos) == 2
    assert len(modelo.aulas) == 2
    assert len(modelo.clases) == 2
    assert not detectar_choques(modelo.clases)

    analizador, modelo = analizar("horario_con_choque.hor")
    assert not analizador.gestor_errores.errores
    choques = detectar_choques(modelo.clases)
    assert len(choques) == 1
    assert choques[0].tipo == "CATEDRATICO"
    assert choques[0].recurso == "DOC-001"


def test_recuperacion_acumula_errores():
    analizador, modelo = analizar("horario_con_errores.hor")
    tipos = [error.tipo for error in analizador.gestor_errores.errores]
    assert len(tipos) == 7
    assert TipoError.CADENA_SIN_CERRAR in tipos
    assert TipoError.CODIGO_MAL_FORMADO in tipos
    assert TipoError.DIA_NO_RECONOCIDO in tipos
    assert TipoError.HORA_FUERA_DE_RANGO in tipos
    assert len(modelo.cursos) == 3
    assert any(
        c.codigo == "DOC-001" and c.nombre == "Otto Rodriguez"
        for c in modelo.catedraticos
    )
    assert [(a.codigo, a.edificio) for a in modelo.aulas] == [
        ("A-101", "T-3"),
        ("LAB~3", "T-5"),
    ]


def test_codigo_con_continuacion_invalida_es_un_error_completo():
    analizador = AnalizadorLexico('"ABC-12X" "ABC-12-3"')
    assert analizador.analizar() == []
    errores = analizador.gestor_errores.errores
    assert len(errores) == 2
    assert all(error.tipo == TipoError.CODIGO_MAL_FORMADO for error in errores)


def test_reportes_normales_excluyen_datos_invalidos_y_reporte_errores_los_conserva():
    analizador, modelo = analizar("horario_con_errores.hor")
    choques = detectar_choques(modelo.clases)

    with TemporaryDirectory() as carpeta:
        rutas = GeneradorReportes(modelo, choques, analizador.gestor_errores.errores).generar_todos(
            carpeta, analizador.gestor_errores.errores
        )
        horario = Path(rutas["horario_semanal"]).read_text(encoding="utf-8")
        carga = Path(rutas["carga_catedraticos"]).read_text(encoding="utf-8")
        estadistico = Path(rutas["estadistico"]).read_text(encoding="utf-8")
        reporte_errores = Path(rutas["errores"]).read_text(encoding="utf-8")

    assert "Lenguajes Formales y de Programacion" in horario
    assert "Redes @1" not in horario
    assert "Bases de Datos" not in horario
    assert "LAB~3" in estadistico
    assert "Persona Rara" not in carga
    assert reporte_errores.count("<tr>") == 8