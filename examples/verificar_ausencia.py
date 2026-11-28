"""examples/verificar_ausencia.py — un acto: probar que una ruta NO esta.

Uso:

    python3 -B examples/verificar_ausencia.py                            # fixture
    python3 -B examples/verificar_ausencia.py --ausente debug.key
    python3 -B examples/verificar_ausencia.py \\
        --manifiesto ../platino-labs/sellos-fecha-cierta-20261009/SHA256SUMS_SELLO_A \\
        --raiz ../platino-labs --ausente tools/sembrar_boveda.sh
    python3 -B examples/verificar_ausencia.py --ausente x.txt --merkle   # testigo transferible

QUE PRUEBA. Que la ausencia de una ruta se pueda recalcular **sin ejecutar el
codigo que la emitio**: este acto no importa el generador y reescribe por su
cuenta la lectura de la pagina, el orden declarado, el digest que la autentica,
la adyacencia del intervalo y el arbol de Merkle. Si las lineas coinciden con
las del modulo es porque el formato esta escrito y no porque los dos llamen a la
misma funcion; si divergen, el desacuerdo es el hallazgo (`P-111a`).

QUE RECIBE. El manifiesto —lo que el sello declaro— y nada mas: ni el arbol, ni
el recibo, ni la maquina donde se produjo. Con `--raiz` compone ademas la
segunda mitad, que el arbol contesta; sin `--raiz` la respuesta es solo sobre la
pagina.

LA PREGUNTA ES NEGATIVA y por eso no la contesta ningun verificador de hashes.
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

QUE NO MIDE, y lo publica en cada corrida. `--universo git` pregunta que rutas
versiona hoy el arbol (`git ls-files`), no que historia hubo: este acto no
recorre el ODB. Un recibo autocontenido vale lo que valga la pagina que lo
acompana; nada aqui fecha la pagina —para eso esta la contrafirma—.

Codigo de salida. La escalera del acto de sello es `0/0/1/1/2` y no distingue
«bloqueado» de «no se sabe»; una compuerta de CI si tiene que distinguirlos:

- `0` la ausencia se sostiene (`ausente`).
- `1` no se sostiene (`presente`: la pagina lo declara, o el arbol lo tiene).
- `2` la entrada no se puede leer (manifiesto ilegible, dialecto no admitido,
  consulta fuera del alfabeto, pagina vacia).
- `3` **no se pudo medir** (`no_medida`): pagina con huecos, ruta fuera del
  universo, o el nombre existe como directorio. Un `3` no es un `0`: no haber
  mirado no es un cero.
"""

from __future__ import annotations

import bisect as _bisect
import hashlib as _hashlib
import os as _os
import subprocess as _subprocess
import sys as _sys
import time as _time
import unicodedata as _unicodedata
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Sequence, Tuple

#: El orden que este acto usa, con nombre y no por omision. Es el del protocolo
#: (§2.1: alfabeto ASCII, forma canonica NFC), no el del volumen: un orden sin
#: declarar hace que dos verificadores honestos coloquen q en dos intervalos
#: distintos sobre la misma pagina. Se reescribe, no se hereda.
ORDEN_DECLARADO = "colacion C sobre bytes UTF-8 (alfabeto §2.1: NFC es la identidad)"

#: La forma canonica de la pagina, y por tanto lo que su digest autentica.
FORMATO_CANONICO = "%s  %s\n"

#: Prefijos de dominio de RFC 6962. Sin ellos, una hoja puede reenviarse como
#: nodo interno y el arbol deja de comprometer una secuencia.
HOJA = b"\x00"
NODO = b"\x01"

VECINO_AUSENTE = "\u22a5"

ALFABETO = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._-"
ANCHURA = 64
HEXADECIMALES = frozenset("0123456789abcdef")
MARCAS_DE_REDACCION = ("<", ">")
PREFIJO_EXPLICITO = "./"

EJEMPLOS = _os.path.dirname(_os.path.abspath(__file__))
MUESTRA = _os.path.join(EJEMPLOS, "sello-de-muestra")
EXCLUSIONES = (".git", "__pycache__", ".venv", "node_modules", ".mypy_cache", ".pytest_cache")

#: Regimenes de plegado del volumen. Se publican: el regimen es entrada, no
#: detalle del observador, y cambia lo que la pagina puede probar.
COLAPSA = "colapsa-el-caso"
DISTINGUE = "distingue-el-caso"
SIN_MEDIR = "no-medido"


class ContratoViolado(Exception):
    """Pre-condicion de §4 incumplida. Una entrada invalida no es un veredicto."""


class VeredictoDeAusencia(str, Enum):
    """Veredicto de la pregunta negativa. Otra pregunta, otro veredicto.

    `no_medida` significa aqui «el orden tiene un hueco» o «nadie miro»; en el
    acto de ubicacion el mismo nombre significa «el universo no indexa esta
    ruta». Mismo nombre, dos sujetos: no se reutilizan.
    """

    AUSENTE = "ausente"
    PRESENTE = "presente"
    NO_MEDIDA = "no_medida"


def _ruta_admisible(ruta: str) -> None:
    """§2.4 y §2.5.2, reescrito: ruta relativa compuesta de slugs (§2.1).

    Fuera del alfabeto no hay orden declarado que consultar, asi que no hay
    prueba: se levanta. Devolver `AUSENTE` para `ñ.txt` seria demostrar una
    ausencia en un orden que nadie definio.
    """

    if not isinstance(ruta, str) or ruta == "":
        raise ContratoViolado("la ruta esta vacia")
    if "\x00" in ruta:
        raise ContratoViolado("NUL prohibido en ruta: %s" % ruta)
    if ruta.startswith("/"):
        raise ContratoViolado("ruta absoluta prohibida (§2.4): %s" % ruta)
    for parte in ruta.split("/"):
        if parte == "":
            raise ContratoViolado("componente vacio en ruta (§2.4): %s" % ruta)
        if parte in (".", ".."):
            raise ContratoViolado("componente de directorio prohibido (§2.1): %s" % ruta)
        if parte.startswith("-"):
            raise ContratoViolado("prefijo '-' prohibido (§2.1): %s" % ruta)
        fuera = sorted({c for c in parte if c not in ALFABETO})
        if fuera:
            raise ContratoViolado("byte fuera del alfabeto (§2.1) en %s: %s" % (ruta, "".join(fuera)))
        if _unicodedata.normalize("NFC", parte) != parte:
            raise ContratoViolado("forma no canonica NFC (§2.1): %s" % ruta)


def canonizar(ruta: str) -> Tuple[str, bool]:
    """La ruta en la forma que el orden usa, y si traia prefijo `./`."""

    if not isinstance(ruta, str) or ruta == "":
        raise ContratoViolado("la consulta no declara ruta")
    limpia = ruta
    prefijada = False
    while limpia.startswith(PREFIJO_EXPLICITO):
        limpia = limpia[len(PREFIJO_EXPLICITO) :]
        prefijada = True
    if limpia == "":
        raise ContratoViolado("la consulta se reduce a vacio")
    _ruta_admisible(limpia)
    return limpia, prefijada


def _clave(ruta: str) -> bytes:
    """Clave de orden byte a byte, colacion C (§3.d.2)."""

    return ruta.encode("utf-8")


@dataclass(frozen=True)
class EntradaDeclarada:
    """Una fila de la pagina. `ruta` es texto, no una ruta ya tipada.

    Una ruta redactada no es una ruta: forzarla al tipo mentiria. Cuando la fila
    es opaca se conserva el texto y el motivo; cuando no lo es, `motivo` esta
    vacio.
    """

    ruta: str
    digest: str
    motivo: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.ruta, str) or self.ruta == "":
            raise ContratoViolado("la fila de la pagina no declara ruta")
        if not isinstance(self.digest, str) or len(self.digest) != ANCHURA:
            raise ContratoViolado("la fila de la pagina no declara digest")
        if any(c not in HEXADECIMALES for c in self.digest):
            raise ContratoViolado("digest no hexadecimal en minusculas: %s" % self.ruta)

    @property
    def opaca(self) -> bool:
        return self.motivo != ""


def _digest_pagina(filas: Sequence[EntradaDeclarada]) -> str:
    texto = "".join(FORMATO_CANONICO % (f.digest, f.ruta) for f in filas)
    return _hashlib.sha256(texto.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Pagina:
    """El manifiesto como **secuencia ordenada**, que es lo que la ausencia usa.

    `filas` esta siempre en orden canonico, venga ordenado o no el archivo. Si no
    venia, `desordenada` lo publica: el testigo lleva indices de **esta**
    secuencia, no de las lineas del archivo.

    `redactadas` cuenta las filas cuya ruta es un marcador. Cualquier valor mayor
    que 0 degrada toda consulta a `NO_MEDIDA`: un hueco en el orden no se acota.

    Una pagina vacia **se levanta**. `∀ p ∈ ∅` es cierto, de modo que una
    implementacion ingenua responderia «ausente» a cualquier consulta sobre un
    manifiesto de cero filas: el falso verde mas barato que existe.
    """

    filas: Tuple[EntradaDeclarada, ...]
    digest: str
    declarado: Tuple[EntradaDeclarada, ...] = ()
    desordenada: bool = False
    redactadas: int = 0

    def __post_init__(self) -> None:
        if not self.filas:
            raise ContratoViolado("una pagina sin filas no prueba ninguna ausencia")
        for previa, actual in zip(self.filas, self.filas[1:]):
            if not _clave(previa.ruta) < _clave(actual.ruta):
                raise ContratoViolado(
                    "la pagina no esta en orden canonico: %s / %s" % (previa.ruta, actual.ruta)
                )
        if not isinstance(self.digest, str) or len(self.digest) != ANCHURA:
            raise ContratoViolado("la pagina no declara digest")


def pagina_desde_filas(filas: Sequence[EntradaDeclarada]) -> Pagina:
    """Construye la secuencia canonica a partir de las filas leidas."""

    declarado = tuple(filas)
    ordenadas = tuple(sorted(declarado, key=lambda f: _clave(f.ruta)))
    return Pagina(
        filas=ordenadas,
        digest=_digest_pagina(ordenadas),
        declarado=declarado,
        desordenada=ordenadas != declarado,
        redactadas=sum(1 for f in ordenadas if f.opaca),
    )


def leer_pagina(texto: str, origen: str = "manifiesto") -> Pagina:
    """Lee el formato de `sha256sum` —`digest  ruta`— y devuelve la pagina.

    Cuatro decisiones que el formato no trae y aqui se declaran:

    - Una ruta con `<` o `>` es **opaca**: no se valida ni se busca, porque
      buscar un marcador de redaccion y no encontrarlo no es una divergencia del
      artefacto, es una laguna del manifiesto.
    - Cualquier otra ruta inadmisible (`..`, absoluta, byte fuera del alfabeto)
      **se levanta**: un manifiesto mal formado no se audita clasificando sus
      filas, se rechaza.
    - El digest debe ser de 64 hexadecimales en minusculas. Este acto no verifica
      anchuras truncadas: la pagina sellada no las usa.
    - Un prefijo `./` explicito se normaliza: denota el mismo archivo. Un
      dialecto ajeno (`SHA256 (ruta) = …`, SRI, `sha256sum` con un solo espacio)
      no se normaliza: **se rechaza**, y el acto no nombra cual era.
    """

    if not isinstance(texto, str):
        raise ContratoViolado("el manifiesto no es texto")
    filas = []
    vistas = set()
    for numero, linea in enumerate(texto.splitlines(), start=1):
        limpia = linea.strip()
        if limpia == "" or limpia.startswith("#"):
            continue
        if len(limpia) < ANCHURA + 2:
            raise ContratoViolado("linea demasiado corta en %s:%d" % (origen, numero))
        digest = limpia[:ANCHURA]
        if any(c not in HEXADECIMALES for c in digest):
            raise ContratoViolado("digest no hexadecimal en minusculas en %s:%d" % (origen, numero))
        if limpia[ANCHURA] != " ":
            raise ContratoViolado("dialecto no admitido en %s:%d" % (origen, numero))
        if limpia[ANCHURA + 1] not in (" ", "*"):
            raise ContratoViolado("marcador de modo no declarado en %s:%d" % (origen, numero))
        ruta = limpia[ANCHURA + 2 :]
        while ruta.startswith(PREFIJO_EXPLICITO):
            ruta = ruta[len(PREFIJO_EXPLICITO) :]
        if ruta == "":
            raise ContratoViolado("fila sin ruta en %s:%d" % (origen, numero))
        if ruta in vistas:
            raise ContratoViolado("el manifiesto repite una ruta en %s:%d" % (origen, numero))
        vistas.add(ruta)
        opaca = any(marca in ruta for marca in MARCAS_DE_REDACCION)
        if not opaca:
            _ruta_admisible(ruta)
        filas.append(
            EntradaDeclarada(
                ruta=ruta,
                digest=digest,
                motivo="ruta redactada: remite a un lugar que el manifiesto no escribe" if opaca else "",
            )
        )
    if not filas:
        raise ContratoViolado("el manifiesto no declara ninguna fila")
    return pagina_desde_filas(filas)


@dataclass(frozen=True)
class Testigo:
    """Lo que un verificador necesita para creer `AUSENTE` sin buscar.

    `posicion` es el indice que q ocupa (`PRESENTE`) u ocuparia (`AUSENTE`) en
    `Pagina.filas`. En los extremos una de las dos filas adyacentes es `None` y
    la prueba sigue valiendo —una sola cola basta cuando q cae fuera del rango—.
    """

    consulta: str
    estado: VeredictoDeAusencia
    posicion: int
    anterior: Optional[EntradaDeclarada]
    siguiente: Optional[EntradaDeclarada]
    digest_pagina: str
    motivo: str = ""

    def intervalo(self) -> str:
        izq = '"%s"' % self.anterior.ruta if self.anterior is not None else VECINO_AUSENTE
        der = '"%s"' % self.siguiente.ruta if self.siguiente is not None else VECINO_AUSENTE
        return "%s < %s < %s" % (izq, self.consulta, der)


def consultar(pagina: Pagina, consulta: str) -> Testigo:
    """El testigo de `consulta` contra la pagina. Funcion pura, sin disco."""

    if not isinstance(pagina, Pagina):
        raise ContratoViolado("la consulta no se hace contra una Pagina")
    q, _ = canonizar(consulta)
    if pagina.redactadas:
        return Testigo(
            consulta=q,
            estado=VeredictoDeAusencia.NO_MEDIDA,
            posicion=-1,
            anterior=None,
            siguiente=None,
            digest_pagina=pagina.digest,
            motivo="la pagina tiene %d filas redactadas: el orden tiene un hueco" % pagina.redactadas,
        )
    claves = [_clave(f.ruta) for f in pagina.filas]
    clave = _clave(q)
    i = _bisect.bisect_left(claves, clave)
    if i < len(claves) and claves[i] == clave:
        return Testigo(
            consulta=q,
            estado=VeredictoDeAusencia.PRESENTE,
            posicion=i,
            anterior=pagina.filas[i],
            siguiente=None,
            digest_pagina=pagina.digest,
            motivo="la fila %d declara la ruta" % i,
        )
    anterior = pagina.filas[i - 1] if i > 0 else None
    siguiente = pagina.filas[i] if i < len(pagina.filas) else None
    motivo = (
        "entre las filas %d y %d" % (i - 1, i)
        if anterior is not None and siguiente is not None
        else ("antes de la primera fila" if siguiente is not None else "despues de la ultima fila")
    )
    return Testigo(
        consulta=q,
        estado=VeredictoDeAusencia.AUSENTE,
        posicion=i,
        anterior=anterior,
        siguiente=siguiente,
        digest_pagina=pagina.digest,
        motivo=motivo,
    )


def verificar(pagina: Pagina, testigo: Testigo) -> bool:
    """Comprueba el testigo **sin buscar**: lee solo las filas que el testigo nombra.

    Compara la pagina autenticada contra `digest_pagina` —que es lo que ata el
    testigo a una pagina concreta— y luego comprueba adyacencia por indice. No
    recorre la pagina: por eso vale O(1) por consulta una vez autenticada, y por
    eso `autenticar` es una operacion aparte que se declara.
    """

    if testigo.digest_pagina != pagina.digest:
        return False
    if pagina.redactadas:
        return False
    n = len(pagina.filas)
    i = testigo.posicion
    if testigo.estado is VeredictoDeAusencia.PRESENTE:
        return 0 <= i < n and pagina.filas[i] == testigo.anterior
    if testigo.estado is not VeredictoDeAusencia.AUSENTE:
        return False
    if not 0 <= i <= n:
        return False
    anterior = pagina.filas[i - 1] if i > 0 else None
    siguiente = pagina.filas[i] if i < n else None
    if anterior != testigo.anterior or siguiente != testigo.siguiente:
        return False
    clave = _clave(testigo.consulta)
    if anterior is not None and not _clave(anterior.ruta) < clave:
        return False
    if siguiente is not None and not clave < _clave(siguiente.ruta):
        return False
    return True


def autenticar(pagina: Pagina) -> str:
    """El digest de la pagina, recalculado. Cuesta O(n) y se hace una vez.

    Declararlo aparte es el punto: `verificar` compara contra el digest que el
    testigo trae, y ese digest solo vale lo que valga la fuente de la que el
    verificador lo obtuvo. Si el testigo trae su propio digest, no se verifica
    nada; hay que contrastarlo con el ancla.
    """

    return _digest_pagina(pagina.filas)


# ---------------------------------------------------------------------------
# Dialecto transferible: raiz Merkle sobre la secuencia (RFC 6962)
# ---------------------------------------------------------------------------


def _mayor_potencia_de_dos_menor(n: int) -> int:
    k = 1
    while k * 2 < n:
        k *= 2
    return k


def _hoja(fila: EntradaDeclarada) -> bytes:
    datos = _clave(fila.ruta) + b"\x00" + fila.digest.encode("ascii")
    return _hashlib.sha256(HOJA + datos).digest()


def raiz_merkle(pagina: Pagina) -> str:
    """El compromiso de la secuencia. `tamano` viaja con la raiz, no dentro."""

    return _raiz([_hoja(f) for f in pagina.filas]).hex()


def _raiz(hojas: Sequence[bytes]) -> bytes:
    if len(hojas) == 1:
        return hojas[0]
    k = _mayor_potencia_de_dos_menor(len(hojas))
    return _hashlib.sha256(NODO + _raiz(hojas[:k]) + _raiz(hojas[k:])).digest()


def _prueba(hojas: Sequence[bytes], i: int) -> Tuple[bytes, ...]:
    if len(hojas) == 1:
        return ()
    k = _mayor_potencia_de_dos_menor(len(hojas))
    if i < k:
        return _prueba(hojas[:k], i) + (_raiz(hojas[k:]),)
    return _prueba(hojas[k:], i - k) + (_raiz(hojas[:k]),)


def _reconstruir(hoja: bytes, camino: Tuple[bytes, ...], i: int, n: int) -> Optional[bytes]:
    """La raiz que explicaria `hoja` en la posicion `i` de una secuencia de `n`."""

    if n == 1:
        return hoja if not camino else None
    if not camino:
        return None
    k = _mayor_potencia_de_dos_menor(n)
    if i < k:
        sub = _reconstruir(hoja, camino[:-1], i, k)
        return None if sub is None else _hashlib.sha256(NODO + sub + camino[-1]).digest()
    sub = _reconstruir(hoja, camino[:-1], i - k, n - k)
    return None if sub is None else _hashlib.sha256(NODO + camino[-1] + sub).digest()


@dataclass(frozen=True)
class TestigoMerkle:
    """Ausencia transferible: se verifica **sin** la pagina, con la raiz.

    Aqui esta lo que la pagina no puede dar: probar «q no esta» a quien no debe
    recibir el inventario. El coste es O(log n) digests, no O(1), y la
    adyacencia la garantiza la posicion: el arbol compromete una secuencia, de
    modo que dos hojas en `i` y `i+1` no admiten nada en medio.
    """

    consulta: str
    estado: VeredictoDeAusencia
    posicion: int
    raiz: str
    tamano: int
    hoja_anterior: Optional[Tuple[str, str]] = None
    camino_anterior: Tuple[str, ...] = ()
    hoja_siguiente: Optional[Tuple[str, str]] = None
    camino_siguiente: Tuple[str, ...] = ()


def testigo_merkle(pagina: Pagina, consulta: str) -> TestigoMerkle:
    t = consultar(pagina, consulta)
    if t.estado is not VeredictoDeAusencia.AUSENTE:
        return TestigoMerkle(
            consulta=t.consulta,
            estado=t.estado,
            posicion=t.posicion if t.estado is VeredictoDeAusencia.PRESENTE else -1,
            raiz=raiz_merkle(pagina),
            tamano=len(pagina.filas),
        )
    hojas = [_hoja(f) for f in pagina.filas]
    i = t.posicion
    anterior = None
    camino_anterior: Tuple[str, ...] = ()
    if i > 0:
        anterior = (pagina.filas[i - 1].ruta, pagina.filas[i - 1].digest)
        camino_anterior = tuple(h.hex() for h in _prueba(hojas, i - 1))
    siguiente = None
    camino_siguiente: Tuple[str, ...] = ()
    if i < len(hojas):
        siguiente = (pagina.filas[i].ruta, pagina.filas[i].digest)
        camino_siguiente = tuple(h.hex() for h in _prueba(hojas, i))
    return TestigoMerkle(
        consulta=t.consulta,
        estado=t.estado,
        posicion=i,
        raiz=raiz_merkle(pagina),
        tamano=len(hojas),
        hoja_anterior=anterior,
        camino_anterior=camino_anterior,
        hoja_siguiente=siguiente,
        camino_siguiente=camino_siguiente,
    )


def verificar_merkle(testigo: TestigoMerkle) -> bool:
    """Verifica el testigo contra su raiz. No necesita la pagina.

    Comprueba cuatro cosas y ninguna sobra: que las dos inclusiones llegan a la
    raiz, que las dos posiciones son consecutivas, que la consulta cae
    estrictamente entre las dos rutas, y que el estado es `AUSENTE`. Sin la
    ultima, un testigo de presencia verificado como ausencia seria un falso
    verde con firma.
    """

    if testigo.estado is not VeredictoDeAusencia.AUSENTE:
        return False
    if testigo.tamano < 1 or not 0 <= testigo.posicion <= testigo.tamano:
        return False
    i = testigo.posicion
    if i > 0:
        if testigo.hoja_anterior is None:
            return False
        ruta, digest = testigo.hoja_anterior
        hoja = _hashlib.sha256(HOJA + _clave(ruta) + b"\x00" + digest.encode("ascii")).digest()
        camino = tuple(bytes.fromhex(h) for h in testigo.camino_anterior)
        if _reconstruir(hoja, camino, i - 1, testigo.tamano) != _raiz_de(testigo.raiz):
            return False
        if not _clave(ruta) < _clave(testigo.consulta):
            return False
    elif testigo.hoja_anterior is not None:
        return False
    if i < testigo.tamano:
        if testigo.hoja_siguiente is None:
            return False
        ruta, digest = testigo.hoja_siguiente
        hoja = _hashlib.sha256(HOJA + _clave(ruta) + b"\x00" + digest.encode("ascii")).digest()
        camino = tuple(bytes.fromhex(h) for h in testigo.camino_siguiente)
        if _reconstruir(hoja, camino, i, testigo.tamano) != _raiz_de(testigo.raiz):
            return False
        if not _clave(testigo.consulta) < _clave(ruta):
            return False
    elif testigo.hoja_siguiente is not None:
        return False
    return True


def _raiz_de(hexadecimal: str) -> Optional[bytes]:
    try:
        return bytes.fromhex(hexadecimal)
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Lo que solo puede contestar el arbol, y se publica aparte
# ---------------------------------------------------------------------------


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
    el arbol solo puede confirmarlo sobre las rutas que su universo indexa. En
    modo `git` la pregunta es que rutas versiona hoy el arbol (`git ls-files`),
    no que historia hubo: este acto no recorre el ODB.
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
            pagina = leer_pagina(flujo.read(), _os.path.basename(ruta_manifiesto))
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
