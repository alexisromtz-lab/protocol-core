"""test_audit.py — casos T-03, T-04 y T-05 sobre `protocol.audit` (§5).

Motor declarado de la corrida:

    python3 -B -m unittest discover -s protocol-core/tests -v

Este archivo **no** vive en `src/`: §6 asigna `tests/` y §0.4(c) gobierna la
biblioteca, no sus pruebas. Aquí sí se usan `tempfile`, `shutil`, `os.utime` y
`dataclasses.replace`. El namespace de prueba es efímero y se destruye en la
limpieza.

Lecturas declaradas. Ninguna se hace pasar por el texto de SPEC.md:

  1. T-03 (endogeneidad) se mide sobre el censo mismo: un objeto con el nombre
     del pie del instrumento se cuenta como cualquier otro. El descuento NO es
     del censo, es de `resta`, y por eso hay dos casos separados: si el censo
     descontara, el segundo no tendría nada que restar.
  2. Los valores esperados de `census` están escritos A MANO (8 / 4 / 6 / 0 /
     23 bytes; 2 / 0 / 3 / 0 / 1 conteos de 0x0A). No se recalculan con el
     instrumento que se está probando: la expectativa y la medición son dos
     caminos distintos o el caso se cuenta dos veces.
  3. T-05 no se mide con una carrera real de dos procesos: se mide la GUARANTÍA.
     El mecanismo de llegada —dos partidas de rutas encerrando la medición— se
     conduce directamente (`_partida_de_rutas` + `_exigir_sin_movimiento`), igual
     que T-10 condujo su mitad negativa sin poder producirla desde `ficha()`.
     Lo que se declara: el movimiento se eleva, no se devuelve como cifra.
  4. El reposo se mide con `os.utime`, no con el reloj: el corte es un instante
     fijo escrito en el archivo (2026-10-09T12:00Z) y las marcas son dos épocas
     fijas (2020 para lo quieto, 2033 para lo posterior). Un caso de reposo que
     dependiera del reloj no podría diferir de su contrario sin dormir.
  5. El caso del DIRECTORIO con marca posterior es el que ve el borrado seguido
     de un alta: el conjunto de rutas queda idéntico y la lista de nombres del
     directorio cambió. Se mide con el directorio raíz —el único objeto del
     subárbol que no es hijo de otro—, y se declara que la ley de `reposo` se
     lee sobre todo objeto del subárbol, directorios incluidos. Este caso fue el
     rojo de la Corrida 3 y su reparación fue del OBJETO (`audit.py` leía los
     hijos y no la raíz), no de la prueba.
  6. `verify` compara contra el objeto, y las divergencias de campo POSTERIOR se
     alcanzan corrompiendo un recibo a mano (`dataclasses.replace`): el orden de
     comparación es del contrato, no del sistema de archivos, y con un objeto
     realmente cambiado el primer campo que diverge es siempre `H`. El caso del
     recibo corrompido declara que está corrompido.
  7. Tocar el `mtime` de un objeto NO produce divergencia: se mide como caso
     positivo del alcance declarado de `verify` (no adjudica la cadena ni el
     certificado, §lectura 13 de `audit.py`).
  8. Este archivo imprime lo medido con el prefijo `MEDICION |`. La corrida es
     el crudo, y un crudo que no puede diferir no es evidencia.

NO CUBIERTO por este archivo (lista cerrada). La carrera real de dos procesos
escribiendo dentro de un `census` no se ejecuta: se mide el mecanismo que la
detecta. La durabilidad frente a un corte de energía (T-11) no pertenece aquí.
`ENAMETOOLONG` y `ENOTSUP` no se provocan. La ventana excedida se mide con una
ventana de un microsegundo y se imprime el transcurrido real: es el único caso
de este archivo cuyo disparo depende de una duración, y por eso imprime su
evidencia. El error `ELOOP` del recorrido se declara y no se provoca: un FIFO
en el árbol colgaría la suite si algo lo abriera por error.
"""

from __future__ import annotations

import dataclasses as _dataclasses
import datetime as _datetime
import errno as _errno
import os as _os
import shutil as _shutil
import sys as _sys
import tempfile as _tempfile
import unittest as _unittest

# Resolución del paquete relativa a ESTE archivo: ninguna ruta absoluta se
# hornea en `src/` (§0.4.b); en las pruebas se usa el árbol efímero de
# `tempfile`, declarado en el docstring.
_SRC = _os.path.join(
    _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), "src"
)
if _SRC not in _sys.path:
    _sys.path.insert(0, _SRC)

from protocol.atomic import reserve  # noqa: E402  (después del ajuste de `sys.path`)
from protocol.audit import (  # noqa: E402
    _exigir_sin_movimiento,
    _partida_de_rutas,
    census,
    reposo,
    resta,
    verify,
)
from protocol.metrics import ficha  # noqa: E402
from protocol.types import (  # noqa: E402
    ALGORITMO,
    OK,
    ContratoViolado,
    Contexto,
    Divergencia,
    ENOENT,
    EstrategiaSelf,
    FuenteT0,
    Hash,
    Indeterminado,
    Inodo,
    Namespace,
    Recibo,
    Slug,
    T0,
    Unidad,
)

#: Etiqueta de volumen de la suite. Es una etiqueta legible, nunca una ruta
#: (§0.4.b): no empieza por `/` y no nombra el directorio real.
VOLUMEN = "suite-audit-volumen"

#: Etiqueta del universo del censo. Tampoco es una ruta (§0.4.b).
UNIVERSO = "suite-audit-universo"

#: Prefijo de la sonda de caso escrita AQUÍ. Los dos nombres difieren SÓLO en el
#: caso de la última letra: es lo único que el `stat` necesita ver.
SONDA_CASO_MENOR = ".suite-caso-menor-a"
SONDA_CASO_MAYOR = ".suite-caso-menor-A"

#: Instante fijo del archivo, no del reloj (§lectura 4). 2026-10-09T12:00:00Z.
CORTE = _datetime.datetime(2026, 10, 9, 12, 0, 0, tzinfo=_datetime.timezone.utc)

#: Dos épocas fijas: lo quieto (2020-09-13T12:26:40Z) y lo posterior al corte
#: (2033-05-18T03:33:20Z).
EPOCA_QUIETA = 1600000000.0
EPOCA_POSTERIOR = 2000000000.0

#: Ventana declarada de la suite, y la ventana imposible del caso de exceso.
VENTANA = _datetime.timedelta(seconds=5)
VENTANA_IMPOSIBLE = _datetime.timedelta(microseconds=1)

#: Contenidos declarados del censo de T-03. Los esperados van escritos a mano
#: en cada caso (§lectura 2).
CUERPOS = {
    "a.txt": b"uno\ndos\n",  # B = 8,  L = 2
    "b.txt": b"tres",  # B = 4,  L = 0
    "d.txt": b"",  # B = 0,  L = 0
    "pie-del-instrumento.txt": b"el pie del instrumento\n",  # B = 23, L = 1
    "sub/c.txt": b"a\nb\nc\n",  # B = 6,  L = 3
}
CUERPOS_ARCHIVO = 5
CUERPOS_BYTE = 41
CUERPOS_LINEA = 6


def _medicion(etiqueta: str, valor: object) -> None:
    print("MEDICION | %s | %s" % (etiqueta, valor))


def _nombre_max(fd: int) -> int:
    """`NAME_MAX` del volumen, medido. Respaldo declarado: 255."""

    try:
        return int(_os.fpathconf(fd, "PC_NAME_MAX"))
    except (OSError, ValueError):
        return 255


def _sonda_caso_propia(fd_root: int) -> bool:
    """¿Distingue el volumen mayúsculas de minúsculas? Sonda de ESTE archivo.

    Camino distinto al de `sonda_caso` sobre el mismo motor, que es el kernel.
    La sonda no borra lo que no creó: sólo borra los dos nombres que abrió.
    """

    fd = _os.open(
        SONDA_CASO_MENOR,
        _os.O_CREAT | _os.O_EXCL | _os.O_WRONLY,
        0o600,
        dir_fd=fd_root,
    )
    try:
        try:
            _os.stat(SONDA_CASO_MAYOR, dir_fd=fd_root, follow_symlinks=False)
            return False
        except OSError as exc:
            if exc.errno == _errno.ENOENT:
                return True
            raise
    finally:
        _os.close(fd)
        for nombre in (SONDA_CASO_MENOR, SONDA_CASO_MAYOR):
            try:
                _os.unlink(nombre, dir_fd=fd_root)
            except OSError as exc:
                if exc.errno != _errno.ENOENT:
                    raise


def _escribir(fd_padre: int, nombre: str, datos: bytes) -> None:
    """Escritura de prueba, confinada al descriptor. No es `reserve`: no sella."""

    fd = _os.open(
        nombre, _os.O_CREAT | _os.O_EXCL | _os.O_WRONLY, 0o600, dir_fd=fd_padre
    )
    try:
        if datos:
            _os.write(fd, datos)
    finally:
        _os.close(fd)


def _ctx(unidad: Unidad, universo: str = UNIVERSO) -> Contexto:
    """Etiqueta de validez completa: los seis campos, declarados antes de medir."""

    return Contexto(
        universo=universo,
        unidad=unidad,
        motor="python3 -B -m unittest discover -s protocol-core/tests",
        t_utc="09Z20Z00Z.000000",
        ventana="5 s",
        umbral="ninguno: el censo no aplica umbral",
    )


def _fijar_mtimes(ruta: str, marca: float) -> int:
    """Fija el `mtime` de TODO el subárbol, el directorio incluido (§lectura 4).

    Recursión por ruta real: es una prueba, y el árbol efímero es suyo. Los
    objetos se fijan antes que su directorio padre, porque crear o borrar mueve
    la marca del padre y no al revés.
    """

    fijados = 0
    for nombre in sorted(_os.listdir(ruta)):
        hijo = _os.path.join(ruta, nombre)
        _os.utime(hijo, (marca, marca))
        fijados += 1
        if _os.path.isdir(hijo):
            fijados += _fijar_mtimes(hijo, marca)
    _os.utime(ruta, (marca, marca))
    return fijados


class _BaseNamespace(_unittest.TestCase):
    """Namespace efímero con sus cuatro parámetros medidos, no supuestos."""

    def setUp(self) -> None:
        self.raiz = _tempfile.mkdtemp(prefix="protocolo-suite-audit-")
        # Orden LIFO de las limpiezas: primero los descriptores, luego el árbol.
        self.addCleanup(_shutil.rmtree, self.raiz, True)
        self.fd = _os.open(self.raiz, _os.O_RDONLY)
        self.addCleanup(_os.close, self.fd)

        self.sensible = _sonda_caso_propia(self.fd)
        self.nombre_max = _nombre_max(self.fd)
        self.motor = (
            FuenteT0.BIRTHTIME
            if hasattr(_os.fstat(self.fd), "st_birthtime")
            else FuenteT0.NINGUNA
        )
        self.ns = Namespace(
            fd_root=self.fd,
            sensible_al_caso=self.sensible,
            nombre_max=self.nombre_max,
            motor_nacimiento=self.motor,
            sincronizacion_directorio=True,
            volumen=VOLUMEN,
        )

    def _sub_namespace(self, nombre: str) -> Namespace:
        """Segundo namespace sobre el MISMO volumen, con sus parámetros medidos."""

        _os.mkdir(nombre, dir_fd=self.fd)
        fd = _os.open(nombre, _os.O_RDONLY, dir_fd=self.fd)
        self.addCleanup(_os.close, fd)
        return Namespace(
            fd_root=fd,
            sensible_al_caso=self.sensible,
            nombre_max=self.nombre_max,
            motor_nacimiento=self.motor,
            sincronizacion_directorio=True,
            volumen=VOLUMEN + "-sub",
        )

    def _arbol_del_censo(self, fd_raiz: int) -> None:
        """Escribe los contenidos declarados de T-03, con su subdirectorio."""

        _os.mkdir("sub", dir_fd=fd_raiz)
        for ruta, datos in sorted(CUERPOS.items()):
            partes = ruta.split("/")
            if len(partes) == 1:
                _escribir(fd_raiz, partes[0], datos)
                continue
            fd_sub = _os.open(partes[0], _os.O_RDONLY, dir_fd=fd_raiz)
            try:
                _escribir(fd_sub, partes[1], datos)
            finally:
                _os.close(fd_sub)


class TestCensoYAutoConteo(_BaseNamespace):
    """§5 T-03 · §1.3 · §3.c — el censo cuenta; `resta` descuenta."""

    def test_t03_el_censo_cuenta_el_pie_y_no_lo_descuenta(self) -> None:
        self._arbol_del_censo(self.fd)

        archivos = census(self.ns, _ctx(Unidad.ARCHIVO))
        bytes_ = census(self.ns, _ctx(Unidad.BYTE))
        lineas = census(self.ns, _ctx(Unidad.LINEA))

        # Cinco objetos regulares: el subdirectorio se atraviesa, no se cuenta.
        self.assertEqual(archivos.valor, CUERPOS_ARCHIVO)
        self.assertEqual(bytes_.valor, CUERPOS_BYTE)
        self.assertEqual(lineas.valor, CUERPOS_LINEA)
        # El pie del instrumento está ADENTRO del número: el censo no se resta.
        self.assertIn("pie-del-instrumento.txt", CUERPOS)
        # La etiqueta de validez viaja dentro del resultado (§1.4).
        for etiqueta, unidad in (
            (archivos, Unidad.ARCHIVO),
            (bytes_, Unidad.BYTE),
            (lineas, Unidad.LINEA),
        ):
            self.assertIsInstance(etiqueta.contexto, Contexto)
            self.assertEqual(etiqueta.contexto.unidad, unidad)
            self.assertEqual(etiqueta.contexto.universo, UNIVERSO)

        _medicion("T-03 censo ARCHIVO", archivos.valor)
        _medicion("T-03 censo BYTE", bytes_.valor)
        _medicion("T-03 censo LINEA", lineas.valor)
        _medicion("T-03 universo de la etiqueta", archivos.contexto.universo)

    def test_t03_unidad_ocurrencia_no_vale_cero(self) -> None:
        self._arbol_del_censo(self.fd)

        with self.assertRaises(ContratoViolado) as ocurrencia:
            census(self.ns, _ctx(Unidad.OCURRENCIA))
        with self.assertRaises(ContratoViolado) as sin_contexto:
            census(self.ns, "no soy una etiqueta de validez")
        with self.assertRaises(ContratoViolado) as ruta_absoluta:
            census(self.ns, _ctx(Unidad.ARCHIVO, universo="/tmp/otro-universo"))

        self.assertEqual(
            ocurrencia.exception.campos.get("unidad"), Unidad.OCURRENCIA.value
        )
        # El tipo se NOMBRA y el valor que se rechaza no se copia al campo: la
        # declaración no repite el objeto, igual que la etiqueta no repite la
        # ruta. Un `assertIn("h", ...)` medía la letra de una palabra, no la
        # declaración (fue el rojo de la Corrida 3).
        self.assertEqual(sin_contexto.exception.campos.get("tipo"), "str")
        self.assertNotIn("no soy", repr(sin_contexto.exception))
        self.assertEqual(
            ruta_absoluta.exception.campos.get("universo"), "/tmp/otro-universo"
        )

        _medicion(
            "T-03 unidades admitidas",
            ocurrencia.exception.campos.get("unidades_admitidas"),
        )
        _medicion("T-03 tipo sin contexto", sin_contexto.exception.campos.get("tipo"))

    def test_t03_resta_elegida_y_doble_descuento(self) -> None:
        bruto = 41
        pie = 1

        # E: el universo ya excluye el pie por enumeración. Restar es descontar
        # dos veces y el resultado NO es un número.
        self.assertEqual(
            resta(bruto, 0, True, EstrategiaSelf.E_EXCLUSION), bruto
        )
        doble = resta(bruto, pie, True, EstrategiaSelf.E_EXCLUSION)
        self.assertIsInstance(doble, Indeterminado)

        # D: deducción aritmética, válida sólo si el pie está congelado.
        self.assertEqual(
            resta(bruto, pie, True, EstrategiaSelf.D_DEDUCCION), bruto - pie
        )
        self.assertEqual(
            resta(bruto, 0, True, EstrategiaSelf.D_DEDUCCION), bruto
        )
        for caso, (m_self, congelado) in {
            "pie no congelado": (pie, False),
            "pie sin enumerar": (None, True),
            "neto negativo": (bruto + 1, True),
        }.items():
            with self.subTest(caso=caso):
                resultado = resta(
                    bruto, m_self, congelado, EstrategiaSelf.D_DEDUCCION
                )
                self.assertIsInstance(resultado, Indeterminado)
                _medicion("T-03 resta indeterminada (%s)" % caso, resultado.razon[:48])

        for etiqueta, argumentos in {
            "estrategia como letra": (bruto, pie, True, "E"),
            "congelamiento como entero": (bruto, pie, 1, EstrategiaSelf.D_DEDUCCION),
            "bruto booleano": (True, pie, True, EstrategiaSelf.D_DEDUCCION),
            "bruto negativo": (-1, pie, True, EstrategiaSelf.D_DEDUCCION),
            "pie negativo": (bruto, -1, True, EstrategiaSelf.D_DEDUCCION),
        }.items():
            with self.subTest(caso=etiqueta):
                with self.assertRaises(ContratoViolado):
                    resta(*argumentos)

        _medicion("T-03 resta E con pie", type(doble).__name__)
        _medicion(
            "T-03 resta D congelada",
            resta(bruto, pie, True, EstrategiaSelf.D_DEDUCCION),
        )


class TestInmunidadDeNamespace(_BaseNamespace):
    """§5 T-04 — el censo de un namespace no cambia cuando otro se mueve."""

    def test_t04_dos_namespaces_del_mismo_volumen(self) -> None:
        ns_a = self._sub_namespace("a")
        ns_b = self._sub_namespace("b")

        _escribir(ns_a.fd_root, "x1.txt", b"x1\n")
        _escribir(ns_a.fd_root, "x2.txt", b"x2\n")
        _escribir(ns_b.fd_root, "y1.txt", b"y1\n")

        a1 = census(ns_a, _ctx(Unidad.ARCHIVO)).valor
        b1 = census(ns_b, _ctx(Unidad.ARCHIVO)).valor
        self.assertEqual((a1, b1), (2, 1))

        # Tres llegadas al namespace vecino.
        for nombre in ("y2.txt", "y3.txt", "y4.txt"):
            _escribir(ns_b.fd_root, nombre, b"mas\n")
        a2 = census(ns_a, _ctx(Unidad.ARCHIVO)).valor
        b2 = census(ns_b, _ctx(Unidad.ARCHIVO)).valor
        self.assertEqual(a2, a1)
        self.assertEqual(b2, b1 + 3)

        # Y una llegada al propio, para que la inmunidad se mida en las dos
        # direcciones: si sólo se midiera una, un censo pegado al vecino pasaría.
        _escribir(ns_a.fd_root, "x3.txt", b"x3\n")
        a3 = census(ns_a, _ctx(Unidad.ARCHIVO)).valor
        b3 = census(ns_b, _ctx(Unidad.ARCHIVO)).valor
        self.assertEqual(a3, a2 + 1)
        self.assertEqual(b3, b2)

        _medicion("T-04 censo de A antes y despues", (a1, a2, a3))
        _medicion("T-04 censo de B antes y despues", (b1, b2, b3))


class TestReposoYMovimiento(_BaseNamespace):
    """§5 T-05 · §3.e INV_TIME — la cota del corte y el motor de llegada."""

    def test_t05_reposo_verdadero_si_nada_excede_el_corte(self) -> None:
        self._arbol_del_censo(self.fd)
        fijados = _fijar_mtimes(self.raiz, EPOCA_QUIETA)

        v = reposo(self.ns, CORTE, VENTANA)
        self.assertIs(v, True)
        _medicion("T-05 reposo con marcas quietas", v)
        _medicion("T-05 objetos con marca fijada", fijados)

    def test_t05_reposo_falso_si_un_objeto_excede_el_corte(self) -> None:
        self._arbol_del_censo(self.fd)
        _fijar_mtimes(self.raiz, EPOCA_QUIETA)
        fd_sub = _os.open("sub", _os.O_RDONLY, dir_fd=self.fd)
        try:
            nombre = "c.txt"
            _os.utime(nombre, (EPOCA_POSTERIOR, EPOCA_POSTERIOR), dir_fd=fd_sub)
        finally:
            _os.close(fd_sub)

        v = reposo(self.ns, CORTE, VENTANA)
        self.assertIs(v, False)
        _medicion("T-05 reposo con un objeto posterior al corte", v)

    def test_t05_reposo_falso_si_el_directorio_se_movio(self) -> None:
        # El conjunto de rutas queda idéntico; lo único que cambió es la lista
        # de nombres del directorio. Es el caso que la cota por archivo no ve
        # (§lectura 5 de `audit.py`).
        self._arbol_del_censo(self.fd)
        _fijar_mtimes(self.raiz, EPOCA_QUIETA)
        _os.utime(self.raiz, (EPOCA_POSTERIOR, EPOCA_POSTERIOR))

        v = reposo(self.ns, CORTE, VENTANA)
        self.assertIs(v, False)
        _medicion("T-05 reposo con el directorio posterior al corte", v)

    def test_t05_el_movimiento_se_declara_y_no_es_una_cifra(self) -> None:
        # La carrera no se produce aquí (§lectura 3): se conduce el mecanismo que
        # la detecta, con una llegada y con una partida.
        _escribir(self.fd, "quieto.txt", b"quieto\n")

        antes = _partida_de_rutas(self.fd)
        _escribir(self.fd, "llega.txt", b"llega\n")
        despues = _partida_de_rutas(self.fd)
        self.assertNotEqual(antes, despues)
        with self.assertRaises(ContratoViolado) as llegada:
            _exigir_sin_movimiento(antes, despues)
        self.assertEqual(llegada.exception.campos.get("llegadas"), 1)
        self.assertEqual(llegada.exception.campos.get("partidas"), 0)
        self.assertEqual(
            llegada.exception.campos.get("entradas_antes"), len(antes)
        )
        self.assertEqual(
            llegada.exception.campos.get("entradas_despues"), len(despues)
        )

        antes2 = _partida_de_rutas(self.fd)
        _os.unlink("llega.txt", dir_fd=self.fd)
        despues2 = _partida_de_rutas(self.fd)
        with self.assertRaises(ContratoViolado) as partida:
            _exigir_sin_movimiento(antes2, despues2)
        self.assertEqual(partida.exception.campos.get("partidas"), 1)
        self.assertEqual(partida.exception.campos.get("llegadas"), 0)

        # Y el caso que NO es movimiento: dos partidas del mismo árbol coinciden
        # (un crudo que no puede diferir no es evidencia, pero aquí la igualdad
        # es el control del detector).
        _exigir_sin_movimiento(antes2, antes2)

        _medicion("T-05 llegadas detectadas", llegada.exception.campos.get("llegadas"))
        _medicion("T-05 partidas detectadas", partida.exception.campos.get("partidas"))

    def test_t05_ventana_excedida_y_cortes_no_admisibles(self) -> None:
        for i in range(40):
            _escribir(self.fd, "objeto-%02d.txt" % i, b"contenido\n" * 4)
        _fijar_mtimes(self.raiz, EPOCA_QUIETA)

        with self.assertRaises(ContratoViolado) as exceso:
            reposo(self.ns, CORTE, VENTANA_IMPOSIBLE)
        transcurrido = exceso.exception.campos.get("transcurrido")
        self.assertIsNotNone(transcurrido)
        self.assertEqual(exceso.exception.campos.get("ventana"), str(VENTANA_IMPOSIBLE))

        with self.assertRaises(ContratoViolado):
            reposo(self.ns, _datetime.datetime(2026, 10, 9, 12, 0, 0), VENTANA)
        with self.assertRaises(ContratoViolado):
            reposo(self.ns, CORTE, _datetime.timedelta(0))
        with self.assertRaises(ContratoViolado):
            reposo(self.ns, CORTE, None)
        with self.assertRaises(ContratoViolado):
            reposo(self.ns, "2026-10-09T12:00:00Z", VENTANA)

        # El universo no se movió y las marcas son anteriores al corte: con la
        # ventana declarada, el mismo objeto da reposo verdadero.
        self.assertIs(reposo(self.ns, CORTE, VENTANA), True)

        _medicion("T-05 transcurrido medido con ventana de 1 microsegundo", transcurrido)
        _medicion("T-05 objetos del arbol", 40)


class TestVerificacion(_BaseNamespace):
    """§2.5.1 · §4 `verify` — el recibo contra el objeto, campo a campo."""

    def test_verify_ok_y_divergencia_del_primer_campo(self) -> None:
        slug = Slug("pieza.txt")
        original = b"contenido sellado\n"
        reserva = reserve(self.ns, slug, original)
        self.assertIs(reserva.sellado, True)

        sellado = ficha(self.ns, slug)
        recibo = Recibo(slug=slug, ficha=sellado)
        self.assertIs(verify(recibo, self.ns), OK)

        # Tocar el mtime NO es divergencia: la marca no vive en el recibo.
        _os.utime("pieza.txt", (EPOCA_POSTERIOR, EPOCA_POSTERIOR), dir_fd=self.fd)
        self.assertIs(verify(recibo, self.ns), OK)

        # El objeto cambia: el primer campo declarado que diverge es H.
        fd = _os.open("pieza.txt", _os.O_WRONLY | _os.O_APPEND, dir_fd=self.fd)
        try:
            _os.write(fd, b"y una linea mas\n")
        finally:
            _os.close(fd)
        divergencia = verify(recibo, self.ns)
        self.assertIsInstance(divergencia, Divergencia)
        self.assertEqual(divergencia.campo, "h")
        self.assertNotEqual(divergencia.esperado, divergencia.medido)

        _medicion("verify recibo intacto", verify(Recibo(slug=slug, ficha=ficha(self.ns, slug)), self.ns))
        _medicion("verify campo divergente", divergencia.campo)

    def test_verify_campos_posteriores_y_anchura_declarada(self) -> None:
        slug = Slug("otra-pieza.txt")
        cuerpo = b"otra pieza del taller\n"
        reserve(self.ns, slug, cuerpo)
        sellado = ficha(self.ns, slug)

        # Divergencias de campo POSTERIOR: el orden es del contrato, no del
        # sistema de archivos (§lectura 6). El recibo corrompido lo declara.
        corruptos = {
            "b": _dataclasses.replace(sellado, b=sellado.b + 1),
            "i": _dataclasses.replace(
                sellado, i=Inodo(dev=sellado.i.dev, ino=sellado.i.ino + 1)
            ),
            "t0": _dataclasses.replace(sellado, t0=T0.nulo()),
        }
        for campo, ficha_corrupta in corruptos.items():
            with self.subTest(campo=campo):
                resultado = verify(Recibo(slug=slug, ficha=ficha_corrupta), self.ns)
                self.assertIsInstance(resultado, Divergencia)
                self.assertEqual(resultado.campo, campo)
                _medicion("verify campo divergente (recibo corrompido)", campo)

        # El truncamiento viaja con su anchura: medir a 64 un recibo sellado a 16
        # produciría una divergencia fabricada por el metro (§lectura 11). El caso
        # se mide en las DOS direcciones y con su control negativo: sin el par, un
        # `verify` que devolviera OK siempre pasaría el positivo.
        corto = _dataclasses.replace(
            sellado,
            h=Hash(ALGORITMO, sellado.h.digest[:16], 16),
        )
        completo = ficha(self.ns, slug)
        self.assertEqual(completo.h.digest[:16], corto.h.digest)
        self.assertNotEqual(completo.h, corto.h)

        # Positivo: `verify` mide con la anchura que el RECIBO declara. Con la
        # anchura completa, el recibo corto divergiría sin que el objeto cambiara.
        self.assertIs(verify(Recibo(slug=slug, ficha=corto), self.ns), OK)
        self.assertIs(verify(Recibo(slug=slug, ficha=completo), self.ns), OK)

        # Control negativo a la MISMA anchura declarada: un dígito cambiado. Un
        # caso que no puede diferir no es evidencia.
        otro = "0" if corto.h.digest[0] != "0" else "1"
        falso = _dataclasses.replace(
            corto, h=Hash(ALGORITMO, otro + corto.h.digest[1:], 16)
        )
        divergencia_ancho = verify(Recibo(slug=slug, ficha=falso), self.ns)
        self.assertIsInstance(divergencia_ancho, Divergencia)
        self.assertEqual(divergencia_ancho.campo, "h")
        _medicion(
            "verify divergencia a anchura declarada", divergencia_ancho.campo
        )

        # La ausencia del objeto no es una divergencia: es el error tipado.
        with self.assertRaises(ENOENT):
            _os.unlink(slug.texto, dir_fd=self.fd)
            verify(Recibo(slug=slug, ficha=sellado), self.ns)

        with self.assertRaises(ContratoViolado):
            verify(sellado, self.ns)

        _medicion("verify anchura declarada del recibo", 16)


if __name__ == "__main__":  # pragma: no cover
    _unittest.main()
