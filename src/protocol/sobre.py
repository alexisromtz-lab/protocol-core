"""src/protocol/sobre.py — el anillo 6: el sobre, que es lo que envuelve al portador.

El anillo 5 aprendio que el portador no es una costumbre sino una gramatica
declarada. Le quedo un borde sin medir: el mismo autor publica **los mismos
bytes** dentro de un sobre criptografico, y hasta aqui esos bytes no se leian.
Medido el 2026-11-25 sobre Debian 12:

- `Release` · 149 266 B · sin sobre · el anillo 5 lo lee: 772 filas, `c0dc59762595`.
- `InRelease` · 151 075 B · firmado en claro · el anillo 5 **no lo lee**: rechaza
  un artefacto oficial e intacto, y ademas miente sobre la causa (`linea 0`,
  `linea 4: 'Origin: Debian'`) cuando lo que sobra es la envoltura de la linea 1.
- `Release.gpg` · 1 760 B · firma pegada · no trae filas: atestigua a **otro**
  archivo, y no lo nombra.

LA LEY DEL ANILLO. El sobre **no cambia el objeto, cambia el archivo**. Quitado
el sobre, la carga de `InRelease` es byte a byte `Release` (149 266 B, sha256
`abcf5882746e0f68` = el del `Release` entero). Dos archivos, un objeto. Por eso
un recibo que publique un solo digest esta confundiendo la identidad del archivo
con la del objeto, y no puede comparar la misma pagina publicada de tres formas.

LA SEGUNDA LEY, que corrige un defecto de este mismo repositorio. `FUENTES.txt`
declaraba sobre el `Release` de Debian «la firma PGP final no se verifica», y ese
archivo **no tiene ni un byte de PGP**. Declarar un punto ciego que no existe es
tan grave como publicar un verde falso: el auditor no puede distinguir «no pude
verificarlo» de «no habia nada que verificar». Por eso aqui el punto ciego se
**mide** —`bytes_firma`— y solo se declara si es mayor que cero; si es cero se
publica `sin sobre | 0 bytes de firma | no habia nada que verificar`, que es un
hecho y no una disculpa.

LAS TRES TOPOLOGIAS, medidas sobre el mismo autor y el mismo contenido:

- `sin_sobre` · la pagina llega por TLS y nadie firma · jq, Node, gh, Go, `Release`.
- `firmado_en_claro` · la carga va dentro de `BEGIN PGP SIGNED MESSAGE` y las
  lineas que empiezan por `-` van escapadas como `- ` · Fedora 41, `InRelease`.
- `firma_pegada` · un archivo aparte, sin carga, cuyo vinculo con el objeto es el
  nombre del archivo (`Release.gpg` ↔ `Release`) · Debian.

De las tres, **dos necesitan que el llamante ponga el nombre**: la firma pegada y
el portador `suelto`. Es el mismo defecto en dos niveles, y se publica, no se
adivina (`SobreSinCarga` nombra lo que falta).

LO QUE ESTE MODULO NO HACE, y lo dice: no valida PGP. No hay verificacion de
clave publica aqui; se publica `firma no verificada` **junto al numero de bytes
que si se vieron**, para que el siguiente anillo pueda cerrarlo sin cambiar esta
pagina. Un sobre que se salta sin contarse es una omision; uno que se cuenta es
una medida.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import List, Optional, Tuple

#: Declaradas, y en este orden cuando haya que publicarlas.
TOPOLOGIAS: Tuple[str, ...] = ("sin_sobre", "firmado_en_claro", "firma_pegada")

_MARCA_MENSAJE = "-----BEGIN PGP SIGNED MESSAGE-----"
_MARCA_FIRMA = "-----BEGIN PGP SIGNATURE-----"
_MARCA_FIN = "-----END PGP SIGNATURE-----"

#: RFC 4880 §7.1: la linea que empieza por `-` lleva el escape `- ` delante.
_ESCAPE = "- "


class SobreInvalido(ValueError):
    """El sobre esta abierto o cerrado sin su pareja. No se lee a medias."""


class SobreSinCarga(ValueError):
    """El artefacto es una firma pegada: atestigua otro archivo y no lo nombra."""

    def __init__(self, bytes_firma: int) -> None:
        self.bytes_firma = bytes_firma
        super().__init__(
            "firma pegada de %d bytes, sin carga: el manifiesto esta en otro archivo "
            "y su nombre no viaja dentro de este" % (bytes_firma,)
        )


def _bytes(texto: str) -> bytes:
    """Los bytes exactos que se entregaron. `surrogateescape` es ida y vuelta."""

    return texto.encode("utf-8", "surrogateescape")


def _lineas(texto: str) -> List[str]:
    crudas = texto.split("\n")
    if crudas and crudas[-1] == "":
        crudas.pop()
    return crudas


@dataclass(frozen=True)
class Sobre:
    """Lo que envuelve a la carga: topologia, dos digests y lo que hubo que deshacer.

    `sobre_digest` es la identidad del **archivo**; `carga_digest`, la del
    **objeto**. Cuando no hay sobre son el mismo, y se publican igual: un solo
    digest es el caso particular de dos, no un caso aparte.
    """

    topologia: str
    sobre_digest: str
    carga_digest: str
    carga: str
    bytes_firma: int = 0
    bloques: int = 0
    escapadas: int = 0
    espacios_finales: int = 0
    crlf: int = 0

    def __post_init__(self) -> None:
        if self.topologia not in TOPOLOGIAS:
            raise ValueError("topologia no declarada: %r" % (self.topologia,))
        if self.topologia != "firma_pegada" and not self.carga:
            raise ValueError("un sobre con carga vacia no es una lectura")

    def hay_firma(self) -> bool:
        """El unico predicado que autoriza a declarar el punto ciego."""

        return self.bytes_firma > 0

    def lineas(self) -> Tuple[str, ...]:
        """Una línea por hecho. El punto ciego sólo se nombra si el byte existe."""

        if self.topologia == "sin_sobre":
            return ("sobre | ninguno | 0 bytes de firma | no habia nada que verificar",)
        salida = [
            "sobre | %s | %d bytes de firma | carga %s | sobre %s | firma no verificada"
            % (
                self.topologia,
                self.bytes_firma,
                self.carga_digest[:12] or "-",
                self.sobre_digest[:12],
            )
        ]
        deshecho = []
        if self.escapadas:
            deshecho.append("%d lineas desescapadas" % (self.escapadas,))
        if self.espacios_finales:
            deshecho.append("%d lineas con espacio final quitado" % (self.espacios_finales,))
        if self.crlf:
            deshecho.append("%d fines de linea CR" % (self.crlf,))
        if deshecho:
            salida.append("deshecho dentro del sobre | %s" % (", ".join(deshecho),))
        return tuple(salida)


def _carga_de(lineas: List[str], desde: int, hasta: int) -> Tuple[str, int, int, int]:
    """Deshace el sobre de las lineas `[desde, hasta)` y devuelve carga y cuentas."""

    limpias: List[str] = []
    escapadas = 0
    espacios = 0
    crlf = 0
    for cruda in lineas[desde:hasta]:
        linea = cruda
        if linea.endswith("\r"):
            linea = linea[:-1]
            crlf += 1
        if linea.startswith(_ESCAPE):
            linea = linea[len(_ESCAPE) :]
            escapadas += 1
        sin_cola = linea.rstrip(" \t")
        if sin_cola != linea:
            espacios += 1
            linea = sin_cola
        limpias.append(linea)
    return "\n".join(limpias) + "\n", escapadas, espacios, crlf


def leer_sobre(texto: str) -> Sobre:
    """Topologia, digests y cuentas. No valida la firma: la cuenta."""

    crudas = _lineas(texto)
    sobre_digest = hashlib.sha256(_bytes(texto)).hexdigest()

    inicio_mensaje: Optional[int] = None
    inicio_firma: Optional[int] = None
    fin_firma: Optional[int] = None
    for numero, cruda in enumerate(crudas):
        marca = cruda.rstrip()
        if marca == _MARCA_MENSAJE and inicio_mensaje is None:
            inicio_mensaje = numero
        elif marca == _MARCA_FIRMA and inicio_firma is None:
            inicio_firma = numero
        elif marca == _MARCA_FIN and fin_firma is None:
            fin_firma = numero

    if inicio_mensaje is not None:
        if inicio_firma is None or fin_firma is None or inicio_firma < inicio_mensaje:
            raise SobreInvalido(
                "mensaje firmado en claro sin bloque de firma cerrado: no se lee a medias"
            )
        hueco = next(
            (i for i in range(inicio_mensaje + 1, inicio_firma) if crudas[i].rstrip() == ""),
            None,
        )
        if hueco is None:
            raise SobreInvalido("el mensaje firmado en claro no separa su cabecera de la carga")
        carga, escapadas, espacios, crlf = _carga_de(crudas, hueco + 1, inicio_firma)
        return Sobre(
            topologia="firmado_en_claro",
            sobre_digest=sobre_digest,
            carga_digest=hashlib.sha256(_bytes(carga)).hexdigest(),
            carga=carga,
            bytes_firma=len("\n".join(crudas[inicio_firma : fin_firma + 1]).encode("utf-8", "surrogateescape")),
            bloques=1,
            escapadas=escapadas,
            espacios_finales=espacios,
            crlf=crlf,
        )

    if inicio_firma is not None:
        if fin_firma is None:
            raise SobreInvalido("bloque de firma sin cerrar")
        if any(c.strip() for c in crudas[:inicio_firma]):
            raise SobreInvalido("lineas antes de la firma: el artefacto no es solo un sobre")
        cuerpo = "\n".join(crudas[inicio_firma : fin_firma + 1])
        return Sobre(
            topologia="firma_pegada",
            sobre_digest=sobre_digest,
            carga_digest="",
            carga="",
            bytes_firma=len(cuerpo.encode("utf-8", "surrogateescape")),
            bloques=1,
        )

    return Sobre(
        topologia="sin_sobre",
        sobre_digest=sobre_digest,
        carga_digest=sobre_digest,
        carga=texto,
    )


def desenvolver(texto: str) -> Tuple[str, Sobre]:
    """La carga y su sobre. Una firma pegada no tiene carga y lo nombra."""

    sobre = leer_sobre(texto)
    if sobre.topologia == "firma_pegada":
        raise SobreSinCarga(sobre.bytes_firma)
    return sobre.carga, sobre
