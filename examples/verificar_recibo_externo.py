"""examples/verificar_recibo_externo.py — un tercero que no llama al generador.

Uso:

    python3 -B examples/verificar_recibo_externo.py --recibo recibo.json
    python3 -B examples/verificar_recibo_externo.py --recibo recibo.json \\
        --manifiesto SHA256SUMS --ausente "cita-09:00-sillon1"
    python3 -B examples/verificar_recibo_externo.py --recibo recibo.json --demo
    python3 -B examples/verificar_recibo_externo.py --recibo recibo.json \\
        --regla regla-A-B.txt --regla regla-B-C.txt      # un --regla por tramo, en orden
    python3 -B examples/verificar_recibo_externo.py --recibo recibo.json --exigir-regla
    python3 -B examples/verificar_recibo_externo.py --recibo recibo.json \\
        --clave R.pub --firma R.firma                    # autoria del recibo

QUE PRUEBA. Que un recibo se pueda cerrar **sin ejecutar el codigo que lo
produjo**. El verificador no importa `protocol`: reescribe por su cuenta el
formato canonico, el digest de pagina, la tabla de degradacion y la busqueda de
vecinos. Si los dos coinciden es porque el formato esta escrito y no porque los
dos llamen a la misma funcion; si divergen, el desacuerdo es el hallazgo.

LA REGLA, Y POR QUE BASTA CON UN DIGEST POR TRAMO. Una cadena de paginas
inventadas pero coherentes consigo mismas —cada tramo declara el digest de sus
propias filas, la frontera cierra porque el falsificador reusa la misma pagina en
el nodo comun— cierra hoy con RC 0 sin probar nada del mundo: prueba que el que
la escribio sabe multiplicar por si mismo. `sha256_entrada` **no** se anade como
campo aparte: la entrada de `B` ya se recalcula de las filas de `B` y se compara
con la salida de `A` (la frontera), de modo que un campo `sha256_entrada` seria
una copia *declarada* de una cantidad *recalculada*: la version debil de lo que
ya se mide. Lo que falta es la **regla**: el digest del artefacto que dice que
transformacion convierte `A` en `B`, declarado fuera del testigo de `B`. Un
`sha256_regla` sin el artefacto delante es otro numero que se cree a si mismo,
asi que el tercero lo coteja contra el archivo que le pasan con `--regla`
(uno por tramo, en orden). Un recibo `recibo-de-composicion/2` exige esa regla
por construccion; `--exigir-regla` se la exige tambien a un `/1`.

QUE RECIBE. Solo el JSON del recibo (que lleva sus paginas dentro) y, si se le
da, el manifiesto publicado, los artefactos de regla y —para medir autoria— una
clave publica y una firma. Nada mas: ni el arbol, ni el generador, ni la maquina
donde se produjo.

LA FIRMA, Y QUE ANADE. Una regla ata el tramo a un artefacto; no dice **quien**
emitio el recibo, y una cadena autentica de bytes puede presentarla cualquiera.
Con `--clave` y `--firma` el tercero coteja una firma Ed25519 —implementada
aqui, bajo la misma prohibicion de importar el generador— sobre el dominio y el
canon del recibo entero. El canon cubre hasta las llaves que este verificador no
conoce: anadir un campo al JSON invalida la firma aunque ninguna otra
comprobacion lo note. Solo se firma un `/2`: un `/1` no ata sus tramos y su
firma solo autenticaria a quien lo fabrico, asi que se acusa (`FIRMA_NO_FIRMABLE`)
en vez de cotejarse.

QUE QUEDA FUERA, y se publica. Comprueba que las paginas encadenadas son las
mismas de punta a punta; **no comprueba que el nodo intermedio hiciera su
trabajo**. Un recibo certifica continuidad de bytes, no correccion de la
transformacion: quien transformo pudo aplicar el cambio equivocado y firmarlo.

EL SOBRE. Un manifiesto de tercero puede venir firmado en claro (`BEGIN PGP
SIGNED MESSAGE`), en cuyo caso el archivo y el objeto son **dos** cosas: el
digest del archivo no es el de la carga. Se desenvuelve aqui, reimplementando
RFC 4880 §7.1 (linea que empieza por `-` viene escapada como `- `), y se
publican los dos digests. Medido el 2026-11-25: sin desenvolver, el
`InRelease` de Debian se leia bien **por casualidad** —la cabecera del sobre
caia en el mismo cubo que los comentarios— y el verificador no podia decir que
parte del archivo habia medido.

Codigo de salida:

- `0` la prueba cierra.
- `1` algo fue alterado (digest, frontera, vecinos, veredicto publicado, firma
  que no coteja, o un `/1` presentado como firmado).
- `2` la entrada no se puede leer (JSON roto, pagina desordenada, falta un
  campo obligatorio, firma o clave mal formadas).
"""

from __future__ import annotations

import hashlib as _hashlib
import json as _json
import re as _re
import sys as _sys
import unicodedata as _unicodedata
from typing import Dict, List, Optional, Sequence, Tuple

#: Se reescribe, no se importa. Es la unica forma de que la comparacion mida
#: algo: dos modulos que importan la misma constante siempre coinciden.
FORMATO_CANONICO = "%s  %s\n"

#: El dominio y la version que el generador firma, reescritos aqui por la misma
#: razon que `FORMATO_CANONICO`: la firma coteja si los dos lados dicen lo mismo.
DOMINIO_FIRMA = b"recibo-de-composicion/2\n"
FORMATO_FIRMABLE = "recibo-de-composicion/2"

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


#: Las cuatro gramaticas, reescritas aqui desde su descripcion y no importadas:
#: dos modulos que importan el mismo patron siempre coinciden, y la coincidencia
#: seria entonces una tautologia. Son disjuntas por la columna donde exigen el
#: separador —`coreutils` en la 65 sin espacio delante, `deb822` con un espacio
#: delante, `bsd` con parentesis y `suelto` con la linea entera.
GRAMATICAS: Tuple[str, ...] = ("coreutils", "bsd", "deb822", "suelto")
_RE_GRAMATICA = {
    "coreutils": _re.compile(r"^([0-9a-f]{64}) [ *](\S.*)$"),
    "bsd": _re.compile(r"^SHA256 \((.+)\) = ([0-9a-f]{64})$"),
    "deb822": _re.compile(r"^ ([0-9a-f]{64}) +([0-9]+) (\S.*)$"),
    "suelto": _re.compile(r"^([0-9a-f]{64})$"),
}
_RE_SECCION = _re.compile(r"^[A-Za-z][A-Za-z0-9]*:[ \t]*$")
_RE_CAMPO = _re.compile(r"^[A-Za-z][A-Za-z0-9-]*: \S.*$")
_SUFIJOS_SUELTOS: Tuple[str, ...] = (".sha256", ".sha256sum", ".sum", ".txt")

_INICIO_CLARO = "-----BEGIN PGP SIGNED MESSAGE-----"
_INICIO_FIRMA = "-----BEGIN PGP SIGNATURE-----"
_FIN_FIRMA = "-----END PGP SIGNATURE-----"


def _desenvolver(texto: str) -> Tuple[str, str, int, int]:
    """`(topologia, carga, bytes de firma, escapadas)`; independiente del generador.

    Tres topologias, medidas sobre el mismo autor publicando el mismo contenido:
    `sin_sobre` (nada que desenvolver), `firmado_en_claro` (el objeto va dentro)
    y `firma_pegada` (el objeto esta en otro archivo y **su nombre no viaja**).

    La carga conserva su salto final: en el armadura ese salto es el separador
    de la linea `-----BEGIN PGP SIGNATURE-----`, y perderlo cambia el digest del
    objeto por un byte (medido: 149 265 contra 149 266 en el `InRelease` de Debian).
    """

    lineas = texto.split("\n")
    peladas = [l.rstrip() for l in lineas]
    claros = [i for i, l in enumerate(peladas) if l == _INICIO_CLARO]
    firmas = [i for i, l in enumerate(peladas) if l == _INICIO_FIRMA]
    if not claros and not firmas:
        return "sin_sobre", texto, 0, 0
    if not claros:
        bloque = _sin_cola(lineas[firmas[0] :])
        return "firma_pegada", "", len("\n".join(bloque).encode()), 0
    cuerpo = lineas[claros[0] + 1 :]
    # La cabecera del mensaje en claro son lineas `Clave: valor` hasta la primera en blanco.
    while cuerpo and cuerpo[0].strip() and _RE_CAMPO.match(cuerpo[0].strip()):
        cuerpo = cuerpo[1:]
    if cuerpo and not cuerpo[0].strip():
        cuerpo = cuerpo[1:]
    corte = next(
        (i for i, l in enumerate(cuerpo) if l.strip() in (_INICIO_FIRMA, _FIN_FIRMA)), len(cuerpo)
    )
    escapadas = 0
    carga = []
    for linea in cuerpo[:corte]:
        if linea.startswith("- "):
            escapadas += 1
            carga.append(linea[2:])
        elif linea.startswith("-"):
            escapadas += 1
            carga.append(linea[1:])
        else:
            carga.append(linea.rstrip())
    cuerpo_carga = "\n".join(carga)
    if cuerpo_carga and not cuerpo_carga.endswith("\n"):
        cuerpo_carga += "\n"
    bloque = _sin_cola(cuerpo[corte:])
    return "firmado_en_claro", cuerpo_carga, len("\n".join(bloque).encode()), escapadas


def _sin_cola(lineas: Sequence[str]) -> List[str]:
    """El bloque de firma sin las lineas vacias que lo siguen: `BEGIN`..`END`."""

    bloque = list(lineas)
    while bloque and not bloque[-1].strip():
        bloque.pop()
    return bloque


def _pares(
    portador: str, texto: str, nombre: Optional[str]
) -> Optional[Tuple[List[Tuple[str, str, str]], int]]:
    """Las filas y cuantas lineas quedaron fuera de la gramatica, o `None`.

    `ignoradas` no es un adorno: un manifiesto del que se ignora la mitad no se
    ha leido, se ha supuesto, y el numero que lo acompania es lo que permite al
    tercero ver que se supuso.
    """

    filas: List[Tuple[str, str, str]] = []
    ignoradas = 0
    seccion: Optional[str] = None
    for cruda in texto.split("\n"):
        linea = cruda[:-1] if cruda.endswith("\r") else cruda
        pelada = linea.strip()
        if not pelada:
            continue
        if pelada.startswith("-----BEGIN PGP SIGNATURE"):
            # El sobre de firma no es manifiesto: no se verifica, y se dice.
            ignoradas += 1
            break
        if pelada.startswith("#") or pelada.startswith("-----") or pelada.startswith("Hash:"):
            ignoradas += 1
            continue
        if _RE_SECCION.match(pelada):
            seccion = pelada
            ignoradas += 1
            continue
        if _RE_CAMPO.match(pelada):
            # Campo del preambulo deb822 (`Origin: Debian`): no es fila.
            ignoradas += 1
            continue
        hallado = _RE_GRAMATICA[portador].match(linea)
        if portador == "deb822":
            if seccion not in (None, "SHA256:"):
                # Fila de otro algoritmo: no es de esta gramatica, y se cuenta.
                ignoradas += 1
                continue
            if not hallado:
                return None
            digest, _, ruta = hallado.groups()
        elif portador == "coreutils":
            if not hallado:
                return None
            digest, ruta = hallado.groups()
        elif portador == "bsd":
            if not hallado:
                return None
            ruta, digest = hallado.groups()
        else:
            if not hallado:
                return None
            if not nombre:
                return None
            digest = hallado.group(1)
            ruta = nombre
            for sufijo in _SUFIJOS_SUELTOS:
                if ruta.endswith(sufijo):
                    ruta = ruta[: -len(sufijo)]
                    break
        filas.append((ruta, digest, ""))
    if not filas:
        return None
    return filas, ignoradas


def _leer_manifiesto(
    texto: str, declarado: str, nombre: Optional[str]
) -> Tuple[List[Tuple[str, str, str]], str, int]:
    """El portador declarado, o el unico que lo explica. Dos lecturas no se eligen."""

    if declarado not in ("auto",) + GRAMATICAS:
        raise EntradaInvalida("portador no declarado: %r" % (declarado,))
    if declarado == "suelto" and not nombre:
        raise EntradaInvalida("el portador suelto no escribe el nombre de la ruta: pase --nombre")
    if declarado != "auto":
        leido = _pares(declarado, texto, nombre)
        if leido is None:
            raise EntradaInvalida("el manifiesto no es %s" % (declarado,))
        return leido[0], declarado, leido[1]
    lecturas = {}
    for uno in GRAMATICAS:
        leido = _pares(uno, texto, nombre)
        if leido is not None:
            lecturas[uno] = leido
    if not lecturas:
        raise EntradaInvalida("ninguna de las cuatro gramaticas explica el manifiesto")
    if len(lecturas) > 1:
        raise EntradaInvalida(
            "el manifiesto abre %d lecturas (%s): declare --portador"
            % (len(lecturas), ", ".join(sorted(lecturas)))
        )
    unico = next(iter(lecturas))
    return lecturas[unico][0], unico, lecturas[unico][1]


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


def _canonizar(objeto: object) -> bytes:
    """El canon del recibo, reescrito: NFC, llaves ordenadas, sin espacios, UTF-8.

    Las cuatro decisiones del generador. Si una sola faltara, la firma no
    cotejaria nunca y el verificador culparia al recibo de su propia deriva.
    """

    def canon(nodo: object) -> object:
        if isinstance(nodo, float):
            raise ValueError("el canon rechaza flotantes: su representacion no es portable")
        if isinstance(nodo, str):
            return _unicodedata.normalize("NFC", nodo)
        if isinstance(nodo, bool) or nodo is None or isinstance(nodo, int):
            return nodo
        if isinstance(nodo, dict):
            return {_unicodedata.normalize("NFC", clave): canon(valor) for clave, valor in nodo.items()}
        if isinstance(nodo, (list, tuple)):
            return [canon(valor) for valor in nodo]
        raise ValueError("tipo no admisible en el canon: %s" % type(nodo).__name__)

    return _json.dumps(
        canon(objeto), sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")


# --- Ed25519 (RFC 8032 §5.1.7) -------------------------------------------
#
# El cotejo de la firma, escrito aqui desde la curva y no importado: un
# verificador que llama al firmador para saber si la firma vale no verifica,
# reproduce. Los cinco vectores oficiales de §7.1 se miden contra **este** bloque
# en P-110a, junto a los del generador; sin esa atadura dos copias divergen solas.

_P = 2 ** 255 - 19
_L = 2 ** 252 + 27742317777372353535851937790883648493
_D = -121665 * pow(121666, _P - 2, _P) % _P
_D2 = 2 * _D % _P
_I = pow(2, (_P - 1) // 4, _P)
_B = (
    15112221349535400772501151409588531511454012693041857206046113283949847762202,
    46316835694926478169428394003475163141307993866256225615783033603165251855960,
    1,
    0,
)
_B = (_B[0], _B[1], 1, _B[0] * _B[1] % _P)


def _punto_suma(p, q):
    x1, y1, z1, t1 = p
    x2, y2, z2, t2 = q
    a = (y1 - x1) * (y2 - x2) % _P
    b = (y1 + x1) * (y2 + x2) % _P
    c = t1 * _D2 % _P * t2 % _P
    d = 2 * z1 * z2 % _P
    e, f, g, h = b - a, d - c, d + c, b + a
    return (e * f % _P, g * h % _P, f * g % _P, e * h % _P)


def _punto_dobla(p):
    x1, y1, z1, _ = p
    a = x1 * x1 % _P
    b = y1 * y1 % _P
    c = 2 * z1 * z1 % _P
    h = a + b
    e = h - (x1 + y1) * (x1 + y1) % _P
    g = a - b
    f = c + g
    return (e * f % _P, g * h % _P, f * g % _P, e * h % _P)


def _punto_escala(k: int, punto) -> tuple:
    resultado = (0, 1, 1, 0)
    for bit in bin(k)[2:]:
        resultado = _punto_dobla(resultado)
        if bit == "1":
            resultado = _punto_suma(resultado, punto)
    return resultado


def _punto_comprime(p) -> bytes:
    x, y, z, _ = p
    inversa = pow(z, _P - 2, _P)
    return ((y * inversa % _P) | (((x * inversa % _P) & 1) << 255)).to_bytes(32, "little")


def _punto_descomprime(bruto: bytes) -> tuple:
    if len(bruto) != 32:
        raise ValueError("un punto Ed25519 mide 32 bytes")
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


def verificar_firma(mensaje: bytes, firma: bytes, publica: bytes) -> bool:
    """`[S]B = R + [k]A` sin cofactor: lo que no mide esa igualdad es `False`."""

    if len(firma) != 64 or len(publica) != 32:
        return False
    s = int.from_bytes(firma[32:], "little")
    if s >= _L:
        return False
    try:
        a = _punto_descomprime(publica)
        r = _punto_descomprime(firma[:32])
    except ValueError:
        return False
    k = int.from_bytes(_hashlib.sha512(firma[:32] + publica + mensaje).digest(), "little") % _L
    return _punto_comprime(_punto_escala(s, _B)) == _punto_comprime(_punto_suma(r, _punto_escala(k, a)))


def _leer_hex(ruta: str, que: str, bytes_esperados: int) -> bytes:
    """Un archivo de hex con comentarios `#` y espacios; el largo se exige, no se adivina."""

    with open(ruta, "r", encoding="utf-8") as flujo:
        crudo = "".join(
            linea.split("#", 1)[0] for linea in flujo.read().splitlines()
        )
    limpio = "".join(crudo.split())
    if len(limpio) != 2 * bytes_esperados:
        raise EntradaInvalida("%s declara %d bytes hex y trae %d" % (que, 2 * bytes_esperados, len(limpio)))
    try:
        return bytes.fromhex(limpio)
    except ValueError:
        raise EntradaInvalida("%s no es hexadecimal" % que) from None


def verificar(
    recibo: Dict[str, object],
    manifiesto: Optional[str],
    ausente: Optional[str],
    portador: str = "auto",
    nombre: Optional[str] = None,
    reglas: Sequence[str] = (),
    exigir_regla: bool = False,
    firma: Optional[bytes] = None,
    clave: Optional[bytes] = None,
) -> Tuple[int, List[str]]:
    lineas: List[str] = []
    fallos = 0
    if firma is not None or clave is not None:
        if firma is None or clave is None:
            raise EntradaInvalida("la firma se coteja contra su clave: faltan --clave o --firma")
        formato = str(recibo.get("formato", ""))
        if formato != FORMATO_FIRMABLE:
            fallos += 1
            lineas.append(
                "firma | FIRMA_NO_FIRMABLE | el recibo declara %s | solo un %s ata sus tramos y su regla"
                % (formato or "sin formato", FORMATO_FIRMABLE)
            )
        else:
            try:
                mensaje = DOMINIO_FIRMA + _canonizar(recibo)
            except ValueError as fallo:
                raise EntradaInvalida("el recibo no se puede canonizar: %s" % fallo) from None
            if verificar_firma(mensaje, firma, clave):
                lineas.append(
                    "firma | valida | clave %s | %d bytes firmados" % (clave.hex()[:12], len(mensaje))
                )
            else:
                fallos += 1
                lineas.append(
                    "firma | REFUTA | la firma no coteja este recibo | clave %s | %d bytes firmados"
                    % (clave.hex()[:12], len(mensaje))
                )
    tramos = recibo.get("tramos")
    if not isinstance(tramos, list) or not tramos:
        raise EntradaInvalida("el recibo no trae tramos")
    if reglas and len(reglas) != len(tramos):
        raise EntradaInvalida(
            "se aportaron %d reglas para %d tramos: una por salto y en orden"
            % (len(reglas), len(tramos))
        )
    ata = 0
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
        declarada_regla = str(tramo.get("sha256_regla", "") or "")
        if declarada_regla and (
            len(declarada_regla) != 64
            or any(c not in "0123456789abcdef" for c in declarada_regla)
        ):
            raise EntradaInvalida(
                "digest de regla no hexadecimal de 64 en el tramo %d" % indice
            )
        if exigir_regla and not declarada_regla:
            fallos += 1
            lineas.append(
                "regla | %s->%s | REGLA_NO_DECLARADA | el tramo no ata su transformacion a una regla declarada fuera"
                % (tramo.get("origen"), tramo.get("destino"))
            )
        elif declarada_regla:
            if indice >= len(reglas):
                fallos += 1
                lineas.append(
                    "regla | %s->%s | REGLA_NO_APORTADA | declara %s y el tercero no trae el artefacto"
                    % (tramo.get("origen"), tramo.get("destino"), declarada_regla[:12])
                )
            else:
                calculada = _hashlib.sha256(
                    reglas[indice].encode("utf-8", "surrogateescape")
                ).hexdigest()
                if calculada != declarada_regla:
                    fallos += 1
                    lineas.append(
                        "regla | %s->%s | REGLA_NO_COINCIDE | declarada %s | artefacto %s"
                        % (tramo.get("origen"), tramo.get("destino"), declarada_regla[:12], calculada[:12])
                    )
                else:
                    ata += 1
                    lineas.append(
                        "regla | %s->%s | ata la transformacion a %s"
                        % (tramo.get("origen"), tramo.get("destino"), calculada[:12])
                    )
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
        topologia, carga, bytes_firma, escapadas = _desenvolver(manifiesto)
        if topologia == "firma_pegada":
            raise EntradaInvalida(
                "firma pegada de %d bytes y cero carga: el manifiesto esta en otro archivo "
                "y su nombre no viaja dentro de este" % (bytes_firma,)
            )
        if topologia != "sin_sobre":
            lineas.append(
                "sobre | %s | %d bytes de firma | %d escapadas | firma no verificada | archivo %s | carga %s"
                % (
                    topologia,
                    bytes_firma,
                    escapadas,
                    _hashlib.sha256(manifiesto.encode("utf-8", "surrogateescape")).hexdigest()[:12],
                    _hashlib.sha256(carga.encode("utf-8", "surrogateescape")).hexdigest()[:12],
                )
            )
        crudas, leido_por, ignoradas = _leer_manifiesto(carga, portador, nombre)
        ordenado = all(a[0].encode() < b[0].encode() for a, b in zip(crudas, crudas[1:]))
        canonica = sorted(crudas, key=lambda fila: fila[0].encode("utf-8"))
        d_manifiesto = _digest_de_pagina(canonica, "manifiesto")
        ultimo = _digest_de_pagina(ultima, "ultima")
        lineas.append("portador | %s | %d filas | %d lineas fuera de la gramatica" % (
            leido_por, len(crudas), ignoradas))
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
    if ata:
        lineas.append(
            "limite | la regla ata %d tramo(s) a un artefacto declarado fuera; no prueba que B aplicara esa regla" % ata
        )
    if firma is not None and not fallos:
        lineas.append(
            "limite | la firma dice quien emitio estos bytes; no que el emisor dijera la verdad ni que la cadena mida lo que afirma medir"
        )
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
        print(
            "uso: verificar_recibo_externo.py --recibo RECIBO.json [--manifiesto F]"
            " [--ausente RUTA] [--portador auto|coreutils|bsd|deb822|suelto] [--nombre F]"
            " [--regla F ...] [--exigir-regla] [--clave R.pub --firma R.firma]"
        )
        return 2
    ruta = argumentos[argumentos.index("--recibo") + 1]
    manifiesto = None
    ausente = None
    if "--manifiesto" in argumentos:
        with open(argumentos[argumentos.index("--manifiesto") + 1], "r", encoding="utf-8") as flujo:
            manifiesto = flujo.read()
    if "--ausente" in argumentos:
        ausente = argumentos[argumentos.index("--ausente") + 1]
    portador = "auto"
    nombre = None
    if "--portador" in argumentos:
        portador = argumentos[argumentos.index("--portador") + 1]
    if "--nombre" in argumentos:
        nombre = argumentos[argumentos.index("--nombre") + 1]
    # `--regla` se repite; el orden de aparicion es el orden de los tramos.
    reglas: List[str] = []
    posicion = 0
    while posicion < len(argumentos):
        if argumentos[posicion] == "--regla":
            if posicion + 1 >= len(argumentos):
                print("entrada-invalida | --regla sin archivo")
                return 2
            with open(argumentos[posicion + 1], "r", encoding="utf-8", errors="surrogateescape") as flujo:
                reglas.append(flujo.read())
            posicion += 2
        else:
            posicion += 1
    exigir_regla = "--exigir-regla" in argumentos
    firma = None
    clave = None
    tiene_clave = "--clave" in argumentos
    tiene_firma = "--firma" in argumentos
    if tiene_clave != tiene_firma:
        print("entrada-invalida | --clave y --firma se dan juntas: una firma sin su clave no se coteja")
        return 2
    try:
        with open(ruta, "r", encoding="utf-8") as flujo:
            datos = _json.load(flujo)
        if not exigir_regla and isinstance(datos, dict):
            exigir_regla = str(datos.get("formato", "")) == "recibo-de-composicion/2"
        if tiene_clave:
            clave = _leer_hex(argumentos[argumentos.index("--clave") + 1], "la clave publica", 32)
            firma = _leer_hex(argumentos[argumentos.index("--firma") + 1], "la firma", 64)
        codigo, lineas = verificar(
            datos, manifiesto, ausente, portador, nombre, reglas, exigir_regla, firma, clave
        )
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
