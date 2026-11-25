"""test_composicion.py — el anillo 4: la cadena, y lo que la cadena no prueba.

Motor declarado de la corrida:

    python3 -B -m unittest discover -s tests

QUE MIDE. Que dos recibos verificados se puedan encadenar sin volver a hashear
el origen, y que la composicion **no invente un veredicto mejor que el peor de
sus tramos**. Un salto opaco en `B -> C` deja el recibo `A -> C` en `no_medida`
aunque `A -> B` haya cerrado perfecto: la comodidad de decir «intacta de punta a
punta» es justo el falso verde que este anillo existe para no producir.

EL ORDEN NO SE INVENTA. La tabla de degradacion es la de `UBICACION.md` §4, de
mejor a peor y sin reordenar: `intacta < reubicada < no_medida < intercambiada <
suplantada < divergente`. P-81 mide que el orden publicado y el que usa la
composicion son el mismo, para que la cadena no pueda degradar por una escala
que solo existe en este archivo.

LO QUE ESTE ARCHIVO ANADE A LA TESIS. El neutro no es «un salto que no hace
nada»: es un salto que no cambia la pagina **y que el empalme puede comprobar**
(P-80). Un `B -> B` sobre otra pagina no es identidad, es basura con forma de
neutro, y componerla rompe la frontera en vez de absorberla. Y la ausencia viaja
solo cuando la pagina que la prueba es la que llega (P-82): probada en `A` y
entregada en `C` sin que la pagina final sea la misma no es una prueba, es una
cita.

P-84 CIERRA LA AUTORREFERENCIA. El recibo lo escribe el generador y hasta aqui lo
leia el mismo repositorio. `examples/verificar_recibo_externo.py` reescribe el
formato, el digest y la tabla de degradacion **sin importar `protocol`**, y este
archivo comprueba que los dos coinciden sobre el mismo recibo. Si el formato
cambia en un solo lado, el desacuerdo es el hallazgo.

NO CUBIERTO (lista cerrada): que el nodo intermedio hiciera **bien** su trabajo
—el recibo certifica continuidad de bytes, no correccion de la transformacion—;
y el coste de recomponer cadenas largas, que no se mide aqui.
"""

from __future__ import annotations

import importlib.util as _importlib_util
import io as _io
import json as _json
import os as _os
import subprocess as _subprocess
import sys as _sys
import tempfile as _tempfile
import unittest as _unittest
from typing import List, Sequence, Tuple

_RAIZ = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
_SRC = _os.path.join(_RAIZ, "src")
if _SRC not in _sys.path:
    _sys.path.insert(0, _SRC)

from protocol.ausencia import (  # noqa: E402
    VeredictoDeAusencia,
    consultar,
    pagina_desde_manifiesto,
)
from protocol.composicion import (  # noqa: E402
    RANGO,
    Recibo,
    Tramo,
    VeredictoDeComposicion,
    a_dict,
    componer,
    desde_dict,
    identidad,
)
from protocol.types import ContratoViolado  # noqa: E402
from protocol.ubicacion import leer_manifiesto  # noqa: E402

_V = VeredictoDeComposicion
_EXTERNO = _os.path.join(_RAIZ, "examples", "verificar_recibo_externo.py")


def _pagina(*rutas: str):
    texto = "".join("%s  %s\n" % (("%x" % (i + 1)) * 64, ruta) for i, ruta in enumerate(rutas))
    return pagina_desde_manifiesto(leer_manifiesto(texto))


def _otra_pagina(*rutas: str):
    texto = "".join("%s  %s\n" % (("%x" % (i + 9)) * 64, ruta) for i, ruta in enumerate(rutas))
    return pagina_desde_manifiesto(leer_manifiesto(texto))


def _salto(
    origen: str,
    destino: str,
    pagina_origen,
    pagina_destino=None,
    veredicto: VeredictoDeComposicion = _V.INTACTA,
    testigos: Sequence[object] = (),
) -> Recibo:
    destino_filas = pagina_destino if pagina_destino is not None else pagina_origen
    return Recibo(
        tramos=(
            Tramo(
                origen=origen,
                destino=destino,
                veredicto=veredicto,
                pagina_origen=pagina_origen.filas if pagina_origen is not None else (),
                pagina_destino=destino_filas.filas if destino_filas is not None else (),
                testigos=tuple(testigos),
            ),
        )
    )


class TestOrdenDeLaComposicion(_unittest.TestCase):
    def test_p79a_el_orden_de_la_composicion_es_el_de_ubicacion(self) -> None:
        """Una sola escala. Dos escalas divergen en cuanto alguien toque una."""

        self.assertEqual(
            [v.value for v in RANGO[:6]],
            ["intacta", "reubicada", "no_medida", "intercambiada", "suplantada", "divergente"],
        )
        self.assertEqual(RANGO[-1].value, "frontera_rota")

    def test_p79b_frontera_rota_es_peor_que_cualquier_tramo(self) -> None:
        """Un empalme roto invalida la cadena, no un tramo: va por encima."""

        self.assertGreater(RANGO.index(_V.FRONTERA_ROTA), RANGO.index(_V.DIVERGENTE))


class TestPropagacionSinFalsoVerde(_unittest.TestCase):
    def test_p79c_un_tramo_opaco_deja_la_cadena_en_no_medida(self) -> None:
        pagina = _pagina("a.tsv", "b.tsv")
        izquierda = _salto("A", "B", pagina)
        derecha = _salto("B", "C", pagina, veredicto=_V.NO_MEDIDA)
        compuesto = componer(izquierda, derecha)
        self.assertIs(compuesto.veredicto, _V.NO_MEDIDA)
        self.assertFalse(compuesto.sostiene)
        self.assertIsNotNone(compuesto.tramo_degradado)
        self.assertEqual(
            (compuesto.tramo_degradado.origen, compuesto.tramo_degradado.destino), ("B", "C")
        )

    def test_p79d_el_peor_estado_gana_y_se_nombra_el_tramo_que_lo_produjo(self) -> None:
        pagina = _pagina("a.tsv", "b.tsv")
        compuesto = componer(
            componer(
                _salto("A", "B", pagina),
                _salto("B", "C", pagina, veredicto=_V.REUBICADA),
            ),
            _salto("C", "D", pagina, veredicto=_V.DIVERGENTE),
        )
        self.assertIs(compuesto.veredicto, _V.DIVERGENTE)
        self.assertEqual(
            (compuesto.tramo_degradado.origen, compuesto.tramo_degradado.destino), ("C", "D")
        )
        self.assertFalse(compuesto.sostiene)

    def test_p79e_el_empalme_que_no_cierra_rompe_la_cadena_y_viaja(self) -> None:
        pagina = _pagina("a.tsv", "b.tsv")
        otra = _otra_pagina("a.tsv", "b.tsv")
        izquierda = _salto("A", "B", pagina)
        derecha = _salto("B", "C", otra)
        compuesto = componer(izquierda, derecha)
        self.assertIs(compuesto.veredicto, _V.FRONTERA_ROTA)
        self.assertIsNotNone(compuesto.frontera)
        esperado, leido = compuesto.frontera
        self.assertEqual(esperado, pagina.digest)
        self.assertEqual(leido, otra.digest)
        # La cadena larga no cura el empalme: lo conserva.
        tercera = componer(compuesto, _salto("C", "D", otra))
        self.assertIs(tercera.veredicto, _V.FRONTERA_ROTA)
        self.assertEqual(tercera.frontera, compuesto.frontera)

    def test_p79f_una_frontera_sin_paginas_es_no_medida_y_no_intacta(self) -> None:
        """El tercer caso: no cerro ni se rompio. Nadie miro."""

        pagina = _pagina("a.tsv", "b.tsv")
        opaco = Recibo(tramos=(Tramo(origen="B", destino="C", veredicto=_V.NO_MEDIDA),))
        compuesto = componer(_salto("A", "B", pagina), opaco)
        self.assertIs(compuesto.veredicto, _V.NO_MEDIDA)
        self.assertTrue(compuesto.frontera_vacua)
        self.assertIsNone(compuesto.frontera)
        self.assertFalse(compuesto.sostiene)


class TestNeutro(_unittest.TestCase):
    def test_p80a_la_identidad_se_absorbe_por_los_dos_lados(self) -> None:
        pagina = _pagina("a.tsv", "b.tsv")
        salto = _salto("A", "B", pagina)
        neutro_derecha = identidad("B", pagina.filas)
        neutro_izquierda = identidad("A", pagina.filas)
        por_derecha = componer(salto, neutro_derecha)
        por_izquierda = componer(neutro_izquierda, salto)
        for compuesto in (por_derecha, por_izquierda):
            self.assertEqual(compuesto.tramos, salto.tramos)
            self.assertEqual(compuesto.cadena(), salto.cadena())
            self.assertIs(compuesto.veredicto, _V.INTACTA)
        # El neutro repetido tampoco deja residuo.
        self.assertEqual(componer(componer(salto, neutro_derecha), neutro_derecha).tramos, salto.tramos)

    def test_p80b_un_neutro_sobre_otra_pagina_no_es_neutro(self) -> None:
        """La basura con forma de neutro: se rechaza al construirla, no al usarla."""

        pagina = _pagina("a.tsv", "b.tsv")
        otra = _otra_pagina("a.tsv", "b.tsv")
        with self.assertRaises(ContratoViolado):
            Tramo(
                origen="B",
                destino="B",
                veredicto=_V.INTACTA,
                pagina_origen=pagina.filas,
                pagina_destino=otra.filas,
            )

    def test_p80c_un_salto_B_a_B_que_no_mira_no_se_absorbe(self) -> None:
        """`no_medida` no es el neutro: es un salto que no miro, y se conserva."""

        pagina = _pagina("a.tsv", "b.tsv")
        opaco = Recibo(tramos=(Tramo(origen="B", destino="B", veredicto=_V.NO_MEDIDA),))
        salto = _salto("A", "B", pagina)
        compuesto = componer(salto, opaco)
        self.assertEqual(len(compuesto.tramos), 2)
        self.assertIs(compuesto.veredicto, _V.NO_MEDIDA)


class TestAsociatividad(_unittest.TestCase):
    def test_p81_agrupar_da_igual_veredicto_cadena_y_tramo_degradado(self) -> None:
        pagina = _pagina("a.tsv", "b.tsv")
        r_ab = _salto("A", "B", pagina)
        r_bc = _salto("B", "C", pagina, veredicto=_V.REUBICADA)
        r_cd = _salto("C", "D", pagina, veredicto=_V.NO_MEDIDA)
        izquierda = componer(componer(r_ab, r_bc), r_cd)
        derecha = componer(r_ab, componer(r_bc, r_cd))
        self.assertIs(izquierda.veredicto, derecha.veredicto)
        self.assertEqual(izquierda.cadena(), derecha.cadena())
        self.assertEqual(
            (izquierda.tramo_degradado.origen, izquierda.tramo_degradado.destino),
            (derecha.tramo_degradado.origen, derecha.tramo_degradado.destino),
        )
        self.assertEqual(len(izquierda.tramos), 3)


class TestAusenciaEnTransito(_unittest.TestCase):
    def test_p82a_el_testigo_viaja_cuando_la_pagina_que_llega_es_la_que_lo_prueba(self) -> None:
        pagina = _pagina("a.tsv", "b.tsv", "c.tsv")
        testigo = consultar(pagina, "bb.tsv")
        self.assertIs(testigo.estado, VeredictoDeAusencia.AUSENTE)
        compuesto = componer(
            _salto("A", "B", pagina, testigos=(testigo,)),
            _salto("B", "C", pagina, veredicto=_V.REUBICADA),
        )
        vigentes = compuesto.ausencias_vigentes()
        self.assertEqual([t.consulta for t in vigentes], ["bb.tsv"])
        # No se rehizo: es el mismo testigo, con el mismo digest de pagina.
        self.assertEqual(vigentes[0].digest_pagina, testigo.digest_pagina)
        self.assertEqual(compuesto.ausencias_historicas(), ())

    def test_p82b_si_la_pagina_cambia_la_ausencia_es_historica_no_vigente(self) -> None:
        pagina = _pagina("a.tsv", "b.tsv", "c.tsv")
        otra = _otra_pagina("a.tsv", "b.tsv", "c.tsv")
        testigo = consultar(pagina, "bb.tsv")
        compuesto = componer(_salto("A", "B", pagina, testigos=(testigo,)), _salto("B", "C", otra))
        self.assertIs(compuesto.veredicto, _V.FRONTERA_ROTA)
        self.assertEqual(compuesto.ausencias_vigentes(), ())
        self.assertEqual([t.consulta for t in compuesto.ausencias_historicas()], ["bb.tsv"])

    def test_p82f_una_cadena_rota_no_hereda_la_ausencia_ni_con_la_misma_pagina(self) -> None:
        """La pagina final puede ser la que prueba el testigo y el camino no existir.

        A entrega `d`, B firma `d`, y C lee **otra** pagina que resulta tener el
        mismo digest que la de A porque C releyo el origen: el testigo encaja y la
        cadena no une los extremos. Publicarlo como vigente seria concluir
        «la ausencia viajo de A a C» de dos hechos que no lo dicen.
        """

        pagina = _pagina("a.tsv", "b.tsv", "c.tsv")
        otra = _otra_pagina("a.tsv", "b.tsv", "c.tsv")
        testigo = consultar(pagina, "bb.tsv")
        compuesto = componer(
            _salto("A", "B", pagina, testigos=(testigo,)),
            _salto("B", "C", otra, pagina),
        )
        self.assertIs(compuesto.veredicto, _V.FRONTERA_ROTA)
        self.assertEqual(compuesto.digest_destino, testigo.digest_pagina)
        self.assertEqual(compuesto.ausencias_vigentes(), ())
        self.assertEqual([t.consulta for t in compuesto.ausencias_sin_transito()], ["bb.tsv"])
        self.assertTrue(any("ausencia sin transito" in l for l in compuesto.lineas()))

    def test_p82c_el_json_no_puede_meter_un_testigo_de_una_pagina_ajena(self) -> None:
        pagina = _pagina("a.tsv", "b.tsv", "c.tsv")
        testigo = consultar(pagina, "bb.tsv")
        datos = a_dict(_salto("A", "B", pagina, testigos=(testigo,)))
        datos["tramos"][0]["testigos"][0]["digest_pagina"] = _otra_pagina("a.tsv").digest
        with self.assertRaises(ContratoViolado):
            desde_dict(datos)

    def test_p82d_el_json_que_miente_sobre_su_digest_no_se_lee(self) -> None:
        pagina = _pagina("a.tsv", "b.tsv")
        datos = a_dict(_salto("A", "B", pagina))
        datos["tramos"][0]["digest_destino"] = "0" * 64
        with self.assertRaises(ContratoViolado):
            desde_dict(datos)

    def test_p82e_el_json_ida_y_vuelta_conserva_vigencia_y_veredicto(self) -> None:
        pagina = _pagina("a.tsv", "b.tsv", "c.tsv")
        testigo = consultar(pagina, "bb.tsv")
        compuesto = componer(
            _salto("A", "B", pagina, testigos=(testigo,)),
            _salto("B", "C", pagina, veredicto=_V.REUBICADA),
        )
        ida = a_dict(compuesto)
        vuelta = desde_dict(_json.loads(_json.dumps(ida)))
        self.assertIs(vuelta.veredicto, compuesto.veredicto)
        self.assertEqual(vuelta.cadena(), compuesto.cadena())
        self.assertEqual([t.consulta for t in vuelta.ausencias_vigentes()], ["bb.tsv"])


def _verificador(*argumentos: str) -> Tuple[int, str]:
    corrida = _subprocess.run(
        [_sys.executable, "-B", _EXTERNO, *argumentos],
        cwd=_RAIZ,
        stdout=_subprocess.PIPE,
        stderr=_subprocess.STDOUT,
        text=True,
    )
    return corrida.returncode, corrida.stdout


class TestVerificadorExterno(_unittest.TestCase):
    def _recibo(self, directorio: str) -> Tuple[str, str]:
        pagina = _pagina("cita-09.tsv", "cita-10.tsv", "cita-11.tsv")
        testigo = consultar(pagina, "cita-09x.tsv")
        compuesto = componer(
            _salto("A", "B", pagina, testigos=(testigo,)),
            _salto("B", "C", pagina, veredicto=_V.REUBICADA),
        )
        ruta = _os.path.join(directorio, "recibo.json")
        with _io.open(ruta, "w", encoding="utf-8") as flujo:
            _json.dump(a_dict(compuesto), flujo)
        manifiesto = _os.path.join(directorio, "SHA256SUMS")
        with _io.open(manifiesto, "w", encoding="utf-8") as flujo:
            flujo.write("".join("%s  %s\n" % (f.h.digest, f.ruta) for f in pagina.filas))
        return ruta, manifiesto

    def test_p84a_el_tercero_cierra_sin_llamar_al_generador(self) -> None:
        with _tempfile.TemporaryDirectory() as directorio:
            ruta, manifiesto = self._recibo(directorio)
            codigo, salida = _verificador(
                "--recibo", ruta, "--manifiesto", manifiesto, "--ausente", "cita-09x.tsv"
            )
            self.assertEqual(codigo, 0, salida)
            self.assertIn("intervalo | cita-09.tsv < cita-09x.tsv < cita-10.tsv", salida)
            self.assertIn("manifiesto | 3 filas", salida)

    def test_p84b_un_digest_alterado_no_cierra(self) -> None:
        with _tempfile.TemporaryDirectory() as directorio:
            ruta, _ = self._recibo(directorio)
            with _io.open(ruta, encoding="utf-8") as flujo:
                datos = _json.load(flujo)
            datos["tramos"][1]["digest_destino"] = "0" * 64
            with _io.open(ruta, "w", encoding="utf-8") as flujo:
                _json.dump(datos, flujo)
            codigo, salida = _verificador("--recibo", ruta)
            self.assertEqual(codigo, 1, salida)
            self.assertIn("alterado", salida)

    def test_p84c_unos_vecinos_alterados_no_cierran(self) -> None:
        with _tempfile.TemporaryDirectory() as directorio:
            ruta, _ = self._recibo(directorio)
            with _io.open(ruta, encoding="utf-8") as flujo:
                datos = _json.load(flujo)
            datos["tramos"][0]["testigos"][0]["siguiente"] = "cita-11.tsv"
            with _io.open(ruta, "w", encoding="utf-8") as flujo:
                _json.dump(datos, flujo)
            codigo, salida = _verificador("--recibo", ruta)
            self.assertEqual(codigo, 1, salida)
            self.assertIn("vecinos alterados", salida)

    def test_p84d_el_verificador_no_importa_el_generador(self) -> None:
        """Si importara `protocol`, coincidir no probaria nada."""

        with _io.open(_EXTERNO, encoding="utf-8") as flujo:
            fuente = flujo.read()
        for prohibido in ("import protocol", "from protocol"):
            self.assertNotIn(prohibido, fuente)

    def test_p84e_las_dos_tablas_declaradas_coinciden(self) -> None:
        especificacion = _importlib_util.spec_from_file_location("_externo", _EXTERNO)
        modulo = _importlib_util.module_from_spec(especificacion)
        especificacion.loader.exec_module(modulo)  # type: ignore[union-attr]
        self.assertEqual(tuple(modulo.RANGO), tuple(v.value for v in RANGO))
        self.assertEqual(modulo.FORMATO_CANONICO, "%s  %s\n")

    def test_p84f_el_verificador_degrada_igual_que_el_modulo(self) -> None:
        pagina = _pagina("cita-09.tsv", "cita-10.tsv")
        compuesto = componer(
            _salto("A", "B", pagina),
            componer(
                Recibo(tramos=(Tramo(origen="B", destino="C", veredicto=_V.NO_MEDIDA),)),
                _salto("C", "D", pagina),
            ),
        )
        with _tempfile.TemporaryDirectory() as directorio:
            ruta = _os.path.join(directorio, "recibo.json")
            with _io.open(ruta, "w", encoding="utf-8") as flujo:
                _json.dump(a_dict(compuesto), flujo)
            codigo, salida = _verificador("--recibo", ruta)
        self.assertEqual(codigo, 0, salida)
        self.assertIn("veredicto | %s |" % compuesto.veredicto.value, salida)
        self.assertIn("sostiene no", salida)
