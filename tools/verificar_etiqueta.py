"""verificar_etiqueta.py — el nombre de la etiqueta y el arbol que apunta dicen lo mismo.

QUE MIDE. Para cada etiqueta `vX.Y.Z`, la version que declara **el arbol del
commit apuntado** —leida con `git show <commit>:<ruta>`, nunca el directorio de
trabajo— y la compara con el nombre de la propia etiqueta. Una etiqueta que
declara otra cosa publica una identidad que nadie puede reproducir desde el
arbol.

EL DEFECTO QUE ESTE ACTO EXISTE PARA IMPEDIR. `tests/test_version.py` mide las
nueve lineas del arbol entre si; una etiqueta no es una linea de ningun archivo,
asi que ninguna prueba del arbol puede verla — y ninguna la vio: la etiqueta
`v0.1.1` apunto durante semanas a un arbol que declaraba `0.1.0`, y el defecto se
repitio al reetiquetar dentro de la misma sesion. El lector tiene que estar fuera
del arbol y correr **antes** del push; despues solo queda descubrirlo.

MODO:
    python3 -B tools/verificar_etiqueta.py --todas
    python3 -B tools/verificar_etiqueta.py --tag v0.2.0 --tag v0.1.0
    python3 -B tools/verificar_etiqueta.py --pre-push     # protocolo de git, stdin
    python3 -B tools/verificar_etiqueta.py --instalar     # escribe .git/hooks/pre-push

Opciones: `--raiz RUTA` (por defecto, la del archivo), `--json`.

RC — la escalera de `protocol.predicado.CodigoDeActo`, importada y no copiada:
`0` REPRODUCE (todas coinciden, o la retirada esta bien hecha y solo informa) ·
`1` REFUTA (una etiqueta publica una version que su arbol no declara, o un
nombre retirado volvio a publicarse: actua quien lo publico) · `2` RANCIO (la
lapida registra otra version que la que declara el objeto que sostiene: actua
quien tiene el registro, y re-emitirlo es gratis) · `3` NO_MEDIDO (no se pudo
juzgar: ninguna etiqueta, un arbol sin version declarada, o una lapida cuyo
sujeto no viaja en este clon) · `64` CONTRATO (uso).
`NO_MEDIDO` nunca degrada a `0`: un padron vacio no es un padron limpio. Ni
`RANCIO` ni `NO_MEDIDO` se disfrazan de `REFUTA`: cada codigo dice quien tiene
que actuar, y el `2` de este acto no significa lo mismo que el `3` de otro.
En `--pre-push` un push sin etiquetas no tiene sujeto y sale `0`: la guarda no
opina sobre lo que no mide, y bloquear un push de ramas seria un falso rojo.

LA ESCALERA VIVE EN EL NUCLEO, NO AQUI. Este acto no trae su propio dialecto:
importa `CodigoDeActo` de `src/protocol` **del arbol del instrumento** —nunca
del arbol medido (`--raiz`), porque el contrato de quien actua es del acto y no
del sujeto— y declara `dont_write_bytecode` antes de importar, porque el acto de
censo cuenta `__pycache__` como entrada de directorio y se para con `OBSERVADOR`
(65): un instrumento no ensucia el universo que mide.

RETIRADAS. Una etiqueta cuyo nombre contradice a su arbol no se arregla sin
reescribir el commit que la sostiene, asi que se **retira**: se borra el nombre
del remoto (`git push origin :refs/tags/<t>`), se conserva el objeto en
`refs/tags-retirados/<t>` —fuera de `refs/tags/`, invisible a `git tag -l` y a
`git push --tags`— y se registra en `examples/etiquetas-retiradas.json`. El
registro no es una promesa: `--todas` vuelve a medirlo y acusa `REAPARECIDA` si
el nombre regresa y `RETIRADA_RANCIA` si el objeto o la version registrada ya no
coinciden. Retirar sin registrar deja el defecto sin lector; registrar sin
volver a medir deja una excepcion permanente.

QUE VIAJA Y QUE NO. Un `git clone` no transporta `refs/tags-retirados/`: solo
trae `refs/heads/*` y `refs/tags/*`. La lapida se midio por primera vez en un
clon en frio y salio `RETIRADA_RANCIA` sobre un arbol intacto —un rojo por la
ausencia del transporte, no por un defecto—, que es la forma exacta del falso
rojo que este acto prohibe en `--pre-push`. Por eso la lapida se mide en tres
escalones, del mas fuerte al mas debil: (1) el ref fuera de banda, si el clon lo
trajo; (2) el commit registrado, que **si** viaja porque la etiqueta apuntaba a
un commit de la historia; (3) nada de los dos, que es `RETIRADA_NO_MEDIDA` —RC 3,
con la orden de medida impresa— y nunca un cero ni una rancia. Un rojo se gana
midiendo; no se hereda de no haber medido.

LIMITES DECLARADOS (lista cerrada):

1. Mide la coincidencia nombre/arbol, no que la version sea la correcta.
2. Sigue una etiqueta anotada hasta su commit; no juzga firmas ni el mensaje.
3. Solo entiende `vX.Y.Z`. Un nombre que no case se publica `IGNORADA`, no se
   aprueba: el universo medido se declara.
4. No coteja una pagina contra un arbol, asi que no tiene `--check`: su
   universo son las etiquetas y la lapida del clon que lo corre, y un clon que
   no las trae mide un universo vacio, que es `NO_MEDIDO` y nunca `0`.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from typing import Dict, List, Optional, Sequence, Tuple

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# El censo cuenta el bytecode como suciedad del universo y se para con
# `OBSERVADOR` (65). Este acto importa el nucleo, asi que se declara antes del
# import y no despues de haber ensuciado el arbol.
sys.dont_write_bytecode = True
_SRC = os.path.join(_RAIZ, "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)
try:
    from protocol.predicado import CodigoDeActo  # noqa: E402  (despues del ajuste de `sys.path`)
except Exception as error:  # pragma: no cover  (arbol incompleto: no hay acto)
    # Sin escalera no se puede nombrar el fallo, y se nombra con el mismo `64`
    # que la escalera reserva a quien llamo: un instrumento incompleto no
    # informa de un arbol roto.
    print("NO INSTALADO: falta la escalera de `protocol.predicado` (%s)" % error, file=sys.stderr)
    sys.exit(64)

_CANONICO = "src/protocol/__init__.py"
_ALTERNO = "pyproject.toml"
_RETIRADAS = os.path.join("examples", "etiquetas-retiradas.json")
_ESPACIO_RETIRADAS = "refs/tags-retirados/"
_PATRON_CANONICO = re.compile(r'^__version__ = "([^"]+)"$', re.MULTILINE)
_PATRON_ALTERNO = re.compile(r'^version = "([^"]+)"$', re.MULTILINE)
_PATRON_ETIQUETA = re.compile(r"^v(\d+\.\d+\.\d+)$")
_MARCA = "instalado por tools/verificar_etiqueta.py"

COINCIDE = "COINCIDE"
DIVERGE = "DIVERGE"
NO_MEDIDO = "NO_MEDIDO"
IGNORADA = "IGNORADA"
RETIRADA = "RETIRADA"
REAPARECIDA = "REAPARECIDA"
RETIRADA_RANCIA = "RETIRADA_RANCIA"
RETIRADA_NO_MEDIDA = "RETIRADA_NO_MEDIDA"

#: Que codigo reclama cada veredicto. La escalera no ordena por gravedad sino
#: por quien tiene que actuar, y por eso `RETIRADA` —un nombre que ya no esta—
#: informa y no condena: el acto esta hecho. `RETIRADA_RANCIA` es `RANCIO` y no
#: `REFUTA` porque lo que no cuadra es el **registro** contra el objeto que
#: sostiene, y el registro se re-emite; `REAPARECIDA` es `REFUTA` porque el
#: nombre vivo contradice una retirada declarada y eso se audita.
_DEL_VEREDICTO = {
    COINCIDE: CodigoDeActo.REPRODUCE,
    RETIRADA: CodigoDeActo.REPRODUCE,
    DIVERGE: CodigoDeActo.REFUTA,
    REAPARECIDA: CodigoDeActo.REFUTA,
    RETIRADA_RANCIA: CodigoDeActo.RANCIO,
    IGNORADA: CodigoDeActo.NO_MEDIDO,
    NO_MEDIDO: CodigoDeActo.NO_MEDIDO,
    RETIRADA_NO_MEDIDA: CodigoDeActo.NO_MEDIDO,
}

#: Los veredictos que este acto puede publicar. P-109 exige que `_DEL_VEREDICTO`
#: los cubra todos: un veredicto sin fila cae a `NO_MEDIDO`, que no dice verde,
#: pero la tabla incompleta es un defecto del acto y se acusa en la suite.
_VEREDICTOS = (
    COINCIDE,
    DIVERGE,
    NO_MEDIDO,
    IGNORADA,
    RETIRADA,
    REAPARECIDA,
    RETIRADA_RANCIA,
    RETIRADA_NO_MEDIDA,
)

#: Precedencia de la actuacion, de la mas fuerte a la mas debil: una refutacion
#: no se tapa con una rancia, y una rancia no se tapa con un no medido. Un censo
#: con una etiqueta refutada y otra sin medir esta refutado, porque re-emitir no
#: arregla una identidad falsa. El orden no es el de la escalera.
_PRECEDENCIA = (CodigoDeActo.REFUTA, CodigoDeActo.RANCIO, CodigoDeActo.NO_MEDIDO)


def _git(raiz: str, *argumentos: str) -> Tuple[int, str, str]:
    proceso = subprocess.run(
        ["git"] + list(argumentos),
        cwd=raiz,
        capture_output=True,
        text=True,
    )
    return proceso.returncode, proceso.stdout, proceso.stderr


def _blob(raiz: str, commit: str, ruta: str) -> Optional[str]:
    codigo, salida, _ = _git(raiz, "show", "%s:%s" % (commit, ruta))
    return salida if codigo == 0 else None


def _declarada(raiz: str, commit: str) -> Tuple[Optional[str], str]:
    """La version que el arbol del commit declara, leida del objeto y no del disco."""

    canonico = _PATRON_CANONICO.search(_blob(raiz, commit, _CANONICO) or "")
    alterno = _PATRON_ALTERNO.search(_blob(raiz, commit, _ALTERNO) or "")
    if canonico and alterno and canonico.group(1) != alterno.group(1):
        return None, "el arbol se declara dos versiones: %s y %s" % (
            canonico.group(1),
            alterno.group(1),
        )
    if canonico:
        return canonico.group(1), ""
    if alterno:
        return alterno.group(1), ""
    return None, "el arbol apuntado no declara la version"


def _fila(
    etiqueta: str,
    commit: Optional[str],
    declara: Optional[str],
    veredicto: str,
    causa: str,
) -> Dict[str, object]:
    return {
        "etiqueta": etiqueta,
        "commit": commit,
        "declara": declara,
        "veredicto": veredicto,
        "causa": causa,
    }


def medir(raiz: str, etiqueta: str, commit: Optional[str] = None) -> Dict[str, object]:
    if commit is None:
        codigo, resuelto, _ = _git(raiz, "rev-parse", "--verify", "%s^{commit}" % etiqueta)
        if codigo != 0:
            return _fila(etiqueta, None, None, NO_MEDIDO, "no existe o no apunta a un commit")
        commit = resuelto.strip()
    version, causa = _declarada(raiz, commit)
    if version is None:
        return _fila(etiqueta, commit, None, NO_MEDIDO, causa)
    nombre = _PATRON_ETIQUETA.match(etiqueta)
    if nombre is None:
        return _fila(etiqueta, commit, version, IGNORADA, "el nombre no es vX.Y.Z")
    if nombre.group(1) != version:
        return _fila(
            etiqueta,
            commit,
            version,
            DIVERGE,
            "la etiqueta dice %s y el arbol declara %s" % (nombre.group(1), version),
        )
    return _fila(etiqueta, commit, version, COINCIDE, "")


def _registro_de_retiradas(raiz: str) -> List[Dict[str, object]]:
    ruta = os.path.join(raiz, _RETIRADAS)
    if not os.path.exists(ruta):
        return []
    with open(ruta, "r", encoding="utf-8") as maneja:
        datos = json.load(maneja)
    return list(datos.get("retiradas", []))


def auditar_retiradas(raiz: str, filas: List[Dict[str, object]]) -> List[Dict[str, object]]:
    """Vuelve a medir cada retirada registrada: el objeto sobrevive, el nombre no.

    Tres formas de que la lapida mienta, y las tres se acusan: el nombre
    retirado sigue publicado (`REAPARECIDA`), el objeto ya no esta donde el
    registro dice, o el arbol de ese objeto declara otra version que la
    registrada (`RETIRADA_RANCIA`). Una retirada que nadie remide es una
    excepcion permanente con mejor redaccion.
    """

    for entrada in _registro_de_retiradas(raiz):
        nombre = str(entrada["etiqueta"])
        esperado = str(entrada.get("declara_en_su_arbol", ""))
        objeto = str(entrada.get("objeto", ""))
        if _git(raiz, "show-ref", "--verify", "--quiet", "refs/tags/" + nombre)[0] == 0:
            filas.append(
                _fila(nombre, None, None, REAPARECIDA, "el nombre retirado sigue publicado en refs/tags/")
            )
            continue
        referencia = _ESPACIO_RETIRADAS + nombre
        codigo_ref, oid, _ = _git(raiz, "rev-parse", "--verify", "--quiet", referencia)
        if codigo_ref == 0 and oid.strip() != objeto:
            filas.append(
                _fila(nombre, oid.strip(), None, RETIRADA_RANCIA, "%s ya no apunta al objeto registrado" % referencia)
            )
            continue
        # Escalon 1: el objeto anotado, si este clon lo tiene —por el ref de
        # fuera de banda o porque su ODB todavia lo guarda—.
        codigo_commit, commit, _ = _git(raiz, "rev-parse", "--verify", "--quiet", objeto + "^{commit}")
        nota = ""
        if codigo_commit != 0:
            # Escalon 2: el commit declarado. La etiqueta apuntaba a un commit de
            # la historia, y la historia si viaja en un clone por defecto.
            codigo_commit, commit, _ = _git(
                raiz, "rev-parse", "--verify", "--quiet", str(entrada.get("commit", "")) + "^{commit}"
            )
            if codigo_commit != 0:
                # Escalon 3: ni el objeto ni el commit. No es una rancia: es que
                # este clon no trae el sujeto, y se dice como se mide.
                filas.append(
                    _fila(
                        nombre,
                        None,
                        None,
                        RETIRADA_NO_MEDIDA,
                        "este clon no trae %s ni el commit registrado; medir con: "
                        "git fetch origin '%s*:%s*'" % (referencia, _ESPACIO_RETIRADAS, _ESPACIO_RETIRADAS),
                    )
                )
                continue
            nota = " (sin %s en este clon: se mide el commit declarado, que si viaja)" % referencia
        version, causa = _declarada(raiz, commit.strip())
        if version != esperado:
            filas.append(
                _fila(
                    nombre,
                    commit.strip(),
                    version,
                    RETIRADA_RANCIA,
                    "la retirada registra %s y su arbol declara %s (%s)%s"
                    % (esperado, version, causa or "sin causa", nota),
                )
            )
            continue
        filas.append(
            _fila(
                nombre,
                commit.strip(),
                version,
                RETIRADA,
                "retirada %s: %s%s" % (entrada.get("retirada", "sin fecha"), entrada.get("por_que", ""), nota),
            )
        )
    return filas


def _todas(raiz: str) -> List[str]:
    codigo, salida, _ = _git(raiz, "tag", "-l")
    if codigo != 0:
        return []
    return [nombre for nombre in salida.split("\n") if nombre]


def _desde_prepush(raiz: str, lineas: Sequence[str]) -> List[Dict[str, object]]:
    """Lee el protocolo de git: `<ref local> <oid local> <ref remoto> <oid remoto>`."""

    filas: List[Dict[str, object]] = []
    for linea in lineas:
        partes = linea.split()
        if len(partes) != 4:
            continue
        ref_local, oid_local, ref_remoto, _ = partes
        if ref_local == "(delete)" or set(oid_local) == {"0"}:
            continue
        if not ref_remoto.startswith("refs/tags/"):
            continue
        filas.append(medir(raiz, ref_remoto[len("refs/tags/") :], oid_local))
    return filas


def _codigo(filas: Sequence[Dict[str, object]]) -> CodigoDeActo:
    """El codigo que reclama la actuacion, con el orden declarado en `_PRECEDENCIA`.

    Sin universo no hay verde: un padron vacio no es un padron limpio. Un
    veredicto que no tenga fila en `_DEL_VEREDICTO` no se adivina: cae a
    `NO_MEDIDO`, que nunca dice verde.
    """

    if not filas:
        return CodigoDeActo.NO_MEDIDO
    reclamados = {
        _DEL_VEREDICTO.get(str(fila["veredicto"]), CodigoDeActo.NO_MEDIDO) for fila in filas
    }
    for codigo in _PRECEDENCIA:
        if codigo in reclamados:
            return codigo
    return CodigoDeActo.REPRODUCE


def _hook(raiz: str) -> int:
    ruta = os.path.join(raiz, ".git", "hooks", "pre-push")
    texto = (
        "#!/bin/sh\n"
        "# %s -- no editar a mano: vuelve a correr --instalar\n"
        'exec python3 -B "$(git rev-parse --show-toplevel)/tools/verificar_etiqueta.py" --pre-push\n'
        % _MARCA
    )
    if os.path.exists(ruta):
        with open(ruta, "r", encoding="utf-8") as maneja:
            previo = maneja.read()
        if _MARCA not in previo:
            print("NO INSTALADO: %s ya existe y no es de este actor." % ruta, file=sys.stderr)
            return int(CodigoDeActo.CONTRATO)
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as maneja:
        maneja.write(texto)
    os.chmod(ruta, 0o755)
    print("INSTALADO: %s" % ruta)
    return int(CodigoDeActo.REPRODUCE)


def _uso() -> int:
    print(__doc__, file=sys.stderr)
    return int(CodigoDeActo.CONTRATO)


def main(argumentos: Sequence[str]) -> int:
    raiz = _RAIZ
    etiquetas: List[str] = []
    todas = False
    prepush = False
    instalar = False
    como_json = False

    pendientes = list(argumentos)
    while pendientes:
        argumento = pendientes.pop(0)
        if argumento == "--todas":
            todas = True
        elif argumento == "--pre-push":
            prepush = True
        elif argumento == "--instalar":
            instalar = True
        elif argumento == "--json":
            como_json = True
        elif argumento == "--tag" and pendientes:
            etiquetas.append(pendientes.pop(0))
        elif argumento == "--raiz" and pendientes:
            raiz = os.path.abspath(pendientes.pop(0))
        else:
            return _uso()

    if instalar:
        return _hook(raiz)

    if prepush:
        filas = _desde_prepush(raiz, sys.stdin.read().split("\n"))
        if not filas:
            print("SIN ETIQUETAS EN ESTE PUSH: el acto no tiene sujeto y no opina (RC 0)")
            return int(CodigoDeActo.REPRODUCE)
    elif todas:
        filas = [medir(raiz, nombre) for nombre in _todas(raiz)]
        filas = auditar_retiradas(raiz, filas)
    elif etiquetas:
        filas = [medir(raiz, nombre) for nombre in etiquetas]
    else:
        return _uso()

    codigo = _codigo(filas)

    if como_json:
        print(json.dumps({"filas": filas, "rc": int(codigo)}, ensure_ascii=False, indent=2))
        return codigo

    for fila in filas:
        print(
            "%-8s %-24s declara=%-8s %s"
            % (
                fila["veredicto"],
                fila["etiqueta"],
                fila["declara"] if fila["declara"] else "-",
                fila["causa"],
            )
        )
    cuenta: Dict[str, int] = {}
    for fila in filas:
        cuenta[str(fila["veredicto"])] = cuenta.get(str(fila["veredicto"]), 0) + 1
    print(
        "RESUMEN: %d etiquetas · %s · RC %d"
        % (
            len(filas),
            " · ".join("%s=%d" % (clave, cuenta[clave]) for clave in sorted(cuenta)),
            codigo,
        )
    )
    return codigo


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
