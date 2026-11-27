"""conservacion.py — anillo 7: el testigo que mide una magnitud y no juzga el calculo.

LA PREGUNTA. `R_ab` dice que las paginas encadenadas son las mismas. No dice que
`B` hiciera su trabajo: un conciliador puede aplicar el cambio equivocado,
sellarlo y publicar `intacta` —el falso verde que `COMPOSICION.md` §7 deja
abierto—. La pregunta es si eso se puede medir **sin que el recibo entienda el
dominio**.

LA RESPUESTA CORTA. La correccion no se puede medir: exige saber que se esperaba.
Lo que si se puede medir es una **magnitud** que la transformacion deba conservar,
si el cliente la declara. Y ahi esta la decision que el algebra no trae: la
conservacion **no es una propiedad del recibo**, es una propiedad del par de
paginas bajo una medida elegida por el cliente. Por eso el veredicto lleva
siempre el nombre de la medida y no existe un `conservada` a secas.

TRES DECISIONES QUE EL ALGEBRA NO TRAE Y AQUI SE DECLARAN.

1. **La medida la declara el cliente y el recibo la obedece.** `filas` cuenta
   entradas; `claves` autentica el conjunto de rutas **sin mirar los digests**.
   Cualquier otra cosa se rechaza: una medida que el modulo eligiera por su
   cuenta seria una opinion, y una opinion que se propaga por una cadena se lee
   como un hecho. El precio de la generalidad es que la medida es un argumento,
   no una constante.

2. **El valor no se acepta: se recalcula.** `valor_origen` y `valor_destino` son
   propiedades derivadas de las paginas, nunca campos. Un recibo que miente
   sobre su propia magnitud no se puede ni construir —la misma disciplina que
   los digests de `Tramo`—, y un tercero puede rehacer la cuenta sin confiar en
   el productor.

3. **Compone por transitividad de la igualdad, y NO es completa.** De
   `f(A)=f(B)` y `f(B)=f(C)` se sigue `f(A)=f(C)`: el veredicto no es una
   heuristica. Pero `no_conservada` **no** afirma que `f(A) != f(C)`: un salto
   puede perder una clave y el siguiente volver a anadirla. La direccion que
   falta es la que convierte una degradacion en una acusacion, y aqui no se da.

LO QUE ESTE MODULO NO HACE (lista cerrada). No lee disco. No decide si el valor
que `B` calculo era el correcto —mide que la magnitud sobreviva, no que el
calculo fuera bueno—. No elige la medida por el cliente. No certifica que el
conjunto de medidas sea suficiente para un dominio: `filas` y `claves` pueden
coincidir mientras el importe de una cita cambia, y eso se publica en la linea
`limite` de cada cadena en vez de silenciarse.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Sequence, Tuple

from .composicion import Recibo
from .types import ContratoViolado
from .ubicacion import EntradaDeclarada

#: Las medidas declaradas. `filas` cuenta; `claves` autentica el conjunto de
#: rutas y **descarta los digests a proposito**: si los incluyera seria el digest
#: de la pagina, y entonces mediria identidad de bytes, que es el anillo 4 y no
#: esto.
MEDIDAS: Tuple[str, ...] = ("filas", "claves")


def declarar_medida(nombre: str) -> str:
    """Valida el nombre de la medida. Fuera de `MEDIDAS` no hay que medir."""

    if not isinstance(nombre, str) or not nombre:
        raise ContratoViolado("la medida no se declara sola", valor=nombre)
    if nombre not in MEDIDAS:
        raise ContratoViolado("medida desconocida", valor=nombre, conocidas=list(MEDIDAS))
    return nombre


def medir(filas: Sequence[EntradaDeclarada], medida: str) -> str:
    """El valor de la medida sobre una pagina. Texto legible, comparable por `==`.

    El nombre viaja dentro del valor para que dos valores de medidas distintas no
    se puedan comparar por accidente: `"filas=5" != "claves=..."` incluso cuando
    ambos son cadenas.
    """

    nombre = declarar_medida(medida)
    if nombre == "filas":
        return "filas=%d" % len(filas)
    texto = "".join("%s\n" % ruta for ruta in sorted(f.ruta for f in filas))
    return "claves=%s" % hashlib.sha256(texto.encode("utf-8")).hexdigest()


def _corto(valor: str) -> str:
    """El valor para las lineas: el digest recortado a 12, la cuenta entera."""

    nombre, _, resto = valor.partition("=")
    return "%s=%s" % (nombre, resto[:12] if nombre == "claves" else resto)


class VeredictoDeConservacion(str, Enum):
    """Tres estados, y el del medio es el que un algebra de dos valores pierde.

    `sin_medida` no es «conserve» ni «no conserve»: a un lado del salto le falta
    la pagina, de modo que la comparacion **no se pudo hacer**. Es el mismo
    tercer caso que `frontera_vacua` en el anillo 4, y por eso no se degrada a
    `conservada` en ninguna direccion.
    """

    CONSERVADA = "conservada"
    SIN_MEDIDA = "sin_medida"
    NO_CONSERVADA = "no_conservada"


#: De menos a mas grave. No se importa de otro documento porque no hay otro: el
#: orden de degradacion de `UBICACION.md` §4 habla de objetos, y este habla de una
#: magnitud que el cliente eligio. Inventarlo aqui y publicarlo es lo unico
#: honesto, y P-99 mide que el orden declarado sea exactamente este.
RANGO: Tuple[VeredictoDeConservacion, ...] = (
    VeredictoDeConservacion.CONSERVADA,
    VeredictoDeConservacion.SIN_MEDIDA,
    VeredictoDeConservacion.NO_CONSERVADA,
)


def rango(veredicto: VeredictoDeConservacion) -> int:
    """Posicion en el orden declarado. Fuera de el no hay orden que consultar."""

    try:
        return RANGO.index(veredicto)
    except ValueError:  # pragma: no cover - el enum cierra el conjunto
        raise ContratoViolado("veredicto fuera del orden declarado", valor=veredicto) from None


@dataclass(frozen=True)
class Conservacion:
    """Un salto `A -> B` medido con **una** medida declarada por el cliente.

    Las paginas se guardan enteras y los valores no: `valor_origen` y
    `valor_destino` se recalculan en cada acceso. Guardar el valor y la pagina
    seria guardar dos fuentes de verdad, y la que se lee primero gana.
    """

    origen: str
    destino: str
    medida: str
    pagina_origen: Tuple[EntradaDeclarada, ...] = ()
    pagina_destino: Tuple[EntradaDeclarada, ...] = ()

    def __post_init__(self) -> None:
        declarar_medida(self.medida)

    @property
    def valor_origen(self) -> str:
        return medir(self.pagina_origen, self.medida)

    @property
    def valor_destino(self) -> str:
        return medir(self.pagina_destino, self.medida)

    @property
    def veredicto(self) -> VeredictoDeConservacion:
        if not self.pagina_origen or not self.pagina_destino:
            return VeredictoDeConservacion.SIN_MEDIDA
        if self.valor_origen == self.valor_destino:
            return VeredictoDeConservacion.CONSERVADA
        return VeredictoDeConservacion.NO_CONSERVADA

    @property
    def conserva(self) -> bool:
        return self.veredicto is VeredictoDeConservacion.CONSERVADA

    @property
    def es_identidad(self) -> bool:
        """`A -> A` con la misma pagina. Sin la pagina igual no hay neutro.

        Es la leccion del anillo 4 aplicada a la magnitud: un salto que declara
        no mover el nodo y entrega **otra** pagina no es el neutro, es basura con
        forma de neutro —conserva la medida y cambio el objeto—.
        """

        return self.origen == self.destino and self.pagina_origen == self.pagina_destino and self.conserva

    def linea(self) -> str:
        return "salto | %s->%s | %s | %s -> %s | %s" % (
            self.origen,
            self.destino,
            self.medida,
            _corto(self.valor_origen),
            _corto(self.valor_destino),
            self.veredicto.value,
        )


@dataclass(frozen=True)
class CadenaDeConservacion:
    """Saltos encadenados bajo **una sola** medida.

    Mezclar medidas en una cadena no es un dato, es un error de lectura: el
    maximo de dos ordenes distintos no existe. Se rechaza al construir.
    """

    saltos: Tuple[Conservacion, ...]

    def __post_init__(self) -> None:
        if not self.saltos:
            raise ContratoViolado("una cadena sin saltos no conserva nada")
        medidas = sorted({salto.medida for salto in self.saltos})
        if len(medidas) != 1:
            raise ContratoViolado("la cadena mezcla medidas", medidas=medidas)
        for previo, actual in zip(self.saltos, self.saltos[1:]):
            if previo.destino != actual.origen:
                raise ContratoViolado(
                    "los saltos de la cadena no se tocan", previo=previo.destino, actual=actual.origen
                )

    @property
    def medida(self) -> str:
        return self.saltos[0].medida

    @property
    def origen(self) -> str:
        return self.saltos[0].origen

    @property
    def destino(self) -> str:
        return self.saltos[-1].destino

    @property
    def empalmes(self) -> Tuple[Tuple[str, str, str], ...]:
        """Nodos donde lo que un salto dejo y el siguiente leyo no coinciden.

        Es el defecto que **no vive en ningun salto**: los dos pueden conservar
        por separado y el nodo intermedio publicar dos magnitudes distintas. El
        algebra de la cadena no lo puede heredar de sus tramos; hay que mirar el
        empalme, y por eso se mira aqui.
        """

        salida: List[Tuple[str, str, str]] = []
        for previo, actual in zip(self.saltos, self.saltos[1:]):
            if not previo.pagina_destino or not actual.pagina_origen:
                continue
            dejado, leido = previo.valor_destino, actual.valor_origen
            if dejado != leido:
                salida.append((previo.destino, dejado, leido))
        return tuple(salida)

    @property
    def empalmes_sin_medir(self) -> Tuple[str, ...]:
        """Nodos cuyo empalme no se pudo comparar. El tercer caso, no el segundo."""

        nodos: List[str] = []
        for previo, actual in zip(self.saltos, self.saltos[1:]):
            if not previo.pagina_destino or not actual.pagina_origen:
                nodos.append(previo.destino)
        return tuple(nodos)

    @property
    def veredicto(self) -> VeredictoDeConservacion:
        if self.empalmes:
            return VeredictoDeConservacion.NO_CONSERVADA
        peor = max((salto.veredicto for salto in self.saltos), key=rango)
        if self.empalmes_sin_medir and rango(peor) < rango(VeredictoDeConservacion.SIN_MEDIDA):
            return VeredictoDeConservacion.SIN_MEDIDA
        return peor

    @property
    def conserva(self) -> bool:
        return self.veredicto is VeredictoDeConservacion.CONSERVADA

    @property
    def tramo_degradado(self) -> Optional[Conservacion]:
        """El primer salto que alcanza el peor rango. Nombra uno, no el conjunto."""

        tope = rango(self.veredicto)
        for salto in self.saltos:
            if rango(salto.veredicto) == tope:
                return salto
        return None

    def cadena(self) -> str:
        partes = [self.saltos[0].origen]
        for salto in self.saltos:
            partes.append("->")
            partes.append(salto.destino)
        return " ".join(partes)

    def lineas(self) -> List[str]:
        """La cadena como lineas de texto, en el dialecto de los otros actos.

        La linea `limite` se emite **siempre**, tambien cuando la cadena conserva.
        Es la unica forma de que el lector de un `conservada` no tenga que
        recordar que la magnitud no es el calculo.
        """

        salida = [
            "conservacion | %s" % self.cadena(),
            "medida | %s | declarada por el cliente" % self.medida,
        ]
        for salto in self.saltos:
            salida.append(salto.linea())
        for nodo, dejado, leido in self.empalmes:
            salida.append("empalme | %s | %s != %s" % (nodo, _corto(dejado), _corto(leido)))
        for nodo in self.empalmes_sin_medir:
            salida.append("empalme | %s | sin medir | falta la pagina de un lado" % nodo)
        degradado = self.tramo_degradado
        if degradado is not None and not self.conserva:
            salida.append(
                "degradado | %s->%s | %s" % (degradado.origen, degradado.destino, degradado.veredicto.value)
            )
        if not self.conserva and self.saltos[0].valor_origen == self.saltos[-1].valor_destino:
            salida.append("extremo | el extremo puede coincidir aunque la cadena no conserve")
        salida.append("limite | conserva el transporte, no el calculo: la magnitud elegida puede sobrevivir a un valor mal calculado")
        salida.append("-> %s" % self.veredicto.value)
        return salida


def identidad(nodo: str, pagina: Sequence[EntradaDeclarada], medida: str) -> Conservacion:
    """El neutro: un salto `nodo -> nodo` con la misma pagina y la medida intacta."""

    return Conservacion(nodo, nodo, medida, tuple(pagina), tuple(pagina))


def componer(izq: CadenaDeConservacion, der: CadenaDeConservacion) -> CadenaDeConservacion:
    """Encadena dos cadenas si se tocan, y **absorbe** las identidades.

    Componer con el neutro devuelve el otro operando igual, no con un salto de
    mas: un monoide cuyo elemento neutro deja basura no es un monoide. Las
    identidades internas se descartan por la misma razon —`A->B`, `B->B`, `B->C`
    es `A->B`, `B->C`— salvo que **todo** sea identidad, en cuyo caso se conserva
    una: la cadena vacia no certifica nada.
    """

    if izq.medida != der.medida:
        raise ContratoViolado("no se componen cadenas de medidas distintas", izquierda=izq.medida, derecha=der.medida)
    if izq.destino != der.origen:
        raise ContratoViolado("las cadenas no se tocan", izquierda=izq.destino, derecha=der.origen)
    if es_identidad_sola(izq):
        return der
    if es_identidad_sola(der):
        return izq
    saltos = tuple(s for s in izq.saltos + der.saltos if not s.es_identidad)
    if not saltos:
        return izq
    return CadenaDeConservacion(saltos)


def es_identidad_sola(cadena: CadenaDeConservacion) -> bool:
    """La cadena es exactamente un salto y ese salto es el neutro."""

    return len(cadena.saltos) == 1 and cadena.saltos[0].es_identidad


def de_recibo(recibo: Recibo, medida: str) -> CadenaDeConservacion:
    """Los saltos de un recibo del anillo 4, medidos con la medida declarada.

    Es el puente entre los dos anillos y el unico punto donde se tocan: el
    recibo trae las paginas, y la conservacion solo anade la pregunta.
    """

    declarar_medida(medida)
    saltos = tuple(
        Conservacion(tramo.origen, tramo.destino, medida, tramo.pagina_origen, tramo.pagina_destino)
        for tramo in recibo.tramos
    )
    return CadenaDeConservacion(saltos)


def medidas_de(recibo: Recibo) -> Tuple[CadenaDeConservacion, ...]:
    """Una cadena por medida declarada, sobre el mismo recibo.

    Un recibo, dos preguntas, dos respuestas. Se devuelven juntas para que
    publicar solo la que conviene exija borrar una linea a la vista.
    """

    return tuple(de_recibo(recibo, medida) for medida in MEDIDAS)
