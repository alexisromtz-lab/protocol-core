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

EL UNIVERSO ES UNA CONTINUACIÓN, NO UN PEAJE. `intacta` se decide con las rutas
que el manifiesto declara; el universo sólo hace falta para nombrar un destino
cuando una ruta falla. `adjudicar_por_rutas` mide lo declarado y devuelve `None`
—no un veredicto— cuando no alcanza, así que el barrido se paga sólo en el caso
que lo necesita. Falsador: P-43.

EL DIALECTO ES UNA ENTRADA. Un manifiesto no es texto abstracto: es una
gramática. Medido el 2026-11-24 contra cinco manifiestos públicos reales, este
lector admite uno (jq 1.7.1, `sha256sum`), normaliza el prefijo `./` de otro
(el instalador de Debian) y **nombra** los que no lee (OpenBSD, npm) en vez de
describir el síntoma. Si el dialecto no viaja en el recibo, dos verificadores
honestos firman veredictos incomparables sobre el mismo árbol: la dependencia de
observador entrando por la puerta de la evidencia y no por la de la máquina.

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
    "PREFIJO_EXPLICITO",
    "DIALECTO_ADMITIDO",
    "EstadoDeEntrada",
    "VeredictoDeUbicacion",
    "EntradaDeclarada",
    "Manifiesto",
    "Juicio",
    "Adjudicacion",
    "Indice",
    "leer_manifiesto",
    "leer_manifiesto_hash",
    "indice_por_contenido",
    "adjudicar",
]

# Convención declarada, no deducida: los ángulos no pertenecen a `ALFABETO`
# (§2.1), así que un segmento entre ellos no puede nombrar un archivo de este
# protocolo. Marca una redacción, y una redacción no se lee como pérdida.
MARCAS_DE_REDACCION: Tuple[str, ...] = ("<", ">")

#: Un prefijo `./` no elige otro archivo: elige el mismo, escrito con el
#: directorio actual delante. `sha256sum x` y `sha256sum ./x` emiten la misma
#: fila con distinta ortografía, y el manifiesto del instalador de Debian es
#: exactamente eso —640 filas `./MANIFEST`, `./cdrom/...`— que este lector
#: rechazaba antes de medir contra el manifiesto real (2026-11-24). Normalizarlo
#: no es adivinar: no hay dos sujetos. Pero **se cuenta y se publica**, porque
#: una normalización que no se mide es una huella del lector convertida en dato
#: del objeto.
PREFIJO_EXPLICITO = "./"

#: El dialecto que este lector admite, con nombre y no por omisión. El dialecto
#: del manifiesto es una **entrada**, y una entrada no declarada reintroduce la
#: dependencia de observador por la puerta de adelante: dos verificadores
#: honestos que leen dialectos distintos firman recibos incomparables sobre el
#: mismo árbol. Falsador: P-33.
DIALECTO_ADMITIDO = "sha256sum: digest + dos espacios + ruta (marcador de modo «*» admitido)"


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
    SUPLANTADA = "suplantada"
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


def _dialecto(limpia: str) -> str:
    """Nombre del dialecto ajeno que la línea usa, o `""` si no se reconoce.

    Sólo se nombran los tres que se midieron contra manifiestos públicos reales
    (2026-11-24): OpenBSD 7.7, el registro de npm y cualquier `sha256sum` escrito
    con un solo espacio. Nombrar el dialecto **no lo admite**: convierte «falta
    el separador» —un síntoma— en el nombre de lo que hay que convertir antes de
    que el recibo pueda firmarse.
    """

    if limpia.startswith(("SHA256 (", "SHA512 (", "SHA1 (")):
        return "BSD tradicional «SHA256 (ruta) = hex»"
    cabecera, _, resto = limpia.partition("-")
    if cabecera in ("sha1", "sha256", "sha384", "sha512") and resto.endswith("="):
        return "SRI base64 «%s-…»" % cabecera
    if (
        len(limpia) > ANCHURA_COMPLETA + 1
        and limpia[ANCHURA_COMPLETA] == " "
        and limpia[ANCHURA_COMPLETA + 1] not in (" ", "*")
        and all(c in "0123456789abcdef" for c in limpia[:ANCHURA_COMPLETA])
    ):
        return "sha256sum con un solo espacio (se exige «digest__ruta» o «digest *ruta»)"
    return ""


@dataclass(frozen=True)
class Manifiesto:
    """El manifiesto leído, con la huella del lector publicada junto a las filas.

    Sin `dialecto` el recibo describe el árbol pero no la lectura, y la lectura
    es la mitad del resultado: misma evidencia, dos lectores, dos veredictos.
    `prefijadas` cuenta las filas que traían `./` explícito y se normalizaron;
    `0` es una medición, no un hueco.
    """

    filas: Tuple[EntradaDeclarada, ...]
    dialecto: str
    prefijadas: int

    def __post_init__(self) -> None:
        if not isinstance(self.dialecto, str) or self.dialecto.strip() == "":
            raise ContratoViolado("el manifiesto no declara dialecto")
        if not isinstance(self.prefijadas, int) or isinstance(self.prefijadas, bool):
            raise ContratoViolado("la cuenta de prefijos no es entera", valor=self.prefijadas)
        if self.prefijadas < 0 or self.prefijadas > len(self.filas):
            raise ContratoViolado(
                "la cuenta de prefijos excede las filas",
                prefijadas=self.prefijadas,
                filas=len(self.filas),
            )


def leer_manifiesto(texto: str, origen: str = "manifiesto") -> Manifiesto:
    """Lee el formato de `sha256sum`: `digest  ruta`, ordenado o no.

    Cuatro decisiones que el formato no trae y aquí se declaran:

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
    - Un prefijo `./` explícito se normaliza y **se cuenta** (`prefijadas`):
      denota el mismo archivo. Un dialecto ajeno no se normaliza y **se
      nombra** al rechazarlo: denota otra gramática.
    """

    if not isinstance(texto, str):
        raise ContratoViolado("el manifiesto no es texto", origen=origen)
    entradas: List[EntradaDeclarada] = []
    vistas = set()
    prefijadas = 0
    for numero, linea in enumerate(texto.splitlines(), start=1):
        limpia = linea.strip()
        if limpia == "" or limpia.startswith("#"):
            continue
        if len(limpia) < ANCHURA_COMPLETA + 2:
            ajeno = _dialecto(limpia)
            if ajeno:
                raise ContratoViolado(
                    "dialecto no admitido: %s" % ajeno, origen=origen, linea=numero
                )
            raise ContratoViolado("línea de manifiesto demasiado corta", origen=origen, linea=numero)
        digest = limpia[:ANCHURA_COMPLETA]
        separador = limpia[ANCHURA_COMPLETA : ANCHURA_COMPLETA + 2]
        cruda = limpia[ANCHURA_COMPLETA + 2 :]
        if separador[0] != " ":
            ajeno = _dialecto(limpia)
            if ajeno:
                raise ContratoViolado(
                    "dialecto no admitido: %s" % ajeno, origen=origen, linea=numero
                )
            raise ContratoViolado("falta el separador del manifiesto", origen=origen, linea=numero)
        if separador[1] not in (" ", "*"):
            ajeno = _dialecto(limpia)
            if ajeno:
                raise ContratoViolado(
                    "dialecto no admitido: %s" % ajeno, origen=origen, linea=numero
                )
            raise ContratoViolado("marcador de modo no declarado", origen=origen, linea=numero)
        ruta = cruda
        while ruta.startswith(PREFIJO_EXPLICITO):
            ruta = ruta[len(PREFIJO_EXPLICITO) :]
        if ruta != cruda:
            prefijadas += 1
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
    return Manifiesto(tuple(entradas), DIALECTO_ADMITIDO, prefijadas)


def leer_manifiesto_hash(texto: str, origen: str = "manifiesto") -> Tuple[EntradaDeclarada, ...]:
    """Sólo las filas. Se conserva para no romper §3; el dialecto viaja en `leer_manifiesto`."""

    return leer_manifiesto(texto, origen).filas


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
    #: Rutas que el universo **sí** trajo y que no se pudieron medir de forma
    #: estable: el archivo cambió, o desapareció, entre `isfile` y la lectura.
    #: No entran en `por_ruta` —no hay digest que publicar— pero tampoco son
    #: `omitidas`: no es que sus bytes no sean del manifiesto, es que nadie los
    #: llegó a leer. Se publican aquí para que la fila declarada salga `OPACO`
    #: con el motivo del instrumento y no `DIVERGE` con una acusación falsa.
    inestables: Tuple[str, ...] = field(default_factory=tuple)

    @classmethod
    def desde_mapa(
        cls,
        por_ruta: Mapping[str, str],
        omitidas: Iterable[str] = (),
        inestables: Iterable[str] = (),
    ) -> "Indice":
        """Construye el índice desde un mapa ya medido.

        Existe para que el inverso se derive del directo en un solo sitio: dos
        tablas que se llenan por separado divergen, y el índice es justo el par
        que tiene que cuadrar. `omitidas` e `inestables` viajan aquí porque la
        vía rápida las descubre midiendo y no puede dejarlas en el camino.
        """

        acumulado: Dict[str, List[str]] = {}
        for ruta, digest in por_ruta.items():
            acumulado.setdefault(digest, []).append(ruta)
        return cls(
            por_ruta=dict(por_ruta),
            por_digest={d: tuple(sorted(rs)) for d, rs in acumulado.items()},
            leidas=len(por_ruta),
            omitidas=tuple(sorted(omitidas)),
            inestables=tuple(sorted(inestables)),
        )

    def digest_en(self, ruta: str) -> Optional[str]:
        return self.por_ruta.get(ruta)

    def rutas_con(self, digest: str) -> Tuple[str, ...]:
        return self.por_digest.get(digest, ())

    def multiplicidad(self, digest: str) -> int:
        return len(self.rutas_con(digest))


def _digest_de_archivo(completa: str) -> Optional[str]:
    """El digest de los bytes, o `None` si el archivo no se pudo medir estable.

    Un digest calculado mientras otro proceso escribe no es el digest de nada:
    es una mezcla de dos estados que nunca existió entera en disco. Publicarlo
    acusaría al artefacto de una alteración que ocurrió en el instrumento. Se
    mide antes y después de leer y, si el tamaño, la fecha, el inodo o el
    dispositivo cambiaron —o si los bytes leídos no son los que el archivo
    declara tener—, no se emite digest: `None` es `no medido`, no `distinto`.

    `mtime_ns` puede repetirse en un reemplazo rápido; por eso también se
    comparan el inodo y el tamaño leído. Ninguno de los cuatro es suficiente
    solo, y los cuatro juntos no son una garantía: son la parte del intervalo
    que se puede medir con `fstat`.
    """

    try:
        with open(completa, "rb") as f:
            antes = os.fstat(f.fileno())
            h = hashlib.sha256()
            leidos = 0
            for bloque in iter(lambda: f.read(1 << 16), b""):
                leidos += len(bloque)
                h.update(bloque)
            despues = os.fstat(f.fileno())
    except OSError:
        return None
    estable = (antes.st_size, antes.st_mtime_ns, antes.st_ino, antes.st_dev) == (
        despues.st_size,
        despues.st_mtime_ns,
        despues.st_ino,
        despues.st_dev,
    )
    if not estable or leidos != despues.st_size:
        return None
    return h.hexdigest()


def indice_por_contenido(
    raiz: str, rutas: Iterable[str], sondear: Iterable[str] = ()
) -> Indice:
    """Indexa el universo dado, medido contra la raíz.

    Un enlace simbólico no se sigue y un directorio no se lee: sus bytes no son
    los bytes del manifiesto, y seguirlos haría que el índice dependiera de algo
    que el manifiesto no declara. Ambos se publican en `omitidas`. Una lectura
    que no se puede cerrar de forma estable se publica en `inestables`, y por
    eso el índice no afirma el digest de esa ruta.

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
    inestables: List[str] = []
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
        if digest is None:
            inestables.append(ruta)
            continue
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
        inestables=tuple(sorted(inestables)),
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
    observadas: Tuple[str, ...] = ()
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
            # El testigo nombra las k rutas medidas, no una elegida: un destino
            # único cuando hay k es una afirmación que el índice no sostiene.
            if len(self.observadas) != self.multiplicidad:
                raise ContratoViolado(
                    "una reubicación nombra sus k caminos", declarada=self.declarada, k=self.multiplicidad
                )
            if self.observada not in self.observadas:
                raise ContratoViolado("el testigo no está entre los caminos publicados", declarada=self.declarada)
        if self.estado is EstadoDeEntrada.CONFORME and self.medido != self.h.digest:
            raise ContratoViolado("un conforme cuyo medido no es el declarado", declarada=self.declarada)
        if self.estado is EstadoDeEntrada.OPACO and self.motivo == "":
            raise ContratoViolado("una fila opaca declara el motivo", declarada=self.declarada)

    @property
    def vaciada(self) -> bool:
        """La ruta declarada quedó sin bytes: nadie la ocupó."""

        return self.estado is EstadoDeEntrada.REUBICADO and self.medido is None

    @property
    def suplantada(self) -> bool:
        """La ruta declarada la ocupan bytes que el manifiesto no declara."""

        return self.estado is EstadoDeEntrada.REUBICADO and self.medido is not None and not self.ocupante_declarado

    @property
    def canje(self) -> bool:
        """La ruta declarada la ocupa el digest declarado de **otra** fila.

        Eso no se sostiene solo: si `p1` lleva el digest de `p2`, la fila de
        `p2` tiene necesariamente su digest fuera de su ruta, así que un canje
        es mutuo por construcción y no hay que postularlo.
        """

        return self.estado is EstadoDeEntrada.REUBICADO and self.ocupante_declarado


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

        - `divergente` manda: hay bytes declarados que ya no están. Es un
          hallazgo positivo de pérdida.
        - `suplantada` le sigue: los bytes declarados existen en otra ruta, pero
          la ruta sellada la ocupan bytes que el manifiesto no declara. El
          artefacto sobrevive y la frontera fue violada: llamarlo `reubicada`
          sería un falso verde en la dirección peligrosa, y llamarlo
          `intercambiada` afirmaría un canje que no ocurrió.
        - `intercambiada` después: un artefacto reubicado cuya ruta la ocupa el
          digest declarado de otra fila. Los bytes existen y la frontera está
          rota por una permutación, no por una intrusión.
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
        if any(j.suplantada for j in self.reubicados):
            return VeredictoDeUbicacion.SUPLANTADA
        if any(j.canje for j in self.reubicados):
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
                destino = (
                    j.observada
                    if j.multiplicidad == 1
                    else "%d caminos: %s" % (j.multiplicidad, ", ".join(j.observadas))
                )
                lineas.append(
                    "%s %s -> %s%s"
                    % (
                        j.estado.value,
                        j.declarada,
                        destino,
                        " (ruta ocupada por bytes no declarados)"
                        if j.suplantada
                        else (" (ruta ocupada)" if j.canje else (" (ruta vaciada)" if j.vaciada else "")),
                    )
                )
            elif j.estado is EstadoDeEntrada.DIVERGE:
                lineas.append(
                    "%s %s (%s)"
                    % (
                        j.estado.value,
                        j.declarada,
                        j.motivo or ("ausente" if j.medido is None else "bytes alterados"),
                    )
                )
            elif j.estado is EstadoDeEntrada.OPACO:
                lineas.append("%s %s (%s)" % (j.estado.value, j.declarada, j.motivo))
        return tuple(lineas)

    def fibras(self) -> Tuple[str, ...]:
        """Las fibras declaradas con más de una ruta, y cuántas se conservaron.

        Un manifiesto puede declarar `k >= 2` rutas distintas con el mismo
        digest. Ese conjunto —la fibra de contenido → rutas, restringida a lo
        declarado— también está declarado: se conserva sólo si **cada** una de
        sus rutas sigue midiendo `h`, y publicar una sola de ellas afirmaría más
        de lo medido. Se emite una línea por fibra, con las k rutas nombradas.
        """

        declaradas_por_digest: Dict[str, List[str]] = {}
        for j in self.juicios:
            if j.estado is not EstadoDeEntrada.OPACO:
                declaradas_por_digest.setdefault(j.h.digest, []).append(j.declarada)
        lineas: List[str] = []
        for digest in sorted(declaradas_por_digest):
            rutas = sorted(declaradas_por_digest[digest])
            if len(rutas) < 2:
                continue
            conformes = sum(1 for j in self.conformes if j.h.digest == digest)
            lineas.append(
                "fibra | %s | %d declaradas | %d conformes | %s"
                % (digest, len(rutas), conformes, ", ".join(rutas))
            )
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
    rutas_declaradas = {e.ruta for e in entradas if not e.opaca}
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
        # Una ruta que existe en disco y que el universo no indexó no es una
        # reubicación: es un universo que no miró. Decir "se movió" afirmaría
        # algo que el índice no midió. El motivo distingue **por qué** el
        # universo no la tiene —un enlace o un directorio no son bytes de
        # archivo; una ruta ausente del índice es una laguna del universo— y
        # esta comprobación va antes de buscar candidatas: si la ruta no se
        # midió, el hecho de que su digest aparezca o no en otro sitio no
        # cambia que aquí no hay medición.
        if medido is None and entrada.ruta in indice.inestables:
            juicios.append(
                Juicio(
                    declarada=entrada.ruta,
                    h=entrada.h,
                    estado=EstadoDeEntrada.OPACO,
                    multiplicidad=indice.multiplicidad(entrada.h.digest),
                    motivo="la lectura del archivo no cerró estable: no hay digest que publicar",
                )
            )
            continue
        if medido is None and entrada.ruta in indice.fuera_del_universo:
            juicios.append(
                Juicio(
                    declarada=entrada.ruta,
                    h=entrada.h,
                    estado=EstadoDeEntrada.OPACO,
                    multiplicidad=indice.multiplicidad(entrada.h.digest),
                    motivo=(
                        "la ruta es un enlace o un directorio: el manifiesto mide bytes de archivo"
                        if entrada.ruta in indice.omitidas
                        else "la ruta existe en disco y el universo declarado no la indexa"
                    ),
                )
            )
            continue
        candidatas = [r for r in indice.rutas_con(entrada.h.digest) if r != entrada.ruta]
        if candidatas:
            # La ruta declarada quedó sin bytes y el digest sólo aparece en
            # rutas que el manifiesto **ya declaraba**: nadie recibió nada, así
            # que no hay reubicación. Es una fibra declarada que perdió un
            # miembro, y se acusa como pérdida, no como movimiento.
            if medido is None and all(r in rutas_declaradas for r in candidatas):
                juicios.append(
                    Juicio(
                        declarada=entrada.ruta,
                        h=entrada.h,
                        estado=EstadoDeEntrada.DIVERGE,
                        observada=None,
                        multiplicidad=len(candidatas),
                        observadas=tuple(sorted(candidatas)),
                        medido=None,
                        motivo="la ruta quedó sin bytes y el digest sólo consta en rutas ya declaradas",
                    )
                )
                continue
            juicios.append(
                Juicio(
                    declarada=entrada.ruta,
                    h=entrada.h,
                    estado=EstadoDeEntrada.REUBICADO,
                    observada=sorted(candidatas)[0],
                    observadas=tuple(sorted(candidatas)),
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


def _resuelve_dentro(raiz_resuelta: str, completa: str) -> bool:
    """¿La ruta real del archivo cae dentro de la raíz real del universo?

    Un manifiesto es una entrada de quien pide el acto, así que una fila que
    resuelve fuera de `--raiz` —por `..`, por ruta absoluta o por un enlace en
    un directorio intermedio— no se lee: el manifiesto no decide qué archivos
    del host evaluador se abren. La comparación es sobre rutas resueltas, no
    sobre texto: `raiz/enlace/archivo` puede estar fuera con la ruta intacta.
    """

    real = os.path.realpath(completa)
    try:
        return os.path.commonpath((raiz_resuelta, real)) == raiz_resuelta
    except ValueError:  # volúmenes distintos: no hay prefijo común que sostener
        return False


def adjudicar_por_rutas(
    entradas: Sequence[EntradaDeclarada], raiz: str
) -> Optional[Tuple[Adjudicacion, Indice]]:
    """La vía rápida: adjudica con las rutas declaradas y **no** recorre el universo.

    QUE MIDE. `intacta` es una afirmación sobre las rutas que el manifiesto
    declara: cada una conserva su digest en su sitio. Se decide leyendo esas
    rutas y nada más. El universo —las rutas que el manifiesto **no** declara—
    sólo hace falta para nombrar un destino cuando una ruta falla, o para
    publicar `k` observado. Recorrerlo antes de mirar las rutas declaradas cobra
    el precio del caso raro en todos los casos: medido el 2026-11-24 sobre el
    Sello A de platino-labs, 87 813 caminos para adjudicar 14 filas, de las que
    10 se sostienen en su sitio. Un verificador que cuesta dos minutos por PR no
    se adopta como compuerta; con la vía rápida cuesta lo que cuesta leer el
    manifiesto.

    CONTRATO DE DEVOLUCIÓN. Devuelve `(adjudicacion, indice)` **sólo** si el
    veredicto es `INTACTA`; en cualquier otro caso devuelve `None` y el llamador
    barre el universo. El `None` no es un error ni un veredicto: una ruta que
    aquí falta no es `DIVERGE` —sus bytes pueden estar en otra parte, y eso lo
    decide el universo— es la señal de que este índice no alcanza.

    POR QUÉ LA DEVOLUCIÓN PARCIAL NO PUEDE MENTIR. Sin universo no hay
    candidatas, así que `adjudicar` no puede emitir `REUBICADO`; una fila
    opaca, ausente, inestable o fuera de la raíz deja el veredicto por debajo de
    `intacta`. La única salida que cruza esta frontera es la que exige que
    **todas** las filas declaradas se midieron estables en su ruta con su
    digest, y ésa es exactamente la que el barrido no puede mejorar.
    """

    if not entradas:
        return None
    raiz_resuelta = os.path.realpath(raiz)
    por_ruta: Dict[str, str] = {}
    omitidas: List[str] = []
    inestables: List[str] = []
    for entrada in entradas:
        if entrada.opaca:
            # Una fila redactada no se puede medir aquí y el motivo es asunto
            # del manifiesto, no del árbol: que lo adjudique el acto completo.
            return None
        completa = os.path.join(raiz, *entrada.ruta.split("/"))
        if os.path.islink(completa) or not os.path.isfile(completa):
            omitidas.append(entrada.ruta)
            continue
        if not _resuelve_dentro(raiz_resuelta, completa):
            omitidas.append(entrada.ruta)
            continue
        digest = _digest_de_archivo(completa)
        if digest is None:
            inestables.append(entrada.ruta)
            continue
        por_ruta[entrada.ruta] = digest
    indice = Indice.desde_mapa(por_ruta, omitidas, inestables)
    adjudicacion = adjudicar(entradas, indice)
    if adjudicacion.veredicto is not VeredictoDeUbicacion.INTACTA:
        return None
    return adjudicacion, indice
