"""composicion.py — anillo 4: dos recibos verificados hacen un recibo transitivo.

LA PREGUNTA. Un lote sale de A, pasa por un nodo B —conciliacion, respaldo,
empaquetado— y llega a C. Hoy un auditor que quiere hablar de A -> C tiene que
volver a hashear contra A conservando todos los intermedios. La pregunta es si
dos recibos que **ya** se verificaron, `R_ab` y `R_bc`, bastan para emitir
`R_ac` sin volver a leer los bytes.

LA RESPUESTA CORTA. Si y solo si la frontera cierra: lo que `R_ab` dejo en B es
exactamente lo que `R_bc` leyo en B. Si no cierra, la composicion no es un
recibo peor: es un recibo sobre dos sujetos distintos, y el unico veredicto
honesto es `frontera_rota`.

TRES DECISIONES QUE EL ALGEBRA NO TRAE Y AQUI SE DECLARAN.

1. **El orden de degradacion no se inventa: se importa.** `UBICACION.md` §4 ya
   publica el orden de sus seis veredictos —divergente por encima de suplantada,
   suplantada por encima de intercambiada, intercambiada por encima de no_medida,
   y reubicada por encima de intacta—. Componer es tomar el maximo de ese orden,
   de modo que la cadena hereda el peor tramo y lo **nombra**. Un septimo valor,
   `frontera_rota`, entra arriba porque no degrada un tramo: invalida todos los
   siguientes.

2. **La identidad se absorbe, no se arrastra.** Componer con un tramo
   `B -> B` intacto y sin filas nuevas tiene que devolver el recibo de entrada
   **igual**, no un recibo con un tramo de mas. Un monoide cuyo elemento neutro
   deja basura no es un monoide: es una lista.

3. **El recibo lleva sus paginas.** Un tramo declara las filas que leyo y las que
   dejo; los digests son propiedades **recalculadas** de esas filas, nunca
   entradas. Asi un recibo que miente sobre su propia pagina no se puede ni
   construir, y un tercero puede rehacer la cuenta sin confiar en el productor.

LO QUE ESTE MODULO NO HACE (lista cerrada). No lee disco: compone lo que ya se
midio. No autentica quien produjo los recibos —eso es la contrafirma, otro
acto—. Transporta el `sha256_regla` que un tramo declare, pero no lo coteja:
leer el artefacto de la regla es el acto del tercero, y por eso vive en el
verificador externo y no aqui. No decide si B hizo bien su trabajo: comprueba
que las paginas encadenadas sean las mismas y, si el recibo es `/2`, a que regla
se ato cada salto; no que la transformacion fuera la correcta. No propaga una
ausencia probada en A como ausencia en C: la conserva con la pagina que la
prueba y la publica como `historica` si esa pagina ya no es la final.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Sequence, Tuple

from .ausencia import Testigo, VeredictoDeAusencia
from .types import ALGORITMO, ContratoViolado, Hash
from .ubicacion import EntradaDeclarada

#: La forma canonica de una pagina. Es la misma que `ausencia.FORMATO_CANONICO` y
#: por eso el digest compone: dos formulas distintas sobre el mismo contenido dan
#: dos digests y la frontera no cerraria nunca. `test_composicion` importa la
#: constante ajena en vez de copiarla, y el verificador externo la reescribe a
#: proposito para que una deriva se note.
FORMATO_CANONICO = "%s  %s\n"


class VeredictoDeComposicion(str, Enum):
    """Los seis del acto de ubicacion, mas el unico que solo existe al componer.

    Los seis conservan **el mismo valor de cadena** que `VeredictoDeUbicacion`
    para que el JSON de un recibo se lea sin traduccion. `frontera_rota` no
    traduce nada: no hay acto de ubicacion que pueda emitirlo, porque un acto de
    ubicacion mira un arbol y esto mira el empalme de dos recibos.
    """

    INTACTA = "intacta"
    REUBICADA = "reubicada"
    NO_MEDIDA = "no_medida"
    INTERCAMBIADA = "intercambiada"
    SUPLANTADA = "suplantada"
    DIVERGENTE = "divergente"
    FRONTERA_ROTA = "frontera_rota"


#: De menos a mas grave. Las seis primeras posiciones son el orden publicado en
#: `UBICACION.md` §4, leido de abajo arriba; la septima se anade arriba con su
#: razon: una frontera rota no degrada un tramo, invalida todos los que siguen, y
#: por eso tiene que ser el valor que se nombre cuando coincida con otro.
RANGO: Tuple[VeredictoDeComposicion, ...] = (
    VeredictoDeComposicion.INTACTA,
    VeredictoDeComposicion.REUBICADA,
    VeredictoDeComposicion.NO_MEDIDA,
    VeredictoDeComposicion.INTERCAMBIADA,
    VeredictoDeComposicion.SUPLANTADA,
    VeredictoDeComposicion.DIVERGENTE,
    VeredictoDeComposicion.FRONTERA_ROTA,
)

#: Los dos veredictos bajo los cuales un acto de ubicacion **certifica** (RC 0 en
#: `verificar_sello`). La composicion no reutiliza el RC del acto: publica el
#: veredicto y cada consumidor decide, pero deja escrito quien sostiene la
#: afirmacion, para que un tercero no tenga que recordarlo.
SOSTIENEN = (VeredictoDeComposicion.INTACTA, VeredictoDeComposicion.REUBICADA)


def rango(veredicto: VeredictoDeComposicion) -> int:
    """Posicion en el orden declarado. Fuera de el no hay orden que consultar."""

    try:
        return RANGO.index(veredicto)
    except ValueError:  # pragma: no cover - el enum cierra el conjunto
        raise ContratoViolado("veredicto fuera del orden declarado", valor=veredicto) from None


def digest_de_pagina(filas: Sequence[EntradaDeclarada]) -> str:
    """El digest de una secuencia **ya canonica**. No ordena: comprueba.

    Ordenar aqui escondería el defecto que el anillo 3 publica con
    `desordenada`: un exportador que entrega las filas en otro orden tiene que
    decirlo, y una funcion que reordena en silencio le quita la ocasion.
    """

    for previa, actual in zip(filas, filas[1:]):
        if not previa.ruta.encode("utf-8") < actual.ruta.encode("utf-8"):
            raise ContratoViolado(
                "la pagina no esta en orden canonico", previa=previa.ruta, actual=actual.ruta
            )
    texto = "".join(FORMATO_CANONICO % (f.h.digest, f.ruta) for f in filas)
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def _opacas(filas: Sequence[EntradaDeclarada]) -> Tuple[str, ...]:
    return tuple(f.ruta for f in filas if f.opaca)


@dataclass(frozen=True)
class Tramo:
    """Un salto ya medido: el veredicto de un acto de ubicacion sobre `A -> B`.

    `pagina_origen` y `pagina_destino` son las filas tal como el acto las leyo y
    las dejo. Los digests **no** son campos: se recalculan en cada acceso, de
    modo que no existe un estado en el que el digest declarado y las filas
    discrepen. Un recibo que se equivoca se equivoca en sus filas, que es lo
    unico que un tercero puede volver a contar.
    """

    origen: str
    destino: str
    veredicto: VeredictoDeComposicion
    pagina_origen: Tuple[EntradaDeclarada, ...] = ()
    pagina_destino: Tuple[EntradaDeclarada, ...] = ()
    testigos: Tuple[Testigo, ...] = ()
    #: El `sha256` del artefacto que declara **la regla** del salto —la
    #: transformacion acordada fuera del testigo de `B`—, o `""` si el tramo no
    #: ata su transformacion a nada. No es el digest de la pagina: ese se
    #: recalcula de las filas. Este es una **entrada**, la unica de este objeto,
    #: y por eso viaja declarada y el tercero la coteja contra el artefacto que
    #: le entreguen. Sin ella la cadena prueba continuidad, no autoria.
    sha256_regla: str = ""

    def __post_init__(self) -> None:
        if self.sha256_regla and (
            len(self.sha256_regla) != 64
            or any(c not in "0123456789abcdef" for c in self.sha256_regla)
        ):
            raise ContratoViolado("la regla declarada no es un sha256", valor=self.sha256_regla)
        for etiqueta in (self.origen, self.destino):
            if not isinstance(etiqueta, str) or etiqueta.strip() == "":
                raise ContratoViolado("el tramo no declara nodo", valor=etiqueta)
        if self.origen == self.destino and self.veredicto is VeredictoDeComposicion.INTACTA:
            if self.pagina_origen or self.pagina_destino:
                if self.digest_origen != self.digest_destino:
                    raise ContratoViolado(
                        "un tramo de identidad no puede cambiar la pagina",
                        origen=self.digest_origen,
                        destino=self.digest_destino,
                    )
        if self.veredicto is VeredictoDeComposicion.NO_MEDIDA:
            return
        if not self.pagina_destino:
            raise ContratoViolado(
                "un tramo que certifica no puede dejar una pagina vacia", nodo=self.destino
            )

    @property
    def digest_origen(self) -> str:
        return digest_de_pagina(self.pagina_origen) if self.pagina_origen else ""

    @property
    def digest_destino(self) -> str:
        return digest_de_pagina(self.pagina_destino) if self.pagina_destino else ""

    @property
    def opacas(self) -> Tuple[str, ...]:
        return tuple(dict.fromkeys(_opacas(self.pagina_origen) + _opacas(self.pagina_destino)))

    @property
    def es_identidad(self) -> bool:
        """El neutro del monoide, y la razon por la que `componer` lo absorbe.

        Exige las tres cosas: mismo nodo, pagina sin cambio y ningun testigo
        nuevo. Un `B -> B` con un tramo `no_medida` no es identidad, es un salto
        que no mira, y tragarselo seria un falso verde con forma de neutro.
        """

        return (
            self.origen == self.destino
            and self.veredicto is VeredictoDeComposicion.INTACTA
            and self.digest_origen == self.digest_destino
            and not self.opacas
            and not self.testigos
        )


@dataclass(frozen=True)
class Recibo:
    """Uno o mas tramos encadenados, con su frontera y sus ausencias.

    `frontera` es `None` cuando el empalme cerro, y el par `(esperado, leido)`
    cuando no: no hay tramo que nombrar porque el defecto esta entre dos, y
    sintetizar un salto que nadie midio seria inventar el sujeto.

    `frontera_vacua` es el tercer caso, el que un algebra de dos valores
    confunde con el primero: a uno de los lados le falta la pagina, de modo que
    el empalme **no se pudo comprobar**. No es «cerro» ni «se rompio»; es
    `no_medida`, y por eso un recibo con esta bandera no sostiene nada aunque
    todos sus tramos se sostengan por separado.
    """

    tramos: Tuple[Tramo, ...]
    frontera: Optional[Tuple[str, str]] = None
    frontera_vacua: bool = False

    def __post_init__(self) -> None:
        if not self.tramos:
            raise ContratoViolado("un recibo sin tramos no certifica nada")
        for previo, actual in zip(self.tramos, self.tramos[1:]):
            if previo.destino != actual.origen:
                raise ContratoViolado(
                    "los tramos del recibo no se tocan", previo=previo.destino, actual=actual.origen
                )

    @property
    def origen(self) -> str:
        return self.tramos[0].origen

    @property
    def destino(self) -> str:
        return self.tramos[-1].destino

    @property
    def digest_origen(self) -> str:
        return self.tramos[0].digest_origen

    @property
    def digest_destino(self) -> str:
        return self.tramos[-1].digest_destino

    @property
    def veredicto(self) -> VeredictoDeComposicion:
        if self.frontera is not None:
            return VeredictoDeComposicion.FRONTERA_ROTA
        peor = max((t.veredicto for t in self.tramos), key=rango)
        if self.frontera_vacua and rango(peor) < rango(VeredictoDeComposicion.NO_MEDIDA):
            return VeredictoDeComposicion.NO_MEDIDA
        return peor

    @property
    def sostiene(self) -> bool:
        return self.veredicto in SOSTIENEN

    @property
    def tramo_degradado(self) -> Optional[Tramo]:
        """El primer tramo que alcanza el peor rango. Nombra uno, no el conjunto.

        Cuando dos tramos empatan en el peor estado se nombra el primero: el
        recibo no elige cual importa mas, elige cual ocurrio antes, que es un
        hecho del camino y no una preferencia del lector.
        """

        if self.frontera is not None:
            return None
        tope = rango(self.veredicto)
        for tramo in self.tramos:
            if rango(tramo.veredicto) == tope:
                return tramo
        return None

    @property
    def testigos(self) -> Tuple[Testigo, ...]:
        return tuple(t for tramo in self.tramos for t in tramo.testigos)

    def ausencias_vigentes(self) -> Tuple[Testigo, ...]:
        """Las que se probaron contra la pagina **final**, y solo si la cadena sostiene.

        Dos condiciones y no una. Que la pagina final sea la que prueba el
        testigo dice que la ausencia sigue siendo cierta **del ultimo nodo**;
        que la cadena sostenga dice que ese ultimo nodo es el mismo objeto que
        salio del primero. Con la frontera rota las dos cosas pueden ser verdad
        por separado y la conclusion —«esta ausencia viajo de A a C»— seria
        falsa: alguien sustituyo el nodo intermedio.

        Una ausencia probada en A sigue siendo cierta de A para siempre, y por
        eso no se borra: se publica como historica. Lo que no se puede es
        heredarla a C —que es lo que haria un `grep` de cero sobre la cadena— sin
        que la pagina que la prueba sea la que llega.
        """

        if not self.sostiene:
            return ()
        final = self.digest_destino
        return tuple(t for t in self.testigos if t.digest_pagina == final)

    def ausencias_sin_transito(self) -> Tuple[Testigo, ...]:
        """Probadas contra la pagina final, pero la cadena no une los extremos.

        El tercer caso, que no es «vigente» ni «historica»: el testigo no
        envejecio, lo que no esta es el camino.
        """

        if self.sostiene:
            return ()
        final = self.digest_destino
        return tuple(t for t in self.testigos if t.digest_pagina == final)

    def ausencias_historicas(self) -> Tuple[Testigo, ...]:
        final = self.digest_destino
        return tuple(t for t in self.testigos if t.digest_pagina != final)

    def cadena(self) -> str:
        """`A -d1-> B -d2-> C`, con los digests recortados a 12."""

        partes = [self.tramos[0].origen]
        for tramo in self.tramos:
            partes.append("-%s->" % (tramo.digest_destino[:12] or "vacio"))
            partes.append(tramo.destino)
        return " ".join(partes)

    def lineas(self) -> List[str]:
        """El recibo como lineas de texto, en el dialecto de los otros actos."""

        salida = [
            "cadena | %s" % self.cadena(),
            "tramos | %d | peor | %s" % (len(self.tramos), self.veredicto.value),
        ]
        if self.frontera_vacua:
            salida.append("frontera | sin medir | falta la pagina de un lado del empalme")
        if self.frontera is not None:
            esperado, leido = self.frontera
            salida.append(
                "frontera | rota | el tramo anterior dejo %s y el siguiente leyo %s"
                % (esperado[:12] or "vacio", leido[:12] or "vacio")
            )
        degradado = self.tramo_degradado
        if degradado is not None and not self.sostiene:
            salida.append(
                "degradado | %s -> %s | %s" % (degradado.origen, degradado.destino, degradado.veredicto.value)
            )
            for ruta in degradado.opacas:
                salida.append("opaca | %s" % ruta)
        for testigo in self.ausencias_vigentes():
            salida.append("ausencia vigente | %s | %s" % (testigo.consulta, testigo.intervalo()))
        for testigo in self.ausencias_sin_transito():
            salida.append(
                "ausencia sin transito | %s | probada contra la pagina final y la cadena no sostiene"
                % testigo.consulta
            )
        for testigo in self.ausencias_historicas():
            salida.append(
                "ausencia historica | %s | probada contra %s" % (testigo.consulta, testigo.digest_pagina[:12])
            )
        salida.append("-> %s" % self.veredicto.value)
        return salida


def identidad(nodo: str, pagina: Sequence[EntradaDeclarada]) -> Recibo:
    """El neutro: un salto `nodo -> nodo` que no cambia la pagina ni prueba nada."""

    filas = tuple(pagina)
    tramo = Tramo(
        origen=nodo,
        destino=nodo,
        veredicto=VeredictoDeComposicion.INTACTA,
        pagina_origen=filas,
        pagina_destino=filas,
    )
    return Recibo(tramos=(tramo,))


def _cruce(izquierda: Recibo, derecha: Recibo) -> Optional[Tuple[str, str]]:
    """La frontera, o `None` si cierra.

    Tres casos, y el tercero es el que importa: si a cualquiera de los dos lados
    le falta pagina, la frontera no esta rota —esta **sin medir**—, y llamarla
    rota seria afirmar un cambio que nadie midio.
    """

    esperado = izquierda.digest_destino
    leido = derecha.digest_origen
    if not esperado or not leido:
        return None
    if esperado != leido:
        return (esperado, leido)
    return None


def componer(izquierda: Recibo, derecha: Recibo) -> Recibo:
    """`R_ab` seguido de `R_bc`, con la frontera comprobada y el peor estado arriba.

    Levanta si los recibos no se tocan —eso es una entrada invalida del que
    compone, no un hallazgo— y devuelve un recibo con `frontera_rota` si se tocan
    pero las paginas no coinciden, que si es un hallazgo: alguien sustituyo el
    nodo intermedio, o el recibo miente.
    """

    if not isinstance(izquierda, Recibo) or not isinstance(derecha, Recibo):
        raise ContratoViolado("solo se componen recibos", valor=type(izquierda))
    if izquierda.destino != derecha.origen:
        raise ContratoViolado(
            "los recibos no comparten nodo", izquierda=izquierda.destino, derecha=derecha.origen
        )
    tramos: List[Tramo] = list(izquierda.tramos) + list(derecha.tramos)
    absorbidos = tuple(t for t in tramos if not t.es_identidad)
    if absorbidos:
        tramos = list(absorbidos)
    # Una frontera rota o vacua no se cura al seguir componiendo: viaja, porque
    # el empalme roto sigue estando dentro de la cadena larga.
    heredada = izquierda.frontera if izquierda.frontera is not None else derecha.frontera
    vacua = (
        izquierda.frontera_vacua
        or derecha.frontera_vacua
        or not izquierda.digest_destino
        or not derecha.digest_origen
    )
    frontera = _cruce(izquierda, derecha) if heredada is None else None
    return Recibo(
        tramos=tuple(tramos),
        frontera=heredada if heredada is not None else frontera,
        frontera_vacua=vacua and heredada is None and frontera is None,
    )


def a_dict(recibo: Recibo) -> Dict[str, object]:
    """El recibo en JSON, con las filas dentro y los digests recalculados.

    Los digests se publican **ademas** de las filas, aunque se deriven, para que
    un tercero pueda comprobar la derivacion en vez de creersela.

    La version del formato dice que prueba la cadena. Si algun tramo declara su
    `sha256_regla`, el recibo es `recibo-de-composicion/2` y **cada** tramo
    publica la suya; si ninguno la declara, sigue siendo `/1` y el JSON es el de
    antes, byte a byte. La version no es cosmetica: un `/1` solo afirma
    continuidad de bytes; un `/2` afirma, ademas, a que regla se ato cada salto.
    """

    con_regla = any(tramo.sha256_regla for tramo in recibo.tramos)
    tramos = []
    for tramo in recibo.tramos:
        entrada: Dict[str, object] = {
            "origen": tramo.origen,
            "destino": tramo.destino,
            "veredicto": tramo.veredicto.value,
            "digest_origen": tramo.digest_origen,
            "digest_destino": tramo.digest_destino,
            "pagina_origen": [_fila_dict(f) for f in tramo.pagina_origen],
            "pagina_destino": [_fila_dict(f) for f in tramo.pagina_destino],
            "testigos": [_testigo_dict(t) for t in tramo.testigos],
        }
        if con_regla:
            entrada["sha256_regla"] = tramo.sha256_regla
        tramos.append(entrada)
    return {
        "formato": "recibo-de-composicion/2" if con_regla else "recibo-de-composicion/1",
        "origen": recibo.origen,
        "destino": recibo.destino,
        "veredicto": recibo.veredicto.value,
        "sostiene": recibo.sostiene,
        "frontera": list(recibo.frontera) if recibo.frontera is not None else None,
        "frontera_vacua": recibo.frontera_vacua,
        "tramos": tramos,
    }


def _fila_dict(fila: EntradaDeclarada) -> Dict[str, str]:
    return {"ruta": fila.ruta, "digest": fila.h.digest, "motivo": fila.motivo}


def _testigo_dict(testigo: Testigo) -> Dict[str, object]:
    return {
        "consulta": testigo.consulta,
        "estado": testigo.estado.value,
        "posicion": testigo.posicion,
        "anterior": testigo.anterior.ruta if testigo.anterior is not None else None,
        "siguiente": testigo.siguiente.ruta if testigo.siguiente is not None else None,
        "digest_pagina": testigo.digest_pagina,
    }


def desde_dict(datos: Dict[str, object]) -> Recibo:
    """Reconstruye un recibo leido de JSON, revalidando todo lo que se pueda.

    Se revalidan las filas y la forma; los digests publicados **no** se aceptan
    como entrada —se recalculan y se comparan, y si no cuadran se levanta—, de
    modo que un JSON manipulado no se convierte en un recibo valido por la puerta
    de atras.
    """

    from .types import Hash

    if not isinstance(datos, dict) or datos.get("formato") not in (
        "recibo-de-composicion/1",
        "recibo-de-composicion/2",
    ):
        raise ContratoViolado("el recibo no declara el formato", valor=datos.get("formato"))
    formato = datos["formato"]
    crudos = datos.get("tramos")
    if not isinstance(crudos, list) or not crudos:
        raise ContratoViolado("el recibo no trae tramos")
    tramos: List[Tramo] = []
    for crudo in crudos:
        try:
            veredicto = VeredictoDeComposicion(str(crudo["veredicto"]))
            origen = str(crudo["origen"])
            destino = str(crudo["destino"])
            pagina_origen = _filas(crudo.get("pagina_origen"))
            pagina_destino = _filas(crudo.get("pagina_destino"))
        except (KeyError, TypeError, ValueError) as fallo:
            raise ContratoViolado("el tramo no se puede leer", motivo=str(fallo)) from None
        tramo = Tramo(
            origen=origen,
            destino=destino,
            veredicto=veredicto,
            pagina_origen=pagina_origen,
            pagina_destino=pagina_destino,
            testigos=_testigos(crudo.get("testigos"), pagina_origen, pagina_destino),
            sha256_regla=str(crudo.get("sha256_regla", "") or ""),
        )
        for publicado, recalculado in (
            (crudo.get("digest_origen"), tramo.digest_origen),
            (crudo.get("digest_destino"), tramo.digest_destino),
        ):
            if publicado != recalculado:
                raise ContratoViolado(
                    "el digest publicado no corresponde a las filas",
                    publicado=publicado,
                    recalculado=recalculado,
                )
        tramos.append(tramo)
    frontera = datos.get("frontera")
    if frontera is not None:
        if not isinstance(frontera, list) or len(frontera) != 2:
            raise ContratoViolado("la frontera declarada no es un par", valor=frontera)
        frontera = (str(frontera[0]), str(frontera[1]))
    vacua = datos.get("frontera_vacua", False)
    if not isinstance(vacua, bool):
        raise ContratoViolado("la bandera de frontera vacua no es booleana", valor=vacua)
    if formato == "recibo-de-composicion/2":
        sin_regla = [t.destino for t in tramos if not t.sha256_regla]
        if sin_regla:
            raise ContratoViolado("un recibo /2 declara la regla de cada tramo", nodos=sin_regla)
    elif any(t.sha256_regla for t in tramos):
        raise ContratoViolado("un recibo /1 no puede declarar reglas sin cambiar de formato")
    recibo = Recibo(tramos=tuple(tramos), frontera=frontera, frontera_vacua=vacua)
    publicado = datos.get("veredicto")
    if publicado is not None and publicado != recibo.veredicto.value:
        raise ContratoViolado(
            "el veredicto publicado no se sigue de los tramos",
            publicado=publicado,
            recalculado=recibo.veredicto.value,
        )
    return recibo


def _filas(crudas: object) -> Tuple[EntradaDeclarada, ...]:
    if not crudas:
        return ()
    if not isinstance(crudas, list):
        raise ContratoViolado("la pagina declarada no es una lista", valor=type(crudas))
    filas = []
    for cruda in crudas:
        if not isinstance(cruda, dict) or "ruta" not in cruda or "digest" not in cruda:
            raise ContratoViolado("la fila declarada no trae ruta y digest", valor=cruda)
        filas.append(
            EntradaDeclarada(
                ruta=str(cruda["ruta"]),
                h=Hash(algoritmo=ALGORITMO, digest=str(cruda["digest"])),
                motivo=str(cruda.get("motivo", "")),
            )
        )
    return tuple(filas)


def _pagina_de(
    declarada: str,
    pagina_origen: Tuple[EntradaDeclarada, ...],
    pagina_destino: Tuple[EntradaDeclarada, ...],
) -> Tuple[EntradaDeclarada, ...]:
    """La pagina contra la que el testigo dice haber sido probado.

    Si el recibo no la trae, el testigo no se puede recomprobar y se levanta. Es
    la unica respuesta que no inventa: el testigo es la mitad comprobable del
    recibo, y aceptarlo contra otra pagina lo convierte en una afirmacion del
    productor sobre un sujeto que ya no esta.
    """

    for filas in (pagina_destino, pagina_origen):
        if filas and digest_de_pagina(filas) == declarada:
            return filas
    raise ContratoViolado(
        "el testigo declara una pagina que el recibo no trae", digest=declarada[:12] or "vacio"
    )


def _testigos(
    crudos: object,
    pagina_origen: Tuple[EntradaDeclarada, ...],
    pagina_destino: Tuple[EntradaDeclarada, ...],
) -> Tuple[Testigo, ...]:
    """Reconstruye los testigos **contra las filas del propio recibo**.

    Un testigo que viaja como texto libre es una afirmacion del productor; uno
    que se rehace contra las filas que el recibo trae es una afirmacion
    comprobable. Se rehace: el vecino publicado tiene que ser el vecino que las
    filas dan.
    """

    if not crudos:
        return ()
    if not isinstance(crudos, list):
        raise ContratoViolado("los testigos no son una lista", valor=type(crudos))
    if not pagina_origen and not pagina_destino:
        raise ContratoViolado("un testigo sin pagina no se puede recomprobar")
    testigos = []
    for crudo in crudos:
        if not isinstance(crudo, dict):
            raise ContratoViolado("el testigo no es un objeto", valor=crudo)
        consulta = str(crudo.get("consulta", ""))
        try:
            estado = VeredictoDeAusencia(str(crudo.get("estado")))
        except ValueError:
            raise ContratoViolado("el testigo declara un estado desconocido", valor=crudo.get("estado")) from None
        declarada = str(crudo.get("digest_pagina", ""))
        filas = _pagina_de(declarada, pagina_origen, pagina_destino)
        indice: Dict[str, EntradaDeclarada] = {f.ruta: f for f in filas}
        anterior = crudo.get("anterior")
        siguiente = crudo.get("siguiente")
        for vecino, nombre in ((anterior, "anterior"), (siguiente, "siguiente")):
            if vecino is None:
                continue
            if str(vecino) not in indice:
                raise ContratoViolado(
                    "el testigo nombra un vecino que su pagina no tiene", vecino=str(vecino), lado=nombre
                )
        testigos.append(
            Testigo(
                consulta=consulta,
                estado=estado,
                posicion=int(crudo.get("posicion", 0)),  # type: ignore[arg-type]
                anterior=indice[str(anterior)] if anterior is not None else None,
                siguiente=indice[str(siguiente)] if siguiente is not None else None,
                digest_pagina=declarada,
            )
        )
    return tuple(testigos)
