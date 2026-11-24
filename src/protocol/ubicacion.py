"""Adjudicación por contenido: la identidad de un artefacto es su digest, no su ruta.

DEFECTO QUE MIDE. Un manifiesto sellado declara pares `(ruta, digest)`. El
verificador de un sello comparaba ruta contra ruta y devolvía ROJO cuando cuatro
actas se habían movido a `actas/` sin que un solo byte cambiara: confundía la
topología del árbol con la identidad del contenido. Medido el 2026-11-24 sobre
`SHA256SUMS_SELLO_A`: 14/14 conformes por hash, 10/14 por ruta.

QUE MIDE. Cuatro estados por fila, exhaustivos y mutuamente excluyentes, sobre la
función `S: ruta -> digest` del árbol observado:

    conforme    S(p) = h                    los bytes sellados, en su ruta sellada
    reubicado   S(p) != h y h está en S     los bytes sellados, en otra ruta
    diverge     h no está en S              no están: alterados o perdidos
    opaco       p no es una ruta            la fila remite a algo que no se lee

UN INTERCAMBIO NO ES UNA REUBICACIÓN. Si dos artefactos canjean sus rutas, cada
fila queda «reubicada» con multiplicidad 1 —el esquema que sólo mira el digest la
llamaría limpia— y sin embargo es exactamente lo que un sello existe para
detectar. Por eso cada fila reubicada publica si su ruta quedó **vacía** o si
algo la **ocupó**, y el acto distingue `intercambiada` de `reubicada`. Falsador:
P-27.

LA MULTIPLICIDAD SE PUBLICA. Si el digest aparece en `k` rutas, el recibo no puede
decir cuál se movió; puede decir que hay `k`. Ocultar `k` convierte una ambigüedad
en una afirmación. Falsador: P-26.

EL UNIVERSO ES DECLARADO. `indice_por_contenido` indexa sólo las rutas que se le
entregan, y devuelve cuántas leyó y cuáles omitió para que el acto las publique.
`ALL` no es un universo: recorrer el sistema de archivos entero mete `.venv` y
`node_modules` en el denominador y hace que el mismo acto dé cifras distintas en
cada máquina.

LO QUE NO HACE. No firma, no fecha y no decide autoría: dice dónde están los
bytes. La fecha cierta la aporta el ancla y la adjudicación de esa ancla es la
contrafirma, que es otro objeto.
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from .types import (
    ALGORITMO,
    ANCHURA_COMPLETA,
    ContratoViolado,
    Hash,
    RutaRelativa,
)

__all__ = [
    "MARCAS_DE_REDACCION",
    "EstadoDeEntrada",
    "VeredictoDeUbicacion",
    "EntradaDeclarada",
    "Juicio",
    "Adjudicacion",
    "Indice",
    "leer_manifiesto_hash",
    "indice_por_contenido",
    "adjudicar",
]

# Convención declarada, no deducida: los ángulos no pertenecen a `ALFABETO`
# (§2.1), así que un segmento entre ellos no puede nombrar un archivo de este
# protocolo. Marca una redacción, y una redacción no se lee como pérdida.
MARCAS_DE_REDACCION: Tuple[str, ...] = ("<", ">")


class EstadoDeEntrada(str, Enum):
    """Estado de una fila del manifiesto contra un árbol observado."""

    CONFORME = "conforme"
    REUBICADO = "reubicado"
    DIVERGE = "diverge"
    OPACO = "opaco"


class VeredictoDeUbicacion(str, Enum):
    """Veredicto del acto completo. Es otra pregunta que la contrafirma.

    La contrafirma adjudica *si un ancla cubre un acto*; esto adjudica *si un
    árbol contiene los bytes que un manifiesto declara*. Reutilizar
    `VeredictoAdjudicado` para las dos preguntas haría que un mismo objeto
    respondiera por dos sujetos distintos.
    """

    INTACTA = "intacta"
    REUBICADA = "reubicada"
    INTERCAMBIADA = "intercambiada"
    DIVERGENTE = "divergente"
    NO_MEDIDA = "no_medida"


# ---------------------------------------------------------------------------
# El manifiesto, tal como se leyó
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EntradaDeclarada:
    """Una fila del manifiesto. `ruta` es texto, no `RutaRelativa`.

    Una ruta redactada no es una ruta: forzarla al tipo mentiría. Cuando la fila
    es opaca se conserva el texto y el motivo; cuando no lo es, la ruta ya pasó
    por `RutaRelativa` y `motivo` está vacío.
    """

    ruta: str
    h: Hash
    motivo: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.ruta, str) or self.ruta == "":
            raise ContratoViolado("la fila del manifiesto no declara ruta", valor=self.ruta)
        if not isinstance(self.h, Hash):
            raise ContratoViolado("la fila del manifiesto no declara Hash", ruta=self.ruta)

    @property
    def opaca(self) -> bool:
        return self.motivo != ""


def _es_redactada(ruta: str) -> bool:
    return any(marca in ruta for marca in MARCAS_DE_REDACCION)


def leer_manifiesto_hash(texto: str, origen: str = "manifiesto") -> Tuple[EntradaDeclarada, ...]:
    """Lee el formato de `sha256sum`: `digest  ruta`, ordenado o no.

    Tres decisiones que el formato no trae y aquí se declaran:

    - Una ruta con `<` o `>` es **opaca**: no se convierte en `RutaRelativa` ni
      se busca, porque buscar un marcador de redacción y no encontrarlo no es
      una divergencia del artefacto, es una laguna del manifiesto.
    - Cualquier otra ruta inadmisible (`..`, absoluta, byte fuera del alfabeto)
      **se levanta**: un manifiesto mal formado no se audita clasificando sus
      filas, se rechaza. Confundir «no se puede leer» con «no está» es el error
      que este módulo existe para no cometer.
    - El digest debe ser de 64 hexadecimales en minúsculas. Una anchura truncada
      no se acepta aquí: para eso está `Hash(anchura=...)`, y el manifiesto
      sellado no la usa.
    """

    if not isinstance(texto, str):
        raise ContratoViolado("el manifiesto no es texto", origen=origen)
    entradas: List[EntradaDeclarada] = []
    vistas = set()
    for numero, linea in enumerate(texto.splitlines(), start=1):
        limpia = linea.strip()
        if limpia == "" or limpia.startswith("#"):
            continue
        if len(limpia) < ANCHURA_COMPLETA + 2:
            raise ContratoViolado("línea de manifiesto demasiado corta", origen=origen, linea=numero)
        digest = limpia[:ANCHURA_COMPLETA]
        separador = limpia[ANCHURA_COMPLETA : ANCHURA_COMPLETA + 2]
        ruta = limpia[ANCHURA_COMPLETA + 2 :]
        if separador[0] != " ":
            raise ContratoViolado("falta el separador del manifiesto", origen=origen, linea=numero)
        if separador[1] not in (" ", "*"):
            raise ContratoViolado("marcador de modo no declarado", origen=origen, linea=numero)
        if ruta == "":
            raise ContratoViolado("fila sin ruta", origen=origen, linea=numero)
        h = Hash(algoritmo=ALGORITMO, digest=digest)
        if ruta in vistas:
            raise ContratoViolado("el manifiesto repite una ruta", origen=origen, ruta=ruta)
        vistas.add(ruta)
        if _es_redactada(ruta):
            entradas.append(
                EntradaDeclarada(
                    ruta=ruta,
                    h=h,
                    motivo="ruta redactada: remite a un lugar que el manifiesto no escribe",
                )
            )
            continue
        RutaRelativa(ruta)
        entradas.append(EntradaDeclarada(ruta=ruta, h=h))
    if not entradas:
        raise ContratoViolado("el manifiesto no declara ninguna fila", origen=origen)
    return tuple(entradas)


# ---------------------------------------------------------------------------
# El árbol, indexado por contenido
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Indice:
    """`S: ruta -> digest` y su inverso por contenido, con multiplicidad.

    Las rutas son texto: una ruta observada es lo que el árbol tiene, y el árbol
    puede tener nombres que el alfabeto del protocolo no admite. Rechazarlos al
    indexar escondería el archivo en vez de medirlo.
    """

    por_ruta: Mapping[str, str]
    por_digest: Mapping[str, Tuple[str, ...]]
    leidas: int = 0
    omitidas: Tuple[str, ...] = field(default_factory=tuple)
    #: Rutas que **existen en disco** y que el universo declarado no indexó
    #: (no versionadas, o fuera de las exclusiones). Sin esto, un artefacto
    #: presente pero invisible al índice aparece como `REUBICADO` limpio
    #: —"se movió"— cuando en realidad el universo no lo miró. Medido: el
    #: sello A da 14 reubicados con universo `git ls-files` y 10 conformes +
    #: 4 reubicados con universo de disco, sobre el mismo árbol.
    fuera_del_universo: Tuple[str, ...] = field(default_factory=tuple)

    @classmethod
    def desde_mapa(cls, por_ruta: Mapping[str, str]) -> "Indice":
        """Construye el índice desde un mapa ya medido.

        Existe para que el inverso se derive del directo en un solo sitio: dos
        tablas que se llenan por separado divergen, y el índice es justo el par
        que tiene que cuadrar.
        """

        acumulado: Dict[str, List[str]] = {}
        for ruta, digest in por_ruta.items():
            acumulado.setdefault(digest, []).append(ruta)
        return cls(
            por_ruta=dict(por_ruta),
            por_digest={d: tuple(sorted(rs)) for d, rs in acumulado.items()},
            leidas=len(por_ruta),
        )

    def digest_en(self, ruta: str) -> Optional[str]:
        return self.por_ruta.get(ruta)

    def rutas_con(self, digest: str) -> Tuple[str, ...]:
        return self.por_digest.get(digest, ())

    def multiplicidad(self, digest: str) -> int:
        return len(self.rutas_con(digest))


def _digest_de_archivo(completa: str) -> str:
    h = hashlib.sha256()
    with open(completa, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 16), b""):
            h.update(bloque)
    return h.hexdigest()


def indice_por_contenido(
    raiz: str, rutas: Iterable[str], sondear: Iterable[str] = ()
) -> Indice:
    """Indexa el universo dado, medido contra la raíz.

    Un enlace simbólico no se sigue y un directorio no se lee: sus bytes no son
    los bytes del manifiesto, y seguirlos haría que el índice dependiera de algo
    que el manifiesto no declara. Ambos se publican en `omitidas`.

    `sondear` son las rutas declaradas que hay que comprobar **en disco**
    aunque el universo no las traiga. Un universo barato (`git ls-files`) no ve
    lo no versionado, y esa ceguera no puede salir como "no está": una ruta que
    existe en disco y no en el universo es una laguna del universo, y se
    publica en `fuera_del_universo` para que la adjudicación no la lea como
    ausencia.
    """

    if not os.path.isdir(raiz):
        raise ContratoViolado("la raíz del universo no es un directorio", raiz=raiz)
    por_ruta: Dict[str, str] = {}
    acumulado: Dict[str, List[str]] = {}
    omitidas: List[str] = []
    for ruta in rutas:
        if not isinstance(ruta, str) or ruta == "":
            raise ContratoViolado("ruta de universo no textual", valor=ruta)
        completa = os.path.join(raiz, *ruta.split("/"))
        if os.path.islink(completa):
            omitidas.append(ruta)
            continue
        if not os.path.isfile(completa):
            omitidas.append(ruta)
            continue
        digest = _digest_de_archivo(completa)
        por_ruta[ruta] = digest
        acumulado.setdefault(digest, []).append(ruta)
    por_digest = {d: tuple(sorted(rs)) for d, rs in acumulado.items()}
    fuera = [
        ruta
        for ruta in sondear
        if ruta not in por_ruta and os.path.lexists(os.path.join(raiz, *ruta.split("/")))
    ]
    return Indice(
        por_ruta=por_ruta,
        por_digest=por_digest,
        leidas=len(por_ruta),
        omitidas=tuple(sorted(omitidas)),
        fuera_del_universo=tuple(sorted(fuera)),
    )


# ---------------------------------------------------------------------------
# La adjudicación
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Juicio:
    """Una fila adjudicada. El testigo va aquí, no en un mensaje de error."""

    declarada: str
    h: Hash
    estado: EstadoDeEntrada
    observada: Optional[str] = None
    multiplicidad: int = 0
    medido: Optional[str] = None
    ocupante_declarado: bool = False
    motivo: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.estado, EstadoDeEntrada):
            raise ContratoViolado("juicio sin estado tipado", declarada=self.declarada)
        if self.estado is EstadoDeEntrada.REUBICADO:
            if self.observada is None:
                raise ContratoViolado("una reubicación sin testigo no es un juicio", declarada=self.declarada)
            if self.multiplicidad < 1:
                raise ContratoViolado("una reubicación publica su multiplicidad", declarada=self.declarada)
        if self.estado is EstadoDeEntrada.CONFORME and self.medido != self.h.digest:
            raise ContratoViolado("un conforme cuyo medido no es el declarado", declarada=self.declarada)
        if self.estado is EstadoDeEntrada.OPACO and self.motivo == "":
            raise ContratoViolado("una fila opaca declara el motivo", declarada=self.declarada)

    @property
    def vaciada(self) -> bool:
        """La ruta declarada quedó sin bytes: nadie la ocupó."""

        return self.estado is EstadoDeEntrada.REUBICADO and self.medido is None


@dataclass(frozen=True)
class Adjudicacion:
    """El acto: los catorce juicios y su peor hallazgo."""

    juicios: Tuple[Juicio, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.juicios, tuple):
            raise ContratoViolado("los juicios no son tupla")

    def cuenta(self, estado: EstadoDeEntrada) -> int:
        return sum(1 for j in self.juicios if j.estado is estado)

    @property
    def conformes(self) -> Tuple[Juicio, ...]:
        return tuple(j for j in self.juicios if j.estado is EstadoDeEntrada.CONFORME)

    @property
    def reubicados(self) -> Tuple[Juicio, ...]:
        return tuple(j for j in self.juicios if j.estado is EstadoDeEntrada.REUBICADO)

    @property
    def divergentes(self) -> Tuple[Juicio, ...]:
        return tuple(j for j in self.juicios if j.estado is EstadoDeEntrada.DIVERGE)

    @property
    def opacos(self) -> Tuple[Juicio, ...]:
        return tuple(j for j in self.juicios if j.estado is EstadoDeEntrada.OPACO)

    @property
    def veredicto(self) -> VeredictoDeUbicacion:
        """El peor hallazgo, con un orden declarado y no negociable.

        - `divergente` manda: hay bytes que ya no están. Es un hallazgo positivo.
        - `intercambiada` le sigue: un artefacto reubicado cuya ruta no quedó
          vacía. Los bytes existen y la frontera está rota; el sello existe para
          nombrar justo eso.
        - `no_medida` va después: no saber no se lee como cero, y tampoco se lee
          como un hallazgo positivo.
        - `reubicada` es benigna y explicada: los bytes están, la ruta cambió.
        - `intacta` exige que **todas** las filas sean conformes, y que haya
          filas: un acto sin filas es `no_medida`, no `intacta`.
        """

        if not self.juicios:
            return VeredictoDeUbicacion.NO_MEDIDA
        if self.divergentes:
            return VeredictoDeUbicacion.DIVERGENTE
        if any(not j.vaciada for j in self.reubicados):
            return VeredictoDeUbicacion.INTERCAMBIADA
        if self.opacos:
            return VeredictoDeUbicacion.NO_MEDIDA
        if self.reubicados:
            return VeredictoDeUbicacion.REUBICADA
        return VeredictoDeUbicacion.INTACTA

    @property
    def conforme(self) -> bool:
        """¿La afirmación del acto se sostiene?

        La afirmación es sobre **bytes**: los artefactos sellados existen en este
        árbol. Qué ruta tengan es otro predicado, y sale en `testigos()`.
        """

        return self.veredicto in (VeredictoDeUbicacion.INTACTA, VeredictoDeUbicacion.REUBICADA)

    def testigos(self) -> Tuple[str, ...]:
        """Las filas que no son conformes, en una línea cada una, ordenadas."""

        lineas: List[str] = []
        for j in sorted(self.juicios, key=lambda x: x.declarada):
            if j.estado is EstadoDeEntrada.REUBICADO:
                lineas.append(
                    "%s %s -> %s%s"
                    % (
                        j.estado.value,
                        j.declarada,
                        j.observada,
                        "" if j.vaciada else " (ruta ocupada)",
                    )
                )
            elif j.estado is EstadoDeEntrada.DIVERGE:
                lineas.append(
                    "%s %s (%s)"
                    % (j.estado.value, j.declarada, "ausente" if j.medido is None else "bytes alterados")
                )
            elif j.estado is EstadoDeEntrada.OPACO:
                lineas.append("%s %s (%s)" % (j.estado.value, j.declarada, j.motivo))
        return tuple(lineas)

    def resumen(self) -> str:
        partes = [
            "%d %s" % (self.cuenta(EstadoDeEntrada.CONFORME), EstadoDeEntrada.CONFORME.value),
            "%d %s" % (self.cuenta(EstadoDeEntrada.REUBICADO), EstadoDeEntrada.REUBICADO.value),
            "%d %s" % (self.cuenta(EstadoDeEntrada.DIVERGE), EstadoDeEntrada.DIVERGE.value),
            "%d %s" % (self.cuenta(EstadoDeEntrada.OPACO), EstadoDeEntrada.OPACO.value),
        ]
        return "%s -> %s" % (" / ".join(partes), self.veredicto.value)


def adjudicar(entradas: Sequence[EntradaDeclarada], indice: Indice) -> Adjudicacion:
    """Adjudica cada fila contra el índice. Función pura: no toca el disco."""

    if not isinstance(indice, Indice):
        raise ContratoViolado("se adjudica contra un Indice, no contra un mapa suelto")
    declarados = {e.h.digest for e in entradas}
    juicios: List[Juicio] = []
    for entrada in entradas:
        if entrada.opaca:
            juicios.append(
                Juicio(
                    declarada=entrada.ruta,
                    h=entrada.h,
                    estado=EstadoDeEntrada.OPACO,
                    motivo=entrada.motivo,
                )
            )
            continue
        medido = indice.digest_en(entrada.ruta)
        if medido == entrada.h.digest:
            juicios.append(
                Juicio(
                    declarada=entrada.ruta,
                    h=entrada.h,
                    estado=EstadoDeEntrada.CONFORME,
                    observada=entrada.ruta,
                    multiplicidad=indice.multiplicidad(entrada.h.digest),
                    medido=medido,
                )
            )
            continue
        candidatas = [r for r in indice.rutas_con(entrada.h.digest) if r != entrada.ruta]
        if candidatas:
            # Una ruta que existe en disco y que el universo no indexó no es
            # una reubicación: es un universo que no miró. Decir "se movió"
            # afirmaría algo que el índice no midió.
            if medido is None and entrada.ruta in indice.fuera_del_universo:
                juicios.append(
                    Juicio(
                        declarada=entrada.ruta,
                        h=entrada.h,
                        estado=EstadoDeEntrada.OPACO,
                        multiplicidad=len(candidatas),
                        motivo="la ruta existe en disco y el universo declarado no la indexa",
                    )
                )
                continue
            juicios.append(
                Juicio(
                    declarada=entrada.ruta,
                    h=entrada.h,
                    estado=EstadoDeEntrada.REUBICADO,
                    observada=candidatas[0],
                    multiplicidad=len(candidatas),
                    medido=medido,
                    ocupante_declarado=bool(medido is not None and medido in declarados),
                )
            )
            continue
        juicios.append(
            Juicio(
                declarada=entrada.ruta,
                h=entrada.h,
                estado=EstadoDeEntrada.DIVERGE,
                observada=None,
                multiplicidad=0,
                medido=medido,
            )
        )
    return Adjudicacion(juicios=tuple(juicios))
