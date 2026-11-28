"""test_ausencia.py — el anillo 3, medido por sus falsadores.

Motor declarado de la corrida:

    python3 -B -m unittest discover -s tests

QUE MIDE. Que una ruta pueda probarse **ausente** de un manifiesto con un
testigo que no recorre el manifiesto, y que esa prueba sea transferible sin
entregar el inventario.

LO QUE ESTE ARCHIVO ANADE A LA TESIS. Los anillos anteriores adjudican
presencias; una presencia se decide contra el arbol, y el arbol siempre se puede
mirar. La ausencia se decide contra el **orden**, y el orden solo prueba si el
testigo es un intervalo **adyacente**: entre dos filas cualesquiera siempre cabe
algo. P-48 mide la adyacencia, P-52 el testigo falsificado, y P-55 el mismo
testigo verificado contra 32 bytes de raiz sin la pagina.

TRES TRAMPAS QUE SE CIERRAN AQUI Y NO EN EL CODIGO DE OTROS. Una pagina vacia
responde «ausente» a todo por cuantificacion universal vacia (P-54); una pagina
con una fila redactada tiene un agujero en el orden y no acota nada (P-53); y un
nombre que existe como **directorio** no es una ruta declarada (P-56). Las tres
dan verde en un verificador ingenuo.

LA PUERTA QUE SE ABRE AQUI (P-111). El acto deja de importar el generador y
reproduce por su cuenta la lectura, el orden, el testigo y el arbol. La
equivalencia no se afirma: P-111c compara el digest y el testigo de cinco formas
del mismo manifiesto contra el modulo, P-111d corre el acto bajo `env -i` desde
un directorio ajeno, y P-111a vigila que el import no vuelva.

NO CUBIERTO (lista cerrada): la firma y el ancla —el acto no fecha—; el coste en
segundos, que se publica como medicion y no como umbral; y la corrida contra el
sello real de platino-labs, que es un acto externo por comando.
"""

from __future__ import annotations

import hashlib as _hashlib
import dataclasses as _dataclasses
import importlib.util as _importlib_util
import os as _os
import shutil as _shutil
import subprocess as _subprocess
import sys as _sys
import tempfile as _tempfile
import unittest as _unittest

_RAIZ = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
_SRC = _os.path.join(_RAIZ, "src")
if _SRC not in _sys.path:
    _sys.path.insert(0, _SRC)

from protocol.ausencia import (  # noqa: E402
    FORMATO_CANONICO,
    ORDEN_DECLARADO,
    Pagina,
    VeredictoDeAusencia,
    autenticar,
    canonizar,
    consultar,
    pagina_desde_manifiesto,
    raiz_merkle,
    testigo_merkle as fabricar_testigo_merkle,
    verificar,
    verificar_merkle,
)
from protocol.types import ContratoViolado  # noqa: E402
from protocol.ubicacion import leer_manifiesto  # noqa: E402

_ACTO = _os.path.join(_RAIZ, "examples", "verificar_ausencia.py")


def _digest(ruta: str) -> str:
    """Un digest estable por ruta: no se regenera, se deriva del nombre."""

    return _hashlib.sha256(("sello:" + ruta).encode("utf-8")).hexdigest()


def _texto(rutas) -> str:
    return "".join("%s  %s\n" % (_digest(r), r) for r in rutas)


def _pagina(rutas) -> Pagina:
    return pagina_desde_manifiesto(leer_manifiesto(_texto(rutas), "prueba"))


class TestTestigoDeIntervalo(_unittest.TestCase):
    """P-48 · la ausencia se prueba con dos filas **adyacentes**, no con dos filas."""

    def test_p48_intervalo_adyacente(self) -> None:
        pagina = _pagina(["a.md", "b.md", "d.md"])
        t = consultar(pagina, "c.md")
        self.assertIs(VeredictoDeAusencia.AUSENTE, t.estado, t)
        self.assertEqual(2, t.posicion)
        self.assertEqual("b.md", t.anterior.ruta)
        self.assertEqual("d.md", t.siguiente.ruta)
        self.assertEqual('"b.md" < c.md < "d.md"', t.intervalo())
        self.assertTrue(verificar(pagina, t))

    def test_p48b_un_intervalo_suelto_no_basta(self) -> None:
        # `a.md` < `c.md` < `d.md` tambien, y `b.md` cae dentro: la prueba es la
        # adyacencia y no la desigualdad.
        pagina = _pagina(["a.md", "b.md", "d.md"])
        t = consultar(pagina, "c.md")
        self.assertEqual("b.md", t.anterior.ruta)
        self.assertNotEqual("a.md", t.anterior.ruta)


class TestPresenciaYExtremos(_unittest.TestCase):
    """P-49 · la consulta que **es** una fila no se contesta con un intervalo."""

    def test_p49_presente_no_es_ausente(self) -> None:
        pagina = _pagina(["a.md", "b.md", "c.md"])
        t = consultar(pagina, "b.md")
        self.assertIs(VeredictoDeAusencia.PRESENTE, t.estado)
        self.assertEqual(1, t.posicion)
        self.assertTrue(verificar(pagina, t))

    def test_p50_extremos_llevan_un_vecino_y_son_prueba(self) -> None:
        pagina = _pagina(["m.md", "n.md"])
        antes = consultar(pagina, "a.md")
        self.assertIsNone(antes.anterior)
        self.assertEqual("m.md", antes.siguiente.ruta)
        self.assertTrue(verificar(pagina, antes))
        despues = consultar(pagina, "z.md")
        self.assertEqual("n.md", despues.anterior.ruta)
        self.assertIsNone(despues.siguiente)
        self.assertTrue(verificar(pagina, despues))

    def test_p50b_consulta_normalizada_y_rechazo_fuera_del_alfabeto(self) -> None:
        self.assertEqual(("a.md", True), canonizar("./a.md"))
        self.assertEqual(("a.md", False), canonizar("a.md"))
        for invalida in ("", "\u00f1.md", "a//b.md", "/abs.md"):
            with self.assertRaises(ContratoViolado, msg=invalida):
                canonizar(invalida)


class TestOrdenDeclarado(_unittest.TestCase):
    """P-51 · el orden es de la pagina y no del archivo, y el digest lo publica."""

    def test_p51_pagina_desordenada_prueba_lo_mismo(self) -> None:
        ordenada = _pagina(["a.md", "b.md", "c.md"])
        desordenada = _pagina(["c.md", "a.md", "b.md"])
        self.assertFalse(ordenada.desordenada)
        self.assertTrue(desordenada.desordenada)
        self.assertEqual(ordenada.digest, desordenada.digest)
        self.assertEqual(
            consultar(ordenada, "b1.md").intervalo(), consultar(desordenada, "b1.md").intervalo()
        )

    def test_p51b_digest_reproducible_por_comando(self) -> None:
        pagina = _pagina(["b.md", "a.md"])
        texto = "".join(FORMATO_CANONICO % (f.h.digest, f.ruta) for f in pagina.filas)
        self.assertEqual(_hashlib.sha256(texto.encode("utf-8")).hexdigest(), pagina.digest)
        self.assertEqual(pagina.digest, autenticar(pagina))
        self.assertIn("colacion C", ORDEN_DECLARADO)


class TestTestigoFalsificado(_unittest.TestCase):
    """P-52 · un testigo que viaja puede mentir; verificarlo cuesta O(1) y lo cierra."""

    def test_p52_alterar_un_vecino_rompe_la_prueba(self) -> None:
        pagina = _pagina(["a.md", "b.md", "d.md"])
        t = consultar(pagina, "c.md")
        falso = type(t)(
            consulta=t.consulta,
            estado=t.estado,
            posicion=t.posicion,
            anterior=pagina.filas[0],
            siguiente=t.siguiente,
            digest_pagina=t.digest_pagina,
        )
        self.assertFalse(verificar(pagina, falso))

    def test_p52b_mover_la_posicion_rompe_la_prueba(self) -> None:
        pagina = _pagina(["a.md", "b.md", "d.md"])
        t = consultar(pagina, "c.md")
        falso = type(t)(
            consulta=t.consulta,
            estado=t.estado,
            posicion=0,
            anterior=t.anterior,
            siguiente=t.siguiente,
            digest_pagina=t.digest_pagina,
        )
        self.assertFalse(verificar(pagina, falso))

    def test_p52c_testigo_de_otra_pagina_no_vale(self) -> None:
        pagina = _pagina(["a.md", "b.md", "d.md"])
        otra = _pagina(["a.md", "b.md", "e.md"])
        self.assertFalse(verificar(otra, consultar(pagina, "c.md")))

    def test_p52d_consulta_fuera_del_intervalo_no_vale(self) -> None:
        pagina = _pagina(["a.md", "b.md", "d.md"])
        t = consultar(pagina, "c.md")
        falso = type(t)(
            consulta="z.md",
            estado=t.estado,
            posicion=t.posicion,
            anterior=t.anterior,
            siguiente=t.siguiente,
            digest_pagina=t.digest_pagina,
        )
        self.assertFalse(verificar(pagina, falso))


class TestPaginaConHuecos(_unittest.TestCase):
    """P-53 · una pagina con una fila redactada no prueba ausencia de nada.

    El agujero esta donde el orden deberia tener una fila: `q` puede caer dentro
    y el intervalo parece limpio. El modulo no adivina: `no_medida`.
    """

    def test_p53_fila_redactada_degrada_a_no_medida(self) -> None:
        texto = _texto(["a.md", "b.md"])
        texto += "%s  <expediente>/VERIFICAR.sh\n" % _digest("oculta")
        pagina = pagina_desde_manifiesto(leer_manifiesto(texto, "prueba"))
        self.assertEqual(1, pagina.redactadas)
        for consulta in ("c.md", "a.md", "zz.md"):
            t = consultar(pagina, consulta)
            self.assertIs(VeredictoDeAusencia.NO_MEDIDA, t.estado, consulta)
            self.assertIn("redactadas", t.motivo)
            self.assertFalse(verificar(pagina, t))


class TestPaginaVacia(_unittest.TestCase):
    """P-54 · `∀ p ∈ ∅` es cierto, y por eso una pagina vacia no es un cero."""

    def test_p54_pagina_vacia_se_rechaza(self) -> None:
        with self.assertRaises(ContratoViolado):
            Pagina(filas=(), digest=_hashlib.sha256(b"").hexdigest())

    def test_p54b_el_lector_ya_rechaza_el_manifiesto_vacio(self) -> None:
        # La misma ley, una capa antes: si el lector no rechazara el vacio, la
        # pagina lo heredaria y el acto responderia «ausente» a todo.
        with self.assertRaises(ContratoViolado):
            leer_manifiesto("", "vacio")


class TestMerkle(_unittest.TestCase):
    """P-55 · el testigo transferible se verifica sin la pagina, contra la raiz."""

    def _pagina_grande(self) -> Pagina:
        return _pagina(["r%02d.md" % i for i in range(9)])

    def test_p55_testigo_verifica_contra_la_raiz(self) -> None:
        pagina = self._pagina_grande()
        t = fabricar_testigo_merkle(pagina, "r04c.md")
        self.assertIs(VeredictoDeAusencia.AUSENTE, t.estado)
        self.assertEqual(9, t.tamano)
        self.assertTrue(verificar_merkle(t))
        self.assertEqual(raiz_merkle(pagina), t.raiz)
        # el camino es logaritmico: 9 hojas no pueden costar 9 digests
        self.assertLessEqual(len(t.camino_anterior), 4)
        self.assertLessEqual(len(t.camino_siguiente), 4)

    def test_p55b_hoja_alterada_no_llega_a_la_raiz(self) -> None:
        pagina = self._pagina_grande()
        t = fabricar_testigo_merkle(pagina, "r04c.md")
        ruta, _ = t.hoja_siguiente
        falso = type(t)(
            consulta=t.consulta,
            estado=t.estado,
            posicion=t.posicion,
            raiz=t.raiz,
            tamano=t.tamano,
            hoja_anterior=t.hoja_anterior,
            camino_anterior=t.camino_anterior,
            hoja_siguiente=(ruta, _digest("otra-cosa")),
            camino_siguiente=t.camino_siguiente,
        )
        self.assertFalse(verificar_merkle(falso))

    def test_p55c_raiz_ajena_y_presencia_no_pasan(self) -> None:
        pagina = self._pagina_grande()
        t = fabricar_testigo_merkle(pagina, "r04c.md")
        otra = _pagina(["r%02d.md" % i for i in range(8)] + ["s99.md"])
        ajena = type(t)(
            consulta=t.consulta,
            estado=t.estado,
            posicion=t.posicion,
            raiz=raiz_merkle(otra),
            tamano=t.tamano,
            hoja_anterior=t.hoja_anterior,
            camino_anterior=t.camino_anterior,
            hoja_siguiente=t.hoja_siguiente,
            camino_siguiente=t.camino_siguiente,
        )
        self.assertFalse(verificar_merkle(ajena))
        presente = fabricar_testigo_merkle(pagina, "r03.md")
        self.assertIs(VeredictoDeAusencia.PRESENTE, presente.estado)
        self.assertFalse(verificar_merkle(presente))

    def test_p55d_el_compromiso_ata_la_secuencia_no_el_conjunto(self) -> None:
        # Dos paginas con las mismas filas son el mismo conjunto y una sola
        # secuencia: la raiz coincide, y por eso la adyacencia se puede probar
        # contra 32 bytes.
        a = _pagina(["a.md", "b.md", "c.md"])
        b = _pagina(["c.md", "b.md", "a.md"])
        self.assertEqual(a.digest, b.digest)
        self.assertEqual(raiz_merkle(a), raiz_merkle(b))
        self.assertTrue(verificar_merkle(fabricar_testigo_merkle(a, "b1.md")))


class _Acto(_unittest.TestCase):
    """Base: un arbol temporal y el acto por comando, como lo corre un cliente."""

    def setUp(self) -> None:
        self.dir = _tempfile.mkdtemp(prefix="ausencia-")
        self.addCleanup(_shutil.rmtree, self.dir, True)
        for nombre in ("a.md", "b.md", "d.md"):
            with open(_os.path.join(self.dir, nombre), "wb") as flujo:
                flujo.write(nombre.encode("utf-8"))
        _os.mkdir(_os.path.join(self.dir, "vendor"))
        with open(_os.path.join(self.dir, "vendor", "copia.md"), "wb") as flujo:
            flujo.write(b"a.md")
        self.manifiesto = _os.path.join(self.dir, "SHA256SUMS")
        with open(self.manifiesto, "w", encoding="utf-8") as flujo:
            flujo.write(_texto(["a.md", "b.md", "d.md"]))

    def _correr(self, consulta: str, extra=()) -> tuple:
        corrida = _subprocess.run(
            [
                _sys.executable,
                "-B",
                _ACTO,
                "--manifiesto",
                self.manifiesto,
                "--raiz",
                self.dir,
                "--ausente",
                consulta,
            ]
            + list(extra),
            cwd=_RAIZ,
            stdout=_subprocess.PIPE,
            stderr=_subprocess.STDOUT,
            check=False,
        )
        return corrida.returncode, corrida.stdout.decode("utf-8", "replace")

    def _linea(self, crudo: str, prefijo: str) -> str:
        for linea in crudo.splitlines():
            if linea.startswith(prefijo):
                return linea
        self.fail("el acto no publica %r" % prefijo)


class TestActoComposicion(_Acto):
    """P-56 · la pagina declara rutas; el arbol puede tener un **directorio**."""

    def test_p56_directorio_no_es_ausencia_probada(self) -> None:
        codigo, crudo = self._correr("vendor")
        self.assertEqual(3, codigo, crudo)
        # Dos capas con dos respuestas y las dos publicadas: la pagina **si**
        # prueba que `vendor` no es una fila; el arbol refuta la conclusion.
        self.assertIn("ausente", self._linea(crudo, "ausencia |"))
        self.assertIn("directorio", self._linea(crudo, "arbol-ausencia |"))
        self.assertIn("-> no_medida", crudo)

    def test_p56b_lo_que_el_manifiesto_no_cubre_sale_presente(self) -> None:
        # `vendor/copia.md` existe en el arbol y no esta declarado: la pagina
        # prueba su ausencia y el arbol la refuta. Es la mitad vendible.
        codigo, crudo = self._correr("vendor/copia.md")
        self.assertEqual(1, codigo, crudo)
        self.assertIn("presente", self._linea(crudo, "arbol-ausencia |"))

    def test_p56c_ausencia_probada_sale_en_cero(self) -> None:
        codigo, crudo = self._correr("c.md")
        self.assertEqual(0, codigo, crudo)
        self.assertIn('"b.md" < c.md < "d.md"', crudo)
        self.assertIn("arbol-ausencia | ausente", crudo)
        self.assertIn(ORDEN_DECLARADO, crudo)


class TestActoRegimenDeCaso(_Acto):
    """P-57 · donde el volumen pliega mayusculas, dos filas son un archivo."""

    def test_p57_el_acto_publica_el_regimen_del_volumen(self) -> None:
        codigo, crudo = self._correr("b1.md")
        linea = self._linea(crudo, "caso |")
        self.assertEqual(0, codigo, crudo)
        # El regimen se mide, no se supone: se exige que el acto nombre uno de
        # los dos, y que la respuesta sea coherente con el que nombre.
        codigo2, crudo2 = self._correr("B.MD")
        if "colapsa-el-caso" in linea:
            # La pagina prueba `B.MD` ausente porque el orden distingue cajas; el
            # volumen no, y el acto publica el choque en vez de elegir.
            self.assertIn("caso-choque | b.md", crudo2)
            self.assertNotIn("-> ausente", crudo2)
            self.assertNotEqual(0, codigo2, crudo2)
        else:
            self.assertIn("distingue-el-caso", linea)
            self.assertNotIn("caso-choque", crudo2)
            self.assertEqual(0, codigo2, crudo2)


class TestActoEntrada(_Acto):
    """P-58 · entrada invalida es RC 2 y no un veredicto (ley 22)."""

    def test_p58_manifiesto_ilegible(self) -> None:
        corrida = _subprocess.run(
            [
                _sys.executable,
                "-B",
                _ACTO,
                "--manifiesto",
                _os.path.join(self.dir, "no-existe"),
                "--ausente",
                "a.md",
            ],
            cwd=_RAIZ,
            stdout=_subprocess.PIPE,
            stderr=_subprocess.STDOUT,
            check=False,
        )
        crudo = corrida.stdout.decode("utf-8", "replace")
        self.assertEqual(2, corrida.returncode, crudo)
        self.assertIn("ENTRADA INVALIDA", crudo)
        self.assertNotIn("Traceback", crudo)

    def test_p58b_consulta_fuera_del_alfabeto(self) -> None:
        codigo, crudo = self._correr("\u00f1.md")
        self.assertEqual(2, codigo, crudo)
        self.assertIn("ENTRADA INVALIDA", crudo)

    def test_p58c_merkle_verificado_en_el_recibo(self) -> None:
        codigo, crudo = self._correr("c.md", ("--merkle",))
        self.assertEqual(0, codigo, crudo)
        self.assertIn("merkle-verificado | si", crudo)
        self.assertIn("merkle | raiz ", crudo)


class TestUniversoDeLaAusencia(_Acto):
    """P-59 · la ausencia sobre lo que el universo no indexa no se puede probar.

    Es la ley de proyeccion aplicada al anverso: el acto de sello resuelve `auto`
    a git porque busca artefactos declarados, y lo declarado esta versionado. La
    ausencia pregunta por lo no declarado, y esa mitad no se versiona nunca.
    """

    def test_p59_git_no_prueba_ausencia_de_lo_no_versionado(self) -> None:
        _subprocess.run(["git", "init", "-q", self.dir], check=False, stdout=_subprocess.DEVNULL)
        _subprocess.run(
            ["git", "-C", self.dir, "add", "a.md", "b.md", "d.md"],
            check=False,
            stdout=_subprocess.DEVNULL,
            stderr=_subprocess.DEVNULL,
        )
        codigo, crudo = self._correr("vendor/copia.md", ("--universo", "git"))
        self.assertEqual(3, codigo, crudo)
        self.assertIn("no_medida", self._linea(crudo, "arbol-ausencia |"))
        # y el universo por omision si puede: el archivo esta en disco
        codigo2, crudo2 = self._correr("vendor/copia.md")
        self.assertEqual(1, codigo2, crudo2)


class TestFalsadorReservado(_Acto):
    """P-60 · `git ls-files` que falla no es «la ruta no esta versionada»."""

    def test_p60_git_que_falla_degrada_a_no_medida(self) -> None:
        # P-48 estaba reservado a esta laguna antes de que el anillo 3 ocupara la
        # numeracion; queda como P-60 y cierra la lista de «no cubierto» de
        # UBICACION.md §5.
        directorio = _os.path.join(self.dir, "no-git")
        _os.makedirs(directorio, exist_ok=True)
        with open(_os.path.join(directorio, "a.md"), "wb") as flujo:
            flujo.write(b"a.md")
        corrida = _subprocess.run(
            [
                _sys.executable,
                "-B",
                _ACTO,
                "--manifiesto",
                self.manifiesto,
                "--raiz",
                directorio,
                "--universo",
                "git",
                "--ausente",
                "c.md",
            ],
            cwd=_RAIZ,
            stdout=_subprocess.PIPE,
            stderr=_subprocess.STDOUT,
            check=False,
        )
        crudo = corrida.stdout.decode("utf-8", "replace")
        self.assertEqual(3, corrida.returncode, crudo)
        self.assertIn("no_medida", self._linea(crudo, "arbol-ausencia |"))
        self.assertNotIn("ausencia | el universo lo indexa", crudo)


_ACTO_MODULO = None


def _acto_como_modulo():
    """Carga el acto como modulo suelto, sin anadir nada a `sys.path`."""

    global _ACTO_MODULO
    if _ACTO_MODULO is None:
        especificacion = _importlib_util.spec_from_file_location("acto_de_ausencia", _ACTO)
        modulo = _importlib_util.module_from_spec(especificacion)
        _sys.modules["acto_de_ausencia"] = modulo
        especificacion.loader.exec_module(modulo)
        _ACTO_MODULO = modulo
    return _ACTO_MODULO


def _acto_en_frio(manifiesto: str, consulta: str, extra=(), cwd=None):
    """`env -i` desde un directorio ajeno al arbol: sin PYTHONPATH, sin maquina."""

    corrida = _subprocess.run(
        [_sys.executable, "-B", _ACTO, "--manifiesto", manifiesto, "--ausente", consulta] + list(extra),
        cwd=cwd or _tempfile.mkdtemp(prefix="frio-"),
        env={},
        stdout=_subprocess.PIPE,
        stderr=_subprocess.STDOUT,
        check=False,
    )
    return corrida.returncode, corrida.stdout.decode("utf-8", "replace")


class TestTerceraPuertaSinGenerador(_unittest.TestCase):
    """P-111 · la ausencia se verifica **sin** importar el generador (§7, 3/4).

    Lo que se mide aqui no es que el acto haga lo mismo —eso ya lo dicen P-56 a
    P-60, que corren bajo los dos—, sino que lo haga **por su cuenta**: cero
    imports del generador, mismas tablas declaradas, mismo digest de pagina, y la
    corrida bajo `env -i` en un directorio ajeno al arbol.
    """

    def test_p111a_cero_imports_del_generador(self) -> None:
        with open(_ACTO, "r", encoding="utf-8") as flujo:
            fuente = flujo.read()
        for prohibido in ("import protocol", "from protocol"):
            self.assertNotIn(prohibido, fuente)
        # Y no llega al arbol por la puerta de atras: sin `sys.path` no hay `src/`.
        self.assertNotIn("sys.path", fuente)

    def test_p111b_las_tablas_declaradas_son_las_del_contrato(self) -> None:
        acto = _acto_como_modulo()
        self.assertEqual(ORDEN_DECLARADO, acto.ORDEN_DECLARADO)
        self.assertEqual(FORMATO_CANONICO, acto.FORMATO_CANONICO)
        self.assertEqual("ausente", acto.VeredictoDeAusencia.AUSENTE.value)
        self.assertEqual("presente", acto.VeredictoDeAusencia.PRESENTE.value)
        self.assertEqual("no_medida", acto.VeredictoDeAusencia.NO_MEDIDA.value)

    def test_p111c_misma_pagina_y_mismo_testigo_sobre_el_mismo_texto(self) -> None:
        acto = _acto_como_modulo()
        textos = (
            _texto(["a.md", "b.md", "d.md"]),
            _texto(["d.md", "a.md", "b.md"]),
            "".join("%s  ./%s\n" % (_digest(r), r) for r in ("a.md", "b.md", "d.md")),
            "".join("%s *%s\n" % (_digest(r), r) for r in ("a.md", "b.md", "d.md")),
            _texto(["a.md", "b.md"]) + "%s  <expediente>/VERIFICAR.sh\n" % _digest("x"),
        )
        for texto in textos:
            nucleo = pagina_desde_manifiesto(leer_manifiesto(texto, "prueba"))
            copia = acto.leer_pagina(texto, "prueba")
            self.assertEqual(nucleo.digest, copia.digest, texto)
            self.assertEqual(nucleo.desordenada, copia.desordenada, texto)
            self.assertEqual(nucleo.redactadas, copia.redactadas, texto)
            self.assertEqual(
                [f.ruta for f in nucleo.filas], [f.ruta for f in copia.filas], texto
            )
            for consulta in ("a.md", "b.md", "c.md", "e.md", "0.md"):
                uno = consultar(nucleo, consulta)
                otro = acto.consultar(copia, consulta)
                self.assertEqual(uno.estado, otro.estado, (texto, consulta))
                self.assertEqual(uno.intervalo(), otro.intervalo(), (texto, consulta))

    def test_p111d_env_i_fuera_del_arbol(self) -> None:
        directorio = _tempfile.mkdtemp(prefix="ausencia-fria-")
        self.addCleanup(_shutil.rmtree, directorio, True)
        manifiesto = _os.path.join(directorio, "SHA256SUMS")
        with open(manifiesto, "w", encoding="utf-8") as flujo:
            flujo.write(_texto(["a.md", "b.md", "d.md"]))

        codigo, crudo = _acto_en_frio(manifiesto, "c.md", cwd=directorio)
        self.assertEqual(0, codigo, crudo)
        self.assertIn("-> ausente", crudo)
        self.assertIn("verificado | si", crudo)

        # Un byte del vecino: la pagina sigue ordenada, el testigo ya no la ata.
        with open(manifiesto, "w", encoding="utf-8") as flujo:
            flujo.write(
                "".join(
                    "%s  %s\n" % (_digest(r)[:-1] + ("0" if _digest(r)[-1] != "0" else "1"), r)
                    for r in ("a.md", "b.md", "d.md")
                )
            )
        codigo2, crudo2 = _acto_en_frio(manifiesto, "c.md", cwd=directorio)
        self.assertEqual(0, codigo2, crudo2)
        self.assertNotIn(pagina_desde_manifiesto(leer_manifiesto(_texto(["a.md", "b.md", "d.md"]), "x")).digest, crudo2)

        # Fila redactada: el orden tiene un hueco y no se acota.
        with open(manifiesto, "w", encoding="utf-8") as flujo:
            flujo.write(_texto(["a.md", "d.md"]) + "%s  <x>/s.sh\n" % _digest("x"))
        codigo3, crudo3 = _acto_en_frio(manifiesto, "c.md", cwd=directorio)
        self.assertEqual(3, codigo3, crudo3)
        self.assertIn("-> no_medida", crudo3)

        # Dialecto ajeno: se rechaza, no se normaliza.
        with open(manifiesto, "w", encoding="utf-8") as flujo:
            flujo.write("SHA256 (a.md) = %s\n" % _digest("a.md"))
        codigo4, crudo4 = _acto_en_frio(manifiesto, "c.md", cwd=directorio)
        self.assertEqual(2, codigo4, crudo4)
        self.assertIn("ENTRADA INVALIDA", crudo4)

    def test_p111e_el_testigo_merkle_se_verifica_sin_la_pagina(self) -> None:
        acto = _acto_como_modulo()
        pagina = acto.leer_pagina(_texto(["a.md", "b.md", "d.md"]), "prueba")
        testigo = acto.testigo_merkle(pagina, "c.md")
        self.assertTrue(acto.verificar_merkle(testigo))
        self.assertEqual(3, testigo.tamano)
        self.assertEqual(("b.md", "d.md"), (testigo.hoja_anterior[0], testigo.hoja_siguiente[0]))
        # La raiz es el unico dato que hay que recibir de fuera: cambiarla rompe.
        roto = _dataclasses.replace(testigo, raiz=("00" if testigo.raiz[:2] != "00" else "11") + testigo.raiz[2:])
        self.assertFalse(acto.verificar_merkle(roto))
        # Y cambiar la consulta del testigo, sin tocar los caminos, tambien.
        desplazado = _dataclasses.replace(testigo, consulta="a.md")
        self.assertFalse(acto.verificar_merkle(desplazado))


if __name__ == "__main__":
    _unittest.main()
