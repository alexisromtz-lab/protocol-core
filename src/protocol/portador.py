"""src/protocol/portador.py — el portador: la gramática con la que se leen los bytes.

El manifiesto es el único objeto que un tercero nos entrega. Todo lo que este
repositorio certifica empieza por leerlo, y hasta aquí esa lectura estaba escrita
en un solo sitio —`split("  ", 1)`— que no era una gramática declarada sino una
costumbre: la de `sha256sum` de GNU. Medido el 2026-11-25 sobre cinco artefactos
públicos, **una de cinco familias de portador se leía**, tres se rechazaban con
un mensaje que no nombraba nada y una —el `Release` de Debian— se leía mal y
acusaba de alteración a un archivo intacto.

Por qué esto no es un detalle de comodidad. La página que el recibo firma es una
lista de pares `(ruta, digest)`. Si dos gramáticas pueden leer los mismos bytes,
los mismos bytes tienen dos páginas y el recibo tiene dos sujetos sin saberlo
(§A2.2 aplicado al portador). La defensa no es adivinar mejor: es que las
gramáticas admitidas sean **disjuntas** —cada línea tiene como mucho una
lectura— y que la lectura se **declare**, no se prefiera.

Las cuatro gramáticas, cada una contra un artefacto real publicado:

- `coreutils` · `digest__ruta` y `digest *ruta` · jq 1.7.1, Node 22, gh 2.62.
- `bsd` · `SHA256 (ruta) = digest`, envuelto en claro firmado PGP · Fedora 41.
- `deb822` · ` digest  tamaño ruta`, **con el espacio inicial** · Debian 12
  `Release`, sección `SHA256:`.
- `suelto` · un solo `digest`; el nombre vive en el nombre del archivo · Go 1.23.3.

Son disjuntas por construcción, no por suerte: `deb822` exige espacio inicial,
`coreutils` exige el digest en la columna cero, `bsd` exige el prefijo `SHA256 (`
y `suelto` exige que la línea entera sea hexadecimal. La consecuencia es el
teorema del anillo: **la lectura es una función, no una elección** — y por eso
una página se puede publicar sin publicar además quién la leyó.

Lo que sí puede cambiar la lectura es el **recorte**: quitar el espacio inicial
de cada línea —lo que hace cualquier `sed`, cualquier copia al portapapeles y
cualquier `.strip()`— convierte el `Release` de Debian en un archivo de
`coreutils` con las rutas empezando por el tamaño. Mismo archivo, otro digest.
Por eso `recortes()` no adivina: devuelve la lectura alternativa, y quien lea
sin declarar portador recibe las dos.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

#: Anchura del digest admitido. El manifiesto sellado no usa anchuras truncadas.
ANCHURA = 64

_HEX = "[0-9a-f]{%d}" % ANCHURA

#: La forma canónica de una página. Idéntica a la de `ausencia` y `composicion`:
#: una página tiene **una** forma, o cada módulo firmaría un objeto distinto.
FORMATO_CANONICO = "%s  %s\n"

#: Declaradas, y en este orden cuando haya que publicarlas.
GRAMATICAS: Tuple[str, ...] = ("coreutils", "bsd", "deb822", "suelto")

_RE_COREUTILS = re.compile(r"^(%s) ([ *])(.+)$" % _HEX)
_RE_BSD = re.compile(r"^SHA256 \((.+)\) = (%s)$" % _HEX)
_RE_DEB822 = re.compile(r"^ (%s) +([0-9]+) (\S.*)$" % _HEX)
_RE_SUELTO = re.compile(r"^(%s)$" % _HEX)

_RE_CABECERA_DE_SECCION = re.compile(r"^(SHA256|SHA512|SHA1|MD5Sum):[ \t]*$")
_RE_MD5 = re.compile(r"^[0-9a-f]{32} [ *]\S")

#: Campo de cabecera de un documento deb822 (`Origin: Debian`). Se ignora y se cuenta.
_RE_CAMPO = re.compile(r"^([A-Za-z][A-Za-z0-9-]*):")

#: La gramática de una línea, por portador. Una sola tabla: la que usa el rechazo
#: para nombrar la primera línea que no pertenece al portador declarado.
_LINEA = {
    "coreutils": _RE_COREUTILS,
    "bsd": _RE_BSD,
    "deb822": _RE_DEB822,
    "suelto": _RE_SUELTO,
}

_PGP_INICIO = "-----BEGIN PGP SIGNED MESSAGE-----"
_PGP_FIRMA = "-----BEGIN PGP SIGNATURE-----"

#: Sufijos que el portador `suelto` hereda del nombre del archivo.
_SUFIJOS_SUELTOS: Tuple[str, ...] = (".sha256", ".sha256sum", ".sum", ".txt")

#: Prefijo explícito que denota el mismo archivo y se normaliza contándolo.
PREFIJO_EXPLICITO = "./"


class PortadorDesconocido(ValueError):
    """Ninguna gramática declarada explica todas las líneas. No se adivina."""

    def __init__(self, linea: int, texto: str, dialecto: str = "") -> None:
        self.linea = linea
        self.texto = texto
        self.dialecto = dialecto
        detalle = "dialecto ajeno: %s" % dialecto if dialecto else "ninguna gramática lo explica"
        super().__init__("linea %d: %s | %r" % (linea, detalle, texto[:90]))


class PortadorIncompleto(ValueError):
    """El portador elegido necesita un dato que no se dio. Se nombra cuál."""


class RecorteAmbiguo(ValueError):
    """Sin portador declarado, los bytes admiten dos lecturas y se publican las dos."""

    def __init__(self, lecturas: Sequence["Lectura"]) -> None:
        self.lecturas = tuple(lecturas)
        detalle = "; ".join(
            "%s%s=%d filas dig %s" % (l.portador, " (recorte)" if l.recorte else "", len(l.pares), l.digest()[:12])
            for l in self.lecturas
        )
        super().__init__("dos lecturas del mismo archivo: %s" % detalle)


@dataclass(frozen=True)
class Lectura:
    """Una lectura completa: qué portador, qué pares, y qué hubo que normalizar.

    `pares` va en el orden del archivo, porque el digest autentica una secuencia.
    `digest()` la ordena canónicamente, que es la operación que la página publica.
    """

    portador: str
    pares: Tuple[Tuple[str, str], ...]
    envoltura: str = ""
    comentarios: int = 0
    ignoradas: int = 0
    prefijadas: int = 0
    crlf: int = 0
    recorte: bool = False
    fuente: str = ""

    def __post_init__(self) -> None:
        if self.portador not in GRAMATICAS:
            raise ValueError("portador no declarado: %r" % (self.portador,))
        if not self.pares:
            raise ValueError("una lectura sin filas no es una lectura")

    def canonicos(self) -> Tuple[Tuple[str, str], ...]:
        return tuple(sorted(self.pares, key=lambda par: par[0].encode("utf-8")))

    def digest(self) -> str:
        texto = "".join(FORMATO_CANONICO % (digest, ruta) for ruta, digest in self.canonicos())
        return hashlib.sha256(texto.encode("utf-8")).hexdigest()

    def fuera_de_sitio(self) -> int:
        return sum(1 for a, b in zip(self.pares, self.canonicos()) if a != b)

    def lineas(self) -> Tuple[str, ...]:
        salida = [
            "portador | %s | %d filas | %s%s | digest %s"
            % (
                self.portador,
                len(self.pares),
                "canonico" if self.fuera_de_sitio() == 0 else "reordenado",
                " | recorte" if self.recorte else "",
                self.digest()[:12],
            )
        ]
        if self.envoltura:
            salida.append(
                "envoltura | %s | %d bloques ignorados | firma no verificada"
                % (self.envoltura, self.ignoradas)
            )
        elif self.ignoradas:
            salida.append("envoltura | %d bloques ignorados" % (self.ignoradas,))
        normalizado = []
        if self.prefijadas:
            normalizado.append("%d prefijos ./" % (self.prefijadas,))
        if self.crlf:
            normalizado.append("%d fines de linea CR" % (self.crlf,))
        if normalizado:
            salida.append("normalizado | %s | mismo archivo, se cuenta" % ", ".join(normalizado))
        if not self.envoltura and not self.ignoradas and not normalizado:
            salida.append("envoltura | ninguna | 0 normalizaciones")
        return tuple(salida)


def _sin_cr(linea: str) -> Tuple[str, int]:
    if linea.endswith("\r"):
        return linea[:-1], 1
    return linea, 0


def _cuerpo_simple(portador: str, lineas: Sequence[str]) -> Tuple[List[Tuple[int, str]], str, int, int, int]:
    """coreutils y suelto: comentarios y blancos fuera; el resto es cuerpo."""

    utiles: List[Tuple[int, str]] = []
    comentarios = 0
    crlf = 0
    for numero, cruda in enumerate(lineas, start=1):
        linea, quita = _sin_cr(cruda)
        crlf += quita
        limpia = linea.strip()
        if limpia == "":
            continue
        if limpia.startswith("#"):
            comentarios += 1
            continue
        utiles.append((numero, linea.rstrip()))
    return utiles, "", 0, comentarios, crlf


def _cuerpo_bsd(lineas: Sequence[str]) -> Tuple[List[Tuple[int, str]], str, int, int, int]:
    """`BSD` puede venir envuelto en una firma PGP en claro: se salta y se declara."""

    utiles: List[Tuple[int, str]] = []
    envoltura = ""
    comentarios = 0
    crlf = 0
    dentro = True
    for numero, cruda in enumerate(lineas, start=1):
        linea, quita = _sin_cr(cruda)
        crlf += quita
        limpia = linea.strip()
        if linea == _PGP_INICIO:
            envoltura = "pgp"
            continue
        if linea.startswith(_PGP_FIRMA):
            dentro = False
            continue
        if not dentro:
            continue
        if limpia.startswith("Hash:"):
            continue
        if limpia == "":
            continue
        if limpia.startswith("#"):
            comentarios += 1
            continue
        utiles.append((numero, linea.rstrip()))
    return utiles, envoltura, 0, comentarios, crlf


def _cuerpo_deb822(lineas: Sequence[str]) -> Tuple[List[Tuple[int, str]], str, int, int, int]:
    """Documento deb822: cabecera, secciones y la firma final se cuentan, no se leen.

    Estados: `cabecera` (campos `Clave: valor` y cabeceras de sección) →
    `cuerpo` (dentro de `SHA256:`) → vuelta a `cabecera` en la línea en blanco.
    Sin cabeceras de sección el documento es un *fragmento* y su cuerpo empieza
    en la primera línea que no es un campo.
    """

    utiles: List[Tuple[int, str]] = []
    envoltura = ""
    ignoradas = 0
    comentarios = 0
    crlf = 0
    estado = "cabecera"
    for numero, cruda in enumerate(lineas, start=1):
        linea, quita = _sin_cr(cruda)
        crlf += quita
        limpia = linea.strip()
        if linea == _PGP_INICIO or linea.startswith(_PGP_FIRMA):
            if envoltura:
                envoltura += " + pgp"
            break
        # Las secciones de un `Release` van encadenadas, sin línea en blanco:
        # la cabecera se reconoce en cualquier estado o `SHA256:` se pierde
        # dentro de `MD5Sum:` (medido: línea 786 de 1558 el 2026-11-25).
        if _RE_CABECERA_DE_SECCION.match(limpia):
            if limpia.startswith("SHA256:"):
                envoltura = "seccion SHA256"
                estado = "cuerpo"
            else:
                ignoradas += 1
                estado = "otra"
            continue
        if estado == "cuerpo":
            if limpia == "":
                estado = "cabecera"
                continue
            utiles.append((numero, linea.rstrip()))
            continue
        if estado == "otra":
            if limpia == "":
                estado = "cabecera"
            continue
        if limpia == "" or _RE_CAMPO.match(limpia):
            ignoradas += bool(limpia)
            continue
        if limpia.startswith("#"):
            comentarios += 1
            continue
        estado = "cuerpo"
        utiles.append((numero, linea.rstrip()))
    return utiles, envoltura, ignoradas, comentarios, crlf


def _cuerpo(portador: str, lineas: Sequence[str]) -> Tuple[List[Tuple[int, str]], str, int, int, int]:
    """(número, texto) útiles, más (envoltura, bloques ignorados, comentarios, crlf)."""

    if portador == "bsd":
        return _cuerpo_bsd(lineas)
    if portador == "deb822":
        return _cuerpo_deb822(lineas)
    return _cuerpo_simple(portador, lineas)


def _empareja(portador: str, utiles: Sequence[Tuple[int, str]], nombre: Optional[str]) -> Optional[List[Tuple[str, str]]]:
    """Los pares, o `None` si alguna línea no pertenece a la gramática."""

    if not utiles:
        return None
    if portador == "suelto" and len(utiles) != 1:
        return None
    pares: List[Tuple[str, str]] = []
    for _, linea in utiles:
        if portador == "coreutils":
            hallado = _RE_COREUTILS.match(linea)
            if not hallado:
                return None
            digest, _, ruta = hallado.groups()
        elif portador == "bsd":
            hallado = _RE_BSD.match(linea)
            if not hallado:
                return None
            ruta, digest = hallado.groups()
        elif portador == "deb822":
            hallado = _RE_DEB822.match(linea)
            if not hallado:
                return None
            digest, _, ruta = hallado.groups()
        else:
            hallado = _RE_SUELTO.match(linea)
            if not hallado:
                return None
            digest = hallado.group(1)
            if not nombre:
                raise PortadorIncompleto(
                    "el portador suelto no escribe el nombre de la ruta: hace falta el nombre del archivo"
                )
            prefijo = nombre
            for sufijo in _SUFIJOS_SUELTOS:
                if prefijo.endswith(sufijo):
                    prefijo = prefijo[: -len(sufijo)]
                    break
            ruta = prefijo
            if not ruta:
                raise PortadorIncompleto(
                    "el nombre del archivo %r no deja ruta al quitarle el sufijo" % (nombre,)
                )
        pares.append((ruta, digest))
    return pares


def _lineas(texto: str) -> List[str]:
    """Parte por `\n` **sin** comerse el `\r`: el fin de línea CR se cuenta, no se adivina."""

    crudas = texto.split("\n")
    if crudas and crudas[-1] == "":
        crudas.pop()
    return crudas


def _tabula(portador: str, texto: str, nombre: Optional[str]) -> Optional[Lectura]:
    utiles, envoltura, ignoradas, comentarios, crlf = _cuerpo(portador, _lineas(texto))
    pares = _empareja(portador, utiles, nombre)
    if pares is None:
        return None
    prefijadas = 0
    limpios: List[Tuple[str, str]] = []
    for ruta, digest in pares:
        original = ruta
        while ruta.startswith(PREFIJO_EXPLICITO):
            ruta = ruta[len(PREFIJO_EXPLICITO) :]
        if ruta != original:
            prefijadas += 1
        limpios.append((ruta, digest))
    return Lectura(
        portador=portador,
        pares=tuple(limpios),
        envoltura=envoltura,
        comentarios=comentarios,
        ignoradas=ignoradas,
        prefijadas=prefijadas,
        crlf=crlf,
        fuente=nombre or "",
    )


def dialecto_ajeno(linea: str) -> str:
    """Nombre del dialecto que la línea usa y no se admite, o `""`.

    Nombrarlo **no lo admite**: convierte «no se pudo leer» —un síntoma— en el
    nombre de lo que hay que convertir antes de que la página se pueda firmar.
    """

    limpia = linea.strip()
    if limpia.startswith(("SHA256 (", "SHA512 (", "SHA1 (")):
        return "BSD sin la forma exacta «SHA256 (ruta) = hex»"
    if limpia.startswith(("MD5 (", "MD5SUM (")):
        return "BSD con un algoritmo que la página no usa"
    cabecera, _, resto = limpia.partition("-")
    if cabecera in ("sha1", "sha256", "sha384", "sha512") and resto.endswith("="):
        return "SRI base64 «%s-…»: el digest no es hexadecimal" % cabecera
    if "(" in limpia and ")" in limpia and "=" in limpia:
        return "OpenSSL «ALG (ruta) = hex»"
    if (
        len(limpia) > ANCHURA + 1
        and limpia[ANCHURA] == " "
        and limpia[ANCHURA + 1] not in (" ", "*")
        and all(c in "0123456789abcdef" for c in limpia[:ANCHURA])
    ):
        return "sha256sum con un solo espacio, o deb822 con el espacio inicial recortado"
    if _RE_CABECERA_DE_SECCION.match(limpia) and not limpia.startswith("SHA256:"):
        return "seccion de otro algoritmo de un deb822"
    if _RE_MD5.match(limpia):
        return "md5sum: 32 hex, y la pagina solo firma SHA-256"
    return ""


def _candidatos(
    texto: str, nombre: Optional[str]
) -> Tuple[Tuple[str, ...], Tuple[PortadorIncompleto, ...]]:
    """Los portadores que explican el archivo y los que lo explican pero están incompletos."""

    salida = []
    incompletos = []
    for portador in GRAMATICAS:
        try:
            if _tabula(portador, texto, nombre) is not None:
                salida.append(portador)
        except PortadorIncompleto as exc:
            incompletos.append(exc)
    return tuple(salida), tuple(incompletos)


def facultades(texto: str, nombre: Optional[str] = None) -> Tuple[str, ...]:
    """Los portadores declarados que explican **todas** las líneas del archivo."""

    return _candidatos(texto, nombre)[0]


def detectar(texto: str, nombre: Optional[str] = None) -> str:
    """El portador único, o el rechazo que nombra la primera línea inclasificable.

    No se prefiere una gramática cuando falla otra: si dos explicaran el archivo
    el resultado no sería una lectura sino una elección, y una elección no se
    puede publicar como si fuera el archivo.
    """

    posibles, incompletos = _candidatos(texto, nombre)
    if len(posibles) == 1:
        return posibles[0]
    if len(posibles) > 1:
        raise RecorteAmbiguo(tuple(leer(texto, p, nombre) for p in posibles))
    if incompletos:
        # El archivo sí se explica: lo que falta es el dato que su portador no escribe.
        raise incompletos[0]
    for numero, cruda in enumerate(_lineas(texto), start=1):
        linea, _ = _sin_cr(cruda)
        if linea.strip() == "" or linea.strip().startswith("#") or linea.strip().startswith("Hash:"):
            continue
        if linea == _PGP_INICIO or linea.startswith("-----"):
            continue
        raise PortadorDesconocido(numero, linea, dialecto_ajeno(linea))
    raise PortadorDesconocido(1, "", "el archivo no trae ninguna línea de manifiesto")


def leer(texto: str, portador: str, nombre: Optional[str] = None) -> Lectura:
    """Lee declarando el portador. Declarar no adivina: si no encaja, se rechaza."""

    if portador not in GRAMATICAS:
        raise PortadorDesconocido(0, portador, "portador no declarado en GRAMATICAS")
    lectura = _tabula(portador, texto, nombre)
    if lectura is not None:
        return lectura
    utiles = _cuerpo(portador, _lineas(texto))[0]
    patron = _LINEA[portador]
    for numero, linea in utiles:
        if not patron.match(linea):
            ajenos = [otro for otro in facultades(texto, nombre) if otro != portador]
            if ajenos:
                # Nombrar el que sí encaja no lo adopta: la lectura sigue rechazada.
                raise PortadorDesconocido(
                    numero,
                    linea,
                    "%s; el archivo se explica por %s" % (dialecto_ajeno(linea) or "otra forma", ", ".join(ajenos)),
                )
            raise PortadorDesconocido(numero, linea, dialecto_ajeno(linea))
    raise PortadorDesconocido(
        utiles[0][0] if utiles else 0,
        utiles[0][1] if utiles else "",
        "ninguna linea del archivo explica la gramatica %r" % (portador,),
    )


def _recortado(texto: str) -> str:
    """Un espacio inicial menos en cada línea. Lo que hace `sed 's/^ //'`."""

    salida = []
    for cruda in _lineas(texto):
        salida.append(cruda[1:] if cruda.startswith(" ") else cruda)
    return "\n".join(salida) + ("\n" if texto.endswith("\n") else "")


def recortes(texto: str, nombre: Optional[str] = None) -> Tuple[Lectura, ...]:
    """La lectura alternativa que produce quitar el espacio inicial, si existe.

    El `Release` de Debian es `deb822` **por su espacio inicial**. Recortarlo lo
    convierte en un archivo de `coreutils` con las rutas empezando por el tamaño,
    que es exactamente el falso rojo medido el 2026-11-25. Se devuelve la lectura,
    no una sospecha: dos digests del mismo nombre, para que se vean los dos.
    """

    propio = set(facultades(texto, nombre))
    alternativas = []
    for portador in facultades(_recortado(texto), nombre):
        if portador in propio:
            continue
        lectura = _tabula(portador, _recortado(texto), nombre)
        if lectura is None:
            continue
        alternativas.append(
            Lectura(
                portador=lectura.portador,
                pares=lectura.pares,
                envoltura=lectura.envoltura,
                comentarios=lectura.comentarios,
                ignoradas=lectura.ignoradas,
                prefijadas=lectura.prefijadas,
                crlf=lectura.crlf,
                recorte=True,
                fuente=lectura.fuente,
            )
        )
    return tuple(alternativas)


def leer_sin_declarar(texto: str, nombre: Optional[str] = None) -> Lectura:
    """El camino cómodo: detecta, y si el recorte abre otra lectura, las publica."""

    portador = detectar(texto, nombre)
    propia = leer(texto, portador, nombre)
    alternativas = recortes(texto, nombre)
    if alternativas:
        raise RecorteAmbiguo((propia,) + alternativas)
    return propia
