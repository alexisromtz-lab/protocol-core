#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""El cuarto acto: una contrafirma sobre la página del censo, con ancla real.

El predicado prueba **qué** ocurrió; el ancla prueba **cuándo** y que el acto no
cambió después. Este acto es el que convierte la página en objeto vendible:
levanta el predicado desde el archivo publicado —sin el emisor—, comprueba que el
archivo de la ancla y el de enfrente son el mismo acto, y emite la respuesta.

Lo que este acto **no** mide, y por eso lo declara:

  · No alcanza la red: que la ancla exista en el remoto se declara, no se sondea.
  · El verificador es el mismo árbol que emitió la página. Es una
    auto-contrafirma: prueba que el acto es verificable por quien no lo emitió,
    no que un tercero independiente lo haya verificado. El nombre lo dice.
  · `RANCIO` y `REFUTA` comparten RC 1. El código de salida dice si la ancla
    está vigente; el valor tipado dice **qué** hacer con ella.

Uso:  contrafirmar_censo.py [--check]
RC:   0 ancla vigente · 1 rancio, refuta o no medida (la línea `VEREDICTO DE ANCLA`
      dice cuál) · 2 contrato
"""

from __future__ import annotations

import json as _json
import pathlib as _pathlib
import subprocess as _subprocess
import sys as _sys

RAIZ = _pathlib.Path(__file__).resolve().parent.parent
if str(RAIZ / "src") not in _sys.path:
    _sys.path.insert(0, str(RAIZ / "src"))

from protocol.predicado import (  # noqa: E402
    Contrafirma,
    VeredictoAdjudicado,
    VeredictoDeAncla,
    contrafirmar,
    desde_cuerpo,
    verificar_contrafirma,
)
from protocol.types import ContratoViolado, Divergencia, RutaRelativa  # noqa: E402

DECLARACION = RAIZ / "examples" / "ancla-declarada.txt"
CONJUNTO = RAIZ / "examples" / "contrafirma-censo.json"
VERIFICADOR = "protocol-core/examples/contrafirmar_censo.py (auto-contrafirma)"


def _declaracion() -> dict:
    campos = {}
    for linea in DECLARACION.read_text(encoding="utf-8").splitlines():
        limpia = linea.strip()
        if not limpia or limpia.startswith("#"):
            continue
        if "=" not in limpia:
            raise ContratoViolado("la declaración va en pares `clave=valor`", linea=limpia)
        clave, valor = limpia.split("=", 1)
        campos[clave.strip()] = valor.strip()
    for exigido in ("repositorio", "ancla", "ruta"):
        if not campos.get(exigido):
            raise ContratoViolado("la declaración nombra el ancla completa", falta=exigido)
    return campos


def _git(*argumentos):
    proceso = _subprocess.run(
        ("git",) + argumentos,
        cwd=str(RAIZ),
        stdout=_subprocess.PIPE,
        stderr=_subprocess.PIPE,
        check=False,
    )
    if proceso.returncode != 0:
        raise ContratoViolado(
            "git no respondió: sin ancla no hay contrafirma",
            comando="git " + " ".join(argumentos),
            error=proceso.stderr.decode("utf-8", "replace").strip(),
        )
    return proceso.stdout.decode("utf-8", "replace")


def _fecha_de_la_ancla(ancla):
    sello = _git("show", "-s", "--format=%cI", ancla).strip()
    if not sello:
        raise ContratoViolado("la ancla no declara fecha", ancla=ancla)
    return sello


def _acto(decl):
    """La contrafirma se emite sobre el acto de la ancla, no sobre el de enfrente.

    El ancla es lo publicado; si la contrafirma se emitiera sobre el archivo de
    la mesa, una página manipulada produciría su propia contrafirma y el
    verificador no tendría contra qué divergir.
    """

    ruta = decl["ruta"]
    alli = desde_cuerpo(_git("show", "%s:%s" % (decl["ancla"], ruta)).encode("utf-8"))
    ancla = "%s@%s · %s" % (
        decl["repositorio"],
        decl["ancla"][:12],
        _fecha_de_la_ancla(decl["ancla"]),
    )
    return contrafirmar(alli, VERIFICADOR, VeredictoAdjudicado.CONFIRMA, ancla)


def _bytes_de_enfrente(decl):
    """Los bytes de la página que está en la mesa, o `None` si no se puede leer dentro de la raíz.

    La declaración la edita una persona, así que `ruta` es **entrada**, no una
    constante: una ruta que sale de la raíz (`..`, absoluta) o un enlace que
    apunta fuera haría que el verificador leyera archivos del host del
    evaluador. Lo que no está dentro no se lee —se adjudica `NO_MEDIDA` con su
    motivo—, porque un verificador que se deja sacar de su árbol confirma
    objetos que no son el suyo.
    """

    try:
        confinada = RutaRelativa(decl["ruta"])
    except ContratoViolado as exc:
        print("OPACO | %s | la ruta declarada no es del namespace: %s" % (decl["ruta"], exc))
        return None
    alli = (RAIZ / confinada.texto).resolve()
    try:
        alli.relative_to(RAIZ)
    except ValueError:
        print("OPACO | %s | la ruta declarada sale de la raiz" % decl["ruta"])
        return None
    if not alli.is_file():
        print("OPACO | %s | la ruta declarada no es un archivo de este arbol" % decl["ruta"])
        return None
    return alli.read_bytes()


def _mismo_acto(decl, contrafirma):
    """¿El archivo de la mesa es el acto que la contrafirma cubre?"""

    datos = _bytes_de_enfrente(decl)
    if datos is None:
        return VeredictoDeAncla.NO_MEDIDA
    enfrente = desde_cuerpo(datos)
    if enfrente.digest() != contrafirma.digest_del_predicado:
        print(
            "RANCIO | el ancla describe otro arbol: la pagina de enfrente no es la "
            "del ancla | enfrente %s ancla %s"
            % (enfrente.digest().digest, contrafirma.digest_del_predicado.digest)
        )
        return VeredictoDeAncla.RANCIO
    return VeredictoDeAncla.VIGENTE


def _entorno():
    return {
        "plataforma": _sys.platform,
        "runtime": "python %d.%d" % _sys.version_info[:2],
        "no_medido": [
            "la publicacion del ancla en el remoto se declara; este acto no alcanza la red",
            "la independencia del verificador: es el mismo arbol que emitio la pagina",
        ],
    }


def _cuerpo(contrafirma, decl):
    return {
        "contrafirma": contrafirma.cuerpo(),
        "repositorio": decl["repositorio"],
        "ancla": decl["ancla"],
        "ruta": decl["ruta"],
        "entorno": _entorno(),
    }


def _pagina(cuerpo):
    return _json.dumps(cuerpo, indent=2, ensure_ascii=False, sort_keys=True)


def _adjudicar(contrafirma, decl):
    """La verificación en frío: ¿la contrafirma cubre la página que tengo delante?"""

    datos = _bytes_de_enfrente(decl)
    if datos is None:
        return VeredictoDeAncla.NO_MEDIDA
    enfrente = desde_cuerpo(datos)
    resultado = verificar_contrafirma(enfrente, contrafirma)
    if isinstance(resultado, Divergencia):
        print(
            "REFUTA | %s | esperado %s medido %s"
            % (resultado.campo, resultado.esperado, resultado.medido)
        )
        return VeredictoDeAncla.REFUTA
    print(
        "CONFIRMA | la contrafirma cubre la pagina de enfrente | %s"
        % contrafirma.digest_del_predicado.digest
    )
    return VeredictoDeAncla.VIGENTE


def _cierre(veredicto, detalle):
    """Publica el veredicto de ancla y lo traduce a RC.

    Los cuatro valores salen por la línea `VEREDICTO DE ANCLA`, no por el código
    de salida: `RANCIO` y `REFUTA` comparten RC 1 porque los dos son "no está
    vigente", y quien tenga que decidir entre re-emitir y auditar lee la línea.
    """

    print("VEREDICTO DE ANCLA | %s | %s" % (veredicto.value, detalle))
    return 0 if veredicto is VeredictoDeAncla.VIGENTE else 1


def main(argumentos):
    comprobar = "--check" in argumentos
    decl = _declaracion()
    contrafirma = _acto(decl)
    pagina = _pagina(_cuerpo(contrafirma, decl))
    print("MEDICION | digest del predicado | %s" % contrafirma.digest_del_predicado.digest)
    print("MEDICION | ancla | %s" % contrafirma.ancla)
    print("MEDICION | veredicto adjudicado | %s" % contrafirma.veredicto.value)
    if comprobar:
        if not CONJUNTO.exists():
            print("FALTA | la contrafirma emitida no existe | %s" % CONJUNTO.name)
            return _cierre(VeredictoDeAncla.NO_MEDIDA, "no hay contrafirma emitida que comparar")
        if CONJUNTO.read_text(encoding="utf-8") != pagina + "\n":
            print("DIVERGE | la contrafirma emitida no es la de este acto | %s" % CONJUNTO.name)
            return _cierre(VeredictoDeAncla.REFUTA, "el archivo emitido no declara este acto")
        print("REPRODUCE | contrafirma-censo.json | %s" % contrafirma.digest_del_predicado.digest)
    else:
        CONJUNTO.write_text(pagina + "\n", encoding="utf-8")
        print(
            "EMITE | contrafirma-censo.json | %d lineas / %d B"
            % (pagina.count("\n") + 1, len(pagina.encode("utf-8")) + 1)
        )
    veredicto = _mismo_acto(decl, contrafirma)
    if veredicto is VeredictoDeAncla.VIGENTE:
        veredicto = _adjudicar(contrafirma, decl)
    return _cierre(veredicto, "ancla %s sobre %s" % (decl["ancla"][:12], decl["ruta"]))


if __name__ == "__main__":
    try:
        raise SystemExit(main(_sys.argv[1:]))
    except ContratoViolado as exc:
        print("CONTRATO | %s" % exc)
        raise SystemExit(2)
