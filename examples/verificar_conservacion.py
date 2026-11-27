"""examples/verificar_conservacion.py — un tercero que mide sin el generador.

Uso:

    python3 -B examples/verificar_conservacion.py --demo
    python3 -B examples/verificar_conservacion.py --medida claves

QUE PRUEBA. Que la conservacion de una magnitud se pueda recalcular **sin
ejecutar el codigo que la emitio**: este acto no importa `protocol` y reescribe
por su cuenta las dos medidas, el orden de degradacion y la comparacion de cada
empalme. Si las lineas coinciden con las del modulo es porque el formato esta
escrito y no porque los dos llamen a la misma funcion; si divergen, el
desacuerdo es el hallazgo (`P-106a`).

QUE RECIBE. Las tres paginas de la agenda —lo que cada salto leyo y lo que dejo—
y nada mas: ni el arbol, ni el recibo, ni la maquina donde se produjo.

QUE NO MIDE, y lo publica en cada corrida. Que el nodo intermedio calculara
**bien**. `filas` y `claves` son magnitudes sobre las claves: un importe mal
recalculado las atraviesa intacto, y por eso la linea `limite` sale siempre.

LAS DOS MEDIDAS, reescritas aqui para que una deriva se note:

- `filas` cuenta entradas de la pagina.
- `claves` autentica el conjunto de rutas **ordenado**, y descarta los digests a
  proposito: si los incluyera mediria identidad de bytes, que no es esta
  pregunta.

Lo que un salto dejo y el siguiente leyo tiene que coincidir en el nodo
intermedio. Si no coincide, la cadena no conserva aunque los dos saltos
conserven por separado: el defecto no vive en ningun salto, vive en el empalme.

Codigo de salida:

- `0` la cadena se midio.
- `2` la medida pedida no existe.
"""

from __future__ import annotations

import hashlib as _hashlib
import sys as _sys
from typing import Dict, List, Sequence, Tuple

#: El orden declarado, de mejor a peor. Se reescribe, no se importa.
RANGO: Tuple[str, ...] = ("conservada", "sin_medida", "no_conservada")

#: Las medidas que este acto sabe recalcular, en el orden en que se publican.
MEDIDAS: Tuple[str, ...] = ("filas", "claves")

LIMITE = (
    "limite | conserva el transporte, no el calculo: la magnitud elegida puede"
    " sobrevivir a un valor mal calculado"
)

#: Las tres paginas de la agenda: `A` con sus importes, `B` con el importe de las
#: 10:00 **recalculado mal** —misma clave, misma cuenta, otro digest— y `C` con
#: esa cita reubicada del sillon 2 al 4.
_PAGINAS: Dict[str, Tuple[str, ...]] = {
    "A": ("cita-09-00-sillon1", "cita-10-00-sillon2", "cita-11-00-sillon2"),
    "B": ("cita-09-00-sillon1", "cita-10-00-sillon2", "cita-11-00-sillon2"),
    "C": ("cita-09-00-sillon1", "cita-10-00-sillon2", "cita-11-00-sillon4"),
}

_SALTOS: Tuple[Tuple[str, str], ...] = (("A", "B"), ("B", "C"))

#: El valor que el acto publicaria para `B` si tuviera que declararlo. No se usa
#: para medir: existe para que se vea que la magnitud no lo mira.
_DIGEST_DECLARADO = "0" * 64


def _filas(nodo: str, valores: Sequence[Tuple[str, str]]) -> List[Tuple[str, str]]:
    """`(ruta, digest)` de una pagina. El digest es el de la clave, no el importe."""

    if nodo == "B":
        return [(ruta, _hashlib.sha256((ruta + "|recalculado").encode("utf-8")).hexdigest()) for ruta in valores]
    return [(ruta, _hashlib.sha256((ruta + "|original").encode("utf-8")).hexdigest()) for ruta in valores]


def _medir(filas: Sequence[Tuple[str, str]], medida: str) -> str:
    if medida == "filas":
        return "filas=%d" % len(filas)
    texto = "".join("%s\n" % ruta for ruta in sorted(ruta for ruta, _ in filas))
    return "claves=%s" % _hashlib.sha256(texto.encode("utf-8")).hexdigest()


def _corto(valor: str) -> str:
    nombre, _, resto = valor.partition("=")
    return "%s=%s" % (nombre, resto[:12] if nombre == "claves" else resto)


def _veredicto(izquierda: str, derecha: str, medida: str) -> str:
    if not izquierda or not derecha:
        return "sin_medida"
    return "conservada" if _medir(izquierda, medida) == _medir(derecha, medida) else "no_conservada"


def medir_cadena(paginas: Dict[str, Sequence[Tuple[str, str]]], medida: str) -> List[str]:
    """Las lineas de la cadena. Mismo dialecto que el modulo, reescrito aqui."""

    if medida not in MEDIDAS:
        raise ValueError("medida desconocida: %r" % (medida,))
    saltos = []
    for origen, destino in _SALTOS:
        saltos.append((origen, destino, paginas[origen], paginas[destino]))

    partes = [saltos[0][0]]
    for _, destino, _, _ in saltos:
        partes.append("->")
        partes.append(destino)
    salida = ["conservacion | %s" % " ".join(partes), "medida | %s | declarada por el cliente" % medida]
    for origen, destino, izquierda, derecha in saltos:
        salida.append(
            "salto | %s->%s | %s | %s -> %s | %s"
            % (
                origen,
                destino,
                medida,
                _corto(_medir(izquierda, medida)),
                _corto(_medir(derecha, medida)),
                _veredicto(izquierda, derecha, medida),
            )
        )
    empalmes = []
    for (_, nodo, _, derecha), (_, _, izquierda, _) in zip(saltos, saltos[1:]):
        if not derecha or not izquierda:
            empalmes.append("empalme | %s | sin medir | falta la pagina de un lado" % nodo)
            continue
        dejado, leido = _medir(derecha, medida), _medir(izquierda, medida)
        if dejado != leido:
            empalmes.append("empalme | %s | %s != %s" % (nodo, _corto(dejado), _corto(leido)))
    salida.extend(empalmes)
    peor = max(
        [estado for estado in (_veredicto(i, d, medida) for _, _, i, d in saltos)]
        + (["no_conservada"] if any(e.startswith("empalme |") and "!=" in e for e in empalmes) else []),
        key=RANGO.index,
    )
    if any("falta la pagina" in e for e in empalmes) and RANGO.index(peor) < RANGO.index("sin_medida"):
        peor = "sin_medida"
    if peor != "conservada":
        for origen, destino, izquierda, derecha in saltos:
            if _veredicto(izquierda, derecha, medida) == peor:
                salida.append("degradado | %s->%s | %s" % (origen, destino, peor))
                break
        if _medir(saltos[0][2], medida) == _medir(saltos[-1][3], medida):
            salida.append("extremo | el extremo puede coincidir aunque la cadena no conserve")
    salida.append(LIMITE)
    salida.append("-> %s" % peor)
    return salida


def _paginas() -> Dict[str, Sequence[Tuple[str, str]]]:
    return {nodo: _filas(nodo, valores) for nodo, valores in _PAGINAS.items()}


def main(argumentos: Sequence[str]) -> int:
    medidas = MEDIDAS
    if "--medida" in argumentos:
        pedida = argumentos[list(argumentos).index("--medida") + 1] if len(argumentos) > 1 else ""
        if pedida not in MEDIDAS:
            _sys.stderr.write("medida desconocida: %r\n" % (pedida,))
            return 2
        medidas = (pedida,)
    elif "--demo" not in argumentos:
        _sys.stderr.write("nada que hacer: use --demo o --medida\n")
        return 2
    paginas = _paginas()
    for medida in medidas:
        for linea in medir_cadena(paginas, medida):
            print(linea)
    return 0


if __name__ == "__main__":
    _sys.exit(main(_sys.argv[1:]))
