"""src/protocol/ausencia.py — Anillo 3: probar que una ruta **no** esta declarada.

Los anillos anteriores adjudican presencias. `predicado` pregunta si un recibo
emitido conserva su identidad; `ubicacion` pregunta si un arbol conserva los
bytes que un manifiesto declara. Falta la pregunta que todo auditor hace y que
ningun verificador de hashes contesta: **¿puedes probar que esto NO esta?**

No es la negacion de `ubicacion`. La presencia se decide contra el arbol; la
ausencia se decide contra la **pagina**, y son dos sujetos distintos. De ahi
salen las tres tesis de este modulo.

1. **La ausencia es un predicado del orden, no del arbol.** Un «no existe
   ningun elemento con la propiedad P» solo se decide agotando el conjunto. Pero
   «la ruta q no es una fila de M» se decide sobre M, que es finito y explicito.
   El testigo es un intervalo: la fila mayor que q y la menor que q, **adyacentes
   en el orden canonico**. Sin adyacencia el testigo no prueba nada: dos filas
   cualesquiera no acotan, porque cualquier q cae entre alguna pareja.

2. **La adyacencia no se verifica con dos filas.** Se verifica teniendo la
   pagina entera (`Pagina`) o teniendo un compromiso que ate la posicion
   (Merkle, `testigo_merkle`). De ahi los dos dialectos de testigo y el coste
   declarado de cada uno: autenticar la pagina cuesta O(n) una vez, y entonces
   cada consulta cuesta O(1); con raiz Merkle el testigo cuesta O(log n) y se
   verifica **sin** la pagina. El `O(1)` sin mas es falso: ignora la
   autenticacion.

3. **Una pagina con huecos no prueba ausencia.** Una fila redactada (`<...>`) no
   es un nombre: el orden tiene un agujero y q podria caer dentro del agujero.
   El modulo responde `NO_MEDIDA`, no `AUSENTE`.

Y una cuarta, que no es de este modulo pero lo condiciona: el orden de la pagina
es sobre **cadenas**; el orden del sistema de archivos puede ser sobre cadenas
**plegadas a minusculas**. Donde el volumen colapsa el caso, `a.txt` y `A.txt`
designan un archivo. La pagina prueba `a.txt ∉ M` y el arbol tiene esos bytes. El
acto `examples/verificar_ausencia.py` publica ese regimen en vez de elegir uno.

Falsadores: P-48 a P-57 en `tests/test_ausencia.py`.
"""

from __future__ import annotations

import bisect
import hashlib
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Sequence, Tuple

from .types import ContratoViolado, RutaRelativa
from .ubicacion import EntradaDeclarada, Manifiesto

#: El orden que este modulo usa, con nombre y no por omision. Es el del
#: protocolo (§2.1: alfabeto ASCII, forma canonica NFC), no el del volumen: un
#: orden sin declarar hace que dos verificadores honestos coloquen q en dos
#: intervalos distintos sobre la misma pagina.
ORDEN_DECLARADO = "colacion C sobre bytes UTF-8 (alfabeto §2.1: NFC es la identidad)"

#: La forma canonica de la pagina, y por tanto lo que su digest autentica. Es una
#: entrada declarada: dos serializaciones distintas del mismo contenido dan dos
#: digests y el testigo deja de viajar.
FORMATO_CANONICO = "%s  %s\n"

#: Prefijos de dominio de RFC 6962. Sin ellos, una hoja puede reenviarse como
#: nodo interno y el arbol deja de comprometer una secuencia.
HOJA = b"\x00"
NODO = b"\x01"

VECINO_AUSENTE = "\u22a5"


class VeredictoDeAusencia(str, Enum):
    """Veredicto de la pregunta negativa. Otra pregunta, otro veredicto.

    No se reutiliza `VeredictoDeUbicacion`: alli `no_medida` significa «el
    universo no indexa esta ruta» y aqui «el orden tiene un hueco» o «nadie
    miro». Mismo nombre, dos sujetos.

    Una entrada invalida **no es un veredicto** (ley 22): se levanta
    `ContratoViolado` y el acto sale con RC 2.
    """

    AUSENTE = "ausente"
    PRESENTE = "presente"
    NO_MEDIDA = "no_medida"


def canonizar(ruta: str) -> Tuple[str, bool]:
    """La ruta en la forma que el orden usa, y si traia prefijo `./`.

    Fuera del alfabeto de §2.1 no hay orden declarado que consultar, asi que no
    hay prueba: se levanta. Devolver `AUSENTE` para `ñ.txt` seria demostrar una
    ausencia en un orden que nadie definio.
    """

    if not isinstance(ruta, str) or ruta == "":
        raise ContratoViolado("la consulta no declara ruta", valor=ruta)
    limpia = ruta
    prefijada = False
    while limpia.startswith("./"):
        limpia = limpia[2:]
        prefijada = True
    if limpia == "":
        raise ContratoViolado("la consulta se reduce a vacio", valor=ruta)
    RutaRelativa(limpia)
    return limpia, prefijada


def _clave(ruta: str) -> bytes:
    """Clave de orden byte a byte, la misma que `RutaRelativa.clave_bytes`."""

    return ruta.encode("utf-8")


def _digest_pagina(filas: Sequence[EntradaDeclarada]) -> str:
    texto = "".join(FORMATO_CANONICO % (f.h.digest, f.ruta) for f in filas)
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Pagina:
    """El manifiesto como **secuencia ordenada**, que es lo que la ausencia usa.

    `filas` esta siempre en orden canonico, venga ordenado o no el archivo. Si no
    venia, `desordenada` lo publica: el testigo lleva indices de **esta**
    secuencia, no de las lineas del archivo, y sin declararlo un tercero
    comprobaria los indices contra su copia y no contra el orden.

    `redactadas` cuenta las filas cuya ruta es un marcador (`<...>`). Cualquier
    valor mayor que 0 degrada toda consulta a `NO_MEDIDA`: un hueco en el orden
    no se puede acotar.

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
                    "la pagina no esta en orden canonico", previa=previa.ruta, actual=actual.ruta
                )
        if not isinstance(self.digest, str) or len(self.digest) != 64:
            raise ContratoViolado("la pagina no declara digest", valor=self.digest)


def pagina_desde_manifiesto(manifiesto: Manifiesto) -> Pagina:
    """Construye la secuencia canonica a partir del manifiesto leido."""

    declarado = tuple(manifiesto.filas)
    filas = tuple(sorted(declarado, key=lambda f: _clave(f.ruta)))
    return Pagina(
        filas=filas,
        digest=_digest_pagina(filas),
        declarado=declarado,
        desordenada=filas != declarado,
        redactadas=sum(1 for f in filas if f.opaca),
    )


@dataclass(frozen=True)
class Testigo:
    """Lo que un verificador necesita para creer `AUSENTE` sin buscar.

    `posicion` es el indice que q ocupa (`PRESENTE`) u ocuparia (`AUSENTE`) en
    `Pagina.filas`. `anterior` y `siguiente` son las dos filas adyacentes; en los
    extremos, una de las dos es `None` y la prueba sigue siendo valida —una sola
    cola basta cuando q cae fuera del rango declarado—.
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
        raise ContratoViolado("la consulta no se hace contra una Pagina", valor=type(pagina))
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
    i = bisect.bisect_left(claves, clave)
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
    recorre la pagina: por eso vale O(1) por consulta una vez que la pagina esta
    autenticada, y por eso `autenticar` es una operacion aparte y se declara.
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
    datos = _clave(fila.ruta) + b"\x00" + fila.h.digest.encode("ascii")
    return hashlib.sha256(HOJA + datos).digest()


def raiz_merkle(pagina: Pagina) -> str:
    """El compromiso de la secuencia. `tamano` viaja con la raiz, no dentro."""

    return _raiz([_hoja(f) for f in pagina.filas]).hex()


def _raiz(hojas: Sequence[bytes]) -> bytes:
    if len(hojas) == 1:
        return hojas[0]
    k = _mayor_potencia_de_dos_menor(len(hojas))
    return hashlib.sha256(NODO + _raiz(hojas[:k]) + _raiz(hojas[k:])).digest()


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
        return None if sub is None else hashlib.sha256(NODO + sub + camino[-1]).digest()
    sub = _reconstruir(hoja, camino[:-1], i - k, n - k)
    return None if sub is None else hashlib.sha256(NODO + camino[-1] + sub).digest()


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
        if t.estado is VeredictoDeAusencia.PRESENTE:
            return TestigoMerkle(
                consulta=t.consulta,
                estado=t.estado,
                posicion=t.posicion,
                raiz=raiz_merkle(pagina),
                tamano=len(pagina.filas),
            )
        return TestigoMerkle(
            consulta=t.consulta, estado=t.estado, posicion=-1, raiz=raiz_merkle(pagina), tamano=len(pagina.filas)
        )
    hojas = [_hoja(f) for f in pagina.filas]
    i = t.posicion
    anterior = None
    camino_anterior: Tuple[str, ...] = ()
    if i > 0:
        anterior = (pagina.filas[i - 1].ruta, pagina.filas[i - 1].h.digest)
        camino_anterior = tuple(h.hex() for h in _prueba(hojas, i - 1))
    siguiente = None
    camino_siguiente: Tuple[str, ...] = ()
    if i < len(hojas):
        siguiente = (pagina.filas[i].ruta, pagina.filas[i].h.digest)
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
        hoja = hashlib.sha256(HOJA + _clave(ruta) + b"\x00" + digest.encode("ascii")).digest()
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
        hoja = hashlib.sha256(HOJA + _clave(ruta) + b"\x00" + digest.encode("ascii")).digest()
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
