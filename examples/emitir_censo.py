"""examples/emitir_censo.py — el segundo acto: contar el universo y publicar la discrepancia.

Uso:

    python3 -B examples/emitir_censo.py           # observa, compara y sella la página
    python3 -B examples/emitir_censo.py --check   # re-observa y compara: reproduce o diverge

Qué compra quien compra esto. La cifra honesta de un corpus no es «cuántos
hay»: es el par `declarado − observado`. El lado declarado vive en
`examples/censo-declarado.txt` y lo escribe una persona antes de ver el
resultado; el observado lo mide `protocol.audit.census` sobre el árbol; la
discrepancia es la resta. Los tres viajan en la salida. Publicar dos de los
tres es publicar una cifra que nadie puede refutar.

Límites declarados:

  1. El censo NO descuenta el pie del instrumento (§lectura 1 de `audit`), y en
     este acto el instrumento vive **dentro** del universo contado: `audit.py`
     está en `src/protocol`. Se declara en `entorno.no_medido` en vez de
     restarlo, porque restar un pie no enumerado es el doble descuento de §3.c.
  2. El acto **no lleva reloj**. `t_utc` se hereda del lado declarado y la fecha
     cierta la aporta el ancla (§4 de `PREDICADO.md`): el predicado prueba qué,
     el ancla prueba cuándo. Un `t_utc` de pared haría irreproducible el acto, y
     un `--check` que se saltara el reloj sería un falso verde en la dirección
     peligrosa.
  3. Si el universo contiene artefactos de byte-compilación del intérprete
     (`__pycache__`, `*.pyc`), el acto NO corre. Contarlos haría que el número
     dependiera de quién ejecutó Python antes en esta máquina; borrarlos en
     silencio sería medir un universo que ya no es el que hay.

Lo que este script **no** hace: no firma y no ancla. Emite el enunciado; la
contrafirma con fecha cierta es otro acto y otro objeto.
"""

from __future__ import annotations

import hashlib as _hashlib
import json as _json
import os as _os
import sys as _sys

RAIZ = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
EJEMPLOS = _os.path.join(RAIZ, "examples")
DECLARADO = _os.path.join(EJEMPLOS, "censo-declarado.txt")
SALIDA = _os.path.join(EJEMPLOS, "censo-vigente.txt")
PAGINA = _os.path.join(EJEMPLOS, "predicado-censo.json")

_sys.path.insert(0, _os.path.join(RAIZ, "src"))

from protocol.audit import census, volumen_medido  # noqa: E402
from protocol.predicado import Entorno, Predicado, VeredictoReclamado  # noqa: E402
from protocol.types import (  # noqa: E402
    ALGORITMO,
    Contexto,
    EntradaManifiesto,
    Hash,
    RutaRelativa,
    Unidad,
)

_UNIDADES = {"archivo": Unidad.ARCHIVO, "byte": Unidad.BYTE, "linea": Unidad.LINEA}

_CAMPOS_DECLARADOS = ("ruta", "universo", "unidad", "motor", "t_utc", "ventana", "umbral")


def _medicion(etiqueta: str, valor: object) -> None:
    print("MEDICION | %s | %s" % (etiqueta, valor))


def _declaracion() -> dict:
    """Lee el lado declarado. Falla cerrado si falta un campo o sobra uno."""

    valores = {}
    with open(DECLARADO, "r", encoding="utf-8") as flujo:
        for numero, linea in enumerate(flujo, 1):
            limpia = linea.strip()
            if not limpia or limpia.startswith("#"):
                continue
            clave, _, valor = limpia.partition("=")
            if not _:
                raise SystemExit("censo-declarado.txt:%d no es clave=valor" % numero)
            valores[clave.strip()] = valor.strip()

    faltan = [campo for campo in _CAMPOS_DECLARADOS if not valores.get(campo)]
    if faltan:
        raise SystemExit("el lado declarado está incompleto: %r" % (faltan,))
    sobran = [clave for clave in valores if clave not in _CAMPOS_DECLARADOS + ("declarado",)]
    if sobran:
        raise SystemExit("el lado declarado tiene claves que nadie lee: %r" % (sobran,))
    return valores


def _exigir_universo_limpio(raiz: str) -> None:
    """El intérprete deja basura que no viaja con el código: se para, no se borra."""

    sucio = []
    for directorio, subdirectorios, archivos in _os.walk(raiz):
        if "__pycache__" in subdirectorios:
            sucio.append(_os.path.join(directorio, "__pycache__"))
        sucio.extend(
            _os.path.join(directorio, nombre) for nombre in archivos if nombre.endswith(".pyc")
        )
    if sucio:
        raise SystemExit(
            "el universo contiene artefactos de byte-compilación y no se mide: %r. "
            "Contarlos ata el número a quién ejecutó Python antes." % (sorted(sucio)[:3],)
        )


def _observado(declaracion: dict) -> int:
    """Cuenta el universo declarado y devuelve la cifra, con su etiqueta de validez."""

    ruta = RutaRelativa(declaracion["ruta"])
    raiz = _os.path.join(RAIZ, ruta.texto)
    _exigir_universo_limpio(raiz)

    ctx = Contexto(
        universo=declaracion["universo"],
        unidad=_UNIDADES[declaracion["unidad"]],
        motor=declaracion["motor"],
        t_utc=declaracion["t_utc"],
        ventana=declaracion["ventana"],
        umbral=declaracion["umbral"],
    )
    fd = _os.open(raiz, _os.O_RDONLY)
    try:
        etiqueta = census(volumen_medido(fd, declaracion["universo"]), ctx)
    finally:
        _os.close(fd)
    return etiqueta.valor


def _discrepancia(declarado: str, observado: int) -> tuple:
    """El operador: `observado − declarado`, o `NO_MEDIDO` si no hay contra qué."""

    if declarado == "":
        return "NO_MEDIDO", VeredictoReclamado.NO_MEDIDO
    esperado = int(declarado)
    diferencia = observado - esperado
    veredicto = (
        VeredictoReclamado.CONFORME if diferencia == 0 else VeredictoReclamado.NO_CONFORME
    )
    return str(diferencia), veredicto


def _vigente(declaracion: dict, observado: int, diferencia: str) -> bytes:
    lineas = [
        "universo=%s" % declaracion["universo"],
        "unidad=%s" % declaracion["unidad"],
        "motor=%s" % declaracion["motor"],
        "t_utc=%s" % declaracion["t_utc"],
        "ventana=%s" % declaracion["ventana"],
        "umbral=%s" % declaracion["umbral"],
        "ruta=%s" % declaracion["ruta"],
        "declarado=%s" % (declaracion.get("declarado") or "NO_MEDIDO"),
        "observado=%d" % observado,
        "discrepancia=%s" % diferencia,
    ]
    return ("\n".join(lineas) + "\n").encode("utf-8")


def _referencias(relativas: tuple) -> tuple:
    entradas = []
    for relativa in relativas:
        with open(_os.path.join(RAIZ, relativa), "rb") as flujo:
            digest = _hashlib.sha256(flujo.read()).hexdigest()
        entradas.append(EntradaManifiesto(RutaRelativa(relativa), Hash(ALGORITMO, digest)))
    return tuple(entradas)


def _entradas(declaracion: dict) -> tuple:
    """TODO objeto del universo declarado, con su hash: la cifra se ata a los bytes."""

    prefijo = declaracion["ruta"].rstrip("/")
    relativas = []
    for directorio, _, archivos in _os.walk(_os.path.join(RAIZ, prefijo)):
        for nombre in archivos:
            absoluta = _os.path.join(directorio, nombre)
            relativas.append(_os.path.relpath(absoluta, RAIZ).replace(_os.sep, "/"))
    return _referencias(sorted(relativas))


def _codigo() -> tuple:
    # El `codigo` de un acto son los módulos que el acto **necesita**, no todo
    # lo que haya en el paquete. Un glob mete en la identidad del acto módulos
    # que no ejecuta: al entrar `ubicacion.py` en `src/protocol`, la página del
    # censo cambió sin que el censo cambiara, y una contrafirma viva quedó
    # RANCIA por un módulo que el acto no importa. El alcance del acto es el
    # del acto (§A2.4), no el del directorio.
    fuente = (
        "src/protocol/audit.py",
        "src/protocol/predicado.py",
        "src/protocol/types.py",
        "examples/emitir_censo.py",
    )
    return _referencias(tuple(sorted(fuente)))


def _predicado(
    declaracion: dict, observado: int, diferencia: str, veredicto: VeredictoReclamado, salida: bytes
) -> Predicado:
    if declaracion.get("declarado"):
        afirmacion = (
            "el universo %s cuenta %d (%s); la declaracion vigente dice %s; "
            "la discrepancia es %s"
            % (
                declaracion["universo"],
                observado,
                declaracion["unidad"],
                declaracion["declarado"],
                diferencia,
            )
        )
    else:
        afirmacion = (
            "el universo %s cuenta %d (%s) y no hay declaracion vigente contra la que comparar"
            % (declaracion["universo"], observado, declaracion["unidad"])
        )
    return Predicado(
        afirmacion=afirmacion,
        entradas=_entradas(declaracion),
        codigo=_codigo(),
        entorno=Entorno(
            _sys.platform,
            "CPython %d.%d.%d" % _sys.version_info[:3],
            (
                "el instrumento vive dentro del universo contado: el censo no descuenta su pie",
                "el instante del censo lo aporta el ancla, no un reloj de pared",
                "plataformas distintas de la de esta corrida: no medidas desde aqui",
            ),
        ),
        salida=EntradaManifiesto(
            RutaRelativa("examples/censo-vigente.txt"),
            Hash(ALGORITMO, _hashlib.sha256(salida).hexdigest()),
        ),
        veredicto=veredicto,
        h_prev=None,
    )


def main(argv: tuple) -> int:
    declaracion = _declaracion()
    observado = _observado(declaracion)
    diferencia, veredicto = _discrepancia(declaracion.get("declarado", ""), observado)
    salida = _vigente(declaracion, observado, diferencia)
    predicado = _predicado(declaracion, observado, diferencia, veredicto, salida)
    digest = predicado.digest()
    pagina = predicado.pagina()

    _medicion("declarado", declaracion.get("declarado") or "NO_MEDIDO")
    _medicion("observado", observado)
    _medicion("discrepancia", diferencia)

    if "--check" in argv:
        if not _os.path.exists(PAGINA) or not _os.path.exists(SALIDA):
            print("NO_MEDIDO: no hay pagina previa que reproducir")
            return 2
        with open(SALIDA, "rb") as flujo:
            salida_previa = flujo.read()
        with open(PAGINA, "rb") as flujo:
            pagina_previa = flujo.read()
        _medicion("salida reproducida", salida_previa == salida)
        # La página se compara entera: comparar sólo la salida dejaría pasar una
        # página rancia con cifra fresca, que es el falso verde que este acto mide.
        _medicion("pagina reproducida", pagina_previa == (pagina + "\n").encode("utf-8"))
        if salida_previa != salida or pagina_previa != (pagina + "\n").encode("utf-8"):
            print("DIVERGE | la pagina declarada no describe este arbol")
            return 1
        print("REPRODUCE | %s" % digest.digest)
        _medicion("veredicto declarado", veredicto.value)
        return 0

    with open(SALIDA, "wb") as flujo:
        flujo.write(salida)
    with open(PAGINA, "wb") as flujo:
        flujo.write((pagina + "\n").encode("utf-8"))
    _medicion("pagina", PAGINA)
    _medicion("lineas", len(pagina.splitlines()))
    _medicion("bytes", len(pagina.encode("utf-8")))
    _medicion("digest", digest.digest)
    _medicion("referencias", (len(predicado.entradas), len(predicado.codigo)))
    _medicion("veredicto", veredicto.value)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(tuple(_sys.argv[1:])))
