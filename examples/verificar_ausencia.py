"""examples/verificar_ausencia.py — un acto: probar que una ruta NO esta.

Uso:

    python3 -B examples/verificar_ausencia.py                            # fixture
    python3 -B examples/verificar_ausencia.py --ausente debug.key
    python3 -B examples/verificar_ausencia.py \\
        --manifiesto ../platino-labs/sellos-fecha-cierta-20261009/SHA256SUMS_SELLO_A \\
        --raiz ../platino-labs --ausente tools/sembrar_boveda.sh
    python3 -B examples/verificar_ausencia.py --ausente x.txt --merkle   # testigo transferible

La pregunta es negativa y por eso no la contesta ningun verificador de hashes.
`sha256sum -c` certifica lo que el manifiesto declara; no puede decir nada de lo
que no declara, porque su universo es la lista de filas. Aqui el universo es la
**pagina entera**, y el testigo es un intervalo: la fila mayor que la consulta y
la fila menor que la consulta, **adyacentes en el orden canonico**.

Que la adyacencia sea la que prueba y no el intervalo suelto es el punto
aritmetico del acto. Entre dos filas cualesquiera siempre cabe algo; entre dos
filas consecutivas de una secuencia comprometida, no. De ahi salen los dos
dialectos de testigo, y el acto publica en cual decidio:

- **con la pagina delante** el testigo se verifica en O(1) por consulta —se
  comprueba la posicion, no se busca— pero **autenticar la pagina cuesta O(n)
  una vez**. El O(1) sin mas es falso: ignora la autenticacion.
- **con `--merkle`** el testigo son dos caminos de inclusion de O(log n) digests
  y se verifica contra una raiz de 32 bytes **sin** la pagina. Es lo que se puede
  entregar a un tercero a quien no se le quiere dar el inventario.

El orden se declara, no se hereda del volumen. La pagina ordena por bytes UTF-8
sobre el alfabeto de §2.1; un sistema de archivos puede plegar mayusculas, y
donde las pliega `a.txt` y `A.txt` son **el mismo archivo** aunque sean dos filas
distintas del orden. El acto mide el regimen del volumen y lo publica; si la
consulta colapsa con una fila, contesta `no_medida` en vez de elegir.

Y el nombre no es el archivo: la pagina declara **rutas**, el arbol puede tener
un **directorio** con ese nombre. `vendor` no esta declarado y existe; por eso
con `--raiz` la respuesta compone las dos preguntas y las publica por separado.

Codigo de salida. La escalera del acto de sello es `0/0/1/1/2` y no distingue
«bloqueado» de «no se sabe»; una compuerta de CI si tiene que distinguirlos:

- `0` la ausencia se sostiene (`ausente`).
- `1` no se sostiene (`presente`: la pagina lo declara, o el arbol lo tiene).
- `2` la entrada no se puede leer (manifiesto ilegible, consulta fuera del
  alfabeto, pagina vacia).
- `3` **no se pudo medir** (`no_medida`): pagina con huecos, ruta fuera del
  universo, o el nombre existe como directorio. Un `3` no es un `0`: no haber
  mirado no es un cero.
"""

from __future__ import annotations

import os as _os
import subprocess as _subprocess
import sys as _sys
import time as _time

RAIZ = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
if RAIZ not in _sys.path:
    _sys.path.insert(0, RAIZ)

from src.protocol.ausencia import (  # noqa: E402
    ORDEN_DECLARADO,
    Testigo,
    VeredictoDeAusencia,
    autenticar,
    consultar,
    pagina_desde_manifiesto,
    raiz_merkle,
    testigo_merkle,
    verificar,
    verificar_merkle,
)
from src.protocol.types import ContratoViolado  # noqa: E402
from src.protocol.ubicacion import leer_manifiesto  # noqa: E402

EJEMPLOS = _os.path.join(RAIZ, "examples")
MUESTRA = _os.path.join(EJEMPLOS, "sello-de-muestra")
EXCLUSIONES = (".git", "__pycache__", ".venv", "node_modules", ".mypy_cache", ".pytest_cache")

#: Regimenes de plegado del volumen. Se publican: el regimen es entrada, no
#: detalle del observador, y cambia lo que la pagina puede probar.
COLAPSA = "colapsa-el-caso"
DISTINGUE = "distingue-el-caso"
SIN_MEDIR = "no-medido"


def _medicion(etiqueta: str, valor: object) -> None:
    print("MEDICION | %s | %s" % (etiqueta, valor))


def _argumento(argv: tuple, nombre: str, defecto: str) -> str:
    if nombre in argv:
        posicion = argv.index(nombre)
        if posicion + 1 >= len(argv):
            raise SystemExit("falta el valor de %s" % nombre)
        return argv[posicion + 1]
    return defecto


def _voltear_caso(ruta: str) -> str:
    """La misma ruta con la primera letra ASCII cambiada de caja."""

    for i, caracter in enumerate(ruta):
        if "a" <= caracter <= "z":
            return ruta[:i] + caracter.upper() + ruta[i + 1 :]
        if "A" <= caracter <= "Z":
            return ruta[:i] + caracter.lower() + ruta[i + 1 :]
    return ""


def regimen_de_caso(raiz: str, candidatas: tuple) -> tuple:
    """Mide si el volumen pliega mayusculas. Devuelve (regimen, nota, ruta_sonda).

    No escribe nada: voltea la caja de una ruta que ya existe y compara inodos.
    Mismo inodo ⇒ el volumen las trata como el mismo archivo; inodo distinto ⇒
    son dos archivos y el volumen distingue; no resuelve ⇒ distingue. Se sondean
    varias rutas porque una puede no tener letras o chocar con un archivo real.
    """

    for ruta in candidatas:
        volteada = _voltear_caso(ruta)
        if not volteada or volteada == ruta:
            continue
        original = _os.path.join(raiz, ruta)
        otra = _os.path.join(raiz, volteada)
        try:
            a = _os.stat(original)
        except OSError:
            continue
        try:
            b = _os.stat(otra)
        except OSError:
            return DISTINGUE, "sonda %s -> %s no resuelve" % (ruta, volteada), ruta
        if a.st_ino == b.st_ino and a.st_dev == b.st_dev:
            return COLAPSA, "sonda %s -> %s es el mismo inodo" % (ruta, volteada), ruta
        return DISTINGUE, "sonda %s -> %s es otro inodo" % (ruta, volteada), ruta
    return SIN_MEDIR, "ninguna ruta declarada admite sonda de caso", ""


def _en_universo(raiz: str, ruta: str, modo: str) -> tuple:
    """¿La ruta cae dentro del universo que el arbol indexa? (estado, nota).

    Es la mitad de la ley de proyeccion: la pagina prueba algo sobre sus filas, y
    el arbol solo puede confirmarlo sobre las rutas que su universo indexa.
    """

    if modo == "git" or modo == "auto":
        proceso = _subprocess.run(
            ["git", "-C", raiz, "ls-files", "--error-unmatch", "--", ruta],
            stdout=_subprocess.DEVNULL,
            stderr=_subprocess.DEVNULL,
        )
        if modo == "git":
            if proceso.returncode == 0:
                return "dentro", "git ls-files lo indexa"
            if proceso.returncode == 1:
                return "fuera", "git ls-files no lo versiona"
            return "sin_medir", "git ls-files respondio %d" % proceso.returncode
    partes = ruta.split("/")
    if any(p in EXCLUSIONES for p in partes):
        return "fuera", "la caminata excluye %s" % next(p for p in partes if p in EXCLUSIONES)
    return "dentro", "la caminata no lo excluye"


def main(argv: tuple) -> int:
    marca = _time.monotonic()
    ruta_manifiesto = _argumento(argv, "--manifiesto", _os.path.join(MUESTRA, "MANIFIESTO.txt"))
    consulta = _argumento(argv, "--ausente", "")
    raiz = _argumento(argv, "--raiz", "")
    modo = _argumento(argv, "--universo", "auto")
    if modo == "auto":
        # El acto de sello resuelve `auto` a git porque busca artefactos
        # declarados, y lo declarado esta versionado por definicion. La ausencia
        # pregunta por lo que **no** esta declarado, y ahi la mitad interesante
        # (secretos, salidas de build, copias vendorizadas) nunca se versiona:
        # un universo git no puede probar su ausencia por construccion.
        modo = "disco"
    con_merkle = "--merkle" in argv

    if not consulta:
        print("ENTRADA INVALIDA | --ausente | la consulta es obligatoria")
        return 2
    if modo not in ("auto", "git", "disco"):
        print("ENTRADA INVALIDA | --universo | %s no es un universo" % modo)
        return 2
    try:
        with open(ruta_manifiesto, "r", encoding="utf-8") as flujo:
            manifiesto = leer_manifiesto(flujo.read(), _os.path.basename(ruta_manifiesto))
    except (OSError, UnicodeDecodeError) as fallo:
        print("ENTRADA INVALIDA | %s | no se puede leer" % ruta_manifiesto)
        _medicion("motivo", type(fallo).__name__)
        return 2
    except ContratoViolado as fallo:
        print("ENTRADA INVALIDA | %s | %s" % (_os.path.basename(ruta_manifiesto), fallo))
        return 2
    if raiz and not _os.path.isdir(raiz):
        print("ENTRADA INVALIDA | %s | la raiz del universo no es un directorio" % raiz)
        return 2

    try:
        pagina = pagina_desde_manifiesto(manifiesto)
        testigo = consultar(pagina, consulta)
    except ContratoViolado as fallo:
        print("ENTRADA INVALIDA | %s | %s" % (consulta, fallo))
        return 2

    veredicto = testigo.estado
    print(
        "ausencia | %s | %s | %s"
        % (testigo.consulta, testigo.estado.value, testigo.motivo or "sin motivo")
    )
    print("orden | %s" % ORDEN_DECLARADO)
    print(
        "pagina | %d %s | %s | %d redactadas | digest %s"
        % (
            len(pagina.filas),
            "fila" if len(pagina.filas) == 1 else "filas",
            "desordenada" if pagina.desordenada else "canonica",
            pagina.redactadas,
            pagina.digest,
        )
    )
    if testigo.estado is VeredictoDeAusencia.AUSENTE:
        print("testigo | %s | posicion %d" % (testigo.intervalo(), testigo.posicion))
    elif testigo.estado is VeredictoDeAusencia.PRESENTE:
        print("testigo | fila %d | %s" % (testigo.posicion, testigo.anterior.ruta if testigo.anterior else ""))

    autenticada = autenticar(pagina) == pagina.digest
    print("verificado | %s | O(1) contra la pagina autenticada" % ("si" if verificar(pagina, testigo) else "no"))
    print("autenticacion | %s | O(n) una vez | %d filas" % ("si" if autenticada else "no", len(pagina.filas)))

    if con_merkle:
        transferible = testigo_merkle(pagina, consulta)
        print(
            "merkle | raiz %s | tamano %d | %s"
            % (transferible.raiz, transferible.tamano, "prueba %d digests" % (
                len(transferible.camino_anterior) + len(transferible.camino_siguiente)
            ))
        )
        print("merkle-verificado | %s | sin la pagina" % ("si" if verificar_merkle(transferible) else "no"))

    # El regimen del caso es entrada. Donde el volumen pliega mayusculas, la
    # pagina puede probar `a.txt` ausente y el arbol tener esos mismos bytes bajo
    # `A.txt`: dos filas del orden, un solo archivo.
    if raiz:
        regimen, nota, sonda = regimen_de_caso(raiz, tuple(f.ruta for f in pagina.filas))
        print("caso | %s | %s" % (regimen, nota))
        if regimen == COLAPSA:
            plegada = testigo.consulta.casefold()
            choque = [f.ruta for f in pagina.filas if f.ruta.casefold() == plegada and f.ruta != testigo.consulta]
            if choque:
                print(
                    "caso-choque | %s | la pagina prueba %s y el volumen no distingue %s"
                    % (choque[0], testigo.consulta, choque[0])
                )
                veredicto = VeredictoDeAusencia.NO_MEDIDA
        _medicion("sonda de caso", sonda or "sin sonda")

    # La segunda mitad de la ley de proyeccion: la pagina habla de filas, el
    # arbol de rutas indexadas. Sólo se compone cuando la pagina ya dijo
    # `ausente`: si la pagina declara la ruta, o no pudo ordenarla, preguntarle
    # al arbol agrega un sujeto y no una prueba.
    if raiz and testigo.estado is VeredictoDeAusencia.AUSENTE:
        universo = modo
        dentro, nota = _en_universo(raiz, testigo.consulta, universo)
        absoluta = _os.path.join(raiz, testigo.consulta)
        existe = _os.path.lexists(absoluta)
        es_directorio = existe and _os.path.isdir(absoluta)
        print("arbol | %s | %s" % (universo, nota))
        if dentro != "dentro":
            print("arbol-ausencia | no_medida | %s" % nota)
            veredicto = VeredictoDeAusencia.NO_MEDIDA
        elif es_directorio:
            print("arbol-ausencia | no_medida | el nombre existe como directorio: la pagina declara rutas, no prefijos")
            veredicto = VeredictoDeAusencia.NO_MEDIDA
        elif existe:
            print("arbol-ausencia | presente | el arbol lo tiene y la pagina no lo declara")
            veredicto = VeredictoDeAusencia.PRESENTE
        else:
            print("arbol-ausencia | ausente | el universo lo indexa y no esta")
    else:
        print("arbol | (no medido: sin --raiz) | la respuesta es sobre la pagina")

    print("-> %s" % veredicto.value)
    codigos = {
        VeredictoDeAusencia.AUSENTE: 0,
        VeredictoDeAusencia.PRESENTE: 1,
        VeredictoDeAusencia.NO_MEDIDA: 3,
    }
    codigo = codigos[veredicto]
    with open(ruta_manifiesto, "rb") as flujo:
        _medicion("lineas", len(flujo.read().splitlines()))
    print(
        "coste | %d declaradas | %d autenticadas | %s"
        % (len(pagina.filas), len(pagina.filas), "con merkle" if con_merkle else "sin merkle")
    )
    _medicion("reloj de duracion ms", int((_time.monotonic() - marca) * 1000))
    _medicion("codigo de salida", codigo)
    return codigo


if __name__ == "__main__":
    _sys.exit(main(tuple(_sys.argv[1:])))
