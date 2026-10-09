"""test_atomic.py — casos T-01 y T-09 sobre `protocol.atomic` (§5).

Motor declarado de la corrida:

    python3 -B -m unittest discover -s protocol-core/tests -v

Este archivo **no** vive en `src/`: §6 asigna `tests/` y §0.4(c) gobierna la
biblioteca, no sus pruebas. Aquí sí se usan `tempfile`, `shutil`, `os.mkdir` y
`os.symlink`. El namespace de prueba es efímero y se destruye en la limpieza.

Lecturas declaradas. Ninguna se hace pasar por el texto de SPEC.md:

  1. El encargo nombra `Handle`. `atomic.py` declara el mapa de nombres y
     `types.py` no tiene clase con ese nombre: `Handle` es `Reserva` (estado
     posterior al acto, no un descriptor vivo). Se mide sobre `Reserva` y se
     declara. «Descriptor sincronizado» se lee como `sellado is True` (la
     barrera `fsync`) más `sincronizacion_directorio` en `(True, ⊥)` —nunca
     `False`: un volumen que no sella se declara `⊥`—.
  2. Los cuatro parámetros del `Namespace` se **miden** antes de declararse
     (§2.4 · §8.3: lo que es parámetro no se supone): `nombre_max` por
     `os.fpathconf(fd, "PC_NAME_MAX")` —con `255` declarado como respaldo para
     volúmenes que no lo expongan—, `sensible_al_caso` por una sonda propia
     escrita en este archivo, y `motor_nacimiento` por la presencia real de
     `st_birthtime` en el `st` del descriptor raíz.
  3. `sonda_caso` NO se mide contra el `Namespace`: los dos salen de la misma
     medición y compararlos sería contarse dos veces. Se mide contra la sonda
     propia del punto 2 —dos CAMINOS de código distintos— y se declara que el
     motor es el mismo (el kernel): lo que se cruza son caminos, no motores.
  4. El objeto preexistente del control negativo se mide con `metrics.ficha()`
     —la misma capa que lo mide en producción— y **no** con una lectura de este
     archivo; el contenido se verifica además con un lector propio (`_leer`),
     para que la comprobación del contenido no sea circular con el `H` del
     instrumento.
  5. T-01 verifica que la colisión no alteró el recurso previo: `B`, `H` e `I`
     medidos antes y después de la segunda reserva deben coincidir, y el
     contenido debe ser el primero —no el segundo—.
  6. Este archivo imprime lo medido con el prefijo `MEDICION |`. La corrida es
     el crudo, y un crudo que no puede diferir no es evidencia.

NO CUBIERTO por este archivo (lista cerrada). El sellado del directorio no se
mide: se declara. La durabilidad frente a un corte de energía (T-11) no se puede
medir en proceso. `ENAMETOOLONG` y `ENOTSUP` no se provocan. La carrera real de
T-01 con dos procesos no se ejecuta: se mide la garantía que `O_EXCL` da
—la segunda apertura colapsa—, no la concurrencia. El peldaño
`statx(STATX_BTIME)` de INV-7 sigue declarado NO IMPLEMENTADO y no se simula.
"""

from __future__ import annotations

import errno as _errno
import hashlib as _hashlib
import os as _os
import shutil as _shutil
import sys as _sys
import tempfile as _tempfile
import unittest as _unittest

# Resolución del paquete relativa a ESTE archivo: ninguna ruta absoluta se
# hornea (§0.4.b aplicado a las pruebas por simetría, no por obligación).
_SRC = _os.path.join(
    _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), "src"
)
if _SRC not in _sys.path:
    _sys.path.insert(0, _SRC)

from protocol.atomic import (  # noqa: E402  (después del ajuste de `sys.path`)
    SLUG_SONDA_CASO_MAYOR,
    SLUG_SONDA_CASO_MENOR,
    SLUG_SONDA_EXCL,
    reserve,
    sonda_caso,
    sonda_excl,
)
from protocol.metrics import ficha  # noqa: E402
from protocol.types import (  # noqa: E402
    CertificadoCaso,
    CertificadoExclusividad,
    EEXIST,
    FuenteT0,
    Inodo,
    Namespace,
    Reserva,
    Slug,
    T0,
)

#: Etiqueta de volumen de la suite. Es una etiqueta legible, nunca una ruta
#: (§0.4.b): no empieza por `/` y no nombra el directorio real.
VOLUMEN = "suite-atomic-volumen"

#: Prefijo de la sonda de caso escrita AQUÍ. Los dos nombres difieren SÓLO en el
#: caso de la última letra: es lo único que el `stat` necesita ver.
SONDA_CASO_MENOR = ".suite-caso-menor-a"
SONDA_CASO_MAYOR = ".suite-caso-menor-A"


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

    Camino distinto al de `sonda_caso` —crea con `os.open`, consulta con
    `os.stat`— sobre el mismo motor, que es el kernel. La sonda no borra lo que
    no creó: sólo borra los dos nombres que ella abrió.
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


def _leer(fd_padre: int, nombre: str) -> bytes:
    """Lector propio de la prueba: no pasa por el instrumento (§lectura 4)."""

    fd = _os.open(nombre, _os.O_RDONLY, dir_fd=fd_padre)
    try:
        trozos = []
        while True:
            trozo = _os.read(fd, 1 << 20)
            if not trozo:
                break
            trozos.append(trozo)
        return b"".join(trozos)
    finally:
        _os.close(fd)


def _existe(fd_padre: int, nombre: str) -> bool:
    try:
        _os.stat(nombre, dir_fd=fd_padre, follow_symlinks=False)
        return True
    except OSError as exc:
        if exc.errno == _errno.ENOENT:
            return False
        raise


class _BaseNamespace(_unittest.TestCase):
    """Namespace efímero con sus cuatro parámetros medidos, no supuestos."""

    def setUp(self) -> None:
        self.raiz = _tempfile.mkdtemp(prefix="protocolo-suite-atomic-")
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


class TestReservaExclusiva(_BaseNamespace):
    """§5 T-01 — INV_EXCL: la segunda apertura colapsa y no trunca."""

    def test_t01_reserva_exclusiva_y_no_truncamiento(self) -> None:
        slug = Slug("ranura-01.bin")
        primero = b"ranura 01: contenido integro\r\ncon CR y LF\n"
        segundo = b"SEGUNDA ESCRITURA: no debe entrar\n"

        reserva = reserve(self.ns, slug, primero)
        self.assertIsInstance(reserva, Reserva)
        self.assertIs(reserva.sellado, True)
        self.assertIs(reserva.completa, True)
        self.assertIn(reserva.sincronizacion_directorio, (True, None))
        self.assertIsInstance(reserva.i, Inodo)
        self.assertIsInstance(reserva.t0, T0)
        self.assertEqual(reserva.slug, slug)

        antes = ficha(self.ns, slug)
        self.assertEqual(antes.b, len(primero))
        self.assertEqual(antes.i, reserva.i)
        self.assertEqual(
            antes.h.digest, _hashlib.sha256(primero).hexdigest()
        )

        with self.assertRaises(EEXIST) as contexto:
            reserve(self.ns, slug, segundo)
        colision = contexto.exception
        self.assertIsInstance(colision, EEXIST)
        self.assertEqual(colision.errno_nombre, "EEXIST")
        self.assertEqual(colision.campos.get("errno_numero"), _errno.EEXIST)

        despues = ficha(self.ns, slug)
        self.assertEqual(despues.b, antes.b)
        self.assertEqual(despues.i, antes.i)
        self.assertEqual(despues.h, antes.h)
        self.assertEqual(_leer(self.fd, slug.texto), primero)
        self.assertNotEqual(_leer(self.fd, slug.texto), segundo)

        _medicion("T-01 B de la reserva", antes.b)
        _medicion("T-01 I de la reserva", (antes.i.dev, antes.i.ino))
        _medicion("T-01 H de la reserva", antes.h.digest)
        _medicion("T-01 B tras la colision", despues.b)
        _medicion("T-01 I tras la colision", (despues.i.dev, despues.i.ino))
        _medicion("T-01 errno de la colision", colision.errno_nombre)


class TestSondasDeVolumen(_BaseNamespace):
    """§5 T-09 · INV-9 — los dos certificados, y el control negativo."""

    def test_t09_certificado_de_caso_contra_el_volumen_real(self) -> None:
        certificado = sonda_caso(self.ns)
        self.assertIsInstance(certificado, CertificadoCaso)
        self.assertIsInstance(certificado.sensible_al_caso, bool)
        self.assertEqual(certificado.volumen, VOLUMEN)

        propio = _sonda_caso_propia(self.fd)
        self.assertEqual(
            certificado.sensible_al_caso,
            propio,
            "el certificado del modulo y la sonda propia del archivo discrepan",
        )
        # El certificado se emite con los nombres de sonda ya borrados.
        for slug in (SLUG_SONDA_CASO_MENOR, SLUG_SONDA_CASO_MAYOR):
            self.assertFalse(_existe(self.fd, slug.texto))

        _medicion("T-09 sonda_caso certificado", certificado.sensible_al_caso)
        _medicion("T-09 sonda propia del archivo", propio)

    def test_t09_control_negativo_sonda_excl_no_borra_lo_que_no_creo(self) -> None:
        previo = b"objeto previo: la sonda no lo creo\n"

        ocupada = reserve(self.ns, SLUG_SONDA_EXCL, previo)
        self.assertIs(ocupada.sellado, True)

        antes = ficha(self.ns, SLUG_SONDA_EXCL)
        self.assertEqual(antes.b, len(previo))
        self.assertEqual(antes.i, ocupada.i)

        with self.assertRaises(EEXIST) as contexto:
            sonda_excl(self.ns)
        self.assertIsInstance(contexto.exception, EEXIST)
        self.assertEqual(contexto.exception.errno_nombre, "EEXIST")

        despues = ficha(self.ns, SLUG_SONDA_EXCL)
        self.assertEqual(despues.b, antes.b)
        self.assertEqual(despues.i, antes.i)
        self.assertEqual(despues.h, antes.h)
        self.assertEqual(_leer(self.fd, SLUG_SONDA_EXCL.texto), previo)

        # El objeto previo sigue ocupando su nombre: la sonda no lo liberó.
        self.assertTrue(_existe(self.fd, SLUG_SONDA_EXCL.texto))

        _medicion("T-09 negativo B del objeto previo", despues.b)
        _medicion("T-09 negativo I del objeto previo", (despues.i.dev, despues.i.ino))

        _os.unlink(SLUG_SONDA_EXCL.texto, dir_fd=self.fd)

    def test_t09_sonda_excl_certifica_atomicidad(self) -> None:
        certificado = sonda_excl(self.ns)
        self.assertIsInstance(certificado, CertificadoExclusividad)
        self.assertIs(certificado.atomico, True)
        self.assertEqual(certificado.volumen, VOLUMEN)

        # El nombre de sonda queda libre: el certificado se emite con la sonda
        # ya borrada.
        self.assertFalse(_existe(self.fd, SLUG_SONDA_EXCL.texto))

        _medicion("T-09 sonda_excl atomico", certificado.atomico)


if __name__ == "__main__":  # pragma: no cover
    _unittest.main()
