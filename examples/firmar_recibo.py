"""examples/firmar_recibo.py — el acto del emisor: firmar un recibo `/2` y publicar su clave.

Uso:

    python3 -B examples/firmar_recibo.py --recibo recibo.json --semilla semilla.hex
    python3 -B examples/firmar_recibo.py --recibo recibo.json --semilla semilla.hex \\
        --firma-salida R.firma --clave-salida R.pub

Lo que este acto compra. Un recibo ata sus tramos a la regla que los transformo,
pero viaja sin autor: cualquiera lo copia, cambia una pagina y lo vuelve a
presentar con la misma forma. La firma Ed25519 sobre el dominio y el canon del
recibo dice **quien** lo emitio y **sobre que bytes exactamente**, y el tercero
la coteja con `verificar_recibo_externo.py --clave R.pub --firma R.firma` sin
ejecutar nada de aqui.

Solo se firma un `/2`. Un `/1` certifica continuidad de bytes y no declara la
regla de sus tramos: firmarlo autenticaria a quien lo fabrico, no un acto. El
acto se niega (RC 2) en vez de emitir una firma que el tercero va a rechazar.

La semilla no se imprime, no se escribe en el recibo y no viaja en la salida: la
unica cosa publica es la clave, que se deriva de ella. Si el archivo de clave ya
existe con **otro** contenido, el acto se niega (RC 1) antes de firmar: reescribir
una clave publicada en silencio parte en dos la familia de recibos de esa llave,
y una firma que nadie puede cotejar es peor que ninguna.

RC:

    0  recibo firmado y clave publicada
    1  la clave publicada no es la de esta semilla: no se reescribe
    2  la entrada no se puede leer o el recibo no es firmable
"""

from __future__ import annotations

import json as _json
import os as _os
import sys as _sys
from typing import List, Optional, Sequence

RAIZ = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
_sys.path.insert(0, _os.path.join(RAIZ, "src"))

from protocol.firma import bytes_firmados, clave_publica, firmar_recibo  # noqa: E402
from protocol.types import ContratoViolado  # noqa: E402


def _leer_hex(ruta: str, que: str, bytes_esperados: int) -> bytes:
    with open(ruta, "r", encoding="utf-8") as flujo:
        crudo = "".join(linea.split("#", 1)[0] for linea in flujo.read().splitlines())
    limpio = "".join(crudo.split())
    if len(limpio) != 2 * bytes_esperados:
        raise ContratoViolado(
            "%s declara %d bytes hex y trae %d" % (que, 2 * bytes_esperados, len(limpio))
        )
    return bytes.fromhex(limpio)


def _escribir(ruta: str, texto: str) -> None:
    with open(ruta, "w", encoding="utf-8") as mano:
        mano.write(texto if texto.endswith("\n") else texto + "\n")


def _por_defecto(ruta_recibo: str, extension: str) -> str:
    base = ruta_recibo[:-5] if ruta_recibo.endswith(".json") else ruta_recibo
    return base + extension


def main(argv: Sequence[str]) -> int:
    argumentos = list(argv)
    if "--recibo" not in argumentos or "--semilla" not in argumentos:
        print(
            "uso: firmar_recibo.py --recibo RECIBO.json --semilla SEMILLA.hex"
            " [--firma-salida R.firma] [--clave-salida R.pub]"
        )
        return 2
    ruta = argumentos[argumentos.index("--recibo") + 1]
    firma_salida = (
        argumentos[argumentos.index("--firma-salida") + 1]
        if "--firma-salida" in argumentos
        else _por_defecto(ruta, ".firma")
    )
    clave_salida = (
        argumentos[argumentos.index("--clave-salida") + 1]
        if "--clave-salida" in argumentos
        else _por_defecto(ruta, ".pub")
    )
    try:
        semilla = _leer_hex(argumentos[argumentos.index("--semilla") + 1], "la semilla", 32)
        with open(ruta, "r", encoding="utf-8") as flujo:
            datos = _json.load(flujo)
        publica = clave_publica(semilla)
        publicada: Optional[bytes] = None
        if _os.path.exists(clave_salida):
            with open(clave_salida, "r", encoding="utf-8") as flujo:
                previa = "".join(flujo.read().split())
            publicada = bytes.fromhex(previa) if len(previa) == 64 else b""
        if publicada is not None and publicada != publica:
            print(
                "clave | %s | REFUTA | el archivo ya publica %s y esta semilla da %s"
                % (clave_salida, publicada.hex()[:12] or "nada legible", publica.hex()[:12])
            )
            print("-> no firma")
            return 1
        firmados = len(bytes_firmados(datos))
        firma = firmar_recibo(datos, semilla)
    except ContratoViolado as fallo:
        print("entrada-invalida | %s" % fallo)
        return 2
    except (OSError, ValueError) as fallo:
        print("entrada-invalida | %s" % fallo)
        return 2
    _escribir(clave_salida, publica.hex())
    _escribir(firma_salida, firma)
    lineas: List[str] = [
        "recibo | %s | %s | %d tramos | %d bytes firmados"
        % (datos.get("formato"), ruta, len(datos.get("tramos") or ()), firmados),
        "clave | %s | publicada en %s" % (publica.hex(), clave_salida),
        "firma | %s | %s" % (firma[:32] + "..." + firma[-8:], firma_salida),
        "limite | la firma autentica quien emitio estos bytes; no que el emisor midiera lo que afirma medir",
    ]
    for linea in lineas:
        print(linea)
    print("-> firmado")
    return 0


if __name__ == "__main__":
    _sys.exit(main(tuple(_sys.argv[1:])))
