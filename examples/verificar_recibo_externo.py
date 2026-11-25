"""examples/verificar_recibo_externo.py — un tercero que no llama al generador.

Uso:

    python3 -B examples/verificar_recibo_externo.py --recibo recibo.json
    python3 -B examples/verificar_recibo_externo.py --recibo recibo.json \\
        --manifiesto SHA256SUMS --ausente "cita-09:00-sillon1"
    python3 -B examples/verificar_recibo_externo.py --recibo recibo.json --demo

QUE PRUEBA. Que un recibo se pueda cerrar **sin ejecutar el codigo que lo
produjo**. El verificador no importa `protocol`: reescribe por su cuenta el
formato canonico, el digest de pagina, la tabla de degradacion y la busqueda de
vecinos. Si los dos coinciden es porque el formato esta escrito y no porque los
dos llamen a la misma funcion; si divergen, el desacuerdo es el hallazgo.

QUE RECIBE. Solo el JSON del recibo (que lleva sus paginas dentro) y, si se le
da, el manifiesto publicado. Nada mas: ni el arbol, ni el generador, ni la
maquina donde se produjo.

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
- `1` algo fue alterado (digest, frontera, vecinos, veredicto publicado).
- `2` la entrada no se puede leer (JSON roto, pagina desordenada, falta un
  campo obligatorio).
"""

from __future__ import annotations

import hashlib as _hashlib
import json as _json
import re as _re
import sys as _sys
from typing import Dict, List, Optional, Sequence, Tuple

#: Se reescribe, no se importa. Es la unica forma de que la comparacion mida
#: algo: dos modulos que importan la misma constante siempre coinciden.
FORMATO_CANONICO = "%s  %s\n"

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


def verificar(
    recibo: Dict[str, object],
    manifiesto: Optional[str],
    ausente: Optional[str],
    portador: str = "auto",
    nombre: Optional[str] = None,
) -> Tuple[int, List[str]]:
    lineas: List[str] = []
    fallos = 0
    tramos = recibo.get("tramos")
    if not isinstance(tramos, list) or not tramos:
        raise EntradaInvalida("el recibo no trae tramos")
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
    try:
        with open(ruta, "r", encoding="utf-8") as flujo:
            datos = _json.load(flujo)
        codigo, lineas = verificar(datos, manifiesto, ausente, portador, nombre)
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
