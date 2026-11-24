"""examples/verificar_sello.py — un acto: adjudicar un manifiesto de sellado contra un árbol.

Uso:

    python3 -B examples/verificar_sello.py                 # fixture de muestra
    python3 -B examples/verificar_sello.py --check         # reproduce o diverge
    python3 -B examples/verificar_sello.py \\
        --manifiesto ../platino-labs/sellos-fecha-cierta-20261009/SHA256SUMS_SELLO_A \\
        --raiz ../platino-labs

La afirmación del acto es sobre **bytes**: los artefactos que el manifiesto
declara existen en este árbol, byte a byte. **La ruta no forma parte de la
afirmación**; cuando los bytes están y la ruta cambió, el recibo lo dice
(`REUBICADO` con testigo origen -> destino) en vez de mentir en cualquiera de
las dos direcciones: no llama roto a lo que sólo se movió, ni llama intacto a
un intercambio.

Universo declarado. Para encontrar un artefacto que se movió hay que indexar
rutas que el manifiesto **no** declara, así que el universo es el árbol y no el
manifiesto. Se elige así y se publica siempre en la salida:

- si `--raiz` es la raíz de un árbol git, el universo es `git ls-files`: lo
  versionado. Un archivo no versionado no entra, y eso se declara en `entorno`.
- si no lo es, el universo es una caminata con exclusiones enumeradas
  (`.git`, `__pycache__`, `.venv`, `node_modules`, `.mypy_cache`,
  `.pytest_cache`). Un árbol ajeno a git medido por caminata tiene 4 225 rutas
  versionadas y 104 316 archivos en disco: la caminata sin exclusiones mide el
  entorno del observador, no el corpus.

Lo que este script **no** hace: no re-sella. Re-sellar es un acto externo con su
propio pre-vuelo y su propia fecha cierta; este acto sólo mide lo que un sello
ya emitido dice hoy.
"""

from __future__ import annotations

import hashlib as _hashlib
import json as _json
import os as _os
import subprocess as _subprocess
import sys as _sys

RAIZ = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
EJEMPLOS = _os.path.join(RAIZ, "examples")
MUESTRA = _os.path.join(EJEMPLOS, "sello-de-muestra")
SALIDA = _os.path.join(EJEMPLOS, "veredicto-sello.txt")
PAGINA = _os.path.join(EJEMPLOS, "predicado-sello.json")

_sys.path.insert(0, _os.path.join(RAIZ, "src"))

from protocol.predicado import Entorno, Predicado, VeredictoReclamado  # noqa: E402
from protocol.types import (  # noqa: E402
    ALGORITMO,
    EntradaManifiesto,
    Hash,
    RutaRelativa,
)
from protocol.ubicacion import (  # noqa: E402
    VeredictoDeUbicacion,
    adjudicar,
    indice_por_contenido,
    leer_manifiesto,
)

#: Exclusiones del universo por caminata, enumeradas y no deducidas: una lista
#: que se descubre sola no se puede auditar.
EXCLUSIONES = (
    ".git",
    "__pycache__",
    ".venv",
    "node_modules",
    ".mypy_cache",
    ".pytest_cache",
)


def _medicion(etiqueta: str, valor: object) -> None:
    print("MEDICION | %s | %s" % (etiqueta, valor))


def _referencias(relativas: tuple) -> tuple:
    entradas = []
    for relativa in relativas:
        with open(_os.path.join(RAIZ, relativa), "rb") as flujo:
            digest = _hashlib.sha256(flujo.read()).hexdigest()
        entradas.append(EntradaManifiesto(RutaRelativa(relativa), Hash(ALGORITMO, digest)))
    return tuple(entradas)


def _universo_git(raiz: str) -> tuple:
    """Las rutas versionadas, si `raiz` es la raíz del árbol. Si no, `None`."""

    try:
        tope = _subprocess.run(
            ["git", "-C", raiz, "rev-parse", "--show-toplevel"],
            stdout=_subprocess.PIPE,
            stderr=_subprocess.DEVNULL,
            check=False,
        )
    except OSError:
        return None
    if tope.returncode != 0:
        return None
    declarado = tope.stdout.decode("utf-8", "replace").strip()
    if not declarado or _os.path.realpath(declarado) != _os.path.realpath(raiz):
        return None
    listado = _subprocess.run(
        ["git", "-C", raiz, "ls-files", "-z"],
        stdout=_subprocess.PIPE,
        stderr=_subprocess.DEVNULL,
        check=False,
    )
    if listado.returncode != 0:
        return None
    crudo = listado.stdout.decode("utf-8", "surrogateescape")
    return tuple(ruta for ruta in crudo.split("\x00") if ruta)


def _universo_caminata(raiz: str) -> tuple:
    rutas = []
    for actual, subdirs, ficheros in _os.walk(raiz):
        subdirs[:] = sorted(d for d in subdirs if d not in EXCLUSIONES)
        for nombre in sorted(ficheros):
            completa = _os.path.join(actual, nombre)
            relativa = _os.path.relpath(completa, raiz).replace(_os.sep, "/")
            rutas.append(relativa)
    return tuple(rutas)


def _universo(raiz: str, modo: str = "auto") -> tuple:
    """Devuelve `(rutas, fuente)`, y la fuente se publica en el recibo.

    `auto` prefiere `git ls-files` porque es barato (0,8 s contra 130 s de
    caminata sobre los 83 690 archivos de un árbol de trabajo real), y deja la
    ceguera de lo no versionado a `fuera_del_universo`. `disco` indexa lo que
    el árbol tiene, versionado o no.
    """

    if modo not in ("auto", "git", "disco"):
        raise SystemExit("--universo admite auto, git o disco")
    if modo in ("auto", "git"):
        por_git = _universo_git(raiz)
        if por_git is not None:
            return por_git, "git ls-files"
        if modo == "git":
            raise SystemExit("--universo git exige que --raiz sea la raiz de un arbol git")
    return _universo_caminata(raiz), "caminata con %d exclusiones" % len(EXCLUSIONES)


def _salida(adjudicacion, indice, fuente: str) -> bytes:
    lineas = [
        "universo | %d rutas | %s | %d fuera del universo"
        % (indice.leidas, fuente, len(indice.fuera_del_universo)),
        adjudicacion.resumen(),
    ]
    lineas.extend(adjudicacion.testigos())
    lineas.extend(adjudicacion.fibras())
    return ("\n".join(lineas) + "\n").encode("utf-8")


def _codigo() -> tuple:
    fuentes = [
        "src/protocol/predicado.py",
        "src/protocol/types.py",
        "src/protocol/ubicacion.py",
        "examples/verificar_sello.py",
    ]
    return _referencias(tuple(sorted(fuentes)))


def _reclamado(adjudicacion) -> VeredictoReclamado:
    """El veredicto de la página **se deriva** de la adjudicación, no se escribe.

    Un recibo que declara `conforme` mientras su propia salida dice
    `divergente` es el falso verde exacto que este acto existe para impedir, y
    lo era hasta que la prueba del acto lo midió. `no_medida` no se degrada a
    ninguno de los dos: no saber no es un veredicto sobre los bytes.
    """

    if adjudicacion.veredicto is VeredictoDeUbicacion.NO_MEDIDA:
        return VeredictoReclamado.NO_MEDIDO
    return VeredictoReclamado.CONFORME if adjudicacion.conforme else VeredictoReclamado.NO_CONFORME


def _predicado(entradas: tuple, salida: bytes, lagunas: tuple, reclamado) -> Predicado:
    return Predicado(
        afirmacion=(
            "los artefactos sellados existen byte a byte en este arbol; "
            "la ruta no forma parte de la afirmacion"
        ),
        entradas=entradas,
        codigo=_codigo(),
        entorno=Entorno(
            _sys.platform,
            "CPython %d.%d.%d" % _sys.version_info[:3],
            lagunas,
        ),
        salida=EntradaManifiesto(
            RutaRelativa("examples/veredicto-sello.txt"),
            Hash(ALGORITMO, _hashlib.sha256(salida).hexdigest()),
        ),
        veredicto=reclamado,
        h_prev=None,
    )


def _escribir(ruta: str, datos: bytes) -> None:
    with open(ruta, "wb") as flujo:
        flujo.write(datos)


def _argumento(argv: tuple, nombre: str, defecto: str) -> str:
    if nombre in argv:
        posicion = argv.index(nombre)
        if posicion + 1 >= len(argv):
            raise SystemExit("falta el valor de %s" % nombre)
        return argv[posicion + 1]
    return defecto


def main(argv: tuple) -> int:
    ruta_manifiesto = _argumento(argv, "--manifiesto", _os.path.join(MUESTRA, "MANIFIESTO.txt"))
    raiz = _argumento(argv, "--raiz", MUESTRA)
    modo = _argumento(argv, "--universo", "auto")

    with open(ruta_manifiesto, "r", encoding="utf-8") as flujo:
        manifiesto = leer_manifiesto(flujo.read(), _os.path.basename(ruta_manifiesto))
    declaradas = manifiesto.filas
    rutas, fuente = _universo(raiz, modo)
    # Las rutas declaradas se sondean en disco: un universo barato no ve lo no
    # versionado, y esa ceguera tiene que salir como laguna, no como ausencia.
    indice = indice_por_contenido(raiz, rutas, [d.ruta for d in declaradas if not d.opaca])
    adjudicacion = adjudicar(declaradas, indice)

    salida = _salida(adjudicacion, indice, fuente)
    # El orden del manifiesto no es parte de la afirmación —la adjudicación es
    # por fila y no depende de la posición— pero la página exige orden byte a
    # byte (§3.d.2), así que el conjunto se normaliza aquí y la fixture, que va
    # desordenada a propósito, lo ejercita.
    entradas = tuple(
        sorted(
            (EntradaManifiesto(RutaRelativa(d.ruta), d.h) for d in declaradas if not d.opaca),
            key=lambda e: e.ruta.clave_bytes,
        )
    )
    # Una ruta redactada no es una `RutaRelativa`, así que no puede viajar en
    # `entradas`; su cuenta se declara aquí para que la diferencia entre el
    # manifiesto y la página sea un número publicado y no un hueco silencioso.
    redactadas = sum(1 for d in declaradas if d.opaca)
    lagunas = ["sin firma de tiempo externa: este acto mide un sello ya emitido, no lo emite"]
    if redactadas:
        lagunas.append("%d rutas redactadas no viajan en entradas" % redactadas)
    if fuente == "git ls-files":
        lagunas.append("archivos no versionados no indexados")
    else:
        lagunas.append("universo por caminata: %d exclusiones declaradas" % len(EXCLUSIONES))
    # El dialecto del manifiesto es una entrada: el recibo nombra el que leyó y
    # el borde de los que no lee. Sin esto, dos verificadores honestos firman
    # veredictos incomparables sobre el mismo árbol.
    lagunas.append("dialecto del manifiesto: sha256sum; BSD, SRI y un solo espacio no admitidos")
    if manifiesto.prefijadas:
        lagunas.append("%d rutas con prefijo ./ normalizadas" % manifiesto.prefijadas)
    predicado = _predicado(entradas, salida, tuple(lagunas), _reclamado(adjudicacion))
    pagina = predicado.pagina()
    digest = predicado.digest()

    if "--check" in argv:
        if not _os.path.exists(PAGINA) or not _os.path.exists(SALIDA):
            print("NO_MEDIDO: no hay pagina previa que reproducir")
            return 2
        with open(SALIDA, "rb") as flujo:
            salida_previa = flujo.read()
        with open(PAGINA, "rb") as flujo:
            pagina_previa = flujo.read()
        _medicion("salida reproducida", salida_previa == salida)
        _medicion("pagina reproducida", pagina_previa == (pagina + "\n").encode("utf-8"))
        if salida_previa != salida or pagina_previa != (pagina + "\n").encode("utf-8"):
            print("DIVERGE | la pagina declarada no describe este arbol")
            return 1
        print("REPRODUCE | %s" % digest.digest)
        _medicion("veredicto declarado", _json.loads(pagina_previa.decode("utf-8"))["veredicto"])
        return 0

    es_fixture = (
        _os.path.realpath(raiz) == _os.path.realpath(MUESTRA)
        and _os.path.realpath(ruta_manifiesto)
        == _os.path.realpath(_os.path.join(MUESTRA, "MANIFIESTO.txt"))
    )
    if not es_fixture:
        # La pagina congelada pertenece a la fixture: escribirla con otro
        # sujeto sustituiria la regresion por el acto, y la regresion dejaria
        # de contradecir a su lector. Un sujeto ajeno se mide y se reporta.
        _medicion("acto", "solo lectura: el sujeto no es la fixture, no se escribe pagina")
    else:
        _escribir(SALIDA, salida)
        _escribir(PAGINA, (pagina + "\n").encode("utf-8"))
        _medicion("pagina", PAGINA)
    _medicion("manifiesto", ruta_manifiesto)
    _medicion("raiz", raiz)
    _medicion("dialecto del manifiesto", manifiesto.dialecto)
    _medicion("rutas con prefijo ./ normalizadas", manifiesto.prefijadas)
    _medicion("universo", (indice.leidas, fuente))
    _medicion("omitidas", len(indice.omitidas))
    _medicion("fuera del universo", indice.fuera_del_universo)
    _medicion("adjudicacion", adjudicacion.resumen())
    for testigo in adjudicacion.testigos():
        _medicion("testigo", testigo)
    _medicion("lineas", len(pagina.splitlines()))
    _medicion("bytes", len(pagina.encode("utf-8")))
    _medicion("digest", digest.digest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(tuple(_sys.argv[1:])))
