"""examples/verificar_recibo_externo.py — un tercero que no llama al generador.

Uso:

    python3 -B examples/verificar_recibo_externo.py --recibo recibo.json
    python3 -B examples/verificar_recibo_externo.py --recibo recibo.json \\
        --manifiesto SHA256SUMS --ausente "cita-09:00-sillon1"
    python3 -B examples/verificar_recibo_externo.py --recibo recibo.json --demo

QUE PRUEBA. Que un recibo se pueda cerrar **sin ejecutar el codigo que lo
produjo**. El verificador no importa `protocol`: reescribe por su cuenta el
formato canonico, el digest de pagina, la tabla de degradacion y la busqueda de
vecinos. Si los dos coinciden es porque el formato esta escrito y no porque los
dos llamen a la misma funcion; si divergen, el desacuerdo es el hallazgo.

QUE RECIBE. Solo el JSON del recibo (que lleva sus paginas dentro) y, si se le
da, el manifiesto publicado. Nada mas: ni el arbol, ni el generador, ni la
maquina donde se produjo.

QUE QUEDA FUERA, y se publica. Comprueba que las paginas encadenadas son las
mismas de punta a punta; **no comprueba que el nodo intermedio hiciera su
trabajo**. Un recibo certifica continuidad de bytes, no correccion de la
transformacion: quien transformo pudo aplicar el cambio equivocado y firmarlo.

Codigo de salida:

- `0` la prueba cierra.
- `1` algo fue alterado (digest, frontera, vecinos, veredicto publicado).
- `2` la entrada no se puede leer (JSON roto, pagina desordenada, falta un
  campo obligatorio).
"""

from __future__ import annotations

import hashlib as _hashlib
import json as _json
import sys as _sys
from typing import Dict, List, Optional, Sequence, Tuple

#: Se reescribe, no se importa. Es la unica forma de que la comparacion mida
#: algo: dos modulos que importan la misma constante siempre coinciden.
FORMATO_CANONICO = "%s  %s\n"

#: El orden declarado en `UBICACION.md` §4, de mejor a peor, con `frontera_rota`
#: encima porque un empalme roto invalida la cadena entera y no un tramo.
RANGO: Tuple[str, ...] = (
    "intacta",
    "reubicada",
    "no_medida",
    "intercambiada",
    "suplantada",
    "divergente",
    "frontera_rota",
)

SOSTIENEN: Tuple[str, ...] = ("intacta", "reubicada")


class EntradaInvalida(Exception):
    """Un fallo de la entrada, no del recibo. Sale con 2."""


def _rango(veredicto: str) -> int:
    if veredicto not in RANGO:
        raise EntradaInvalida("veredicto desconocido: %r" % (veredicto,))
    return RANGO.index(veredicto)


def _filas(crudas: object, donde: str) -> List[Tuple[str, str, str]]:
    """`(ruta, digest, motivo)` en el orden en que vienen escritas."""

    if not crudas:
        return []
    if not isinstance(crudas, list):
        raise EntradaInvalida("la pagina de %s no es una lista" % donde)
    salida = []
    for cruda in crudas:
        if not isinstance(cruda, dict) or "ruta" not in cruda or "digest" not in cruda:
            raise EntradaInvalida("fila sin ruta o sin digest en %s" % donde)
        digest = str(cruda["digest"])
        if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            raise EntradaInvalida("digest no hexadecimal de 64 en %s: %r" % (donde, digest))
        salida.append((str(cruda["ruta"]), digest, str(cruda.get("motivo", ""))))
    return salida


def _digest_de_pagina(filas: Sequence[Tuple[str, str, str]], donde: str) -> str:
    """Recalcula el digest **en el orden recibido**, y exige que sea el canonico.

    Ordenar aqui seria comprobar otra cosa: el digest autentica una secuencia, y
    una secuencia que se puede reordenar sin cambiar el digest no autentica el
    orden, que es justo lo que la prueba de ausencia usa.
    """

    for previa, actual in zip(filas, filas[1:]):
        if not previa[0].encode("utf-8") < actual[0].encode("utf-8"):
            raise EntradaInvalida(
                "pagina de %s fuera del orden canonico: %r antes de %r"
                % (donde, previa[0], actual[0])
            )
    texto = "".join(FORMATO_CANONICO % (digest, ruta) for ruta, digest, _ in filas)
    return _hashlib.sha256(texto.encode("utf-8")).hexdigest()


def _vecinos(filas: Sequence[Tuple[str, str, str]], consulta: str) -> Dict[str, object]:
    """La consulta negativa, resuelta sin creerse nada del testigo declarado."""

    claves = [ruta.encode("utf-8") for ruta, _, _ in filas]
    objetivo = consulta.encode("utf-8")
    anterior: Optional[str] = None
    siguiente: Optional[str] = None
    posicion = 0
    for indice, clave in enumerate(claves):
        if clave == objetivo:
            return {"estado": "presente", "posicion": indice}
        if clave < objetivo:
            anterior = filas[indice][0]
            posicion = indice
        elif siguiente is None:
            siguiente = filas[indice][0]
    opacas = [ruta for ruta, _, motivo in filas if motivo]
    if opacas:
        return {"estado": "no_medida", "motivo": "huecos: %s" % ",".join(opacas)}
    return {"estado": "ausente", "anterior": anterior, "siguiente": siguiente, "posicion": posicion}


def verificar(recibo: Dict[str, object], manifiesto: Optional[str], ausente: Optional[str]) -> Tuple[int, List[str]]:
    lineas: List[str] = []
    fallos = 0
    tramos = recibo.get("tramos")
    if not isinstance(tramos, list) or not tramos:
        raise EntradaInvalida("el recibo no trae tramos")
    ultima: List[Tuple[str, str, str]] = []
    previo_destino: Optional[str] = None
    for indice, tramo in enumerate(tramos):
        if not isinstance(tramo, dict):
            raise EntradaInvalida("el tramo %d no es un objeto" % indice)
        origen = _filas(tramo.get("pagina_origen"), "origen")
        destino = _filas(tramo.get("pagina_destino"), "destino")
        d_origen = _digest_de_pagina(origen, "origen") if origen else ""
        d_destino = _digest_de_pagina(destino, "destino") if destino else ""
        veredicto = str(tramo.get("veredicto", ""))
        _rango(veredicto)
        declarado_origen = str(tramo.get("digest_origen", ""))
        declarado_destino = str(tramo.get("digest_destino", ""))
        if declarado_origen != d_origen:
            fallos += 1
            lineas.append(
                "tramo | %s->%s | digest de origen alterado | declarado %s | recalculado %s"
                % (tramo.get("origen"), tramo.get("destino"), declarado_origen[:12] or "vacio", d_origen[:12] or "vacio")
            )
        if declarado_destino != d_destino:
            fallos += 1
            lineas.append(
                "tramo | %s->%s | digest de destino alterado | declarado %s | recalculado %s"
                % (tramo.get("origen"), tramo.get("destino"), declarado_destino[:12] or "vacio", d_destino[:12] or "vacio")
            )
        if previo_destino is not None and d_origen and previo_destino != d_origen:
            fallos += 1
            lineas.append(
                "frontera | rota | el tramo previo dejo %s y este leyo %s"
                % (previo_destino[:12], d_origen[:12])
            )
        elif previo_destino is not None and not d_origen:
            lineas.append("frontera | sin medir | el tramo no trae pagina de origen")
        else:
            lineas.append("tramo | %s->%s | %s | %d filas | %s" % (
                tramo.get("origen"), tramo.get("destino"), veredicto, len(destino), d_destino[:12] or "vacio"))
        previo_destino = d_destino or None
        if origen:
            ultima = origen
        if destino:
            ultima = destino
        for testigo in tramo.get("testigos", ()):  # type: ignore[union-attr]
            if not isinstance(testigo, dict):
                raise EntradaInvalida("testigo ilegible en el tramo %d" % indice)
            declarada = str(testigo.get("digest_pagina", ""))
            if declarada not in (d_destino, d_origen):
                fallos += 1
                lineas.append(
                    "testigo | %s | declara una pagina que el recibo no trae | %s"
                    % (testigo.get("consulta"), declarada[:12] or "vacio")
                )
                continue
            esperado = _vecinos(destino if declarada == d_destino else origen, str(testigo.get("consulta")))
            if esperado.get("estado") != testigo.get("estado"):
                fallos += 1
                lineas.append(
                    "testigo | %s | estado alterado | declarado %s | recalculado %s"
                    % (testigo.get("consulta"), testigo.get("estado"), esperado.get("estado"))
                )
                continue
            if esperado.get("estado") == "ausente" and (
                esperado.get("anterior") != testigo.get("anterior")
                or esperado.get("siguiente") != testigo.get("siguiente")
            ):
                fallos += 1
                lineas.append(
                    "testigo | %s | vecinos alterados | declarado %s..%s | recalculado %s..%s"
                    % (testigo.get("consulta"), testigo.get("anterior"), testigo.get("siguiente"),
                       esperado.get("anterior"), esperado.get("siguiente"))
                )
                continue
            lineas.append(
                "testigo | %s | %s | %s < consulta < %s"
                % (testigo.get("consulta"), testigo.get("estado"), esperado.get("anterior"), esperado.get("siguiente"))
            )

    publicado = str(recibo.get("veredicto", ""))
    if recibo.get("frontera"):
        peor = "frontera_rota"
    else:
        peor = max((str(t.get("veredicto", "")) for t in tramos if isinstance(t, dict)), key=_rango)
        if recibo.get("frontera_vacua") and _rango(peor) < _rango("no_medida"):
            peor = "no_medida"
    if publicado != peor:
        fallos += 1
        lineas.append("veredicto | alterado | declarado %s | recalculado %s" % (publicado, peor))
    else:
        lineas.append("veredicto | %s | recalculado sobre %d tramos | sostiene %s" % (
            peor, len(tramos), "si" if peor in SOSTIENEN else "no"))

    if manifiesto is not None and ultima:
        crudas = []
        for numero, linea in enumerate(manifiesto.splitlines(), 1):
            if not linea.strip():
                continue
            partes = linea.split("  ", 1)
            if len(partes) != 2:
                raise EntradaInvalida("linea %d del manifiesto sin dos columnas" % numero)
            crudas.append((partes[1], partes[0], ""))
        ordenado = all(a[0].encode() < b[0].encode() for a, b in zip(crudas, crudas[1:]))
        canonica = sorted(crudas, key=lambda fila: fila[0].encode("utf-8"))
        d_manifiesto = _digest_de_pagina(canonica, "manifiesto")
        ultimo = _digest_de_pagina(ultima, "ultima")
        if d_manifiesto != ultimo:
            fallos += 1
            lineas.append("manifiesto | no reproduce la ultima pagina | %s | %s" % (d_manifiesto[:12], ultimo[:12]))
        else:
            lineas.append("manifiesto | %d filas | %s | archivo %s" % (
                len(crudas), d_manifiesto[:12], "ya canonico" if ordenado else "fuera de orden, reordenado y reproducido"))

    if ausente is not None:
        if not ultima:
            lineas.append("ausencia | no_medida | el recibo no trae pagina final")
        else:
            vecino = _vecinos(ultima, ausente)
            lineas.append("ausencia | %s | %s" % (ausente, vecino.get("estado")))
            if vecino.get("estado") == "ausente":
                lineas.append("intervalo | %s < %s < %s | adyacentes en la pagina sellada" % (
                    vecino.get("anterior"), ausente, vecino.get("siguiente")))

    lineas.append("limite | el verificador comprueba que las paginas encadenadas son las mismas; no que B hiciera su trabajo")
    return (0 if fallos == 0 else 1), lineas


def _demo() -> Dict[str, object]:
    filas = [
        {"ruta": "cita-09:00-sillon1", "digest": _hashlib.sha256(b"a").hexdigest(), "motivo": ""},
        {"ruta": "cita-10:00-sillon2", "digest": _hashlib.sha256(b"b").hexdigest(), "motivo": ""},
    ]
    d = _hashlib.sha256("".join(FORMATO_CANONICO % (f["digest"], f["ruta"]) for f in filas).encode()).hexdigest()
    tramo = {"origen": "A", "destino": "B", "veredicto": "intacta", "pagina_origen": filas,
             "pagina_destino": filas, "digest_origen": d, "digest_destino": d,
             "testigos": [{"consulta": "cita-09:30-sillon1", "estado": "ausente", "posicion": 0,
                           "anterior": "cita-09:00-sillon1", "siguiente": "cita-10:00-sillon2",
                           "digest_pagina": d}]}
    return {"tramos": [tramo], "frontera": None, "frontera_vacua": False, "veredicto": "intacta"}


def main(argv: Sequence[str]) -> int:
    argumentos = list(argv)
    if "--demo" in argumentos:
        codigo, lineas = verificar(_demo(), None, "cita-09:30-sillon1")
        for linea in lineas:
            print(linea)
        return codigo
    if "--recibo" not in argumentos:
        print("uso: verificar_recibo_externo.py --recibo RECIBO.json [--manifiesto F] [--ausente RUTA]")
        return 2
    ruta = argumentos[argumentos.index("--recibo") + 1]
    manifiesto = None
    ausente = None
    if "--manifiesto" in argumentos:
        with open(argumentos[argumentos.index("--manifiesto") + 1], "r", encoding="utf-8") as flujo:
            manifiesto = flujo.read()
    if "--ausente" in argumentos:
        ausente = argumentos[argumentos.index("--ausente") + 1]
    try:
        with open(ruta, "r", encoding="utf-8") as flujo:
            datos = _json.load(flujo)
        codigo, lineas = verificar(datos, manifiesto, ausente)
    except EntradaInvalida as fallo:
        print("entrada-invalida | %s" % fallo)
        return 2
    except (OSError, ValueError) as fallo:
        print("entrada-invalida | %s" % fallo)
        return 2
    for linea in lineas:
        print(linea)
    print("-> %s" % ("cierra" if codigo == 0 else "no cierra"))
    return codigo


if __name__ == "__main__":
    _sys.exit(main(tuple(_sys.argv[1:])))
