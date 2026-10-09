"""test_metrics.py — casos T-02 y T-10 más la autocerrazón de INV_ISOL (§5).

Motor declarado de la corrida:

    python3 -B -m unittest discover -s protocol-core/tests -v

Este archivo **no** vive en `src/`: §6 asigna `tests/` y §0.4(c) gobierna la
biblioteca, no sus pruebas. La resolución del paquete es relativa a `__file__`:
ninguna ruta absoluta se hornea.

Lecturas declaradas. Ninguna se hace pasar por el texto de SPEC.md:

  1. La tabla esperada de T-02 se escribe **explícita**, no derivada de la ley.
     Si se derivara de `|P_sep| = L + 1`, la prueba sería una tautología: la ley
     la hace cumplir `Particion.__post_init__` por construcción. Lo que puede
     diferir es la tabla de SPEC §7.1 contra la implementación —por ejemplo, si
     `partition` usara `splitlines()` los siete números serían otros—, así que
     se fijan los cinco enteros y las secuencias exactas.
  2. T-10 se mide en sus dos mitades y por eso se importa `_medir_descriptor`
     (privada). La mitad positiva se mide **por `ficha()`**, que es la interfaz
     publicada. La mitad negativa no se puede producir por `ficha()`: exige un
     descriptor ya consumido a medias, y `ficha()` siempre abre al principio. Se
     mide sobre la unidad que `ficha()` invoca —el enlace se verificó por
     lectura del fuente, no por medición: `_ficha_del_descriptor` →
     `_medir_descriptor`—.
  3. La lectura rasgada se provoca **sin carrera y sin hilo**: se leen 4 bytes
     del descriptor y se le deja el cursor movido. La unidad compara `st_size`
     contra lo leído DE ESE descriptor, no contra el tamaño del nombre; si
     reabriera el nombre, el cursor volvería a cero y el caso no enrojecería.
     De ahí que el mismo caso mida dos cosas: la comparación y la identidad del
     descriptor.
  4. La barrera de tipo se mide con tres objetos y un cuarto:
     (a) un directorio —si el orden fuera invertido, `open(O_RDONLY)` sobre un
     directorio **triunfa** en macOS y el error sería `EISDIR`, no `ELOOP`—;
     (b) un enlace simbólico a un objeto regular —`ELOOP` sólo si se comprueba
     el tipo antes de abrir o si se abre con `O_NOFOLLOW`—; (c) un enlace
     quebrado —si se abriera el nombre, el error sería `ENOENT`—; y (d) un FIFO.
     El FIFO es el único caso que mide el «sin intentar `open()`»: una apertura
     de lectura sobre un FIFO sin escritor **cuelga**, de modo que una
     implementación sin barrera no enrojecería, dejaría la corrida colgada —y
     una corrida que no termina no certifica nada—. Para que el caso sea seguro
     se sostienen un lector y un escritor del propio FIFO: así una apertura
     ajena no puede bloquear, y el defecto se ve como `Ficha` en vez de espera.
     Riesgo declarado y aceptado: la guarda es del archivo de pruebas, no del
     instrumento.
  5. INV_ISOL se mide sobre un subárbol recién hecho: la raíz de la suite
     contiene objetos de otros casos y un manifiesto sobre ella mediría ruido
     ajeno. Los objetos se crean con `reserve` (el escritor ya certificado), no
     con `open`, para que el manifiesto mida los mismos objetos que produce la
     biblioteca.
  6. La colación se mide en DOS unidades y por eso el caso está partido en dos.
     El volumen de la suite está declarado insensible al caso y `reserve`
     —correctamente— rechaza todo slug que no sea inyectivo bajo casefold
     (§2.1.3 · INV-9): el nombre que discrimina (`Z.txt` contra `a.txt`) no se
     puede crear en este volumen, y no es un defecto del instrumento sino una
     guarda suya. Por eso la mitad con sistema de archivos usa sólo nombres ya
     invariantes bajo casefold (mide el motor real: recorrido, exclusión de sí
     mismo, resúmenes, orden de bytes sobre rutas relativas completas), y la
     mitad DISCRIMINANTE —orden de bytes contra orden de `casefold`— se mide en
     memoria sobre `RutaRelativa`/`Manifiesto`, sin tocar el sistema de
     archivos. Medirla con nombres minúsculos habría sido una prueba que no
     puede diferir.
  7. Este archivo imprime lo medido con el prefijo `MEDICION |`. La corrida es
     el crudo, y un crudo que no puede diferir no es evidencia.

NO CUBIERTO por este archivo (lista cerrada): `attest()` no se mide aquí —su
cadena de recibos es materia de otra unidad—; el algoritmo distinto de `sha256`
y la anchura truncada no se ejercen; `ENAMETOOLONG` no se provoca; y el
peldaño `statx(STATX_BTIME)` de INV-7 sigue declarado NO IMPLEMENTADO, sin
simulación.
"""

from __future__ import annotations

import errno as _errno
import hashlib as _hashlib
import os as _os
import shutil as _shutil
import stat as _stat
import sys as _sys
import tempfile as _tempfile
import unittest as _unittest

_SRC = _os.path.join(
    _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), "src"
)
if _SRC not in _sys.path:
    _sys.path.insert(0, _SRC)

from protocol.atomic import reserve  # noqa: E402
from protocol.metrics import (  # noqa: E402
    _medir_descriptor,
    ficha,
    manifest,
    partition,
)
from protocol.types import (  # noqa: E402
    ALGORITMO,
    ConjuntoDeclarado,
    ContratoViolado,
    ELOOP,
    EntradaManifiesto,
    ErrorDecodificacion,
    FuenteT0,
    Hash,
    LecturaRasgada,
    Manifiesto,
    Namespace,
    RutaRelativa,
    Slug,
)

VOLUMEN = "suite-metrics-volumen"
VOLUMEN_ISO = "suite-metrics-volumen-iso"
VOLUMEN_SUB = "suite-metrics-volumen-sub"

SONDA_CASO_MENOR = ".suite-metrics-caso-a"
SONDA_CASO_MAYOR = ".suite-metrics-caso-A"

#: §7.1 — los siete flujos, la tabla esperada explícita.
#: `(|P_sep|, |P_lines|, L, fin)`.
CASOS_T02 = (
    (b"", 1, 0, 0, None),
    (b"a", 1, 1, 0, False),
    (b"a\n", 2, 1, 1, True),
    (b"a\nb", 2, 2, 1, False),
    (b"a\nb\n", 3, 2, 2, True),
    (b"\n", 2, 1, 1, True),
    (b"a\n\n", 3, 2, 2, True),
)

#: §7.1 — las dos secuencias exactas, escritas a mano.
#: `(flujo, P_sep, P_lines)`.
P_SEP_T02 = (
    (b"", ("",), ()),
    (b"a", ("a",), ("a",)),
    (b"a\n", ("a", ""), ("a",)),
    (b"a\nb", ("a", "b"), ("a", "b")),
    (b"a\nb\n", ("a", "b", ""), ("a", "b")),
    (b"\n", ("", ""), ("",)),
    (b"a\n\n", ("a", "", ""), ("a", "")),
)

#: Un texto SIN salto de línea cuyo código UTF-16 lleva el byte 0x0A dentro de
#: la unidad multibyte (U+0A41, Gurmukhi): el 0x0A es byte, no carácter.
TEXTO_CON_0A_INTERNO = "a\u0a41"
FLUJO_UTF16_CON_0A_INTERNO = (
    b"\xff\xfe"
    + "a".encode("utf-16-le")
    + "\u0a41".encode("utf-16-le")
)


def _medicion(etiqueta: str, valor: object) -> None:
    print("MEDICION | %s | %s" % (etiqueta, valor))


def _nombre_max(fd: int) -> int:
    """`NAME_MAX` del volumen, medido. Respaldo declarado: 255."""

    try:
        return int(_os.fpathconf(fd, "PC_NAME_MAX"))
    except (OSError, ValueError):
        return 255


def _sonda_caso_propia(fd_root: int) -> bool:
    """Sonda de caso de ESTE archivo: camino distinto, mismo motor (el kernel)."""

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


class _BaseNamespace(_unittest.TestCase):
    """Namespace efímero con sus parámetros medidos, no supuestos."""

    def setUp(self) -> None:
        self.raiz = _tempfile.mkdtemp(prefix="protocolo-suite-metrics-")
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

    def _sub_namespace(self, fd_raiz: int, volumen: str) -> Namespace:
        """Namespace de un subárbol. Hereda lo declarado para la raíz."""

        return Namespace(
            fd_root=fd_raiz,
            sensible_al_caso=self.sensible,
            nombre_max=self.nombre_max,
            motor_nacimiento=self.motor,
            sincronizacion_directorio=True,
            volumen=volumen,
        )


class TestParticion(_BaseNamespace):
    """§5 T-02 — INV_SPLIT y las proyecciones canónicas sobre los siete flujos."""

    def test_t02_los_siete_flujos_contra_la_tabla_explicita(self) -> None:
        for flujo, n_sep, n_lines, l, fin in CASOS_T02:
            particion = partition(flujo)
            self.assertEqual(
                len(particion.p_sep), n_sep, "|P_sep| de %r" % (flujo,)
            )
            self.assertEqual(
                len(particion.p_lines), n_lines, "|P_lines| de %r" % (flujo,)
            )
            self.assertEqual(particion.l, l, "L de %r" % (flujo,))
            self.assertEqual(particion.fin, fin, "fin de %r" % (flujo,))
            self.assertEqual(len(particion.p_sep), particion.l + 1)
            self.assertEqual(particion.vacio, (len(flujo) == 0))

            _medicion(
                "T-02 %r" % (flujo,),
                (len(particion.p_sep), len(particion.p_lines), particion.l, particion.fin),
            )

    def test_t02_las_secuencias_exactas(self) -> None:
        for flujo, esperado_sep, esperado_lines in P_SEP_T02:
            particion = partition(flujo)
            self.assertEqual(
                particion.p_sep, esperado_sep, "P_sep de %r" % (flujo,)
            )
            self.assertEqual(
                particion.p_lines, esperado_lines, "P_lines de %r" % (flujo,)
            )
            # La segunda proyección descarta SÓLO el campo vacío final: en
            # `b"a\n\n"` el campo vacío interior se conserva.

        _medicion("T-02 P_sep de los siete", tuple(p for _, p, _ in P_SEP_T02))
        _medicion("T-02 P_lines de los siete", tuple(q for _, _, q in P_SEP_T02))

    def test_t02_la_ley_de_p_lines_se_sostiene(self) -> None:
        for flujo, _, _, _, _ in CASOS_T02:
            particion = partition(flujo)
            if len(flujo) == 0:
                esperado = 0
            elif particion.fin:
                esperado = particion.l
            else:
                esperado = particion.l + 1
            self.assertEqual(len(particion.p_lines), esperado, "%r" % (flujo,))

    def test_t02_el_byte_no_es_el_caracter(self) -> None:
        # El mismo texto: en UTF-8 el 0x0A no aparece como byte, y en UTF-16 sí.
        en_utf8 = TEXTO_CON_0A_INTERNO.encode("utf-8")
        self.assertEqual(en_utf8.count(0x0A), 0)
        sin_salto = partition(en_utf8)
        self.assertEqual(len(sin_salto.p_sep), 1)
        self.assertEqual(sin_salto.l, 0)

        con_byte_0a = FLUJO_UTF16_CON_0A_INTERNO
        self.assertEqual(con_byte_0a.count(0x0A), 1)
        self.assertEqual(len(con_byte_0a.decode("utf-16")), 2)
        self.assertEqual(con_byte_0a.decode("utf-16").count("\n"), 0)

        with self.assertRaises(ContratoViolado) as contexto:
            partition(con_byte_0a, enc="utf-16")
        self.assertEqual(contexto.exception.__class__.__name__, "ContratoViolado")

        _medicion("T-02 utf-8 bytes 0x0A", en_utf8.count(0x0A))
        _medicion("T-02 utf-16 bytes 0x0A", con_byte_0a.count(0x0A))
        _medicion("T-02 utf-16 saltos de linea", con_byte_0a.decode("utf-16").count("\n"))

    def test_t02_lo_que_no_es_flujo_y_lo_que_no_decodifica(self) -> None:
        with self.assertRaises(ContratoViolado):
            partition("texto")  # type: ignore[arg-type]
        with self.assertRaises(ContratoViolado):
            partition(b"a\n", enc="")
        with self.assertRaises(ContratoViolado):
            partition(b"a\n", enc=None)  # type: ignore[arg-type]
        with self.assertRaises(ErrorDecodificacion):
            partition(b"\xff\xfe\xff", enc="utf-8")


class TestLecturaNoRasgada(_BaseNamespace):
    """§5 T-10 — INV-8 y la barrera de tipo antes de abrir."""

    def test_t10_ficha_mide_b_del_mismo_descriptor(self) -> None:
        slug = Slug("pieza-t10.bin")
        contenido = b"linea 1\nlinea 2\n"
        reserve(self.ns, slug, contenido)

        medida = ficha(self.ns, slug)
        st = _os.stat(slug.texto, dir_fd=self.fd, follow_symlinks=False)

        self.assertEqual(medida.b, len(contenido))
        self.assertEqual(medida.b, st.st_size)
        self.assertEqual(medida.l, contenido.count(0x0A))
        self.assertEqual(medida.i.ino, st.st_ino)
        self.assertEqual(medida.i.dev, st.st_dev)
        self.assertEqual(medida.h.algoritmo, ALGORITMO)
        self.assertEqual(medida.h.digest, _hashlib.sha256(contenido).hexdigest())
        self.assertEqual(medida.fin, True)
        self.assertIs(medida.vacio, False)

        _medicion("T-10 B de ficha", medida.b)
        _medicion("T-10 L de ficha", medida.l)
        _medicion("T-10 H de ficha", medida.h.digest)

    def test_t10_lectura_rasgada_se_declara_sin_carrera(self) -> None:
        slug = Slug("pieza-rasgada.bin")
        contenido = b"0123456789"
        reserve(self.ns, slug, contenido)

        fd = _os.open(slug.texto, _os.O_RDONLY, dir_fd=self.fd)
        try:
            parcial = _os.read(fd, 4)
            self.assertEqual(parcial, contenido[:4])
            with self.assertRaises(LecturaRasgada) as contexto:
                _medir_descriptor(fd)
        finally:
            _os.close(fd)

        rasgada = contexto.exception
        self.assertEqual(rasgada.campos.get("b"), len(contenido))
        self.assertEqual(rasgada.campos.get("leidos"), len(contenido) - 4)

        _medicion("T-10 rasgada b", rasgada.campos.get("b"))
        _medicion("T-10 rasgada leidos", rasgada.campos.get("leidos"))

    def test_t10_barrera_de_tipo_sobre_directorio_y_enlaces(self) -> None:
        _os.mkdir("directorio-t10", dir_fd=self.fd)
        _os.symlink("directorio-t10", "enlace-a-directorio-t10", dir_fd=self.fd)

        reserve(self.ns, Slug("destino-t10.bin"), b"destino regular\n")
        _os.symlink("destino-t10.bin", "enlace-t10", dir_fd=self.fd)
        _os.symlink("no-existe-t10", "quebrado-t10", dir_fd=self.fd)

        for nombre in (
            "directorio-t10",
            "enlace-a-directorio-t10",
            "enlace-t10",
            "quebrado-t10",
        ):
            with self.assertRaises(ELOOP) as contexto:
                ficha(self.ns, Slug(nombre))
            self.assertEqual(contexto.exception.errno_nombre, "ELOOP")
            _medicion("T-10 barrera %s" % (nombre,), contexto.exception.errno_nombre)

        # `ficha` sobre el destino regular SÍ devuelve ficha: no es que todo
        # enrojezca, es que el enlace no es un objeto regular.
        destino = ficha(self.ns, Slug("destino-t10.bin"))
        self.assertEqual(destino.b, len(b"destino regular\n"))

    def test_t10_barrera_antes_de_abrir_sobre_un_fifo(self) -> None:
        slug = Slug("fifo-t10")
        _os.mkfifo(slug.texto, 0o600, dir_fd=self.fd)

        # Guarda del archivo de pruebas (no del instrumento): se sostienen un
        # lector y un escritor del FIFO para que una apertura de lectura no
        # pueda colgar. El defecto, si lo hubiera, se ve como objeto medido en
        # vez de espera infinita.
        fd_lector = _os.open(
            slug.texto, _os.O_RDONLY | _os.O_NONBLOCK, dir_fd=self.fd
        )
        self.addCleanup(_os.close, fd_lector)
        fd_escritor = _os.open(slug.texto, _os.O_WRONLY, dir_fd=self.fd)
        self.addCleanup(_os.close, fd_escritor)

        with self.assertRaises(ELOOP) as contexto:
            ficha(self.ns, slug)
        self.assertEqual(contexto.exception.errno_nombre, "ELOOP")

        # El FIFO sigue siendo un FIFO: la barrera no lo consumió ni lo borró.
        st = _os.stat(slug.texto, dir_fd=self.fd, follow_symlinks=False)
        self.assertTrue(_stat.S_ISFIFO(st.st_mode))

        _medicion("T-10 barrera fifo", contexto.exception.errno_nombre)


class TestManifiestoDeterminista(_BaseNamespace):
    """§3.d INV_ISOL — el manifiesto no se incluye y ordena byte a byte.

    Dos unidades, dos casos. El primero toca el volumen (recorrido real,
    exclusión de sí mismo, resúmenes) con nombres invariantes bajo casefold; el
    segundo mide en memoria la colación, que es lo único que discrimina entre
    el orden de bytes y el de `casefold`, y que en este volumen no se puede
    provocar con un nombre real (§2.1.3 · INV-9).
    """

    def test_inv_isol_colacion_por_bytes_y_no_por_casefold(self) -> None:
        """El orden declarado es `C` (bytes UTF-8), no el de `casefold`.

        Ningún objeto del sistema de archivos entra en este caso: mide la ley
        de orden del tipo. El par que discrimina es `Z.txt` contra `a.txt`
        —bytes: `0x5A` antes que `0x61`; casefold: `a.txt` antes que `Z.txt`—,
        y es justo el par que `reserve` no deja crear aquí, porque el volumen
        no distingue caso y dos nombres que sólo difieran en caso serían un
        solo nombre.
        """
        mayor = RutaRelativa("Z.txt")
        menor = RutaRelativa("a.txt")

        self.assertEqual(mayor.clave_bytes, b"Z.txt")
        self.assertLess(mayor.clave_bytes, menor.clave_bytes)

        # El mismo slug es la razón por la que `reserve` lo rechazaría: su
        # clave de caso no es él mismo.
        self.assertEqual(Slug("Z.txt").clave_casefold, "z.txt")
        self.assertNotEqual(Slug("Z.txt").clave_casefold, Slug("Z.txt").texto)

        por_bytes = [ruta.texto for ruta in (mayor, menor)]
        por_casefold = [
            ruta.texto
            for ruta in sorted((mayor, menor), key=lambda r: r.texto.casefold())
        ]
        self.assertEqual(por_bytes, ["Z.txt", "a.txt"])
        self.assertEqual(por_casefold, ["a.txt", "Z.txt"])
        self.assertNotEqual(por_bytes, por_casefold)

        exclusion = ConjuntoDeclarado(
            slugs=(Slug(".manifiesto"),),
            motivo="el manifiesto no se incluye a si mismo (§3.d.3)",
        )
        conformes = (
            EntradaManifiesto(mayor, Hash(ALGORITMO, "0" * 64)),
            EntradaManifiesto(menor, Hash(ALGORITMO, "1" * 64)),
        )
        manifiesto = Manifiesto(
            entradas=conformes,
            algoritmo=ALGORITMO,
            anchura=None,
            exclusion=exclusion,
        )
        self.assertEqual([ruta.texto for ruta in manifiesto.rutas], por_bytes)

        # La ley se mide en las dos direcciones: el orden de bytes entra, el
        # orden de casefold no.
        with self.assertRaises(ContratoViolado) as contexto:
            Manifiesto(
                entradas=tuple(reversed(conformes)),
                algoritmo=ALGORITMO,
                anchura=None,
                exclusion=exclusion,
            )

        _medicion("INV_ISOL orden por bytes", tuple(por_bytes))
        _medicion("INV_ISOL orden por casefold", tuple(por_casefold))
        _medicion("INV_ISOL rechazo por orden invertido", contexto.exception.mensaje)

    def test_inv_isol_manifiesto_se_excluye_y_ordena_byte_a_byte(self) -> None:
        _os.mkdir("iso", dir_fd=self.fd)
        fd_iso = _os.open("iso", _os.O_RDONLY | _os.O_DIRECTORY, dir_fd=self.fd)
        self.addCleanup(_os.close, fd_iso)
        ns_iso = self._sub_namespace(fd_iso, VOLUMEN_ISO)

        _os.mkdir("sub", dir_fd=fd_iso)
        fd_sub = _os.open("sub", _os.O_RDONLY | _os.O_DIRECTORY, dir_fd=fd_iso)
        self.addCleanup(_os.close, fd_sub)
        ns_sub = self._sub_namespace(fd_sub, VOLUMEN_SUB)

        # Sólo nombres ya invariantes bajo casefold: es lo que el volumen
        # declarado admite (§2.1.3 · INV-9). La colación discriminante se mide
        # en el caso anterior, en memoria.
        contenidos = {
            "a.txt": b"la primera en orden de bytes\n",
            "b.txt": b"la segunda\n",
            "sub/c.txt": b"anidado\n",
            "z.txt": b"la ultima en orden de bytes\n",
            ".manifiesto": b"yo soy el manifiesto, no una entrada\n",
        }
        reserve(ns_iso, Slug("a.txt"), contenidos["a.txt"])
        reserve(ns_iso, Slug("b.txt"), contenidos["b.txt"])
        reserve(ns_iso, Slug("z.txt"), contenidos["z.txt"])
        reserve(ns_iso, Slug(".manifiesto"), contenidos[".manifiesto"])
        reserve(ns_sub, Slug("c.txt"), contenidos["sub/c.txt"])

        exclusion = ConjuntoDeclarado(
            slugs=(Slug(".manifiesto"),),
            motivo="el manifiesto no se incluye a si mismo (§3.d.3)",
        )
        self.assertTrue(exclusion.contiene(Slug(".manifiesto")))

        manifiesto = manifest(ns_iso, exclusion)

        rutas = [ruta.texto for ruta in manifiesto.rutas]
        self.assertEqual(rutas, ["a.txt", "b.txt", "sub/c.txt", "z.txt"])
        self.assertNotIn(".manifiesto", rutas)
        self.assertEqual(manifiesto.orden, "C")
        self.assertEqual(manifiesto.algoritmo, ALGORITMO)
        self.assertEqual(manifiesto.exclusion, exclusion)

        for entrada in manifiesto.entradas:
            self.assertEqual(
                entrada.h.digest, _hashlib.sha256(contenidos[entrada.ruta.texto]).hexdigest()
            )

        # La ruta relativa completa es la clave: `sub/c.txt` entra entre `b.txt`
        # y `z.txt` porque `s` (0x73) cae entre `b` (0x62) y `z` (0x7A), y el
        # separador no decide —se compara la cadena entera, no el último
        # componente—.
        claves = [ruta.clave_bytes for ruta in manifiesto.rutas]
        self.assertEqual(claves, sorted(claves))
        self.assertEqual(claves[0][:1], b"a")
        self.assertLess(b"b.txt", b"sub/c.txt")
        self.assertLess(b"sub/c.txt", b"z.txt")

        _medicion("INV_ISOL rutas del manifiesto", tuple(rutas))
        _medicion("INV_ISOL entradas", len(manifiesto.entradas))
        _medicion("INV_ISOL primera clave", claves[0])


if __name__ == "__main__":  # pragma: no cover
    _unittest.main()
