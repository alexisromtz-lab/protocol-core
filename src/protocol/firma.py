"""firma.py — Ed25519 de la biblioteca estandar, atado al recibo `recibo-de-composicion/2`.

QUE CIERRA. El anillo 7 ata cada tramo a la regla que lo transformo, pero el
recibo viajaba sin autor: cualquiera puede copiarlo, cambiar una pagina y
volver a presentarlo. Una firma Ed25519 sobre los bytes canonicos del recibo
`/2` dice **quien** lo emitio y **sobre que exactamente**. El canon cubre hasta
las llaves que este modulo no conoce: anadir un campo al JSON invalida la firma
aunque el verificador externo no tenga regla para ese campo.

QUE NO CIERRA. Que el emisor dijera la verdad. La firma autentica la cadena, no
la transformacion; firmar una cadena que no ata sus tramos solo autentica quien
la fabrico —por eso un `/1` no se firma: `sha256_regla` por tramo es la
precondicion, no un adorno—.

SIN DEPENDENCIAS. Ed25519 (RFC 8032 §5.1) sobre `hashlib.sha512` y aritmetica
modular, con el cuerpo del primo `p = 2**255 - 19` en coordenadas extendidas
para no invertir en cada suma. Los vectores oficiales de §7.1 viven en
`tests/fixtures/rfc8032.json` y se miden contra **esta** implementacion y contra
la del verificador externo en la misma prueba (P-110a): dos copias que no se
cotejan divergen.

LA FIRMA VA AL LADO DEL RECIBO, no dentro. Una firma que se incluye en el JSON
que firma no puede cubrirse a si misma, y excluirla exige una segunda regla
—«todo menos esta llave»— con su propio agujero. Separada, los bytes firmados
son el recibo entero y la regla de exclusion no existe.

Uso desde codigo:

    from protocol.firma import bytes_firmados, firmar_recibo, verificar_recibo

RC: este modulo no es un acto de linea de comandos; levanta `ContratoViolado`
cuando lo que se le da no es firmable, y devuelve `False` cuando la firma no
coteja.
"""

from __future__ import annotations

import hashlib as _hashlib
from typing import Dict

from .composicion import desde_dict
from .predicado import canonizar
from .types import ContratoViolado

#: El dominio separa esta firma de cualquier otro uso de la misma llave. Lleva
#: la version del formato: un `/3` futuro no puede reutilizar los bytes de `/2`.
DOMINIO = b"recibo-de-composicion/2\n"

#: El unico formato firmable. Un `/1` certifica continuidad de bytes y nada mas.
FORMATO_FIRMABLE = "recibo-de-composicion/2"

_P = 2 ** 255 - 19
_L = 2 ** 252 + 27742317777372353535851937790883648493
_D = -121665 * pow(121666, _P - 2, _P) % _P
_D2 = 2 * _D % _P
_I = pow(2, (_P - 1) // 4, _P)
_BX = 15112221349535400772501151409588531511454012693041857206046113283949847762202
_BY = 46316835694926478169428394003475163141307993866256225615783033603165251855960
_B = (_BX, _BY, 1, _BX * _BY % _P)  # (X : Y : Z : T), con XY = ZT


def _suma(p, q):
    """Suma en coordenadas extendidas; `a = -1` (curva torcida de Edwards)."""

    x1, y1, z1, t1 = p
    x2, y2, z2, t2 = q
    a = (y1 - x1) * (y2 - x2) % _P
    b = (y1 + x1) * (y2 + x2) % _P
    c = t1 * _D2 % _P * t2 % _P
    d = 2 * z1 * z2 % _P
    e, f, g, h = b - a, d - c, d + c, b + a
    return (e * f % _P, g * h % _P, f * g % _P, e * h % _P)


def _dobla(p):
    x1, y1, z1, _ = p
    a = x1 * x1 % _P
    b = y1 * y1 % _P
    c = 2 * z1 * z1 % _P
    h = a + b
    e = h - (x1 + y1) * (x1 + y1) % _P
    g = a - b
    f = c + g
    return (e * f % _P, g * h % _P, f * g % _P, e * h % _P)


def _escala(k: int, punto) -> tuple:
    resultado = (0, 1, 1, 0)
    for bit in bin(k)[2:]:
        resultado = _dobla(resultado)
        if bit == "1":
            resultado = _suma(resultado, punto)
    return resultado


def _comprime(p) -> bytes:
    x, y, z, _ = p
    inversa = pow(z, _P - 2, _P)
    x = x * inversa % _P
    y = y * inversa % _P
    return (y | ((x & 1) << 255)).to_bytes(32, "little")


def _descomprime(bruto: bytes) -> tuple:
    if len(bruto) != 32:
        raise ValueError("un punto Ed25519 mide 32 bytes, no %d" % len(bruto))
    crudo = int.from_bytes(bruto, "little")
    signo, y = crudo >> 255, crudo & ((1 << 255) - 1)
    if y >= _P:
        raise ValueError("la coordenada y no es canonica")
    x2 = (y * y - 1) * pow(_D * y * y + 1, _P - 2, _P) % _P
    if x2 == 0:
        if signo:
            raise ValueError("x = 0 no tiene signo negativo")
        return (0, y, 1, 0)
    x = pow(x2, (_P + 3) // 8, _P)
    if (x * x - x2) % _P:
        x = x * _I % _P
    if (x * x - x2) % _P:
        raise ValueError("el punto no esta sobre la curva")
    if x & 1 != signo:
        x = _P - x
    return (x, y, 1, x * y % _P)


def _escalar_de_semilla(semilla: bytes) -> tuple:
    """El escalar y el prefijo de RFC 8032 §5.1.5, con el recorte declarado."""

    if len(semilla) != 32:
        raise ContratoViolado("la semilla secreta mide 32 bytes", valor=len(semilla))
    resumen = _hashlib.sha512(semilla).digest()
    escalar = int.from_bytes(resumen[:32], "little")
    escalar &= (1 << 254) - 8
    escalar |= 1 << 254
    return escalar, resumen[32:]


def clave_publica(semilla: bytes) -> bytes:
    """Los 32 bytes que se publican; la semilla no sale nunca de aqui."""

    escalar, _ = _escalar_de_semilla(semilla)
    return _comprime(_escala(escalar, _B))


def firmar(mensaje: bytes, semilla: bytes) -> bytes:
    """La firma determinista de RFC 8032 §5.1.6: 64 bytes, sin azar."""

    escalar, prefijo = _escalar_de_semilla(semilla)
    publica = _comprime(_escala(escalar, _B))
    nonce = int.from_bytes(_hashlib.sha512(prefijo + mensaje).digest(), "little") % _L
    r = _comprime(_escala(nonce, _B))
    k = int.from_bytes(_hashlib.sha512(r + publica + mensaje).digest(), "little") % _L
    return r + ((nonce + k * escalar) % _L).to_bytes(32, "little")


def verificar(mensaje: bytes, firma: bytes, publica: bytes) -> bool:
    """`[S]B = R + [k]A` sin cofactor, y todo lo que no mide esa igualdad es `False`."""

    if len(firma) != 64 or len(publica) != 32:
        return False
    s = int.from_bytes(firma[32:], "little")
    if s >= _L:
        return False
    try:
        a = _descomprime(publica)
        r = _descomprime(firma[:32])
    except ValueError:
        return False
    k = int.from_bytes(_hashlib.sha512(firma[:32] + publica + mensaje).digest(), "little") % _L
    return _comprime(_escala(s, _B)) == _comprime(_suma(r, _escala(k, a)))


def bytes_firmados(datos: Dict[str, object]) -> bytes:
    """Lo que la firma cubre: el dominio y el canon del recibo, nada mas.

    Se revalida el recibo con el lector del generador antes de tocarlo: un
    recibo que no se puede releer tampoco se puede firmar, y descubrirlo aqui
    cuesta una excepcion en vez de una firma que el tercero va a rechazar.
    """

    desde_dict(datos)
    if datos.get("formato") != FORMATO_FIRMABLE:
        raise ContratoViolado(
            "solo se firma un recibo %s: un /1 no declara la regla de sus tramos"
            % FORMATO_FIRMABLE,
            formato=datos.get("formato"),
        )
    return DOMINIO + canonizar(datos)


def firmar_recibo(datos: Dict[str, object], semilla: bytes) -> str:
    """La firma del recibo, en hex, para guardarla al lado del JSON."""

    return firmar(bytes_firmados(datos), semilla).hex()


def verificar_recibo(datos: Dict[str, object], firma_hex: str, publica_hex: str) -> bool:
    """`True` si el recibo es exactamente el que firmo esa llave.

    Una firma con forma invalida es un contrato roto —no una firma falsa—; una
    firma bien formada que no coteja es un `False`, que es un veredicto.
    """

    try:
        firma = bytes.fromhex(firma_hex)
        publica = bytes.fromhex(publica_hex)
    except ValueError:
        raise ContratoViolado("la firma y la clave se leen en hex", firma=len(firma_hex))
    if len(firma) != 64 or len(publica) != 32:
        raise ContratoViolado(
            "la firma mide 64 bytes y la clave 32", firma=len(firma), clave=len(publica)
        )
    return verificar(bytes_firmados(datos), firma, publica)
