"""test_conservacion.py — el anillo 7: la magnitud que sobrevive y lo que no certifica.

Motor declarado de la corrida:

    python3 -B -m unittest discover -s tests

QUE MIDE. Que un recibo del anillo 4 —que solo prueba continuidad de bytes— se
pueda ademas preguntar por una **magnitud** que el cliente declara, y que la
respuesta sea falsable: `filas` cuenta entradas, `claves` autentica el conjunto
de rutas, y las dos pueden discrepar sobre el mismo par de paginas. El valor no
se acepta nunca: se recalcula de las paginas, de modo que un recibo no puede
mentir sobre su propia magnitud.

LAS DOS DIRECCIONES, QUE NO SON SIMETRICAS. La conservacion es **completa para
conservar** —`f(A)=f(B)` y `f(B)=f(C)` dan `f(A)=f(C)` por transitividad de la
igualdad, P-100— y **no lo es para acusar**: `no_conservada` no dice que
`f(A) != f(C)`, porque un salto puede perder una clave y el siguiente volver a
anadirla (P-104). Y conservar no es calcular bien: `filas` y `claves` sobreviven
a un valor mal calculado (P-103), que es el hueco que `COMPOSICION.md` §7 deja
abierto. Este anillo lo **acota**, no lo cierra, y la linea `limite` lo dice en
cada corrida.

EL ORDEN NO SE IMPORTA. `conservada < sin_medida < no_conservada` no viene de
`UBICACION.md` §4, que ordena objetos y no magnitudes; se declara en
`conservacion.RANGO` y P-99a mide que el orden publicado y el usado sean el
mismo. `sin_medida` es el tercer estado que un algebra de dos valores pierde:
falta una pagina, y eso no es que la comparacion saliera bien.

LA CADENA DE REFINAMIENTO. `pagina ⊒ claves ⊒ filas`: la misma pagina da las
mismas claves, y las mismas claves dan la misma cuenta. Ninguna implicacion
vuelve (P-100f), y por eso una medida mas fina puede acusar donde la gruesa
callaba, nunca al reves.

NO CUBIERTO (lista cerrada): que la medida elegida sea **suficiente** para un
dominio —lo decide el cliente y la linea `limite` lo declara—; el coste de medir
cadenas largas; y la correccion aritmetica de la transformacion, que ninguna
magnitud sobre las claves puede ver (P-103).
"""

from __future__ import annotations

import ast as _ast
import dataclasses as _dataclasses
import hashlib as _hashlib
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

from protocol.composicion import (  # noqa: E402
    Recibo,
    Tramo,
    VeredictoDeComposicion,
    digest_de_pagina,
)
from protocol.conservacion import (  # noqa: E402
    MEDIDAS,
    RANGO,
    CadenaDeConservacion,
    Conservacion,
    VeredictoDeConservacion,
    componer,
    de_recibo,
    declarar_medida,
    es_identidad_sola,
    identidad,
    medir,
    medidas_de,
    rango,
)
from protocol.types import ALGORITMO, ContratoViolado, Hash  # noqa: E402
from protocol.ubicacion import EntradaDeclarada  # noqa: E402

#: La cadena de negocio de la que habla el guion G11, en sus tres formas: `A` con
#: los importes de la agenda, `B` con un importe **recalculado mal** —misma
#: clave, misma cuenta, otro digest— y `C` con una cita reubicada de sillon.
_VALORES_A = (
    ("cita-09-00-sillon1", "300"),
    ("cita-10-00-sillon2", "450"),
    ("cita-11-00-sillon2", "200"),
)
_VALORES_B = (
    ("cita-09-00-sillon1", "300"),
    ("cita-10-00-sillon2", "999"),
    ("cita-11-00-sillon2", "200"),
)
_VALORES_C = (
    ("cita-09-00-sillon1", "300"),
    ("cita-10-00-sillon2", "999"),
    ("cita-11-00-sillon4", "200"),
)

_ACTO = _os.path.join(_RAIZ, "examples", "verificar_conservacion.py")


def _pagina(valores: Sequence[Tuple[str, str]]) -> Tuple[EntradaDeclarada, ...]:
    filas = []
    for ruta, valor in valores:
        digest = _hashlib.sha256(("%s|%s" % (ruta, valor)).encode("utf-8")).hexdigest()
        filas.append(EntradaDeclarada(ruta, Hash(ALGORITMO, digest)))
    return tuple(filas)


def _recibo(paginas: Sequence[Tuple[EntradaDeclarada, ...]], nombres: Sequence[str]) -> Recibo:
    tramos = []
    for indice, (origen, destino) in enumerate(zip(nombres, nombres[1:])):
        tramos.append(
            Tramo(
                origen=origen,
                destino=destino,
                veredicto=VeredictoDeComposicion.INTACTA,
                pagina_origen=paginas[indice],
                pagina_destino=paginas[indice + 1],
            )
        )
    return Recibo(tramos=tuple(tramos))


def _escribir_paginas(
    carpeta: str, paginas: Sequence[Tuple[str, Sequence[Tuple[str, str]]]]
) -> List[str]:
    """Una pagina por archivo, fuera del arbol: lo que el tercero recibe."""

    rutas: List[str] = []
    for nombre, valores in paginas:
        ruta = _os.path.join(carpeta, nombre + ".txt")
        with open(ruta, "w", encoding="utf-8") as mano:
            for clave, valor in valores:
                mano.write("%s|%s\n" % (clave, valor))
        rutas.append(ruta)
    return rutas


def _acto_aislado(rutas: Sequence[str], extra: Sequence[str], cwd: str) -> "_subprocess.CompletedProcess[str]":
    """`env -i`: sin arbol, sin PYTHONPATH, sin la maquina que produjo la agenda."""

    return _subprocess.run(
        [_sys.executable, "-B", _ACTO, "--paginas", ",".join(rutas)] + list(extra),
        cwd=cwd,
        env={},
        capture_output=True,
        text=True,
    )


class _Base(_unittest.TestCase):
    def setUp(self) -> None:
        self.a = _pagina(_VALORES_A)
        self.b = _pagina(_VALORES_B)
        self.c = _pagina(_VALORES_C)

    def cadena(self, medida: str) -> CadenaDeConservacion:
        return de_recibo(_recibo((self.a, self.b, self.c), ("A", "B", "C")), medida)


class TestLaMedidaEsDelCliente(_Base):
    def test_p99a_el_orden_declarado_es_el_usado(self) -> None:
        self.assertEqual(
            RANGO,
            (
                VeredictoDeConservacion.CONSERVADA,
                VeredictoDeConservacion.SIN_MEDIDA,
                VeredictoDeConservacion.NO_CONSERVADA,
            ),
        )
        self.assertEqual([rango(estado) for estado in RANGO], [0, 1, 2])
        self.assertEqual(MEDIDAS, ("filas", "claves"))
        self.assertEqual(declarar_medida("filas"), "filas")

    def test_p99b_una_medida_sin_nombre_o_desconocida_se_rechaza(self) -> None:
        for nombre in ("", "importes", "Filas"):
            with self.assertRaises(ContratoViolado):
                declarar_medida(nombre)
        with self.assertRaises(ContratoViolado):
            Conservacion("A", "B", "importes", self.a, self.b)
        with self.assertRaises(ContratoViolado):
            de_recibo(_recibo((self.a, self.b), ("A", "B")), "")

    def test_p99c_dos_medidas_dos_respuestas_sobre_el_mismo_par(self) -> None:
        """`A -> B` cambio todos los digests y conserva las dos magnitudes."""

        self.assertTrue(Conservacion("A", "B", "filas", self.a, self.b).conserva)
        self.assertTrue(Conservacion("A", "B", "claves", self.a, self.b).conserva)
        self.assertNotEqual(digest_de_pagina(self.a), digest_de_pagina(self.b))

    def test_p99d_la_medida_cambia_la_respuesta_no_el_par(self) -> None:
        """`B -> C` conserva la cuenta y **no** conserva las claves."""

        self.assertTrue(Conservacion("B", "C", "filas", self.b, self.c).conserva)
        self.assertFalse(Conservacion("B", "C", "claves", self.b, self.c).conserva)

    def test_p99e_el_valor_es_una_propiedad_y_no_un_campo(self) -> None:
        nombres = {campo.name for campo in _dataclasses.fields(Conservacion)}
        self.assertEqual(nombres, {"origen", "destino", "medida", "pagina_origen", "pagina_destino"})
        self.assertEqual([n for n in nombres if n.startswith("valor")], [])

    def test_p99f_suministrar_el_valor_es_un_error_de_tipo(self) -> None:
        with self.assertRaises(TypeError):
            Conservacion("A", "B", "filas", self.a, self.b, valor_destino="filas=99")

    def test_p99g_el_valor_recalculado_es_el_de_la_pagina(self) -> None:
        salto = Conservacion("A", "B", "filas", self.a, self.b)
        self.assertEqual(salto.valor_origen, medir(self.a, "filas"))
        self.assertEqual(salto.valor_destino, medir(self.b, "filas"))
        self.assertEqual(salto.valor_origen, "filas=3")


class TestComposicionYNeutro(_Base):
    def test_p100a_dos_saltos_que_conservan_dan_una_cadena_que_conserva(self) -> None:
        cadena = self.cadena("filas")
        self.assertTrue(cadena.conserva)
        self.assertEqual((cadena.origen, cadena.destino), ("A", "C"))
        self.assertEqual(cadena.lineas()[-1], "-> conservada")

    def test_p100b_asociatividad_en_veredicto_y_en_lineas(self) -> None:
        d = _pagina(_VALORES_B)
        ab = de_recibo(_recibo((self.a, self.b), ("A", "B")), "claves")
        bc = de_recibo(_recibo((self.b, self.c), ("B", "C")), "claves")
        cd = de_recibo(_recibo((self.c, d), ("C", "D")), "claves")
        izquierda = componer(componer(ab, bc), cd)
        derecha = componer(ab, componer(bc, cd))
        self.assertEqual(izquierda.veredicto, derecha.veredicto)
        self.assertEqual(izquierda.lineas(), derecha.lineas())
        self.assertEqual(izquierda, derecha)

    def test_p100c_el_neutro_se_absorbe_y_no_se_arrastra(self) -> None:
        ab = de_recibo(_recibo((self.a, self.b), ("A", "B")), "filas")
        detras = CadenaDeConservacion((identidad("B", self.b, "filas"),))
        delante = CadenaDeConservacion((identidad("A", self.a, "filas"),))
        self.assertTrue(es_identidad_sola(detras))
        self.assertIs(componer(ab, detras), ab)
        self.assertIs(componer(delante, ab), ab)
        self.assertEqual(len(componer(detras, detras).saltos), 1)

    def test_p100d_un_neutro_sobre_otra_pagina_no_es_neutro(self) -> None:
        falso = Conservacion("B", "B", "filas", self.b, self.c)
        self.assertTrue(falso.conserva)
        self.assertFalse(falso.es_identidad)

    def test_p100e_la_pagina_implica_las_claves_y_la_cuenta(self) -> None:
        self.assertEqual(medir(self.a, "claves"), medir(tuple(self.a), "claves"))
        self.assertEqual(medir(self.a, "filas"), medir(tuple(self.a), "filas"))

    def test_p100f_las_claves_implican_la_cuenta_y_no_al_reves(self) -> None:
        self.assertEqual(medir(self.a, "claves"), medir(self.b, "claves"))
        self.assertEqual(medir(self.a, "filas"), medir(self.b, "filas"))
        self.assertEqual(medir(self.b, "filas"), medir(self.c, "filas"))
        self.assertNotEqual(medir(self.b, "claves"), medir(self.c, "claves"))

    def test_p100g_las_claves_no_implican_la_pagina(self) -> None:
        self.assertEqual(medir(self.a, "claves"), medir(self.b, "claves"))
        self.assertNotEqual(digest_de_pagina(self.a), digest_de_pagina(self.b))


class TestPropagacionSinFalsoVerde(_Base):
    def test_p101a_un_salto_que_no_conserva_degrada_la_cadena_y_lo_nombra(self) -> None:
        cadena = self.cadena("claves")
        self.assertIs(cadena.veredicto, VeredictoDeConservacion.NO_CONSERVADA)
        self.assertFalse(cadena.conserva)
        degradado = cadena.tramo_degradado
        self.assertIsNotNone(degradado)
        self.assertEqual((degradado.origen, degradado.destino), ("B", "C"))
        self.assertIn("degradado | B->C | no_conservada", cadena.lineas())
        self.assertNotIn("-> conservada", cadena.lineas())

    def test_p101b_la_misma_cadena_conserva_bajo_la_otra_medida(self) -> None:
        self.assertTrue(self.cadena("filas").conserva)
        self.assertFalse(self.cadena("claves").conserva)
        self.assertEqual(len(medidas_de(_recibo((self.a, self.b, self.c), ("A", "B", "C")))), len(MEDIDAS))


class TestElEmpalme(_Base):
    def test_p102a_un_nodo_que_publica_dos_magnitudes_rompe_el_empalme(self) -> None:
        """Los dos saltos conservan por separado; `B` no coincide consigo mismo."""

        primero = Conservacion("A", "B", "claves", self.a, self.b)
        segundo = Conservacion("B", "C", "claves", self.c, self.c)
        self.assertTrue(primero.conserva)
        self.assertTrue(segundo.conserva)
        cadena = CadenaDeConservacion((primero, segundo))
        self.assertIs(cadena.veredicto, VeredictoDeConservacion.NO_CONSERVADA)
        self.assertEqual(len(cadena.empalmes), 1)
        nodo, dejado, leido = cadena.empalmes[0]
        self.assertEqual(nodo, "B")
        self.assertNotEqual(dejado, leido)
        self.assertIn("empalme | B |", "\n".join(cadena.lineas()))


class TestFalsoVerdeDeclarado(_Base):
    def test_p103a_un_valor_mal_calculado_sobrevive_a_las_dos_medidas(self) -> None:
        """El falsificador de la promesa: conservar **no** es calcular bien."""

        b2 = _pagina(_VALORES_B)
        self.assertEqual(_VALORES_A[1][0], _VALORES_B[1][0])
        self.assertNotEqual(_VALORES_A[1][1], _VALORES_B[1][1])
        recibo = _recibo((self.a, b2, b2), ("A", "B", "C"))
        for medida in MEDIDAS:
            self.assertTrue(de_recibo(recibo, medida).conserva, medida)
        self.assertNotEqual(digest_de_pagina(self.a), digest_de_pagina(b2))

    def test_p103b_la_linea_limite_se_emite_tambien_cuando_conserva(self) -> None:
        b2 = _pagina(_VALORES_B)
        lineas = de_recibo(_recibo((self.a, b2, b2), ("A", "B", "C")), "claves").lineas()
        limite = [linea for linea in lineas if linea.startswith("limite |")]
        self.assertEqual(len(limite), 1)
        self.assertIn("no el calculo", limite[0])


class TestNoAcusaAlExtremo(_Base):
    def test_p104a_una_clave_que_se_pierde_y_se_recupera(self) -> None:
        """`f(A) == f(C)` y la cadena **no** conserva: degradar no es acusar."""

        sin_una = _pagina(_VALORES_A[:2])
        pierde = Conservacion("A", "B", "claves", self.a, sin_una)
        repone = Conservacion("B", "C", "claves", sin_una, self.a)
        self.assertFalse(pierde.conserva)
        self.assertFalse(repone.conserva)
        cadena = CadenaDeConservacion((pierde, repone))
        self.assertIs(cadena.veredicto, VeredictoDeConservacion.NO_CONSERVADA)
        self.assertEqual(cadena.saltos[0].valor_origen, cadena.saltos[-1].valor_destino)
        self.assertIn("extremo |", "\n".join(cadena.lineas()))


class TestSinMedida(_Base):
    def test_p105a_falta_una_pagina_y_el_veredicto_no_es_conservada(self) -> None:
        self.assertIs(
            Conservacion("A", "B", "filas", self.a, ()).veredicto, VeredictoDeConservacion.SIN_MEDIDA
        )
        self.assertIs(
            Conservacion("A", "B", "filas", (), self.b).veredicto, VeredictoDeConservacion.SIN_MEDIDA
        )

    def test_p105b_el_empalme_sin_pagina_no_se_lee_como_conservado(self) -> None:
        cadena = CadenaDeConservacion(
            (
                Conservacion("A", "B", "filas", self.a, ()),
                Conservacion("B", "C", "filas", (), self.c),
            )
        )
        self.assertEqual(cadena.empalmes_sin_medir, ("B",))
        self.assertEqual(cadena.empalmes, ())
        self.assertIs(cadena.veredicto, VeredictoDeConservacion.SIN_MEDIDA)

    def test_p105c_no_se_mezclan_medidas_ni_se_componen_cadenas_que_no_se_tocan(self) -> None:
        filas = self.cadena("filas")
        claves = self.cadena("claves")
        with self.assertRaises(ContratoViolado):
            componer(filas, claves)
        with self.assertRaises(ContratoViolado):
            CadenaDeConservacion((filas.saltos[0], claves.saltos[1]))
        with self.assertRaises(ContratoViolado):
            CadenaDeConservacion(())
        with self.assertRaises(ContratoViolado):
            componer(filas, de_recibo(_recibo((self.b, self.c), ("E", "F")), "filas"))


class TestElTerceroRecalcula(_Base):
    def test_p106a_un_tercero_sin_el_generador_produce_las_mismas_lineas(self) -> None:
        corrida = _subprocess.run(
            [_sys.executable, "-B", _ACTO, "--demo"], cwd=_RAIZ, capture_output=True, text=True
        )
        self.assertEqual(corrida.returncode, 0, msg=corrida.stderr)
        ajeno = [linea for linea in corrida.stdout.splitlines() if linea.strip()]
        recibo = _recibo((self.a, self.b, self.c), ("A", "B", "C"))
        propio: List[str] = []
        for medida in MEDIDAS:
            propio.extend(de_recibo(recibo, medida).lineas())
        self.assertEqual(ajeno, propio)

    def test_p106b_el_acto_ajeno_no_importa_el_generador(self) -> None:
        with open(_ACTO, "r", encoding="utf-8") as mano:
            fuente = mano.read()
        self.assertNotIn("import protocol", fuente)
        self.assertNotIn("from protocol", fuente)

    def test_p106c_una_medida_que_el_acto_no_conoce_sale_con_rc_2(self) -> None:
        corrida = _subprocess.run(
            [_sys.executable, "-B", _ACTO, "--medida", "importes"],
            cwd=_RAIZ,
            capture_output=True,
            text=True,
        )
        self.assertEqual(corrida.returncode, 2, msg=corrida.stdout)

    def test_p106d_una_cadena_de_archivos_fuera_del_arbol_da_las_mismas_lineas(self) -> None:
        with _tempfile.TemporaryDirectory() as carpeta:
            rutas = _escribir_paginas(
                carpeta, (("A", _VALORES_A), ("B", _VALORES_B), ("C", _VALORES_C))
            )
            for medida in MEDIDAS:
                corrida = _acto_aislado(rutas, ("--medida", medida), cwd=carpeta)
                ajeno = [linea for linea in corrida.stdout.splitlines() if linea.strip()]
                propio = de_recibo(_recibo((self.a, self.b, self.c), ("A", "B", "C")), medida).lineas()
                self.assertEqual(ajeno, propio, msg=corrida.stderr)
                esperado = 0 if propio[-1] == "-> conservada" else 1
                self.assertEqual(corrida.returncode, esperado, msg=corrida.stderr)

    def test_p106e_el_acto_recorre_tres_saltos_y_condena_la_fuga_intermedia(self) -> None:
        with _tempfile.TemporaryDirectory() as carpeta:
            integra = _escribir_paginas(
                carpeta,
                (("A", _VALORES_A), ("B", _VALORES_A), ("C", _VALORES_A), ("D", _VALORES_A)),
            )
            corrida = _acto_aislado(
                integra, ("--medida", "filas", "--saltos", "A:B,B:C,C:D"), cwd=carpeta
            )
            self.assertEqual(corrida.returncode, 0, msg=corrida.stderr)
            self.assertIn("conservacion | A -> B -> C -> D", corrida.stdout)

            fuga = _escribir_paginas(
                carpeta,
                (
                    ("A", _VALORES_A),
                    ("B", _VALORES_A),
                    ("C", _VALORES_A[:2]),
                    ("D", _VALORES_A),
                ),
            )
            corrida = _acto_aislado(fuga, ("--medida", "filas"), cwd=carpeta)
            self.assertEqual(corrida.returncode, 1, msg=corrida.stdout)
            self.assertIn("degradado | B->C | no_conservada", corrida.stdout)

    def test_p106f_la_cadena_entra_por_parametro_y_no_por_constante_del_modulo(self) -> None:
        with open(_ACTO, "r", encoding="utf-8") as mano:
            arbol = _ast.parse(mano.read())
        funciones = [
            nodo
            for nodo in arbol.body
            if isinstance(nodo, _ast.FunctionDef) and nodo.name == "medir_cadena"
        ]
        self.assertEqual(len(funciones), 1, "el acto debe tener un solo medir_cadena")
        funcion = funciones[0]
        referidas = {nodo.id for nodo in _ast.walk(funcion) if isinstance(nodo, _ast.Name)}
        constantes = {nombre for nombre in referidas if nombre.startswith(("_SALTOS", "_PAGINAS"))}
        self.assertEqual(constantes, set(), "medir_cadena usa una cadena que no recibio")
        self.assertIn("saltos", [argumento.arg for argumento in funcion.args.args])


if __name__ == "__main__":  # pragma: no cover
    _unittest.main()
