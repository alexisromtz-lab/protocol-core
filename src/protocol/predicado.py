"""protocol.predicado — Anillo 0: el enunciado verificable de una página.

Un `Predicado` ata siete campos: qué se afirma (`afirmacion`), con qué entradas
(`entradas`), con qué código (`codigo`), en qué entorno declarado (`entorno`),
qué salida (`salida`), qué veredicto **reclama** quien produce (`veredicto`), y
el eslabón anterior de la cadena (`h_prev`). Su `digest` es el nombre del acto;
la cadena de digests es el orden.

Tres fronteras se declaran aquí porque cruzarlas en silencio es la mentira más
barata del formato:

1. `veredicto` es **reclamado**, no adjudicado. Quien produce escribe lo que
   cree; la `Contrafirma` de un tercero es lo que se vende. Si ambos viven en el
   mismo objeto, la segunda sólo puede ser la primera repetida.
2. Una cadena de digests **sin ancla** no prueba autoría: quien reescribe todos
   los eslabones recalcula la cadena entera y cuadra. `verificar_cadena` mide
   coherencia interna y orden, no autenticidad. El ancla —commit, DOI,
   contrafirma fechada— es lo único que detecta una reescritura completa. Este
   límite se declara en vez de esconderse: es la razón por la que la
   `Contrafirma` existe.
3. El canon rechaza flotantes y normaliza el texto libre a NFC. Dos plataformas
   no imprimen el mismo flotante igual, y APFS entrega NFD donde Linux entrega
   NFC: un digest que dependa de eso mide la máquina, no el acto. Las rutas no
   se tocan porque `RutaRelativa` hereda el alfabeto ASCII de §2.1, que ya es
   NFC-estable; se declara redundante y se conserva por si el alfabeto se
   ensancha.

Lectura declarada. `TIPO_DE_PREDICADO` nombra la sección `#predicado-v1` de
`PREDICADO.md`, escrito y presente en este repositorio. `SPEC.md` **no** se toca:
está sellado con fecha cierta (sello A, `ad67ece0…`) y una sección nueva lo
invalidaría; el documento del predicado se versiona con git y su historia es su
sello. Un tercero que reimplemente la verificación con `PREDICADO.md` y no lea
este módulo debe obtener los mismos bytes; si discrepan, manda el documento.

Lo que este módulo **no** hace: no abre archivos, no mide el sistema de archivos
y no adjudica. `metrics` mide, `audit.verify` verifica el objeto contra el
recibo, y aquí sólo se compone y se encadena el enunciado. Cero rutas
absolutas, cero relojes, cero criptografía: no se simula una firma que no se
verifica (SPEC §0.4).
"""

from __future__ import annotations

import hashlib as _hashlib
import json as _json
import unicodedata as _unicodedata
from dataclasses import dataclass
from enum import Enum
from typing import Final, Literal, Optional, Tuple, Union

from .types import (
    ALGORITMO,
    ContratoViolado,
    Divergencia,
    EntradaManifiesto,
    Hash,
    RutaRelativa,
)

__all__ = [
    "Contrafirma",
    "Entorno",
    "Eslabon",
    "Predicado",
    "ResultadoCadena",
    "TIPO_DE_ESTATUTO",
    "TIPO_DE_PREDICADO",
    "VeredictoAdjudicado",
    "VeredictoReclamado",
    "canonizar",
    "contrafirmar",
    "desde_cuerpo",
    "desde_in_toto",
    "verificar_cadena",
    "verificar_contrafirma",
]

TIPO_DE_ESTATUTO: Final[str] = "https://in-toto.io/Statement/v1"
TIPO_DE_PREDICADO: Final[str] = (
    "https://github.com/alexisromtz-lab/protocol-core/blob/main/PREDICADO.md#predicado-v1"
)


# ---------------------------------------------------------------------------
# La forma canónica — la única función que hay que reimplementar para verificar
# ---------------------------------------------------------------------------


def _nfc(texto: str) -> str:
    return _unicodedata.normalize("NFC", texto)


def _normalizar(objeto: object, ruta: str = "$") -> object:
    """Devuelve el objeto con sus textuales en NFC, o falla si no es canónico.

    Es un verificador, no un reparador: un flotante no se redondea, se rechaza.
    """

    if isinstance(objeto, float):
        raise ContratoViolado(
            "el canon rechaza flotantes: su representación no es portable y un "
            "digest que dependa de ella mide la máquina, no el acto",
            ruta=ruta,
            valor=repr(objeto),
        )
    if isinstance(objeto, str):
        return _nfc(objeto)
    if isinstance(objeto, bool) or objeto is None or isinstance(objeto, int):
        return objeto
    if isinstance(objeto, dict):
        limpio = {}
        for clave, valor in objeto.items():
            if not isinstance(clave, str):
                raise ContratoViolado("las claves del canon son textuales", ruta=ruta)
            limpio[_nfc(clave)] = _normalizar(valor, ruta + "." + clave)
        return limpio
    if isinstance(objeto, (list, tuple)):
        return [_normalizar(valor, "%s[%d]" % (ruta, indice)) for indice, valor in enumerate(objeto)]
    raise ContratoViolado(
        "tipo no admisible en el canon: sólo texto, entero, booleano, nulo, "
        "lista o diccionario de ellos",
        ruta=ruta,
        tipo=type(objeto).__name__,
    )


def canonizar(objeto: object) -> bytes:
    """La forma canónica: NFC, llaves ordenadas, sin espacios, UTF-8.

    Cualquier tercero que reproduzca estas cuatro decisiones obtiene el mismo
    digest; cualquiera que omita una obtiene otro y lo verá como divergencia.
    """

    bruto = _json.dumps(
        _normalizar(objeto),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )
    return bruto.encode("utf-8")


# ---------------------------------------------------------------------------
# §2.3.8 entorno declarado — la laguna se escribe, no se omite
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Entorno:
    """El entorno **declarado**: plataforma, runtime y lo que no se midió.

    `no_medido` no es adorno: es el campo que impide que un verde por omisión
    pase por verde. Un entorno sin lagunas declaradas afirma que no queda nada
    sin medir, y por eso se escribe con una tupla vacía explícita en vez de
    omitiendo el campo. Un `None` aquí sería una laguna no declarada.
    """

    plataforma: str
    runtime: str
    no_medido: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for campo in ("plataforma", "runtime"):
            valor = getattr(self, campo)
            if not isinstance(valor, str) or valor.strip() == "":
                raise ContratoViolado(
                    "el entorno se declara o no hay enunciado: campo vacío",
                    campo=campo,
                    valor=valor,
                )
            object.__setattr__(self, campo, _nfc(valor))
        if not isinstance(self.no_medido, tuple):
            raise ContratoViolado(
                "`no_medido` es tupla de textuales: la ausencia de lagunas se "
                "declara con `()` y nunca omitiendo el campo",
                tipo=type(self.no_medido).__name__,
            )
        for indice, laguna in enumerate(self.no_medido):
            if not isinstance(laguna, str) or laguna.strip() == "":
                raise ContratoViolado("laguna declarada vacía", indice=indice)
        object.__setattr__(self, "no_medido", tuple(_nfc(x) for x in self.no_medido))


class VeredictoReclamado(str, Enum):
    """Lo que **afirma** quien produce. No es una adjudicación."""

    CONFORME = "conforme"
    NO_CONFORME = "no_conforme"
    NO_MEDIDO = "no_medido"


class VeredictoAdjudicado(str, Enum):
    """Lo que **responde** un tercero que re-ejecutó. Es el objeto vendible."""

    CONFIRMA = "confirma"
    REFUTA = "refuta"
    NO_MEDIDO = "no_medido"


# ---------------------------------------------------------------------------
# §2.5.3 predicado — siete campos, una página
# ---------------------------------------------------------------------------


def _entrada_a_dict(entrada: EntradaManifiesto) -> dict:
    return {"ruta": entrada.ruta.texto, ALGORITMO: entrada.h.digest}


def _exigir_conjunto(entradas: object, campo: str) -> None:
    if not isinstance(entradas, tuple):
        raise ContratoViolado("el conjunto de referencias es tupla", campo=campo)
    for entrada in entradas:
        if not isinstance(entrada, EntradaManifiesto):
            raise ContratoViolado("referencia mal tipada", campo=campo, tipo=type(entrada).__name__)
        if not isinstance(entrada.ruta, RutaRelativa) or not isinstance(entrada.h, Hash):
            raise ContratoViolado("la referencia exige ruta relativa y hash", campo=campo)
        if entrada.h.truncado:
            raise ContratoViolado(
                "una identidad truncada no es identidad: el predicado exige "
                "anchura completa, la única que un tercero puede reproducir",
                ruta=entrada.ruta.texto,
                anchura=entrada.h.anchura,
            )
    claves = [entrada.ruta.clave_bytes for entrada in entradas]
    if any(claves[i] > claves[i + 1] for i in range(len(claves) - 1)):
        raise ContratoViolado("las rutas no están en orden byte a byte (§3.d.2)", campo=campo)
    if len(set(claves)) != len(claves):
        raise ContratoViolado("ruta repetida en el conjunto", campo=campo)


@dataclass(frozen=True)
class Predicado:
    """§2.5.3. `P = (afirmacion, entradas, codigo, entorno, salida, veredicto, h_prev)`.

    `h_prev` es el `digest` del eslabón anterior, o `None` en el origen. Entra
    **dentro** de la forma canónica: por eso el digest de un eslabón cubre el
    enlace, y cambiar un eslabón cambia todos los siguientes.

    `salida` es una referencia con nombre y no un hash suelto: in-toto exige un
    `subject` nombrado, y un hash sin nombre no se puede publicar.
    """

    afirmacion: str
    entradas: Tuple[EntradaManifiesto, ...]
    codigo: Tuple[EntradaManifiesto, ...]
    entorno: Entorno
    salida: EntradaManifiesto
    veredicto: VeredictoReclamado
    h_prev: Optional[Hash] = None

    def __post_init__(self) -> None:
        if not isinstance(self.afirmacion, str) or self.afirmacion.strip() == "":
            raise ContratoViolado("la afirmación se escribe o no hay enunciado")
        object.__setattr__(self, "afirmacion", _nfc(self.afirmacion))
        _exigir_conjunto(self.entradas, "entradas")
        _exigir_conjunto(self.codigo, "codigo")
        if not isinstance(self.entorno, Entorno):
            raise ContratoViolado("el entorno es un `Entorno` declarado, no un diccionario libre")
        if not isinstance(self.salida, EntradaManifiesto):
            raise ContratoViolado("la salida es una referencia nombrada, no un hash suelto")
        if self.salida.h.truncado:
            raise ContratoViolado("la salida exige anchura completa", ruta=self.salida.ruta.texto)
        if not isinstance(self.veredicto, VeredictoReclamado):
            raise ContratoViolado(
                "el veredicto del predicado es RECLAMADO: la adjudicación vive "
                "en la `Contrafirma` de un tercero",
                tipo=type(self.veredicto).__name__,
            )
        if self.h_prev is not None and not isinstance(self.h_prev, Hash):
            raise ContratoViolado("`h_prev` es `Hash` o ⊥", h_prev=type(self.h_prev).__name__)

    def cuerpo(self) -> dict:
        """Los siete campos como estructura canónica. La página es esto."""

        return {
            "afirmacion": self.afirmacion,
            "entradas": [_entrada_a_dict(e) for e in self.entradas],
            "codigo": [_entrada_a_dict(e) for e in self.codigo],
            "entorno": {
                "plataforma": self.entorno.plataforma,
                "runtime": self.entorno.runtime,
                "no_medido": list(self.entorno.no_medido),
            },
            "salida": _entrada_a_dict(self.salida),
            "veredicto": self.veredicto.value,
            "h_prev": None if self.h_prev is None else self.h_prev.digest,
        }

    def digest(self) -> Hash:
        """El nombre del acto: SHA-256 de la forma canónica del cuerpo."""

        return Hash(algoritmo=ALGORITMO, digest=_hashlib.sha256(canonizar(self.cuerpo())).hexdigest())

    def pagina(self) -> str:
        """La página: el cuerpo en JSON legible, para revisar a ojo."""

        return _json.dumps(self.cuerpo(), indent=2, ensure_ascii=False)

    def a_in_toto(self) -> dict:
        """Proyección a `Statement v1`. La salida viaja en `subject`, una sola vez.

        Es una **vista**, no el objeto: el objeto canónico es `cuerpo()`, con los
        siete campos. `desde_in_toto` la invierte, y esa ida y vuelta es lo que
        prueba que la proyección no pierde la afirmación.
        """

        return {
            "_type": TIPO_DE_ESTATUTO,
            "subject": [
                {
                    "name": self.salida.ruta.texto,
                    "digest": {ALGORITMO: self.salida.h.digest},
                }
            ],
            "predicateType": TIPO_DE_PREDICADO,
            "predicate": {
                "afirmacion": self.afirmacion,
                "entradas": [_entrada_a_dict(e) for e in self.entradas],
                "codigo": [_entrada_a_dict(e) for e in self.codigo],
                "entorno": {
                    "plataforma": self.entorno.plataforma,
                    "runtime": self.entorno.runtime,
                    "no_medido": list(self.entorno.no_medido),
                },
                "veredicto": self.veredicto.value,
                "h_prev": None if self.h_prev is None else self.h_prev.digest,
            },
        }


def _entrada_desde_dict(bruto: object, campo: str) -> EntradaManifiesto:
    """Acepta la forma interna `{ruta, sha256}` y la de `subject` `{name, digest}`."""

    if not isinstance(bruto, dict):
        raise ContratoViolado("la referencia proyectada no es diccionario", campo=campo)
    ruta = bruto.get("ruta", bruto.get("name"))
    digest = bruto.get(ALGORITMO)
    if digest is None and isinstance(bruto.get("digest"), dict):
        digest = bruto["digest"].get(ALGORITMO)
    if not isinstance(ruta, str) or not isinstance(digest, str):
        raise ContratoViolado("la referencia proyectada exige ruta y digest", campo=campo)
    return EntradaManifiesto(RutaRelativa(ruta), Hash(algoritmo=ALGORITMO, digest=digest))


def _entorno_desde_dict(bruto: object) -> Entorno:
    """El entorno vuelve de la página con sus tres llaves, `no_medido` incluida.

    `no_medido` no se rellena por omisión: un entorno que llega sin la llave
    afirmaría que no queda nada sin medir sin haberlo escrito.
    """

    if not isinstance(bruto, dict):
        raise ContratoViolado("el entorno de la página no es diccionario", tipo=type(bruto).__name__)
    no_medido = bruto.get("no_medido")
    if not isinstance(no_medido, list):
        raise ContratoViolado(
            "`no_medido` viaja como lista, presente aun vacía: omitirlo declara "
            "que no queda nada sin medir",
            tipo=type(no_medido).__name__,
        )
    return Entorno(
        plataforma=bruto.get("plataforma"),
        runtime=bruto.get("runtime"),
        no_medido=tuple(no_medido),
    )


def _veredicto_reclamado(bruto: object) -> VeredictoReclamado:
    try:
        return VeredictoReclamado(bruto)
    except ValueError as exc:
        raise ContratoViolado(
            "veredicto reclamado no declarado", valor=bruto
        ) from exc


def desde_in_toto(estatuto: object) -> Predicado:
    """Invierte `a_in_toto`. Si no puede, falla: no adivina."""

    if not isinstance(estatuto, dict):
        raise ContratoViolado("el estatuto es un diccionario")
    if estatuto.get("_type") != TIPO_DE_ESTATUTO:
        raise ContratoViolado("estatuto de tipo no declarado", tipo=estatuto.get("_type"))
    if estatuto.get("predicateType") != TIPO_DE_PREDICADO:
        raise ContratoViolado("predicado de tipo distinto: no se traduce", tipo=estatuto.get("predicateType"))
    sujetos = estatuto.get("subject")
    if not isinstance(sujetos, list) or len(sujetos) != 1:
        raise ContratoViolado(
            "el predicado ata UNA salida: varias salidas son varios enunciados",
            sujetos=len(sujetos) if isinstance(sujetos, list) else sujetos,
        )
    cuerpo = estatuto.get("predicate")
    if not isinstance(cuerpo, dict):
        raise ContratoViolado("el predicado proyectado no es diccionario")
    entorno = _entorno_desde_dict(cuerpo.get("entorno"))
    entradas = cuerpo.get("entradas")
    codigo = cuerpo.get("codigo")
    if not isinstance(entradas, list) or not isinstance(codigo, list):
        raise ContratoViolado("los conjuntos proyectados son listas, presentes aun vacías")
    h_prev = cuerpo.get("h_prev")
    return Predicado(
        afirmacion=cuerpo.get("afirmacion"),
        entradas=tuple(_entrada_desde_dict(e, "entradas") for e in entradas),
        codigo=tuple(_entrada_desde_dict(e, "codigo") for e in codigo),
        entorno=entorno,
        salida=_entrada_desde_dict(sujetos[0], "subject"),
        veredicto=_veredicto_reclamado(cuerpo.get("veredicto")),
        h_prev=None if h_prev is None else Hash(algoritmo=ALGORITMO, digest=h_prev),
    )


_CLAVES_DEL_CUERPO: Final[Tuple[str, ...]] = (
    "afirmacion",
    "codigo",
    "entorno",
    "entradas",
    "h_prev",
    "salida",
    "veredicto",
)


def desde_cuerpo(objeto: object) -> Predicado:
    """Invierte `cuerpo()` y `pagina()`: el tercero levanta el acto desde la página.

    Acepta el cuerpo como diccionario o como el texto/bytes JSON que se publicó,
    porque quien verifica tiene un archivo, no un objeto vivo. Exige **las siete
    llaves y ninguna otra**: una de menos es una laguna no declarada —`h_prev`
    ausente no es el origen, es un eslabón sin enlace— y una de más es un acto
    distinto que se leería con el vocabulario viejo.

    Sin esta función el predicado es verificable sólo por quien lo emitió, y una
    contrafirma sin verificador independiente no es un objeto vendible.
    """

    if isinstance(objeto, (bytes, bytearray)):
        try:
            objeto = bytes(objeto).decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ContratoViolado("la página no es UTF-8", causa=str(exc)) from exc
    if isinstance(objeto, str):
        try:
            objeto = _json.loads(objeto)
        except ValueError as exc:
            raise ContratoViolado("la página no es JSON", causa=str(exc)) from exc
    if not isinstance(objeto, dict):
        raise ContratoViolado("la página es un diccionario", tipo=type(objeto).__name__)
    presentes = tuple(sorted(objeto))
    if presentes != _CLAVES_DEL_CUERPO:
        raise ContratoViolado(
            "la página lleva las siete llaves del predicado y ninguna otra",
            faltan=[clave for clave in _CLAVES_DEL_CUERPO if clave not in objeto],
            sobran=[clave for clave in presentes if clave not in _CLAVES_DEL_CUERPO],
        )
    entradas = objeto["entradas"]
    codigo = objeto["codigo"]
    if not isinstance(entradas, list) or not isinstance(codigo, list):
        raise ContratoViolado("los conjuntos de la página son listas, presentes aun vacías")
    h_prev = objeto["h_prev"]
    if h_prev is not None and not isinstance(h_prev, str):
        raise ContratoViolado(
            "`h_prev` es el digest del eslabón anterior o nulo en el origen",
            tipo=type(h_prev).__name__,
        )
    return Predicado(
        afirmacion=objeto["afirmacion"],
        entradas=tuple(_entrada_desde_dict(entrada, "entradas") for entrada in entradas),
        codigo=tuple(_entrada_desde_dict(entrada, "codigo") for entrada in codigo),
        entorno=_entorno_desde_dict(objeto["entorno"]),
        salida=_entrada_desde_dict(objeto["salida"], "salida"),
        veredicto=_veredicto_reclamado(objeto["veredicto"]),
        h_prev=None if h_prev is None else Hash(algoritmo=ALGORITMO, digest=h_prev),
    )


# ---------------------------------------------------------------------------
# La cadena — coherencia interna, declarada como tal
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Eslabon:
    """Dónde se rompe la coherencia y por qué."""

    indice: int
    motivo: str

    def __post_init__(self) -> None:
        if not isinstance(self.indice, int) or isinstance(self.indice, bool) or self.indice < 0:
            raise ContratoViolado("el eslabón se numera con un entero no negativo")
        if not isinstance(self.motivo, str) or self.motivo == "":
            raise ContratoViolado("el eslabón roto declara su motivo")


ResultadoCadena = Union[Literal[True], Eslabon]


def verificar_cadena(cadena: object, exigir_origen: bool = True) -> ResultadoCadena:
    """¿Cada eslabón cita el digest del anterior?

    Mide **coherencia interna**: que nadie editó un eslabón aislado ni cambió el
    orden. No mide autoría: una cadena reescrita de punta a punta, recalculando
    cada digest, devuelve `True` aquí. Ese resultado negativo es el límite
    declarado del Anillo 0 y la razón de la `Contrafirma`.

    `exigir_origen=False` mide un fragmento: un tramo de cadena cuya cabeza no
    es el origen no es una cadena rota, es un universo distinto.
    """

    if not isinstance(cadena, tuple):
        raise ContratoViolado("la cadena es una tupla de predicados, en orden")
    if len(cadena) == 0:
        raise ContratoViolado("una cadena vacía no tiene eslabones que medir")
    for indice, eslabon in enumerate(cadena):
        if not isinstance(eslabon, Predicado):
            raise ContratoViolado("eslabón mal tipado", indice=indice, tipo=type(eslabon).__name__)
    if exigir_origen and cadena[0].h_prev is not None:
        return Eslabon(0, "el primer eslabón no es un origen: declara `h_prev`")
    for indice in range(1, len(cadena)):
        esperado = cadena[indice - 1].digest()
        if cadena[indice].h_prev != esperado:
            return Eslabon(
                indice,
                "`h_prev` no es el digest del eslabón anterior: %s ≠ %s"
                % (
                    "⊥" if cadena[indice].h_prev is None else cadena[indice].h_prev.digest,
                    esperado.digest,
                ),
            )
    return True


# ---------------------------------------------------------------------------
# La contrafirma — el objeto vendible, y lo que se declara que NO es
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Contrafirma:
    """El acto de un tercero sobre un predicado. **No** es una firma criptográfica.

    Este módulo no trae criptografía y no la simula: `ancla` nombra dónde vive la
    prueba —un DOI, un commit publicado, un log de transparencia— o es ⊥ y
    entonces el enunciado no tiene ancla. Una contrafirma sin ancla vale para
    una conversación, no para un auditor.
    """

    verificador: str
    digest_del_predicado: Hash
    veredicto: VeredictoAdjudicado
    ancla: Optional[str] = None

    def __post_init__(self) -> None:
        if not isinstance(self.verificador, str) or self.verificador.strip() == "":
            raise ContratoViolado("la contrafirma nombra a quien la emite")
        object.__setattr__(self, "verificador", _nfc(self.verificador))
        if not isinstance(self.digest_del_predicado, Hash):
            raise ContratoViolado("la contrafirma cubre el digest de un predicado")
        if not isinstance(self.veredicto, VeredictoAdjudicado):
            raise ContratoViolado(
                "la contrafirma adjudica: `VeredictoReclamado` no se reutiliza aquí",
                tipo=type(self.veredicto).__name__,
            )
        if self.ancla is not None:
            if not isinstance(self.ancla, str) or self.ancla.strip() == "":
                raise ContratoViolado("el ancla es un texto no vacío o ⊥")
            object.__setattr__(self, "ancla", _nfc(self.ancla))

    def cuerpo(self) -> dict:
        return {
            "verificador": self.verificador,
            "digest_del_predicado": self.digest_del_predicado.digest,
            "veredicto": self.veredicto.value,
            "ancla": self.ancla,
        }


def contrafirmar(
    predicado: Predicado,
    verificador: str,
    veredicto: VeredictoAdjudicado,
    ancla: Optional[str] = None,
) -> Contrafirma:
    """Un tercero responde sobre el acto que el predicado nombra."""

    if not isinstance(predicado, Predicado):
        raise ContratoViolado("se contrafirma un Predicado")
    return Contrafirma(
        verificador=verificador,
        digest_del_predicado=predicado.digest(),
        veredicto=veredicto,
        ancla=ancla,
    )


def verificar_contrafirma(predicado: Predicado, contrafirma: Contrafirma) -> Union[Literal[True], Divergencia]:
    """¿La contrafirma cubre **este** predicado y no otro?

    No mide autoría ni validez criptográfica: mide el vínculo entre el acto y la
    respuesta, que es lo que un formato puede exigir sin generar confianza falsa.
    """

    if not isinstance(predicado, Predicado) or not isinstance(contrafirma, Contrafirma):
        raise ContratoViolado("la verificación exige predicado y contrafirma tipados")
    medido = predicado.digest()
    if contrafirma.digest_del_predicado != medido:
        return Divergencia(
            campo="digest_del_predicado",
            esperado=contrafirma.digest_del_predicado.digest,
            medido=medido.digest,
        )
    return True
