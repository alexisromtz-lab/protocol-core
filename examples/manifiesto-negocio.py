#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Un manifiesto de negocio, no de software: citas y movimientos.

El anillo 3 mide ausencia sobre una **página** (una secuencia ordenada de rutas
con su digest), no sobre un árbol de código. Eso lo hace aplicable a cualquier
dominio que sepa emitir un `sha256sum`: una agenda, un libro de movimientos, un
expediente. Este acto construye ese sujeto y, sobre todo, declara la pieza que
el álgebra exige y que ningún dominio trae puesta: **la proyección canónica**.

Lo que este acto declara, porque no es deducible del formato:

- `pi(k)` no la elige el motor, la declara el cliente. Aquí está la que usamos
  para el ejemplo: plegado de diacríticos, minúsculas, y los separadores
  colapsados a `-`. Un dominio con otra regla (por ejemplo, que distinga
  mayúsculas en un código de reserva) escribe otra `pi` y la publica con el
  recibo: el orden del que se habla viaja en el acto, no en la cabeza de quien
  lo ejecuta.
- `pi` se aplica **antes** de que la página exista. Después ya no se puede: la
  página es la forma, y su digest autentica la forma. Por eso una ruta con un
  byte fuera del alfabeto (§2.1: `A-Za-z0-9._-`) se rechaza con RC 2 en vez de
  normalizarse a la callada. Un acento que se cae sin decirlo es una fila que
  desaparece.
- Dos claves distintas con la misma `pi` son **la misma clave** y el manifiesto
  no puede llevarlas las dos: `Ávila` y `Avila` no son dos clientes, son un
  choque que el ojo del dueño resuelve y el motor no debe adivinar.

Uso:  manifiesto-negocio.py --emitir DIR [--desordenado] [--choque]
RC:   0 emite · 1 el sujeto no se pudo construir · 2 argumentos
"""

from __future__ import annotations

import argparse as _argparse
import hashlib as _hashlib
import pathlib as _pathlib
import sys as _sys
import unicodedata as _unicodedata

#: Separadores del dominio que la proyección colapsa a `-`.
_SEPARADORES: tuple = (" ", "_", ".", ":", "/", ",")


def proyectar(clave: str) -> str:
    """`pi(k)`: la forma canónica que el cliente declara para su universo.

    No es una función del motor: es una entrada. Se publica junto al recibo para
    que el testigo se pueda comprobar contra la misma proyección con la que se
    construyó la página.
    """

    descompuesta = _unicodedata.normalize("NFD", clave)
    sin_diacriticos = "".join(c for c in descompuesta if not _unicodedata.combining(c))
    plegada = sin_diacriticos.lower()
    for separador in _SEPARADORES:
        plegada = plegada.replace(separador, "-")
    while "--" in plegada:
        plegada = plegada.replace("--", "-")
    return plegada.strip("-")


#: Las citas del día. La clave de negocio es el nombre del cliente; el sufijo es
#: la hora y el sillón, que nunca llevan acento.
CITAS: tuple = (
    "Ávila-cita-09-00-sillon1",
    "Montes-cita-11-15-sillon3",
    "Núñez-cita-12-00-sillon2",
    "Zúñiga-cita-17-30-sillon1",
)

#: Los movimientos del día, con una referencia que sólo lleva dígitos y guiones.
MOVIMIENTOS: tuple = (
    "mov-2026-11-25-0001",
    "mov-2026-11-25-0002",
    "mov-2026-11-25-0003",
)


def _filas(claves: tuple) -> list:
    vistas = {}
    for clave in claves:
        canonica = proyectar(clave)
        if canonica in vistas:
            raise ValueError(
                "colapsa-el-caso: %r y %r proyectan a la misma clave %r"
                % (vistas[canonica], clave, canonica)
            )
        vistas[canonica] = clave
    originales = dict(vistas)
    return (
        [
            (canonica, _hashlib.sha256(canonica.encode("utf-8")).hexdigest())
            for canonica in vistas
        ],
        originales,
    )


def emitir(destino: _pathlib.Path, desordenado: bool, choque: bool) -> int:
    claves = list(CITAS) + list(MOVIMIENTOS)
    if choque:
        # El ojo humano ve dos clientes; la proyección ve una clave. El acto
        # falla aquí, que es exactamente donde debe fallar: antes de sellar.
        claves.append("AVILA-CITA-09-00-SILLON1")
    try:
        filas, originales = _filas(tuple(claves))
    except ValueError as error:
        print("CONTRATO | %s" % error)
        print("-> no se emite: una clave que colapsa se resuelve, no se sella")
        return 1

    # La página se emite en la colación declarada (bytes UTF-8 de la clave
    # canónica). `--desordenado` imita el error real de un exportador: ordenar
    # por el nombre original, donde `Á` empieza en 0xC3 y cae **detrás** de toda
    # la ASCII. El conjunto de filas es el mismo; el orden del archivo, no.
    if desordenado:
        filas = sorted(filas, key=lambda par: originales[par[0]].encode("utf-8"))
    else:
        filas = sorted(filas, key=lambda par: par[0].encode("utf-8"))

    agenda = destino / "agenda"
    agenda.mkdir(parents=True, exist_ok=True)
    for canonica, digest in filas:
        (agenda / ("%s.tsv" % canonica)).write_text(
            "clave=%s\ndigest=%s\n" % (canonica, digest), encoding="utf-8"
        )
    manifiesto = destino / "SHA256SUMS_AGENDA"
    manifiesto.write_text(
        "".join("%s  %s.tsv\n" % (digest, canonica) for canonica, digest in filas),
        encoding="utf-8",
    )
    print("EMITE | %s | %d filas | %s" % (agenda, len(filas), "desordenado" if desordenado else "ordenado"))
    print("EMITE | %s" % manifiesto)
    for canonica, digest in filas[:2]:
        print("  %s  %s.tsv" % (digest[:12], canonica))
    return 0


def main(argv: list) -> int:
    parser = _argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--emitir", required=True, metavar="DIR")
    parser.add_argument("--desordenado", action="store_true")
    parser.add_argument("--choque", action="store_true")
    args = parser.parse_args(argv)
    return emitir(_pathlib.Path(args.emitir), args.desordenado, args.choque)


if __name__ == "__main__":
    _sys.exit(main(_sys.argv[1:]))
