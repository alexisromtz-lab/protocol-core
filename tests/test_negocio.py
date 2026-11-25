"""test_negocio.py — el anillo 3 sobre un sujeto que no es software.

Motor declarado de la corrida:

    python3 -B -m unittest discover -s tests

QUE MIDE. Que la prueba de ausencia valga fuera del arbol de codigo: una agenda
de citas y un libro de movimientos, con nombres en espanol y acentos. Fuera de
APFS el problema cambia de forma — «Avila» y «Ávila» son el mismo cliente para el
dueno, y la normalizacion que lo decide (`pi`) no la elige el motor.

LO QUE ESTE ARCHIVO ANADE A LA TESIS. `pi` es una **entrada**: se aplica antes de
que la pagina exista, y despues ya no se puede aplicar, porque la pagina es la
forma y su digest autentica la forma (P-73, P-74). Dos claves con la misma `pi`
son una clave y el manifiesto no puede llevarlas las dos (P-75). Y el orden que
eligio el exportador **no es el objeto**: el mismo conjunto de filas en dos
ordenes de archivo da el mismo digest, el mismo testigo y el mismo veredicto, y
solo cambia la bandera `desordenada` que lo publica (P-76).

P-72 CIERRA UNA CUENTA QUE SE CONTABA A SI MISMA. En este arbol una clase base
que herede de `unittest.TestCase` se descubre como suite *y* se hereda, de modo
que el denominador publicado sube sin que exista un test mas. El falsador mira
el AST de todo `tests/`: ninguna clase usada como base puede ser un `TestCase`.

NO CUBIERTO (lista cerrada): la firma del cliente sobre su propio manifiesto —el
acto construye el sujeto, no lo autentica—; y la equivalencia de mayusculas del
volumen, que no es del modulo (P-78 mide que el alfabeto las admite y la colacion
las separa).
"""

from __future__ import annotations

import ast as _ast
import importlib.util as _importlib_util
import io as _io
import os as _os
import pathlib as _pathlib
import shutil as _shutil
import subprocess as _subprocess
import sys as _sys
import tempfile as _tempfile
import unittest as _unittest
from typing import Dict, List, Set, Tuple

_RAIZ = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
_TESTS = _os.path.join(_RAIZ, "tests")
_SRC = _os.path.join(_RAIZ, "src")
if _SRC not in _sys.path:
    _sys.path.insert(0, _SRC)

from protocol.ausencia import (  # noqa: E402
    Pagina,
    VeredictoDeAusencia,
    canonizar,
    consultar,
    pagina_desde_manifiesto,
    verificar,
)
from protocol.types import ContratoViolado  # noqa: E402
from protocol.ubicacion import leer_manifiesto  # noqa: E402

_FIXTURE = _os.path.join(_RAIZ, "examples", "manifiesto-negocio.py")
_ACTO = _os.path.join(_RAIZ, "examples", "verificar_ausencia.py")


def _negocio():
    """El acto de negocio, importado por ruta: el nombre lleva guion."""

    spec = _importlib_util.spec_from_file_location("_manifiesto_negocio", _FIXTURE)
    modulo = _importlib_util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


_NEGOCIO = _negocio()


def _digest(ruta: str) -> str:
    return _hashlib_sha256(("sello:" + ruta).encode("utf-8"))


def _hashlib_sha256(datos: bytes) -> str:
    import hashlib

    return hashlib.sha256(datos).hexdigest()


def _leer(ruta: str) -> str:
    with _io.open(ruta, encoding="utf-8") as f:
        return f.read()


def _escribir(ruta: str, texto: str) -> None:
    with _io.open(ruta, "w", encoding="utf-8") as f:
        f.write(texto)


def _texto(rutas) -> str:
    return "".join("%s  %s\n" % (_digest(r), r) for r in rutas)


def _pagina(rutas) -> Pagina:
    return pagina_desde_manifiesto(leer_manifiesto(_texto(rutas), "prueba"))


def _emitir(destino: str, *banderas: str) -> Tuple[int, str]:
    proc = _subprocess.run(
        [_sys.executable, "-B", _FIXTURE, "--emitir", destino] + list(banderas),
        stdout=_subprocess.PIPE,
        stderr=_subprocess.STDOUT,
        cwd=_RAIZ,
    )
    return proc.returncode, proc.stdout.decode("utf-8")


def _clases(clase: _ast.ClassDef) -> List[str]:
    nombres = []
    for base in clase.bases:
        if isinstance(base, _ast.Name):
            nombres.append(base.id)
        elif isinstance(base, _ast.Attribute):
            nombres.append(base.attr)
    return nombres


class TestDenominadorNoSeCuentaAMiMismo(_unittest.TestCase):
    """P-72 · una base que hereda de `TestCase` infla la cuenta de tests."""

    def _censo(
        self,
    ) -> Tuple[Dict[Tuple[str, str], Set[str]], Dict[Tuple[str, str], Set[str]], Dict[Tuple[str, str], bool]]:
        """La clave es `(archivo, clase)`, no el nombre de la clase.

        Con el nombre suelto, dos clases homonimas en archivos distintos se
        pisaban en el diccionario y el denominador bajaba sin que faltara un
        test: el contador que vigila la cuenta se contaba a si mismo mal.
        """

        bases: Dict[Tuple[str, str], Set[str]] = {}
        metodos: Dict[Tuple[str, str], Set[str]] = {}
        hereda_testcase: Dict[Tuple[str, str], bool] = {}
        for nombre in sorted(_os.listdir(_TESTS)):
            if not nombre.endswith(".py"):
                continue
            fuente = _leer(_os.path.join(_TESTS, nombre))
            for nodo in _ast.walk(_ast.parse(fuente, nombre)):
                if not isinstance(nodo, _ast.ClassDef):
                    continue
                clave = (nombre, nodo.name)
                propias = _clases(nodo)
                bases[clave] = set(propias)
                metodos[clave] = {
                    n.name
                    for n in nodo.body
                    if isinstance(n, _ast.FunctionDef) and n.name.startswith("test")
                }
                hereda_testcase[clave] = any(b.endswith("TestCase") for b in propias)

        def resuelve(archivo: str, nombre: str, visto: Set[Tuple[str, str]]) -> bool:
            clave = (archivo, nombre)
            if hereda_testcase.get(clave):
                return True
            if clave in visto:
                return False
            visto.add(clave)
            return any(
                resuelve(archivo, base, visto)
                for base in bases.get(clave, set())
                if (archivo, base) in bases
            )

        for archivo, nombre in list(bases):
            hereda_testcase[(archivo, nombre)] = resuelve(archivo, nombre, set())
        return bases, metodos, hereda_testcase

    def test_p72_una_base_que_hereda_no_define_tests(self) -> None:
        # Un `TestCase` usado como base se descubre a si mismo **y** hereda sus
        # metodos a cada subclase: el mismo test suma dos veces y la cifra
        # publicada deja de ser el numero de preguntas. Un mixin sin `TestCase`
        # no tiene el problema, y es la forma sancionada de parametrizar.
        bases, metodos, hereda = self._censo()
        usadas = {
            (archivo, base)
            for (archivo, _), propias in bases.items()
            for base in propias
            if (archivo, base) in bases
        }
        culpables = sorted(
            ("%s::%s" % clave, sorted(metodos[clave]))
            for clave in usadas
            if hereda[clave] and metodos[clave]
        )
        self.assertEqual([], culpables, "una base que hereda de TestCase no puede traer tests")

    def test_p72b_el_conteo_descubierto_es_la_suma_de_los_metodos(self) -> None:
        # El denominador es lo que `discover` cuenta: los metodos de cada clase
        # hoja **mas** los que hereda de un mixin local. Compararlo con la cifra
        # publicada detecta el dia en que un mixin deje de ser mixin.
        bases, metodos, hereda = self._censo()
        usadas = {
            (archivo, base)
            for (archivo, _), propias in bases.items()
            for base in propias
            if (archivo, base) in bases
        }

        def efectivos(archivo: str, nombre: str, visto: Set[Tuple[str, str]]) -> Set[str]:
            clave = (archivo, nombre)
            if clave in visto:
                return set()
            visto.add(clave)
            total = set(metodos.get(clave, set()))
            for base in bases.get(clave, set()):
                total |= efectivos(archivo, base, visto)
            return total

        suma = sum(
            len(efectivos(archivo, nombre, set()))
            for (archivo, nombre) in bases
            if hereda[(archivo, nombre)] and (archivo, nombre) not in usadas
        )
        suite = _unittest.defaultTestLoader.discover(_TESTS)
        self.assertEqual(suma, suite.countTestCases())


class TestProyeccionDeclarada(_unittest.TestCase):
    """P-73 · `pi` existe, pliega, y no es la identidad disfrazada."""

    def test_p73_pi_pliega_diacriticos_y_es_idempotente(self) -> None:
        self.assertEqual("avila-cita-09-00-sillon1", _NEGOCIO.proyectar("Ávila-cita-09-00-sillon1"))
        claves = tuple(_NEGOCIO.CITAS) + tuple(_NEGOCIO.MOVIMIENTOS)
        for clave in claves:
            una = _NEGOCIO.proyectar(clave)
            self.assertEqual(una, _NEGOCIO.proyectar(una), clave)
            acentuada = len(clave) != len(una)
            self.assertEqual(acentuada, acentuada and una != clave.lower(), clave)
        proyectadas = {_NEGOCIO.proyectar(k) for k in claves}
        self.assertEqual(len(claves), len(proyectadas), "pi no colapsa las claves del sujeto")


class TestAcentoNoEsSlug(_unittest.TestCase):
    """P-74 · un byte fuera del alfabeto sale RC 2: se rechaza, no se normaliza."""

    def test_p74_el_modulo_no_pliega_por_su_cuenta(self) -> None:
        with self.assertRaises(ContratoViolado):
            canonizar("Ávila.tsv")

    def test_p74b_el_acto_declara_entrada_invalida(self) -> None:
        tmp = _tempfile.mkdtemp(prefix="negocio-acento-")
        try:
            manifiesto = _os.path.join(tmp, "SHA256SUMS_ACENTO")
            _escribir(manifiesto, _texto(["Ávila.tsv"]))
            proc = _subprocess.run(
                [
                    _sys.executable, "-B", _ACTO,
                    "--manifiesto", manifiesto,
                    "--ausente", "avila.tsv",
                    "--raiz", tmp,
                    "--universo", "disco",
                ],
                stdout=_subprocess.PIPE, stderr=_subprocess.STDOUT, cwd=_RAIZ,
            )
            salida = proc.stdout.decode("utf-8")
            self.assertEqual(2, proc.returncode, salida)
            self.assertIn("ENTRADA INVALIDA", salida)
        finally:
            _shutil.rmtree(tmp, ignore_errors=True)


class TestChoqueDeClaves(_unittest.TestCase):
    """P-75 · dos clientes, una clave: el acto falla antes de sellar."""

    def test_p75_el_choque_no_se_sella(self) -> None:
        tmp = _tempfile.mkdtemp(prefix="negocio-choque-")
        try:
            destino = _os.path.join(tmp, "emit")
            codigo, salida = _emitir(destino, "--choque")
            self.assertEqual(1, codigo, salida)
            self.assertIn("colapsa-el-caso", salida)
            self.assertIn("AVILA-CITA-09-00-SILLON1", salida)
            self.assertIn("Ávila-cita-09-00-sillon1", salida)
            self.assertFalse(_os.path.exists(_os.path.join(destino, "SHA256SUMS_AGENDA")))
        finally:
            _shutil.rmtree(tmp, ignore_errors=True)


class TestOrdenDelExportadorNoEsElObjeto(_unittest.TestCase):
    """P-76 · dos ordenes de archivo, una pagina: el digest no depende del orden."""

    def test_p76_mismo_conjunto_dos_ordenes_mismo_digest(self) -> None:
        tmp = _tempfile.mkdtemp(prefix="negocio-orden-")
        try:
            ordenado = _os.path.join(tmp, "ordenado")
            exportador = _os.path.join(tmp, "exportador")
            self.assertEqual(0, _emitir(ordenado)[0])
            self.assertEqual(0, _emitir(exportador, "--desordenado")[0])
            p1 = pagina_desde_manifiesto(
                leer_manifiesto(
                    _leer(_os.path.join(ordenado, "SHA256SUMS_AGENDA")),
                    "ordenado",
                )
            )
            p2 = pagina_desde_manifiesto(
                leer_manifiesto(
                    _leer(_os.path.join(exportador, "SHA256SUMS_AGENDA")),
                    "exportador",
                )
            )
            self.assertFalse(p1.desordenada)
            self.assertTrue(p2.desordenada, "el exportador ordeno por el nombre original")
            self.assertEqual(p1.digest, p2.digest)
            self.assertEqual([f.ruta for f in p1.filas], [f.ruta for f in p2.filas])
            t1 = consultar(p1, "avila-cita-09-30-sillon1.tsv")
            t2 = consultar(p2, "avila-cita-09-30-sillon1.tsv")
            self.assertEqual(t1.intervalo(), t2.intervalo())
            self.assertIs(t1.estado, t2.estado)
        finally:
            _shutil.rmtree(tmp, ignore_errors=True)


class TestAusenciaEnNegocio(_unittest.TestCase):
    """P-77 · una cita que nunca existio se prueba con dos vecinos."""

    def test_p77_cita_ausente_entre_dos_adyacentes(self) -> None:
        tmp = _tempfile.mkdtemp(prefix="negocio-ausencia-")
        try:
            destino = _os.path.join(tmp, "emit")
            self.assertEqual(0, _emitir(destino)[0])
            pagina = pagina_desde_manifiesto(
                leer_manifiesto(
                    _leer(_os.path.join(destino, "SHA256SUMS_AGENDA")),
                    "agenda",
                )
            )
            t = consultar(pagina, "avila-cita-09-30-sillon1.tsv")
            self.assertIs(VeredictoDeAusencia.AUSENTE, t.estado, t)
            self.assertEqual("avila-cita-09-00-sillon1.tsv", t.anterior.ruta)
            self.assertEqual("montes-cita-11-15-sillon3.tsv", t.siguiente.ruta)
            self.assertTrue(verificar(pagina, t))
            # El movimiento 0001 existe: la misma pagina contesta PRESENTE.
            self.assertIs(
                VeredictoDeAusencia.PRESENTE,
                consultar(pagina, "mov-2026-11-25-0001.tsv").estado,
            )
        finally:
            _shutil.rmtree(tmp, ignore_errors=True)


class TestColacionYMayusculas(_unittest.TestCase):
    """P-78 · el alfabeto admite mayusculas y la colacion C las pone **antes**."""

    def test_p78_la_colacion_no_es_la_del_volumen(self) -> None:
        # Un exportador que ordena como el volumen escribe `alfa.tsv` primero.
        pagina = _pagina(["alfa.tsv", "Zeta.tsv"])
        self.assertTrue(pagina.desordenada, "la colacion C pone Zeta antes que alfa")
        self.assertEqual(["Zeta.tsv", "alfa.tsv"], [f.ruta for f in pagina.filas])
        # `B.tsv` y `b.tsv` son dos filas legitimas del modulo: que el volumen no
        # pueda llevar las dos a la vez es la frontera del cliente, no del orden.
        dos = _pagina(["B.tsv", "a.tsv", "b.tsv"])
        self.assertEqual(3, len(dos.filas))
        self.assertEqual(["B.tsv", "a.tsv", "b.tsv"], [f.ruta for f in dos.filas])


#: El censo de P-83 se genera, no se sortea: dos corridas miden lo mismo.
_NOMBRES = (
    "Ávila", "Núñez", "Zúñiga", "Güemes", "Íñigo",
    "Peña", "Muñoz", "Berríos", "Ocaña", "Cuevas",
    "Güiza", "Iñárritu", "Zamora", "Núñez", "Álvarez",
    "Herrera", "Ibáñez", "Ortuño", "Vílchez", "Yáñez",
    "Cañas", "Dueñas", "Elorza", "Fariñas", "Begoña",
)
_NOMBRE_DE_PILA = ("Ana", "Jesús", "Lucía", "Íñigo", "Ramón")
_RECURSOS = ("sillon1", "sillon2", "sillon3", "sillon4")
_HORAS = ("09-00", "11-00", "13-00", "15-00", "17-00")


def _censo_de_claves() -> Tuple[List[Tuple[str, str, str, str]], ...]:
    """10 000 citas: 25 apellidos x 20 fechas x 5 horas x 4 recursos."""

    claves = []
    for indice, apellido in enumerate(_NOMBRES):
        nombre = "%s %s" % (_NOMBRE_DE_PILA[indice % len(_NOMBRE_DE_PILA)], apellido)
        for dia in range(20):
            fecha = "2026-12-%02d" % (dia + 1)
            for hora in _HORAS:
                for recurso in _RECURSOS:
                    claves.append((nombre, fecha, hora, recurso))
    return tuple(claves), claves  # type: ignore[return-value]


class TestCensoDeClavesEnEspanol(_unittest.TestCase):
    """P-83 · cuantas claves colapsan segun lo que la clave canonica incluya."""

    def test_p83_el_censo_es_determinista_y_su_orden_no_es_el_objeto(self) -> None:
        claves, _ = _censo_de_claves()
        self.assertEqual(10000, len(claves))
        self.assertEqual(len(claves), len(set(claves)))

    def test_p83b_la_clave_corta_colisiona_y_la_completa_no(self) -> None:
        """Medido: el recurso y la hora no son adorno de la clave, son la clave.

        Si la proyeccion se queda en `(nombre, fecha)`, 9 500 citas de este censo
        colapsan en 500 claves: cada una se fusiona con las otras 19 que comparten
        cliente y dia, y el motor ya no puede probar la ausencia de ninguna. Con
        hora y recurso dentro de la clave, colapsan cero.
        """

        claves, _ = _censo_de_claves()
        cortas = {
            _NEGOCIO.proyectar("%s-%s" % (nombre, fecha)) for nombre, fecha, _, _ in claves
        }
        largas = {
            _NEGOCIO.proyectar("%s-%s-%s-%s" % (nombre, fecha, hora, recurso))
            for nombre, fecha, hora, recurso in claves
        }
        self.assertEqual(500, len(cortas))
        self.assertEqual(10000, len(largas))
        self.assertEqual(9500, len(claves) - len(cortas))

    def test_p83c_el_alfabeto_espanol_no_produce_falsos_rechazos(self) -> None:
        """Cero RC 2 por acentos: tras NFD todo cae dentro de `[a-z0-9._-]`."""

        claves, _ = _censo_de_claves()
        permitido = set("abcdefghijklmnopqrstuvwxyz0123456789._-")
        for nombre, fecha, hora, recurso in claves:
            proyectada = _NEGOCIO.proyectar("%s-%s-%s-%s" % (nombre, fecha, hora, recurso))
            fuera = set(proyectada) - permitido
            self.assertFalse(fuera, "%r -> %r deja %r" % (nombre, proyectada, fuera))
            canonizar(proyectada)  # no levanta: el alfabeto la admite

    def test_p83d_el_mas_y_los_espacios_dobles_son_frontera_declarada(self) -> None:
        """`+52` no es un acento: `+` no está en el alfabeto y se publica RC 2.

        Y el espacio doble **sí** se pliega, porque los separadores están
        declarados: dos exportadores que escriben `Ana  Peña` y `Ana Peña` hablan
        del mismo cliente, y el motor no tiene que adivinarlo dos veces.
        """

        self.assertEqual("ana-pena", _NEGOCIO.proyectar("Ana  Peña"))
        self.assertEqual("ana-pena", _NEGOCIO.proyectar("Ana Peña"))
        with self.assertRaises(ContratoViolado):
            canonizar(_NEGOCIO.proyectar("+52 55 1234 5678"))
