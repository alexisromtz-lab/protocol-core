"""test_ubicacion.py — la adjudicación por contenido, medida por sus falsadores.

Motor declarado de la corrida:

    python3 -B -m unittest discover -s tests

QUE MIDE. Que un manifiesto sellado se adjudique contra un árbol por
**contenido** y no por ruta, con cuatro estados exhaustivos y un testigo por
fila. El caso real que abrió esto: `SHA256SUMS_SELLO_A` de platino-labs daba
14/14 conformes por hash y 10/14 por ruta porque cuatro actas se mudaron a
`actas/` sin que un byte cambiara. El sello estaba intacto; el resolutor era lo
que había envejecido.

LO QUE ESTE ARCHIVO AÑADE A LA TESIS. Un artefacto que cambia de ruta no es el
único caso en que el digest sobrevive sin que la frontera se sostenga: si dos
artefactos **canjean** sus rutas, cada digest sigue existiendo una sola vez y un
esquema que sólo mire el contenido llamaría limpio a un intercambio. P-27 lo
mide y es la razón de que `intercambiada` exista separada de `reubicada`.

EL FIXTURE ES UN CASO DE CADA ESTADO, y está escrito a mano en
`examples/sello-de-muestra/MANIFIESTO.txt`. Los digests son los del sello y el
árbol es el de hoy: la diferencia entre los dos **es** el acto. No se generan en
la corrida, porque un fixture que se regenera no puede contradecir a su lector.

NO CUBIERTO (lista cerrada): la firma y el ancla —el acto no fecha—; el tiempo
de recorrido, que se publica como medición y no como umbral; y la corrida contra
el sello real de platino-labs, que es un acto externo por comando y no una
prueba de esta suite (una prueba que se salta cuando el árbol vecino no está
enseñaría a saltarse la puerta).
"""

from __future__ import annotations

import hashlib as _hashlib
import json as _json
import os as _os
import shutil as _shutil
import subprocess as _subprocess
import sys as _sys
import tempfile as _tempfile
import unittest as _unittest
import unittest.mock as _mock

_RAIZ = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
_SRC = _os.path.join(_RAIZ, "src")
if _SRC not in _sys.path:
    _sys.path.insert(0, _SRC)

from protocol.types import (  # noqa: E402
    ALGORITMO,
    ContratoViolado,
    Hash,
)
from protocol import ubicacion as _ubicacion  # noqa: E402
from protocol.ubicacion import (  # noqa: E402
    DIALECTO_ADMITIDO,
    Adjudicacion,
    EntradaDeclarada,
    EstadoDeEntrada,
    Indice,
    Juicio,
    Manifiesto,
    VeredictoDeUbicacion,
    adjudicar,
    indice_por_contenido,
    leer_manifiesto,
    leer_manifiesto_hash,
)

MUESTRA = _os.path.join(_RAIZ, "examples", "sello-de-muestra")

_A = "a" * 64
_B = "b" * 64
_C = "c" * 64
_D = "d" * 64


def _medicion(etiqueta: str, valor: object) -> None:
    print("MEDICION | %s | %s" % (etiqueta, valor))


def _sha256(datos: bytes) -> str:
    return _hashlib.sha256(datos).hexdigest()


def _h(digest: str) -> Hash:
    return Hash(algoritmo=ALGORITMO, digest=digest)


def _fila(ruta: str, digest: str) -> EntradaDeclarada:
    return EntradaDeclarada(ruta=ruta, h=_h(digest))


class TestLosCuatroEstados(_unittest.TestCase):
    """P-25 · el fixture escrito a mano: un caso de cada estado, y ninguna mezcla."""

    def setUp(self) -> None:
        with open(_os.path.join(MUESTRA, "MANIFIESTO.txt"), encoding="utf-8") as f:
            self.entradas = leer_manifiesto_hash(f.read(), origen="sello-de-muestra")
        self.acto = adjudicar(self.entradas, self._indice())
        self.juicios = {j.declarada: j for j in self.acto.juicios}

    def _indice(self) -> Indice:
        rutas = []
        for base, _dirs, archivos in _os.walk(MUESTRA):
            for nombre in archivos:
                completa = _os.path.join(base, nombre)
                relativa = _os.path.relpath(completa, MUESTRA).replace(_os.sep, "/")
                rutas.append(relativa)
        return indice_por_contenido(MUESTRA, sorted(rutas))

    def test_p25_un_caso_de_cada_estado(self) -> None:
        _medicion("P-25 acto", self.acto.resumen())
        self.assertEqual(1, self.acto.cuenta(EstadoDeEntrada.CONFORME))
        self.assertEqual(3, self.acto.cuenta(EstadoDeEntrada.REUBICADO))
        self.assertEqual(1, self.acto.cuenta(EstadoDeEntrada.DIVERGE))
        self.assertEqual(1, self.acto.cuenta(EstadoDeEntrada.OPACO))
        self.assertEqual(EstadoDeEntrada.CONFORME, self.juicios["acta-uno.md"].estado)
        for linea in self.acto.testigos():
            _medicion("P-25 testigo", linea)

    def test_p25_la_ruta_redactada_no_es_una_perdida(self) -> None:
        """Discriminador: el digest de la fila opaca NO está en el árbol.

        Un lector que ignorara la redacción llamaría `diverge` a esa fila y
        diría que el verificador del sello se perdió. No se perdió: el manifiesto
        no escribe dónde está. La diferencia entre «no está» y «no se puede leer»
        es todo el punto.
        """

        opaca = self.juicios["<expediente-de-sellos>/VERIFICAR_SELLO.sh"]
        self.assertEqual(EstadoDeEntrada.OPACO, opaca.estado)
        self.assertEqual(0, opaca.multiplicidad)
        self.assertIsNone(opaca.medido)
        self.assertIn("redactada", opaca.motivo)

    def test_p25_la_reubicacion_lleva_testigo_y_la_ruta_vaciada(self) -> None:
        dos = self.juicios["acta-dos.md"]
        self.assertEqual(EstadoDeEntrada.REUBICADO, dos.estado)
        self.assertEqual("actas/acta-dos.md", dos.observada)
        self.assertEqual(1, dos.multiplicidad)
        self.assertIsNone(dos.medido)
        self.assertTrue(dos.vaciada)

    def test_p25_la_alteracion_nombra_de_que_lado_fallo(self) -> None:
        tres = self.juicios["acta-tres.md"]
        self.assertEqual(EstadoDeEntrada.DIVERGE, tres.estado)
        self.assertIsNotNone(tres.medido)
        self.assertNotEqual(tres.medido, tres.h.digest)
        self.assertIn("bytes alterados", " ".join(self.acto.testigos()))

    def test_p25_el_peor_hallazgo_manda(self) -> None:
        self.assertEqual(VeredictoDeUbicacion.DIVERGENTE, self.acto.veredicto)
        self.assertFalse(self.acto.conforme)


class TestMultiplicidad(_unittest.TestCase):
    """P-26 · el digest en k rutas se publica con su k, y no se elige por el lector."""

    def test_p26_duplicado_publica_k(self) -> None:
        indice = Indice.desde_mapa({"nueva/a.md": _A, "nueva/copia/a.md": _A})
        acto = adjudicar((_fila("actas/a.md", _A),), indice)
        juicio = acto.juicios[0]
        _medicion("P-26 duplicado", (juicio.estado.value, juicio.observada, juicio.multiplicidad))
        self.assertEqual(EstadoDeEntrada.REUBICADO, juicio.estado)
        self.assertEqual(2, juicio.multiplicidad)
        self.assertEqual(1, len(acto.reubicados))
        self.assertEqual(VeredictoDeUbicacion.REUBICADA, acto.veredicto)

    def test_p26_conforme_tambien_publica_k(self) -> None:
        indice = Indice.desde_mapa({"a.md": _A, "copia/a.md": _A})
        juicio = adjudicar((_fila("a.md", _A),), indice).juicios[0]
        self.assertEqual(EstadoDeEntrada.CONFORME, juicio.estado)
        self.assertEqual(2, juicio.multiplicidad)

    def test_p26_el_testigo_nombra_los_k_caminos(self) -> None:
        """Publicar k en el dato y elegir un destino en el texto es publicar cero.

        Caso real (jq 1.7.1, medido el 2026-11-24): el release trae tres pares de
        binarios byte-idénticos, así que al mover `jq-linux-amd64` a `sub/` el
        testigo nombraba `jq-linux64` — una ruta que nunca se movió y que ya
        estaba declarada. El veredicto era correcto; el destino era inventado.
        """

        indice = Indice.desde_mapa({"nueva/a.md": _A, "nueva/copia/a.md": _A})
        acto = adjudicar((_fila("actas/a.md", _A),), indice)
        juicio = acto.juicios[0]
        self.assertEqual(("nueva/a.md", "nueva/copia/a.md"), juicio.observadas)
        self.assertEqual(
            ("reubicado actas/a.md -> 2 caminos: nueva/a.md, nueva/copia/a.md (ruta vaciada)",),
            acto.testigos(),
        )

    def test_p26_un_testigo_con_k_no_admite_un_solo_camino(self) -> None:
        with self.assertRaises(ContratoViolado):
            Juicio(
                declarada="actas/a.md",
                h=Hash("sha256", _A),
                estado=EstadoDeEntrada.REUBICADO,
                observada="nueva/a.md",
                observadas=("nueva/a.md",),
                multiplicidad=2,
            )


class TestIntercambio(_unittest.TestCase):
    """P-27 · el hallazgo que el esquema «sólo contenido» no puede ver."""

    def test_p27_dos_artefactos_canjean_sus_rutas(self) -> None:
        """Cada digest sigue existiendo una vez. La frontera está rota igual."""

        indice = Indice.desde_mapa({"a.md": _B, "b.md": _A})
        acto = adjudicar((_fila("a.md", _A), _fila("b.md", _B)), indice)
        _medicion("P-27 intercambio", acto.resumen())
        self.assertEqual(2, acto.cuenta(EstadoDeEntrada.REUBICADO))
        for juicio in acto.reubicados:
            self.assertFalse(juicio.vaciada, "la ruta declarada no quedó vacía")
            self.assertTrue(juicio.ocupante_declarado, "la ocupó otro artefacto sellado")
        self.assertEqual(VeredictoDeUbicacion.INTERCAMBIADA, acto.veredicto)
        self.assertFalse(acto.conforme)

    def test_p27_un_byte_despues_de_mover_es_divergencia(self) -> None:
        """Mover sin cambiar es reubicación; mover y tocar es pérdida.

        Sin este caso, `reubicado` podría implementarse buscando el digest en
        cualquier parte y llamar reubicado a un archivo que ya no es el sellado.
        """

        indice = Indice.desde_mapa({"actas/a.md": _D})
        acto = adjudicar((_fila("a.md", _A),), indice)
        self.assertEqual(EstadoDeEntrada.DIVERGE, acto.juicios[0].estado)
        self.assertEqual(VeredictoDeUbicacion.DIVERGENTE, acto.veredicto)

    def test_p27_un_intruso_no_declarado_ocupa_la_ruta(self) -> None:
        """Caso real: jq 1.7.1 trae tres pares de binarios byte-idénticos.

        Mutar un byte de `jq-linux64` deja su digest vivo en su gemelo, así que
        la fila no es pérdida: es una ruta suplantada. Decir `intercambiada`
        afirmaría un canje que no ocurrió (nadie ocupó la otra ruta con el
        digest de esta) y decir `reubicada` sería un falso verde.
        """

        indice = Indice.desde_mapa({"a.md": _C, "actas/a.md": _A})
        acto = adjudicar((_fila("a.md", _A),), indice)
        juicio = acto.juicios[0]
        self.assertEqual(EstadoDeEntrada.REUBICADO, juicio.estado)
        self.assertFalse(juicio.vaciada)
        self.assertFalse(juicio.ocupante_declarado)
        self.assertTrue(juicio.suplantada)
        self.assertFalse(juicio.canje)
        self.assertEqual(VeredictoDeUbicacion.SUPLANTADA, acto.veredicto)
        self.assertNotEqual(VeredictoDeUbicacion.INTERCAMBIADA, acto.veredicto)
        self.assertFalse(acto.conforme)
        self.assertEqual(
            ("reubicado a.md -> actas/a.md (ruta ocupada por bytes no declarados)",),
            acto.testigos(),
        )


class TestOrdenDelVeredicto(_unittest.TestCase):
    """P-28 · el orden es declarado, total, y no se puede negociar por conveniencia."""

    def test_p28_opaco_no_se_lee_como_benigno(self) -> None:
        indice = Indice.desde_mapa({"actas/a.md": _A})
        entradas = (
            _fila("a.md", _A),
            EntradaDeclarada(ruta="<boveda>/x.sh", h=_h(_B), motivo="ruta redactada"),
        )
        acto = adjudicar(entradas, indice)
        _medicion("P-28 opaco+reubicado", acto.resumen())
        self.assertEqual(VeredictoDeUbicacion.NO_MEDIDA, acto.veredicto)
        self.assertFalse(acto.conforme)

    def test_p28_divergencia_manda_sobre_el_intercambio(self) -> None:
        indice = Indice.desde_mapa({"a.md": _B, "b.md": _A})
        entradas = (_fila("a.md", _A), _fila("b.md", _B), _fila("c.md", _C))
        self.assertEqual(VeredictoDeUbicacion.DIVERGENTE, adjudicar(entradas, indice).veredicto)

    def test_p28_suplantacion_manda_sobre_el_intercambio(self) -> None:
        """Las dos violan la frontera; la suplantación además desconoce qué hay."""

        indice = Indice.desde_mapa({"a.md": _C, "actas/a.md": _A, "b.md": _A, "actas/b.md": _B})
        entradas = (_fila("a.md", _A), _fila("b.md", _B))
        acto = adjudicar(entradas, indice)
        _medicion("P-28 suplantada+canje", acto.resumen())
        self.assertEqual(VeredictoDeUbicacion.SUPLANTADA, acto.veredicto)

    def test_p28_sin_filas_no_es_intacta(self) -> None:
        vacia = Adjudicacion(juicios=())
        self.assertEqual(VeredictoDeUbicacion.NO_MEDIDA, vacia.veredicto)
        self.assertFalse(vacia.conforme)

    def test_p28_todo_conforme_es_intacta_y_conforme(self) -> None:
        indice = Indice.desde_mapa({"a.md": _A, "b.md": _B})
        acto = adjudicar((_fila("a.md", _A), _fila("b.md", _B)), indice)
        self.assertEqual(VeredictoDeUbicacion.INTACTA, acto.veredicto)
        self.assertTrue(acto.conforme)
        self.assertEqual((), acto.testigos())

    def test_p28_un_juicio_sin_testigo_no_se_construye(self) -> None:
        with self.assertRaises(ContratoViolado):
            Juicio(declarada="a.md", h=_h(_A), estado=EstadoDeEntrada.REUBICADO, multiplicidad=1)
        with self.assertRaises(ContratoViolado):
            Juicio(declarada="a.md", h=_h(_A), estado=EstadoDeEntrada.OPACO)


class TestLectorDelManifiesto(_unittest.TestCase):
    """P-29 · lo mal formado se rechaza; lo redactado se mide. No se confunden."""

    def test_p29_rechaza_ruta_que_escapa(self) -> None:
        with self.assertRaises(ContratoViolado):
            leer_manifiesto_hash("%s  ../../etc/passwd\n" % _A)

    def test_p29_rechaza_digest_mal_formado_y_ruta_repetida(self) -> None:
        with self.assertRaises(ContratoViolado):
            leer_manifiesto_hash("a" * 63 + "  a.md\n")
        with self.assertRaises(ContratoViolado):
            leer_manifiesto_hash("%s  a.md\n%s  a.md\n" % (_A, _B))

    def test_p29_acepta_marcador_binario_y_comentarios(self) -> None:
        entradas = leer_manifiesto_hash("# cabecera\n\n%s *actas/a.md\n" % _A)
        self.assertEqual(1, len(entradas))
        self.assertEqual("actas/a.md", entradas[0].ruta)
        self.assertFalse(entradas[0].opaca)

    def test_p29_una_ruta_con_espacio_no_es_opaca_es_inadmisible(self) -> None:
        """La redacción es exactamente `<`/`>`: un byte fuera del alfabeto se rechaza."""

        with self.assertRaises(ContratoViolado):
            leer_manifiesto_hash("%s  acta con espacio.md\n" % _A)

    def test_p29_manifiesto_vacio_no_es_un_acto(self) -> None:
        with self.assertRaises(ContratoViolado):
            leer_manifiesto_hash("# solo cabecera\n")


class TestDialectoDelManifiesto(_unittest.TestCase):
    """P-33 · el dialecto del manifiesto es una entrada, y se declara.

    Medido el 2026-11-24 contra cinco manifiestos públicos reales: el lector
    admitía uno (jq 1.7.1), rechazaba el instalador de Debian con el síntoma
    «componente no admisible como slug» y nombraba OpenBSD y npm como si fueran
    líneas rotas. Un manifiesto no es texto abstracto — es una gramática, y una
    gramática no declarada reabre la dependencia de observador por la puerta de
    la evidencia: mismo árbol, dos lectores, dos veredictos, los dos honestos.
    """

    #: Dos filas transcritas del `SHA256SUMS` del instalador de Debian
    #: (espejo estable, 2026-11-24). No se descargan en la corrida: la prueba
    #: mide el lector, no la red.
    DEBIAN = (
        "3a9f1b529229024126b1a025a66262d5af28212bac4d5fe4ec15b664e442b646  ./MANIFEST\n"
        "38e90781622290b5606aeb34dcf89c1dad60f09ccec161754afcf6f0d51fc3f2  ./cdrom/debian-cd_info.tar.gz\n"
    )

    def test_p33_el_prefijo_explicito_se_normaliza_y_se_cuenta(self) -> None:
        manifiesto = leer_manifiesto(self.DEBIAN, "debian")
        _medicion("P-33 Debian", (len(manifiesto.filas), manifiesto.prefijadas))
        self.assertEqual(
            ("MANIFEST", "cdrom/debian-cd_info.tar.gz"), tuple(f.ruta for f in manifiesto.filas)
        )
        self.assertEqual(2, manifiesto.prefijadas)
        self.assertEqual(DIALECTO_ADMITIDO, manifiesto.dialecto)

    def test_p33_el_prefijo_no_blanquea_una_huida(self) -> None:
        """`./../etc/passwd` no es otra ortografía: sigue saliendo del árbol."""

        with self.assertRaises(ContratoViolado):
            leer_manifiesto("%s  ./../etc/passwd\n" % _A)

    def test_p33_un_dialecto_ajeno_se_nombra_al_rechazarlo(self) -> None:
        casos = (
            ("SHA256 (BOOTX64.EFI) = " + _A, "BSD tradicional"),
            ("sha512-" + "A" * 86 + "==", "SRI base64"),
            ("%s actas/a.md" % _A, "un solo espacio"),
        )
        for linea, nombre in casos:
            with self.subTest(dialecto=nombre):
                with self.assertRaises(ContratoViolado) as caja:
                    leer_manifiesto(linea, nombre)
                _medicion("P-33 rechazo", str(caja.exception))
                self.assertIn("dialecto no admitido", str(caja.exception))
                self.assertIn(nombre, str(caja.exception))

    def test_p33_sin_prefijos_se_declara_cero(self) -> None:
        """`0` prefijadas es una medición; el contrato de `leer_manifiesto_hash` no cambia."""

        self.assertEqual(0, leer_manifiesto("%s *actas/a.md\n" % _A).prefijadas)
        self.assertEqual(
            (("actas/a.md", _A),),
            tuple((f.ruta, f.h.digest) for f in leer_manifiesto_hash("%s *actas/a.md\n" % _A)),
        )

    def test_p33_la_cuenta_de_prefijos_no_excede_las_filas(self) -> None:
        with self.assertRaises(ContratoViolado):
            Manifiesto((_fila("a.md", _A),), DIALECTO_ADMITIDO, 2)
        with self.assertRaises(ContratoViolado):
            Manifiesto((_fila("a.md", _A),), "", 0)


class TestIndice(_unittest.TestCase):
    """P-30 · el universo se declara: lo que no se indexa se publica."""

    def test_p30_enlace_y_directorio_se_omiten_y_se_publican(self) -> None:
        with _tempfile.TemporaryDirectory() as raiz:
            with open(_os.path.join(raiz, "a.md"), "wb") as f:
                f.write(b"contenido a\n")
            _os.mkdir(_os.path.join(raiz, "dir"))
            _os.symlink("a.md", _os.path.join(raiz, "enlace.md"))
            indice = indice_por_contenido(raiz, ("a.md", "dir", "enlace.md", "no-existe.md"))
            _medicion("P-30 indice", (indice.leidas, indice.omitidas))
            self.assertEqual(1, indice.leidas)
            self.assertEqual(("dir", "enlace.md", "no-existe.md"), indice.omitidas)
            self.assertEqual(("a.md",), indice.rutas_con(indice.digest_en("a.md") or ""))

    def test_p30_la_raiz_inexistente_no_es_un_universo_vacio(self) -> None:
        with self.assertRaises(ContratoViolado):
            indice_por_contenido("/no/existe/esta/raiz", ("a.md",))


class TestLagunaDelUniverso(_unittest.TestCase):
    """P-31 · un universo ciego no produce reubicaciones: produce lagunas.

    Falsador medido, no supuesto. Contra el sello A real de `platino-labs`,
    con universo `git ls-files`, el acto reportó **14 reubicados, 0
    conformes**; con universo de disco, **10 conformes + 4 reubicados**. La
    diferencia eran 10 rutas que existen en disco y que git no versiona:
    el universo barato no las miró y la adjudicación lo leyó como "se
    movieron". Un "se movió" que sólo significa "no lo busqué" es un falso
    hallazgo en la dirección peligrosa —afirma que la frontera cambió donde
    nadie midió—, y por eso la ruta sondeada sale `OPACO` y no `REUBICADO`.
    """

    def test_p31_lo_no_indexado_y_presente_no_se_lee_como_reubicado(self) -> None:
        with _tempfile.TemporaryDirectory() as raiz:
            with open(_os.path.join(raiz, "acta.md"), "wb") as f:
                f.write(b"bytes sellados\n")
            _os.mkdir(_os.path.join(raiz, "copia"))
            with open(_os.path.join(raiz, "copia", "acta.md"), "wb") as f:
                f.write(b"bytes sellados\n")

            declarada = EntradaDeclarada("acta.md", _h(_sha256(b"bytes sellados\n")))

            # Universo ciego a `acta.md`: sólo ve la copia. El digest está, así
            # que sin sondear esto sería un `REUBICADO` limpio.
            ciego = indice_por_contenido(raiz, ("copia/acta.md",))
            sin_sonda = adjudicar((declarada,), ciego)
            _medicion("P-31 sin sonda", sin_sonda.veredicto.value)
            self.assertEqual(EstadoDeEntrada.REUBICADO, sin_sonda.juicios[0].estado)

            sondeado = indice_por_contenido(raiz, ("copia/acta.md",), ("acta.md",))
            _medicion("P-31 fuera del universo", sondeado.fuera_del_universo)
            self.assertEqual(("acta.md",), sondeado.fuera_del_universo)

            con_sonda = adjudicar((declarada,), sondeado)
            _medicion("P-31 con sonda", con_sonda.resumen())
            self.assertEqual(EstadoDeEntrada.OPACO, con_sonda.juicios[0].estado)
            self.assertIn("no la indexa", con_sonda.juicios[0].motivo)
            self.assertEqual(VeredictoDeUbicacion.NO_MEDIDA, con_sonda.veredicto)
            # La ruta existe: la laguna es del universo, no del objeto.
            self.assertFalse(con_sonda.conforme)

    def test_p31_la_sonda_no_inventa_rutas_ausentes(self) -> None:
        with _tempfile.TemporaryDirectory() as raiz:
            sondeado = indice_por_contenido(raiz, (), ("no-existe.md",))
            self.assertEqual((), sondeado.fuera_del_universo)
            self.assertEqual(0, sondeado.leidas)


#: Cota de la página del acto de sello, medida sobre el acto real del
#: 2026-11-24: 59 líneas y 1 911 bytes con 6 filas declaradas (5 en `entradas`
#: y una redactada) y 4 referencias de código. Creció una línea desde 58/1 825
#: porque el recibo pasó a declarar el dialecto del manifiesto (P-33): es más
#: ancha que las otras dos porque cada fila cuesta 4 líneas, y se declara aparte
#: para que una cota no mida el acto que la escribió.
COPTA_SELLO_LINEAS = 62
COPTA_SELLO_BYTES = 2000


class TestActoDeSello(_unittest.TestCase):
    """P-32 · el cuarto acto: el recibo de la adjudicación, y su veredicto derivado.

    La página congelada pertenece a la fixture `examples/sello-de-muestra`, que
    tiene un caso de cada uno de los cuatro estados. Por eso su veredicto es
    `no_conforme`: si dijera `conforme` mientras su propia salida dice
    `divergente`, el recibo sería el falso verde que el acto existe para
    impedir. Ese defecto existió en el emisor y lo mató esta prueba.
    """

    PAGINA = _os.path.join(_RAIZ, "examples", "predicado-sello.json")
    SALIDA = _os.path.join(_RAIZ, "examples", "veredicto-sello.txt")

    def test_p32_la_pagina_del_sello_cabe_y_declara_su_universo(self) -> None:
        with open(self.PAGINA, "r", encoding="utf-8") as flujo:
            texto = flujo.read()
        cuerpo = _json.loads(texto)
        lineas = len(texto.splitlines())
        bytes_ = len(texto.encode("utf-8"))
        _medicion("P-32 página del sello", (lineas, bytes_))
        _medicion("P-32 referencias del sello", (len(cuerpo["entradas"]), len(cuerpo["codigo"])))
        self.assertLessEqual(lineas, COPTA_SELLO_LINEAS)
        self.assertLessEqual(bytes_, COPTA_SELLO_BYTES)

        with open(self.SALIDA, "rb") as flujo:
            salida = flujo.read()
        self.assertEqual(cuerpo["salida"]["sha256"], _sha256(salida))

        # El universo es parte de la afirmación: una página sin denominador
        # publica un veredicto sin población.
        lineas_salida = salida.decode("utf-8").splitlines()
        self.assertTrue(lineas_salida[0].startswith("universo | "), lineas_salida[0])
        self.assertIn("fuera del universo", lineas_salida[0])

        # La laguna declarada: la fila redactada no viaja en `entradas`, y la
        # diferencia está publicada en vez de escondida.
        self.assertEqual(5, len(cuerpo["entradas"]))
        lagunas = cuerpo["entorno"]["no_medido"]
        self.assertTrue(any("redactada" in laguna for laguna in lagunas), lagunas)
        # El dialecto del manifiesto es una entrada, y el recibo la declara:
        # sin esta fila, dos lectores honestos firman veredictos incomparables.
        self.assertTrue(any("dialecto del manifiesto" in laguna for laguna in lagunas), lagunas)

        # El veredicto se deriva de la adjudicación que la salida publica.
        ultima = lineas_salida[1]
        _medicion("P-32 adjudicación declarada", ultima)
        self.assertIn("-> divergente", ultima)
        self.assertEqual("no_conforme", cuerpo["veredicto"])

    def test_p32_el_acto_reproduce_su_pagina(self) -> None:
        corrida = _subprocess.run(
            [_sys.executable, "-B", _os.path.join(_RAIZ, "examples", "verificar_sello.py"), "--check"],
            cwd=_RAIZ,
            stdout=_subprocess.PIPE,
            stderr=_subprocess.STDOUT,
            check=False,
        )
        crudo = corrida.stdout.decode("utf-8", "replace")
        _medicion("P-32 RC del acto", corrida.returncode)
        self.assertEqual(0, corrida.returncode, crudo)
        self.assertIn("REPRODUCE", crudo)


class TestLagunaYNoPerdida(_unittest.TestCase):
    """P-34 · la ruta que el universo no miró no se acusa de perdida.

    El orden de las comprobaciones en `adjudicar` **es** la regla: mientras la
    guarda de `fuera_del_universo` vivió dentro de la rama de candidatas, una
    ruta que existía en disco y que el índice no tenía daba `DIVERGE` con
    `medido=None` —"ausente"—, que es acusar al artefacto de una pérdida que el
    instrumento nunca midió. `DEFAULT NO_MEDIDO`: no haberlo leído no es un cero.
    """

    def setUp(self) -> None:
        self.tmp = _tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.raiz = self.tmp.name

    def _escribir(self, ruta: str, contenido: bytes) -> str:
        completa = _os.path.join(self.raiz, *ruta.split("/"))
        carpeta = _os.path.dirname(completa)
        if carpeta and not _os.path.isdir(carpeta):
            _os.makedirs(carpeta)
        with open(completa, "wb") as flujo:
            flujo.write(contenido)
        return _sha256(contenido)

    def test_p34_sin_sonda_la_ruta_no_indexada_se_lee_como_ausente(self) -> None:
        """El discriminador: sin `sondear`, el mismo árbol sí produce la acusación."""

        digest = self._escribir("acta.md", b"acta")
        indice = indice_por_contenido(self.raiz, ())
        acto = adjudicar((_fila("acta.md", digest),), indice)
        _medicion("P-34 sin sonda", (acto.resumen(), indice.fuera_del_universo))
        self.assertEqual(EstadoDeEntrada.DIVERGE, acto.juicios[0].estado)
        self.assertEqual(VeredictoDeUbicacion.DIVERGENTE, acto.veredicto)

    def test_p34_con_sonda_la_laguna_del_universo_es_opaca(self) -> None:
        digest = self._escribir("acta.md", b"acta")
        indice = indice_por_contenido(self.raiz, (), sondear=("acta.md",))
        acto = adjudicar((_fila("acta.md", digest),), indice)
        juicio = acto.juicios[0]
        _medicion("P-34 con sonda", (juicio.estado.value, juicio.motivo))
        self.assertEqual(EstadoDeEntrada.OPACO, juicio.estado)
        self.assertIn("no la indexa", juicio.motivo)
        self.assertEqual(0, acto.cuenta(EstadoDeEntrada.DIVERGE))
        self.assertEqual(VeredictoDeUbicacion.NO_MEDIDA, acto.veredicto)

    def test_p34_la_laguna_manda_aunque_el_digest_este_en_otra_ruta(self) -> None:
        """Que los bytes aparezcan en otro sitio no convierte una no-medición en reubicación."""

        digest = self._escribir("acta.md", b"acta")
        self._escribir("copia/acta.md", b"acta")
        indice = indice_por_contenido(self.raiz, ("copia/acta.md",), sondear=("acta.md",))
        acto = adjudicar((_fila("acta.md", digest),), indice)
        juicio = acto.juicios[0]
        _medicion("P-34 laguna con copia", (juicio.estado.value, juicio.multiplicidad, acto.veredicto.value))
        self.assertEqual(EstadoDeEntrada.OPACO, juicio.estado)
        self.assertEqual(1, juicio.multiplicidad)
        self.assertEqual(0, acto.cuenta(EstadoDeEntrada.REUBICADO))
        self.assertEqual(VeredictoDeUbicacion.NO_MEDIDA, acto.veredicto)


class TestLecturaInestable(_unittest.TestCase):
    """P-35 · un archivo que cambia mientras se lee no produce veredicto sobre sus bytes.

    El digest de una lectura que atraviesa una escritura no es el digest de
    ningún estado del archivo: es un híbrido que nunca existió entero. Emitirlo
    acusaría al artefacto de una alteración ocurrida en el instrumento, y
    callarlo lo haría pasar por conforme.
    """

    def setUp(self) -> None:
        self.tmp = _tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.raiz = self.tmp.name
        with open(_os.path.join(self.raiz, "acta.md"), "wb") as flujo:
            flujo.write(b"acta")

    def _fstat_que_crece(self):
        real = _os.fstat
        vistas = []

        def falso(descriptor):
            actual = real(descriptor)
            vistas.append(actual)
            if len(vistas) == 1:
                return actual
            return _os.stat_result(
                (
                    actual.st_mode,
                    actual.st_ino,
                    actual.st_dev,
                    1,
                    0,
                    0,
                    actual.st_size + 1,
                    0,
                    0,
                    0,
                )
            )

        return falso

    def test_p35_la_medicion_inestable_no_devuelve_digest(self) -> None:
        completa = _os.path.join(self.raiz, "acta.md")
        falso = self._fstat_que_crece()
        with _mock.patch.object(_ubicacion.os, "fstat", falso):
            leido = _ubicacion._digest_de_archivo(completa)
        _medicion("P-35 lectura inestable", leido)
        self.assertIsNone(leido)

    def test_p35_el_indice_publica_la_ruta_inestable(self) -> None:
        digest = _sha256(b"acta")
        falso = self._fstat_que_crece()
        with _mock.patch.object(_ubicacion.os, "fstat", falso):
            indice = indice_por_contenido(self.raiz, ("acta.md",), sondear=("acta.md",))
        _medicion("P-35 indice", (indice.inestables, dict(indice.por_ruta)))
        self.assertEqual(("acta.md",), indice.inestables)
        self.assertEqual({}, dict(indice.por_ruta))
        acto = adjudicar((_fila("acta.md", digest),), indice)
        juicio = acto.juicios[0]
        # El motivo del instrumento manda sobre el del universo: la ruta está
        # en los dos conjuntos y lo que hay que publicar es por qué no se midió.
        self.assertEqual(EstadoDeEntrada.OPACO, juicio.estado)
        self.assertIn("no cerró estable", juicio.motivo)
        self.assertEqual(VeredictoDeUbicacion.NO_MEDIDA, acto.veredicto)

    def test_p35_una_lectura_estable_sigue_dando_digest(self) -> None:
        """Sin la mutación, el mismo camino mide: el falsador no puede pasar por accidente."""

        completa = _os.path.join(self.raiz, "acta.md")
        _medicion("P-35 lectura estable", _ubicacion._digest_de_archivo(completa))
        self.assertEqual(_sha256(b"acta"), _ubicacion._digest_de_archivo(completa))


class TestMotivoDelUniverso(_unittest.TestCase):
    """P-36 · el motivo distingue un enlace de una laguna del universo.

    Los dos estados son `OPACO` —en ninguno hay bytes de archivo que medir—,
    pero el motivo es lo que el tercero necesita para saber qué corregir: un
    enlace no se arregla indexándolo, y una ruta no versionada sí.
    """

    def setUp(self) -> None:
        self.tmp = _tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.raiz = self.tmp.name
        with open(_os.path.join(self.raiz, "real.md"), "wb") as flujo:
            flujo.write(b"real")
        _os.symlink("real.md", _os.path.join(self.raiz, "enlace.md"))

    def test_p36_el_enlace_declarado_se_nombra_como_enlace(self) -> None:
        digest = _sha256(b"real")
        indice = indice_por_contenido(self.raiz, ("enlace.md",), sondear=("enlace.md",))
        acto = adjudicar((_fila("enlace.md", digest),), indice)
        juicio = acto.juicios[0]
        _medicion("P-36 enlace", (juicio.estado.value, juicio.motivo))
        self.assertEqual(("enlace.md",), indice.omitidas)
        self.assertEqual(EstadoDeEntrada.OPACO, juicio.estado)
        self.assertIn("enlace o un directorio", juicio.motivo)
        self.assertEqual(VeredictoDeUbicacion.NO_MEDIDA, acto.veredicto)


class TestFibraDeclarada(_unittest.TestCase):
    """P-37/38/39 · el manifiesto puede declarar `k >= 2` rutas con el mismo digest.

    Esa fibra es parte de lo declarado: se conserva sólo si **cada** miembro
    sigue midiendo `h`. Un adjudicador que sólo compare multiconjuntos de hashes
    llama limpio a la fibra que perdió un miembro —el digest sigue existiendo en
    otro sitio— y ese es el falso verde que estas pruebas cierran.
    """

    def test_p37_fibra_intacta_con_k_dos(self) -> None:
        indice = Indice.desde_mapa({"a.md": _A, "b.md": _A})
        acto = adjudicar((_fila("a.md", _A), _fila("b.md", _A)), indice)
        _medicion("P-37 fibra", (acto.resumen(), acto.fibras()))
        self.assertEqual(2, acto.cuenta(EstadoDeEntrada.CONFORME))
        self.assertEqual(2, acto.juicios[0].multiplicidad)
        self.assertEqual(VeredictoDeUbicacion.INTACTA, acto.veredicto)
        self.assertEqual(
            ("fibra | %s | 2 declaradas | 2 conformes | a.md, b.md" % _A,),
            acto.fibras(),
        )

    def test_p38_fibra_con_un_miembro_vaciado_no_es_una_reubicacion(self) -> None:
        """Nadie recibió nada: los bytes siguen donde ya estaban declarados.

        Llamarlo `reubicada` afirmaría un movimiento que no ocurrió y dejaría el
        acto en verde con una copia declarada menos.
        """

        indice = Indice.desde_mapa({"b.md": _A})
        acto = adjudicar((_fila("a.md", _A), _fila("b.md", _A)), indice)
        juicio = acto.juicios[0]
        _medicion("P-38 fibra vaciada", (juicio.estado.value, juicio.motivo, acto.veredicto.value))
        self.assertEqual(EstadoDeEntrada.DIVERGE, juicio.estado)
        self.assertIn("ya declaradas", juicio.motivo)
        self.assertEqual(0, acto.cuenta(EstadoDeEntrada.REUBICADO))
        self.assertFalse(acto.conforme)
        self.assertEqual(VeredictoDeUbicacion.DIVERGENTE, acto.veredicto)
        self.assertEqual(("diverge a.md (la ruta quedó sin bytes y el digest sólo consta en rutas ya declaradas)",), acto.testigos())

    def test_p39_una_gemela_suplantada_no_es_un_canje(self) -> None:
        """Caso real (jq 1.7.1): la ruta sellada la ocupan bytes ajenos y la otra gemela conserva `h`."""

        indice = Indice.desde_mapa({"a.md": _A, "b.md": _C})
        acto = adjudicar((_fila("a.md", _A), _fila("b.md", _A)), indice)
        juicio = acto.juicios[1]
        _medicion("P-39 gemela", (juicio.estado.value, juicio.suplantada, acto.veredicto.value))
        self.assertEqual(EstadoDeEntrada.REUBICADO, juicio.estado)
        self.assertTrue(juicio.suplantada)
        self.assertFalse(juicio.canje)
        self.assertEqual(VeredictoDeUbicacion.SUPLANTADA, acto.veredicto)


class TestRcDelActo(_unittest.TestCase):
    """P-41 — el acto no sale en cero con el sello roto.

    El verificador es lo que un cliente pone en su CI. Si `divergente` devolviera
    0, el pipeline pasaría con el sello roto y el acto mediría sin consecuencias:
    el falso verde que este corpus existe para nombrar. `no_medida` tampoco es
    cero —una ceguera no es un hallazgo limpio—, y por eso comparte el 1 con los
    tres veredictos negativos: la línea `veredicto` dice cuál de los dos es.
    """

    def setUp(self) -> None:
        self.raiz = _tempfile.mkdtemp()
        self.addCleanup(_shutil.rmtree, self.raiz, True)
        self.manifiesto = _os.path.join(self.raiz, "SHA256SUMS")

    def _escribir(self, contenido: bytes) -> str:
        with open(_os.path.join(self.raiz, "a.md"), "wb") as flujo:
            flujo.write(contenido)
        with open(self.manifiesto, "w", encoding="utf-8") as flujo:
            flujo.write("%s  a.md\n" % _hashlib.sha256(b"uno\n").hexdigest())
        return contenido.decode("utf-8")

    def _correr(self):
        return _subprocess.run(
            [
                _sys.executable,
                "-B",
                _os.path.join(_RAIZ, "examples", "verificar_sello.py"),
                "--manifiesto",
                self.manifiesto,
                "--raiz",
                self.raiz,
                "--universo",
                "disco",
            ],
            cwd=_RAIZ,
            stdout=_subprocess.PIPE,
            stderr=_subprocess.STDOUT,
            check=False,
        )

    def _veredicto(self, corrida) -> str:
        for linea in corrida.stdout.decode("utf-8", "replace").splitlines():
            if "adjudicacion" in linea:
                return linea.rsplit("->", 1)[-1].strip()
        self.fail("el acto no publica la adjudicacion")

    def test_p41_intacta_sale_en_cero(self) -> None:
        self._escribir(b"uno\n")
        corrida = self._correr()

        self.assertEqual("intacta", self._veredicto(corrida))
        self.assertEqual(0, corrida.returncode)
        _medicion("P-41 RC | intacta", corrida.returncode)

    def test_p41_divergente_no_sale_en_cero(self) -> None:
        self._escribir(b"dos\n")  # el manifiesto sigue declarando `uno`

        corrida = self._correr()

        self.assertEqual("divergente", self._veredicto(corrida))
        self.assertEqual(1, corrida.returncode)
        _medicion("P-41 RC | divergente", corrida.returncode)


if __name__ == "__main__":
    _unittest.main(verbosity=2)
