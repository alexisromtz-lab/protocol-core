"""test_guiones.py — la pagina de guiones, medida por su propio contrato.

Motor declarado de la corrida:

    python3 -B -m unittest discover -s tests

QUE MIDE. `GUIONES.md` es una pagina (`PREDICADO.md` §ley 29), y una pagina se
falsifica. Este archivo no comprueba que los guiones sean buenos: comprueba que
cumplen las seis reglas que ellos mismos declaran —ninguna cifra sin comando, el
conteo de la suite al dia, la voz dentro de presupuesto, la linea de tiempo
contigua y cada `G` con su falsador—. Un guion que no cumple su contrato produce
un video que contradice al producto que vende.

LO QUE ESTE ARCHIVO ANADE A LA TESIS. El conteo `Ran N tests` aparecia tres
veces en la pagina y ya se habia quedado viejo una vez (119 mientras la suite
declaraba 146): una cifra de guion sin lector envejece en la copia, que es A0.7
aplicado al propio guion. P-61 la ata al instrumento que la produce.

POR QUE EL PARSEO MIRA LA ULTIMA CELDA. El recibo se imprime literal y lleva
`|` dentro (formato `coste | 14 declaradas | …`), asi que la celda de pantalla
contiene barras que no son separadores. Se toma la **primera** celda como tiempo
y la **ultima** como voz; el medio no se parsea.

NO CUBIERTO (lista cerrada): que el video se vea bien; que las cifras sigan
siendo ciertas —eso lo falsa el comando de cada fila, no este archivo—; y que un
clon superficial reproduzca el ancla (§10 de `GUIONES.md`).
"""

from __future__ import annotations

import io as _io
import os as _os
import re as _re
import sys as _sys
import unittest as _unittest

_RAIZ = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
_SRC = _os.path.join(_RAIZ, "src")
if _SRC not in _sys.path:
    _sys.path.insert(0, _SRC)

from protocol.ausencia import VeredictoDeAusencia  # noqa: E402

_GUIONES = _os.path.join(_RAIZ, "GUIONES.md")
_GUIONES_EN = _os.path.join(_RAIZ, "GUIONES_EN.md")

#: 12 palabras cada 4 s es la regla 6 del contrato. Se redondea hacia arriba
#: porque una palabra no se dice en fracciones y una coma no ocupa tiempo.
PALABRAS_POR_SEGUNDO = 3.0

_TIEMPO = _re.compile(r"^(\d+),(\d)$")
_SECCION = _re.compile(r"^## (\d+) · (.*)$", _re.M)
_FILA = _re.compile(r"^\| (\d+,\d)–(\d+,\d) \| .* \| (.*?) \|$", _re.M)
_GUION = _re.compile(r"^G(\d) · .* — (\d+) s(?: · (.+))?$")


def _medicion(etiqueta: str, valor: object) -> None:
    print("MEDICION | %s | %s" % (etiqueta, valor))


def _texto(ruta: str) -> str:
    with _io.open(ruta, encoding="utf-8") as flujo:
        return flujo.read()


def _segundos(cadena: str) -> float:
    entero, _, decimal = cadena.partition(",")
    return float("%s.%s" % (entero, decimal))


def _secciones(texto: str) -> list:
    """(numero, titulo, cuerpo) de cada `## N · titulo`."""

    piezas = _re.split(r"^## ", texto, flags=_re.M)
    salida = []
    for pieza in piezas[1:]:
        cabecera, _, cuerpo = pieza.partition("\n")
        m = _re.match(r"(\d+) · (.*)$", cabecera)
        if m:
            salida.append((int(m.group(1)), m.group(2), cuerpo))
    return salida


def _cuenta_de_la_tabla(texto: str) -> int:
    """La cifra `Ran N tests` de la tabla de §9, leida de su fila 9."""

    for linea in texto.splitlines():
        m = _re.match(r"^\| 9 \| `Ran (\d+) tests`", linea)
        if m:
            return int(m.group(1))
    raise AssertionError("la tabla de cifras no tiene fila 9 con `Ran N tests`")


class _ContratoDeLaPagina:
    """Las seis reglas, medidas sobre una pagina concreta.

    La subclase declara `ARCHIVO` y la tabla de cifras que le corresponde: la
    pagina espanola y la inglesa se miden con el mismo instrumento, o la segunda
    es una traduccion que nadie vigila.
    """

    ARCHIVO = _GUIONES
    TABLA = ("Tabla de cifras", "Figure table")

    def _texto(self) -> str:
        return _texto(self.ARCHIVO)

    def test_p61_el_conteo_de_la_pagina_es_el_de_la_suite(self) -> None:
        """P-61 · el conteo de la suite que la pagina publica es el que la suite declara."""
        vivo = _unittest.defaultTestLoader.discover(_os.path.join(_RAIZ, "tests")).countTestCases()
        publicado = _cuenta_de_la_tabla(self._texto())
        _medicion("P-61 conteo", (publicado, vivo))
        self.assertEqual(vivo, publicado)

    def test_p61b_el_conteo_aparece_tres_veces_y_las_tres_concuerdan(self) -> None:
        # G5 lo enseña dos veces en pantalla y la tabla lo publica una: si uno se
        # mueve y los otros no, la pieza enseña dos verdades distintas.
        texto = self._texto()
        cifras = set(_re.findall(r"Ran (\d+) tests", texto))
        _medicion("P-61b cifras publicadas", sorted(cifras))
        self.assertEqual(1, len(cifras), cifras)

    def test_p62_referencias_a_seccion(self) -> None:
        texto = self._texto()
        numeros = {n for n, _, _ in _secciones(texto)}
        citadas = {int(n) for n in _re.findall(r"§(\d+)", texto)}
        _medicion("P-62 secciones", sorted(numeros))
        _medicion("P-62 citadas", sorted(citadas))
        self.assertEqual(set(), citadas - numeros)

    def test_p63_referencias_a_fila_de_la_tabla(self) -> None:
        # `§9 #11` promete una fila 11 con su comando: una cita a una fila que no
        # existe es una cifra sin procedencia. Las filas se leen solo de la tabla
        # de cifras: los demas cuadros de la pagina empiezan por tiempos o por `G`.
        texto = self._texto()
        tabla = [c for n, t, c in _secciones(texto) if t.startswith(self.TABLA)]
        self.assertEqual(1, len(tabla))
        filas = {int(n) for n in _re.findall(r"^\| (\d+) \| ", tabla[0], flags=_re.M)}
        citadas = {int(n) for n in _re.findall(r"§\d+ #(\d+)", texto)}
        _medicion("P-63 filas de la tabla", sorted(filas))
        _medicion("P-63 filas citadas", sorted(citadas))
        self.assertEqual(set(), citadas - filas)

    def test_p64_numeracion_contigua(self) -> None:
        numeros = [n for n, _, _ in _secciones(self._texto())]
        _medicion("P-64 secciones", numeros)
        self.assertEqual(list(range(len(numeros))), numeros)

    def test_p65_cada_guion_tiene_falsador_en_la_tabla(self) -> None:
        texto = self._texto()
        guiones = {int(n) for n in _re.findall(r"^## \d+ · G(\d) ·", texto, flags=_re.M)}
        falsados = set()
        for linea in texto.splitlines():
            if not linea.startswith("| G"):
                continue
            for n in _re.findall(r"G(\d)", linea.split("|")[1]):
                falsados.add(int(n))
        _medicion("P-65 guiones", sorted(guiones))
        _medicion("P-65 falsados", sorted(falsados))
        self.assertEqual(set(), guiones - falsados)



    def _guiones(self) -> list:
        texto = self._texto()
        salida = []
        for numero, titulo, cuerpo in _secciones(texto):
            m = _GUION.match(titulo)
            if not m:
                continue
            filas = _FILA.findall(cuerpo)
            salida.append((int(m.group(1)), int(m.group(2)), m.group(3), filas, titulo))
        return salida

    def test_p66_contiguedad_y_cierre(self) -> None:
        guiones = self._guiones()
        _medicion("P-66 guiones con linea", [g[0] for g in guiones])
        self.assertGreaterEqual(len(guiones), 6)
        for numero, duracion, _, filas, titulo in guiones:
            self.assertTrue(filas, titulo)
            inicios = [_segundos(t[0]) for t in filas]
            fines = [_segundos(t[1]) for t in filas]
            self.assertEqual(0.0, inicios[0], titulo)
            for anterior, siguiente in zip(fines, inicios[1:]):
                self.assertAlmostEqual(anterior, siguiente, places=6, msg=titulo)
            self.assertAlmostEqual(float(duracion), fines[-1], places=6, msg=titulo)

    def test_p67_la_voz_cabe_en_el_presupuesto(self) -> None:
        # Regla 6: 12 palabras cada 4 s. Lo que no cabe no se acelera: pasa a
        # segunda linea en pantalla. Medido, no prometido.
        excesos = []
        for numero, duracion, _, filas, titulo in self._guiones():
            for inicio, fin, voz in filas:
                segundos = _segundos(fin) - _segundos(inicio)
                palabras = len(voz.split())
                tope = PALABRAS_POR_SEGUNDO * segundos + 1
                if voz.strip() and palabras > tope:
                    excesos.append((numero, inicio, palabras, round(tope, 1)))
        _medicion("P-67 excesos de voz", excesos)
        self.assertEqual([], excesos)



    def test_p68_los_tres_estados_del_acto_estan_en_el_guion(self) -> None:
        texto = self._texto()
        nombres = sorted(v.name.lower() for v in VeredictoDeAusencia)
        _medicion("P-68 estados del acto", nombres)
        for nombre in nombres:
            self.assertIn(
                "`%s`" % nombre,
                texto,
                "el guion no nombra el estado `%s` del acto" % nombre,
            )


class TestGuiones(_ContratoDeLaPagina, _unittest.TestCase):
    ARCHIVO = _GUIONES


class TestGuionesEn(_ContratoDeLaPagina, _unittest.TestCase):
    ARCHIVO = _GUIONES_EN


class TestParidadDeLasDosPaginas(_unittest.TestCase):
    """P-69..P-71 · la segunda pagina no es una traduccion libre: es el mismo contrato.

    Una pagina que se traduce y no se compara empieza igual y termina contando
    otra cosa; y la que se publica primero es la que se cree.
    """

    def _figuras(self, ruta: str) -> set:
        texto = _texto(ruta)
        tabla = [c for n, t, c in _secciones(texto) if t.startswith(("Tabla de cifras", "Figure table"))]
        self.assertEqual(1, len(tabla))
        return set(_re.findall(r"^\| (\d+) \| ", tabla[0], flags=_re.M))

    def test_p69_las_dos_paginas_citan_las_mismas_figuras(self) -> None:
        _es, _en = self._figuras(_GUIONES), self._figuras(_GUIONES_EN)
        _medicion("P-69 figuras", (sorted(_es), sorted(_en)))
        self.assertEqual(_es, _en)

    def test_p70_las_dos_paginas_tienen_los_mismos_guiones_y_duraciones(self) -> None:
        def guiones(ruta: str) -> dict:
            texto = _texto(ruta)
            return dict(_re.findall(r"^## \d+ · G(\d) · .* — (\d+) s", texto, flags=_re.M))

        es, en = guiones(_GUIONES), guiones(_GUIONES_EN)
        _medicion("P-70 guiones", (es, en))
        self.assertEqual(es, en)

    def test_p71_las_dos_paginas_declaran_el_mismo_conteo(self) -> None:
        es, en = _cuenta_de_la_tabla(_texto(_GUIONES)), _cuenta_de_la_tabla(_texto(_GUIONES_EN))
        _medicion("P-71 conteos", (es, en))
        self.assertEqual(es, en)
