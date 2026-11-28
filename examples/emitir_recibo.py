"""examples/emitir_recibo.py — el acto del emisor: encadenar tramos en un recibo.

Uso:

    python3 -B examples/emitir_recibo.py \\
        --tramo A=B --paginas agenda-A.txt,agenda-B.txt \\
        --tramo B=C --paginas agenda-B.txt,agenda-C.txt \\
        --regla regla-A-B.txt --regla regla-B-C.txt \\
        --salida recibo.json

QUE HACE. Lee **dos paginas por tramo** (`sha256sum`, la de origen y la de
destino), encadena los tramos en el orden en que se declaran y los pliega con
`componer`. Dos paginas y no una por nodo: `B` puede cambiar entre `A -> B` y
`B -> C`, y una forma que solo admita una pagina por nodo no puede expresar el
defecto que el algebra existe para nombrar —una frontera que no cierra—, de modo
que emitiria siempre `cierra` y no mediria nada. El pliegue es el
acto: `componer` comprueba cada frontera —el digest destino del tramo previo
contra el digest origen del siguiente— de modo que el recibo que sale no afirma
una continuidad que el emisor no haya medido. Encadenar construyendo el `Recibo`
de golpe saltaria `_cruce` y firmaria la frontera que el cliente *dice* que hay.

LA REGLA ES LA UNICA ENTRADA DECLARADA. Un tramo puede declarar `sha256_regla`:
el digest del artefacto que dice que transformacion convierte `A` en `B`. Ese
digest no se recalcula de las filas —se hashea el archivo que el cliente entrega—
y por eso es lo unico del recibo que un tercero no puede derivar por su cuenta:
se lo tiene que dar el emisor, y el tercero lo coteja con `--regla`. Sin reglas
el recibo es `/1` y solo prueba continuidad de bytes; `firmar_recibo.py` se
niega a firmarlo, y este acto lo dice antes de que el cliente lo descubra.

FORMATO DE SALIDA. `a_dict()` del nucleo, sin inventar campos: el JSON es el que
`verificar_recibo_externo.py` ya sabe leer. El emisor no puede emitir una forma
que su propio tercero no entienda, porque entonces el defecto no seria del
cliente.

RC:   0 emite y la frontera cierra · 1 emite con la frontera rota o el recibo no
      sostiene (el hallazgo viaja en el archivo) · 2 argumentos o entrada
"""

from __future__ import annotations

import hashlib as _hashlib
import json as _json
import os as _os
import sys as _sys
from typing import List, Tuple

RAIZ = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
_sys.path.insert(0, _os.path.join(RAIZ, "src"))

from protocol.ausencia import pagina_desde_manifiesto  # noqa: E402
from protocol.composicion import (  # noqa: E402
    Recibo,
    Tramo,
    VeredictoDeComposicion,
    a_dict,
    componer,
)
from protocol.types import ContratoViolado  # noqa: E402
from protocol.ubicacion import leer_manifiesto  # noqa: E402

USO = (
    "uso: emitir_recibo.py --tramo A=B --paginas ORIGEN.txt,DESTINO.txt"
    " [--tramo ... --paginas ...] [--regla ARCHIVO ...] --salida RECIBO.json"
)


def _valores(argv: List[str], nombre: str) -> List[str]:
    """Los valores de una bandera repetible, en el orden en que aparecen."""

    valores: List[str] = []
    posicion = 0
    while posicion < len(argv):
        if argv[posicion] == nombre:
            if posicion + 1 >= len(argv):
                raise ContratoViolado("%s sin valor" % nombre)
            valores.append(argv[posicion + 1])
            posicion += 2
        else:
            posicion += 1
    return valores


def _arista(declaracion: str) -> Tuple[str, str]:
    if "=" not in declaracion:
        raise ContratoViolado("--tramo se declara ORIGEN=DESTINO", valor=declaracion)
    origen, destino = declaracion.split("=", 1)
    if not origen.strip() or not destino.strip():
        raise ContratoViolado("--tramo con nodo vacio", valor=declaracion)
    return origen.strip(), destino.strip()


def _dos_paginas(declaracion: str) -> Tuple[str, str]:
    """`ORIGEN.txt,DESTINO.txt`. Una ruta con coma no se admite y se declara."""

    partes = declaracion.split(",")
    if len(partes) != 2 or not partes[0].strip() or not partes[1].strip():
        raise ContratoViolado(
            "--paginas se declara ORIGEN.txt,DESTINO.txt (una ruta con coma no se admite)",
            valor=declaracion,
        )
    return partes[0].strip(), partes[1].strip()


def _pagina(ruta: str):
    with open(ruta, "r", encoding="utf-8") as flujo:
        manifiesto = leer_manifiesto(flujo.read(), _os.path.basename(ruta))
    return pagina_desde_manifiesto(manifiesto)


def _digest_de_regla(ruta: str) -> str:
    """El digest del artefacto tal como lo coteja el tercero: bytes, no filas.

    Se lee con la misma pareja `surrogateescape` que `verificar_recibo_externo.py`
    usa para recomputarlo. Cualquier otra lectura daria un digest que solo
    coincide con el suyo mientras el archivo sea UTF-8 puro.
    """

    with open(ruta, "r", encoding="utf-8", errors="surrogateescape") as flujo:
        return _hashlib.sha256(flujo.read().encode("utf-8", "surrogateescape")).hexdigest()


def main(argv: List[str]) -> int:
    argumentos = list(argv)
    if "--salida" not in argumentos:
        print(USO)
        return 2
    posicion = argumentos.index("--salida")
    if posicion + 1 >= len(argumentos):
        print(USO)
        return 2
    salida = argumentos[posicion + 1]

    try:
        aristas = [_arista(d) for d in _valores(argumentos, "--tramo")]
        pares = [_dos_paginas(d) for d in _valores(argumentos, "--paginas")]
        if not aristas:
            raise ContratoViolado("un recibo necesita al menos un tramo")
        if len(pares) != len(aristas):
            raise ContratoViolado(
                "se aportaron %d pares de paginas para %d tramos: uno por tramo, en orden"
                % (len(pares), len(aristas))
            )
        reglas = [_digest_de_regla(r) for r in _valores(argumentos, "--regla")]
        if reglas and len(reglas) != len(aristas):
            raise ContratoViolado(
                "se aportaron %d reglas para %d tramos: una por salto, en orden"
                % (len(reglas), len(aristas))
            )
        leidas = [(_ruta, _pagina(_ruta)) for par in pares for _ruta in par]
    except ContratoViolado as fallo:
        print("entrada-invalida | %s" % fallo)
        return 2
    except (OSError, UnicodeDecodeError) as fallo:
        print("entrada-invalida | %s | %s" % (type(fallo).__name__, fallo))
        return 2

    tramos = []
    for indice, (origen, destino) in enumerate(aristas):
        tramos.append(
            Tramo(
                origen=origen,
                destino=destino,
                veredicto=VeredictoDeComposicion.INTACTA,
                pagina_origen=leidas[2 * indice][1].filas,
                pagina_destino=leidas[2 * indice + 1][1].filas,
                sha256_regla=reglas[indice] if reglas else "",
            )
        )
    # El pliegue, no el atajo: cada frontera se mide al componer. Construir el
    # Recibo entero de una vez saltaria `_cruce` y publicaria como continua una
    # frontera que nadie comparo —y con dos paginas por tramo, esa frontera
    # puede perfectamente no cerrar.
    recibo = Recibo(tramos=(tramos[0],))
    for tramo in tramos[1:]:
        recibo = componer(recibo, Recibo(tramos=(tramo,)))
    datos = a_dict(recibo)
    texto = _json.dumps(datos, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    with open(salida, "w", encoding="utf-8") as flujo:
        flujo.write(texto)

    print(
        "recibo | %s | %s -> %s | %d tramos"
        % (datos["formato"], recibo.origen, recibo.destino, len(tramos))
    )
    print(
        "frontera | %s"
        % (
            "cierra"
            if recibo.frontera is None
            else "ROTA | esperado %s | leido %s"
            % (recibo.frontera[0][:12], recibo.frontera[1][:12])
        )
    )
    for indice, (origen, destino) in enumerate(aristas):
        for lado, (ruta, pagina) in enumerate(leidas[2 * indice : 2 * indice + 2]):
            print(
                "pagina | %s->%s | %s | %s | %d filas | %s%s"
                % (
                    origen,
                    destino,
                    "origen" if lado == 0 else "destino",
                    _os.path.basename(ruta),
                    len(pagina.filas),
                    pagina.digest[:12],
                    " | desordenada: normalizada al orden canonico" if pagina.desordenada else "",
                )
            )
    if reglas:
        for indice, (origen, destino) in enumerate(aristas):
            print("regla | %s->%s | %s" % (origen, destino, reglas[indice][:12]))
    else:
        print(
            "regla | sin regla declarada | el recibo es /1 y firmar_recibo.py se niega a firmarlo"
        )
    print(
        "salida | %s | %d bytes | sha256 %s"
        % (
            salida,
            len(texto.encode("utf-8")),
            _hashlib.sha256(texto.encode("utf-8")).hexdigest()[:12],
        )
    )
    return 0 if recibo.frontera is None and recibo.sostiene else 1


if __name__ == "__main__":
    raise SystemExit(main(_sys.argv[1:]))
