"""examples/verificar_conservacion.py — un tercero que mide sin el generador.

Uso:

    python3 -B examples/verificar_conservacion.py --demo
    python3 -B examples/verificar_conservacion.py --medida claves
    python3 -B examples/verificar_conservacion.py \
        --paginas a.txt,b.txt,c.txt --medida filas

QUE PRUEBA. Que la conservacion de una magnitud se pueda recalcular **sin
ejecutar el codigo que la emitio**: este acto no importa `protocol` y reescribe
por su cuenta las dos medidas, el orden de degradacion y la comparacion de cada
empalme. Si las lineas coinciden con las del modulo es porque el formato esta
escrito y no porque los dos llamen a la misma funcion; si divergen, el
desacuerdo es el hallazgo (`P-106a`).

QUE RECIBE. Las paginas de la cadena —lo que cada salto leyo y lo que dejo— y
nada mas: ni el arbol, ni el recibo, ni la maquina donde se produjo. En modo
externo cada pagina es un archivo de texto con una ruta por linea; si la linea
trae `ruta|valor`, el valor **no se lee**: las dos medidas se calculan sobre las
rutas, y por eso la linea `limite` viaja siempre.

LA CADENA ES LA LISTA DE PAGINAS. `--saltos` no es una segunda fuente de verdad:
los empalmes salen del orden en que se pasan los archivos (`a,b,c` son `a->b` y
`b->c`), y `--saltos` solo se acepta como confirmacion de esa lista. Un empalme
declarado que las paginas no implican no se mide: sale con `2`.

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

- `0` la cadena se midio y, cuando el cliente trajo una cadena, conserva.
- `1` la cadena del cliente no conserva. Solo en modo externo: en `--demo` no
  hay cadena ajena que condenar, hay un dialecto que se muestra.
- `2` la entrada no sirve —medida desconocida, pagina ilegible, saltos que no se
  tocan—: no es un verde.
"""

from __future__ import annotations

import hashlib as _hashlib
import os as _os
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

#: Las tres paginas de la agenda, **solo para `--demo`**: `A` con sus importes,
#: `B` con el importe de las 10:00 **recalculado mal** —misma clave, misma
#: cuenta, otro digest— y `C` con esa cita reubicada del sillon 2 al 4. La
#: cadena que mide el acto no vive aqui: entra por `--paginas`.
_PAGINAS_DEMO: Dict[str, Tuple[str, ...]] = {
    "A": ("cita-09-00-sillon1", "cita-10-00-sillon2", "cita-11-00-sillon2"),
    "B": ("cita-09-00-sillon1", "cita-10-00-sillon2", "cita-11-00-sillon2"),
    "C": ("cita-09-00-sillon1", "cita-10-00-sillon2", "cita-11-00-sillon4"),
}

_SALTOS_DEMO: Tuple[Tuple[str, str], ...] = (("A", "B"), ("B", "C"))

#: El valor que el acto publicaria para `B` si tuviera que declararlo. No se usa
#: para medir: existe para que se vea que la magnitud no lo mira.
_DIGEST_DECLARADO = "0" * 64


def _digest(texto: str) -> str:
    return _hashlib.sha256(texto.encode("utf-8")).hexdigest()


def _cargar_pagina(ruta: str) -> List[Tuple[str, str]]:
    """`(ruta, digest)` de cada linea del archivo. El digest no lo lee la medida.

    Si la linea trae `clave|valor` solo se toma la clave: `filas` cuenta claves y
    `claves` autentica el conjunto de rutas. El digest se publica para que la
    forma de la fila sea la de una pagina, no para medir.
    """

    filas: List[Tuple[str, str]] = []
    with open(ruta, "r", encoding="utf-8") as mano:
        for numero, linea in enumerate(mano, 1):
            texto = linea.rstrip("\n")
            if not texto.strip():
                continue
            clave = texto.split("|", 1)[0].strip()
            if not clave:
                raise ValueError("linea %d sin ruta" % numero)
            filas.append((clave, _digest(texto)))
    return filas


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


def medir_cadena(
    paginas: Dict[str, Sequence[Tuple[str, str]]],
    saltos: Sequence[Tuple[str, str]],
    medida: str,
) -> List[str]:
    """Las lineas de la cadena. Mismo dialecto que el modulo, reescrito aqui.

    `saltos` entra como parametro: este acto no tiene una cadena propia. La
    unica fuente de verdad de la cadena es la lista de paginas; los saltos que
    recibe son los empalmes que esa lista implica, y se comprueba que se toquen.
    """

    if medida not in MEDIDAS:
        raise ValueError("medida desconocida: %r" % (medida,))
    if not saltos:
        raise ValueError("una cadena sin saltos no conserva nada")
    for (_, destino), (origen, _) in zip(saltos, saltos[1:]):
        if destino != origen:
            raise ValueError("los saltos de la cadena no se tocan: %r != %r" % (destino, origen))

    saltos = [(origen, destino, paginas.get(origen, ()), paginas.get(destino, ())) for origen, destino in saltos]

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


def _paginas_demo() -> Dict[str, Sequence[Tuple[str, str]]]:
    return {
        nodo: [(ruta, _digest(ruta)) for ruta in valores] for nodo, valores in _PAGINAS_DEMO.items()
    }


_BANDERAS_CON_VALOR: Tuple[str, ...] = ("--medida", "--paginas", "--saltos")


def _parse(argumentos: Sequence[str]) -> Tuple[Dict[str, str], str]:
    """Las banderas reconocidas y el primer defecto de forma, si lo hay."""

    opciones: Dict[str, str] = {}
    indice = 0
    while indice < len(argumentos):
        token = argumentos[indice]
        if token == "--demo":
            opciones["--demo"] = ""
            indice += 1
            continue
        if token in _BANDERAS_CON_VALOR:
            if indice + 1 >= len(argumentos) or argumentos[indice + 1].startswith("--"):
                return opciones, "falta el valor de %s" % token
            opciones[token] = argumentos[indice + 1]
            indice += 2
            continue
        return opciones, "bandera desconocida: %r" % (token,)
    return opciones, ""


def _externo(opciones: Dict[str, str], medidas: Sequence[str]) -> int:
    rutas = [parte.strip() for parte in opciones["--paginas"].split(",") if parte.strip()]
    if len(rutas) < 2:
        _sys.stderr.write("una cadena necesita al menos dos paginas\n")
        return 2
    paginas: Dict[str, Sequence[Tuple[str, str]]] = {}
    etiquetas: List[str] = []
    for ruta in rutas:
        etiqueta = _os.path.splitext(_os.path.basename(ruta))[0]
        if not etiqueta:
            _sys.stderr.write("la pagina %r no tiene nombre utilizable\n" % (ruta,))
            return 2
        if etiqueta in paginas:
            _sys.stderr.write("dos paginas se llaman %r: el nodo no distingue cual es cual\n" % (etiqueta,))
            return 2
        try:
            paginas[etiqueta] = _cargar_pagina(ruta)
        except (OSError, ValueError) as exc:
            _sys.stderr.write("pagina ilegible %s: %s\n" % (ruta, exc))
            return 2
        etiquetas.append(etiqueta)
    saltos = [(etiquetas[i], etiquetas[i + 1]) for i in range(len(etiquetas) - 1)]
    if "--saltos" in opciones:
        declarados = [tuple(par.strip().split(":", 1)) for par in opciones["--saltos"].split(",") if par.strip()]
        if declarados != saltos:
            _sys.stderr.write("los saltos declarados no son los que la lista de paginas implica\n")
            return 2
    return _publicar(paginas, saltos, medidas, juzga=True)


def _publicar(
    paginas: Dict[str, Sequence[Tuple[str, str]]],
    saltos: Sequence[Tuple[str, str]],
    medidas: Sequence[str],
    juzga: bool,
) -> int:
    """Publica las lineas y devuelve el RC. `juzga` separa medir de condenar.

    El codigo `1` solo existe cuando el cliente trajo una cadena: ahi el acto
    responde si conserva. En `--demo` no hay cadena ajena que condenar.
    """

    conserva = True
    for medida in medidas:
        lineas = medir_cadena(paginas, saltos, medida)
        for linea in lineas:
            print(linea)
        conserva = conserva and lineas[-1] == "-> conservada"
    return 1 if juzga and not conserva else 0


def main(argumentos: Sequence[str]) -> int:
    opciones, defecto = _parse(argumentos)
    if defecto:
        _sys.stderr.write("%s\n" % defecto)
        return 2
    medidas: Sequence[str] = MEDIDAS
    if "--medida" in opciones:
        if opciones["--medida"] not in MEDIDAS:
            _sys.stderr.write("medida desconocida: %r\n" % (opciones["--medida"],))
            return 2
        medidas = (opciones["--medida"],)
    if "--paginas" in opciones:
        if "--demo" in opciones:
            _sys.stderr.write("--demo y --paginas se excluyen: o se muestra el dialecto o se mide una cadena\n")
            return 2
        return _externo(opciones, medidas)
    if "--saltos" in opciones:
        _sys.stderr.write("--saltos sin --paginas: un empalme sin paginas es una afirmacion sin sujeto\n")
        return 2
    if "--demo" not in opciones and "--medida" not in opciones:
        _sys.stderr.write("nada que hacer: use --demo, --medida o --paginas\n")
        return 2
    return _publicar(_paginas_demo(), _SALTOS_DEMO, medidas, juzga=False)


if __name__ == "__main__":
    _sys.exit(main(_sys.argv[1:]))
