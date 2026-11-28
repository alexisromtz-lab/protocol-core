"""examples/emitir_predicado.py — un acto: correr la suite, reducir el veredicto, sellar la página.

Uso:

    python3 -B examples/emitir_predicado.py           # escribe el veredicto y la página
    python3 -B examples/emitir_predicado.py --check   # re-ejecuta y coteja: la escalera de `UBICACION.md` §6.2
                                                      # 0 reproduce · 1 refuta · 2 rancio · 3 no medido

`--check` RC 0 es la compuerta de publicación: el veredicto que se comitea es el
que la página reproduce, no el que quedó de una corrida anterior. El `--check`
**nombra su fallo** con la escalera de `protocol.predicado.CodigoDeActo`: `2`
la página describe otro árbol (se re-emite), `3` no hay página que leer, `1` la
página nombra este árbol y no lo describe (se audita). Compartir un solo `1`
entre los tres obligaba al cliente a parsear prosa para saber qué hacer.

Reducción declarada. Del crudo de `unittest` se conserva el conteo (`Ran N
tests`) y el veredicto (`OK` / `FAILED (...)`); se descarta la duración porque es
un **reloj de pared**: dos corridas idénticas dan tiempos distintos, y un digest
que dependa de ella no certifica el acto, mide la máquina. El reductor es parte
del `codigo` del predicado —sin él la salida no es reproducible, y un artefacto
que no se reproduce no es evidencia—.

Límite declarado. El veredicto reducido distingue verde de rojo y conserva el
conteo; **no** conserva el detalle del rojo. El crudo no forma parte del acto.

Lo que este script **no** hace: no firma. Emite el enunciado; la contrafirma de
un tercero es otro acto y otro objeto (`protocol.predicado.contrafirmar`).
"""

from __future__ import annotations

import hashlib as _hashlib
import json as _json
import os as _os
import subprocess as _subprocess
import sys as _sys

RAIZ = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
EJEMPLOS = _os.path.join(RAIZ, "examples")
SALIDA = _os.path.join(EJEMPLOS, "veredicto-suite.txt")
PAGINA = _os.path.join(EJEMPLOS, "predicado-suite.json")

_sys.path.insert(0, _os.path.join(RAIZ, "src"))

from protocol.predicado import (  # noqa: E402
    CodigoDeActo,
    Entorno,
    Predicado,
    VeredictoReclamado,
    cotejar_pagina,
)
from protocol.types import ALGORITMO, EntradaManifiesto, Hash, RutaRelativa  # noqa: E402


def _medicion(etiqueta: str, valor: object) -> None:
    print("MEDICION | %s | %s" % (etiqueta, valor))


def _veredicto_reducido() -> bytes:
    """Corre la suite y reduce el crudo a conteo + veredicto, sin duración."""

    corrida = _subprocess.run(
        [_sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests"],
        cwd=RAIZ,
        stdout=_subprocess.DEVNULL,
        stderr=_subprocess.PIPE,
        check=False,
    )
    crudo = corrida.stderr.decode("utf-8", "replace")
    lineas = [linea.strip() for linea in crudo.splitlines() if linea.strip()]
    conteo = [linea for linea in lineas if linea.startswith("Ran ")]
    veredicto = [linea for linea in lineas if linea == "OK" or linea.startswith("FAILED")]
    if len(conteo) != 1 or len(veredicto) != 1:
        raise SystemExit(
            "el crudo no tiene la forma esperada: conteo=%r veredicto=%r" % (conteo, veredicto)
        )
    # `Ran 43 tests in 0.051s` -> `Ran 43 tests`: la duración se cae aquí.
    return ("%s\n%s\n" % (conteo[0].split(" in ")[0], veredicto[0])).encode("utf-8")


def _referencias(relativas: tuple) -> tuple:
    entradas = []
    for relativa in relativas:
        with open(_os.path.join(RAIZ, relativa), "rb") as flujo:
            digest = _hashlib.sha256(flujo.read()).hexdigest()
        entradas.append(EntradaManifiesto(RutaRelativa(relativa), Hash(ALGORITMO, digest)))
    return tuple(entradas)


def _codigo() -> tuple:
    # `__init__.py` no se excluye: es donde el árbol declara su versión, y una
    # página que no lo hashea deja que una versión cambie sin mover el acto —
    # el defecto del tag `v0.1.1`, un salto en la identidad declarada.
    fuente = [
        "src/protocol/%s" % nombre
        for nombre in sorted(_os.listdir(_os.path.join(RAIZ, "src", "protocol")))
        if nombre.endswith(".py")
    ]
    return _referencias(sorted(fuente + ["examples/emitir_predicado.py"]))


def _entradas() -> tuple:
    pruebas = [
        "tests/%s" % nombre
        for nombre in sorted(_os.listdir(_os.path.join(RAIZ, "tests")))
        if nombre.endswith(".py") and nombre != "__init__.py"
    ]
    return _referencias(pruebas)


def _predicado(veredicto: bytes) -> Predicado:
    return Predicado(
        afirmacion=(
            "la suite declara su veredicto sobre este codigo y estas pruebas, "
            "en el entorno declarado"
        ),
        entradas=_entradas(),
        codigo=_codigo(),
        entorno=Entorno(
            _sys.platform,
            "CPython %d.%d.%d" % _sys.version_info[:3],
            ("CI linux no medido desde aqui", "detalle del rojo no reducido"),
        ),
        salida=EntradaManifiesto(
            RutaRelativa("examples/veredicto-suite.txt"),
            Hash(ALGORITMO, _hashlib.sha256(veredicto).hexdigest()),
        ),
        veredicto=VeredictoReclamado.CONFORME,
        h_prev=None,
    )


def _escribir(ruta: str, datos: bytes) -> None:
    with open(ruta, "wb") as flujo:
        flujo.write(datos)


def main(argv: tuple) -> int:
    veredicto = _veredicto_reducido()
    predicado = _predicado(veredicto)
    digest = predicado.digest()
    pagina = predicado.pagina()

    if "--check" in argv:
        if not _os.path.exists(PAGINA) or not _os.path.exists(SALIDA):
            print("NO_MEDIDO | no hay pagina previa que reproducir")
            return int(CodigoDeActo.NO_MEDIDO)
        with open(SALIDA, "rb") as flujo:
            salida_previa = flujo.read()
        with open(PAGINA, "rb") as flujo:
            pagina_previa = flujo.read()
        # La pagina se compara entera salvo el entorno del observador (§6.1 de
        # `UBICACION.md`): quien reproduce en otro interprete no miente, y
        # hasta hoy lo pagaba como si mintiera. Lo que si condena es que la
        # pagina nombre otro arbol —eso es RANCIO, y se re-emite— o que nombre
        # este y no lo describa —eso es REFUTA, y se audita—.
        codigo, firmado, detalle = cotejar_pagina(
            pagina_previa,
            pagina + "\n",
            (_sys.platform, "CPython %d.%d.%d" % _sys.version_info[:3]),
        )
        # La salida es artefacto del acto, no del arbol: si la pagina reproduce
        # y el archivo no, la pagina miente sobre su propia salida.
        if codigo is CodigoDeActo.REPRODUCE and salida_previa != veredicto:
            codigo = CodigoDeActo.REFUTA
            detalle = "la salida emitida no es la que la pagina nombra"
        _medicion("salida reproducida", salida_previa == veredicto)
        _medicion("pagina reproducida", codigo is CodigoDeActo.REPRODUCE)
        if codigo is not CodigoDeActo.REPRODUCE:
            print("%s | %s" % (codigo.name, detalle))
            return int(codigo)
        print("REPRODUCE | %s" % firmado)
        _medicion("veredicto declarado", _json.loads(pagina_previa)["veredicto"])
        return int(CodigoDeActo.REPRODUCE)

    _escribir(SALIDA, veredicto)
    _escribir(PAGINA, (pagina + "\n").encode("utf-8"))
    _medicion("pagina", PAGINA)
    _medicion("lineas", len(pagina.splitlines()))
    _medicion("bytes", len(pagina.encode("utf-8")))
    _medicion("digest", digest.digest)
    _medicion("referencias", (len(predicado.entradas), len(predicado.codigo)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(tuple(_sys.argv[1:])))
