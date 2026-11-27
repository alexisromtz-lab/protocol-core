"""test_version.py — P-107: una sola version del arbol, y el padron que la vigila.

Motor declarado de la corrida:

    python3 -B -m unittest discover -s tests

QUE MIDE. Que las nueve lineas de este arbol que declaran la version digan la
misma, y que la lista de esas nueve lineas **no pueda quedarse corta**: el
descubrimiento barre todos los archivos rastreados buscando la cadena de la
version y exige que el resultado sea exactamente el padron. Un padron escrito a
mano que solo se comprueba a si mismo no vigila nada; lo que lo vuelve falsable
es que un sitio nuevo —o uno que se olvido registrar— aparezca en el barrido y
no en la tabla.

EL DEFECTO QUE ESTE TEST EXISTE PARA IMPEDIR. El 27-Nov-2026 el tag `v0.1.1`
apuntaba a un arbol cuyos metadatos declaraban `0.1.0`: la identidad de la
version etiquetada no era reproducible desde el arbol. Ese defecto no es de
esta prueba —un tag es un objeto de git, no un archivo— pero si es de su
familia: una version declarada en varios sitios que diverge sin lector.

NO CUBIERTO (lista cerrada):

1. El tag. Un tag no vive dentro del arbol, asi que ningun archivo del arbol
   puede declararlo ni comprobarlo sin mentir. Se mide fuera, con
   `git describe --tags --exact-match` sobre el commit sellado.
2. Las cifras ajenas a la version que envejecieron en el mismo README —el
   numero de pruebas, el de archivos de `tests/`— y el `requires-python`
   declarado frente al interprete con el que se corre: son deuda declarada, no
   defecto de este test, y arreglarlas aqui seria medir otra cosa.
3. Que la version sea la *correcta*: eso lo decide quien publica. Aqui solo se
   mide que sea **una**.
"""

from __future__ import annotations

import os as _os
import re as _re
import subprocess as _subprocess
import sys as _sys
import unittest as _unittest
from typing import Dict, List, Tuple

_RAIZ = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
_SRC = _os.path.join(_RAIZ, "src")
if _SRC not in _sys.path:
    _sys.path.insert(0, _SRC)

from protocol import __version__ as _VERSION_DEL_ARBOL  # noqa: E402

# (ruta relativa, numero de linea 1-based, patron con un solo grupo de captura)
# Cada fila es un sitio que un lector puede leer: la cabecera del README, el
# metadato del paquete, el campo de citacion, el titulo del aviso.
_DECLARACIONES: Tuple[Tuple[str, int, str], ...] = (
    ("pyproject.toml", 38, r'^version = "([^"]+)"$'),
    ("src/protocol/__init__.py", 17, r'^__version__ = "([^"]+)"$'),
    ("README.md", 3, r"— Versión (\S+)\*\*$"),
    ("README.md", 9, r"^- \*\*Versión\*\*: `([^`]+)`"),
    ("README.md", 58, r'print\(protocol\.__version__\)"\s+# (\S+)$'),
    ("SPEC.md", 3, r"^\*\*Versión\*\* (\S+) ·"),
    ("CITATION.cff", 39, r"protocol-core (\S+) \(Materia A\)\"$"),
    ("CITATION.cff", 41, r'^version: "([^"]+)"$'),
    ("NOTICE", 1, r"^protocol-core (\S+) — NOTICE$"),
)

_SEMVER = _re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")


def _rastreados() -> List[str]:
    salida = _subprocess.run(
        ["git", "ls-files"],
        cwd=_RAIZ,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return [ruta for ruta in salida.split("\n") if ruta]


def _lineas(ruta: str) -> List[str]:
    with open(_os.path.join(_RAIZ, ruta), "r", encoding="utf-8") as maneja:
        return maneja.read().split("\n")


def _declarado(ruta: str, numero: int, patron: str) -> str:
    lineas = _lineas(ruta)
    if numero > len(lineas):
        raise AssertionError("%s tiene %d lineas; el padron cita la %d" % (ruta, len(lineas), numero))
    coincidencias = _re.findall(patron, lineas[numero - 1])
    if len(coincidencias) != 1:
        raise AssertionError(
            "%s:%d declara %d veces la version; el patron tiene que casar una sola"
            % (ruta, numero, len(coincidencias))
        )
    return coincidencias[0]


class TestUnaSolaVersion(_unittest.TestCase):
    def test_p107a_la_version_del_arbol_es_un_semver(self) -> None:
        self.assertRegex(_VERSION_DEL_ARBOL, _SEMVER)

    def test_p107b_los_nueve_sitios_declaran_la_misma(self) -> None:
        for ruta, numero, patron in _DECLARACIONES:
            with self.subTest(ruta=ruta, linea=numero):
                self.assertEqual(_declarado(ruta, numero, patron), _VERSION_DEL_ARBOL)

    def test_p107c_el_padron_es_exactamente_lo_que_el_barrido_encuentra(self) -> None:
        """El falsificador del padron: un sitio sin registrar aparece en el barrido."""

        esperado = {(ruta, numero) for ruta, numero, _ in _DECLARACIONES}
        observado = set()
        for ruta in _rastreados():
            try:
                with open(_os.path.join(_RAIZ, ruta), "r", encoding="utf-8") as maneja:
                    texto = maneja.read()
            except (UnicodeDecodeError, IsADirectoryError, FileNotFoundError):
                continue
            for numero, linea in enumerate(texto.split("\n"), 1):
                if _VERSION_DEL_ARBOL in linea:
                    observado.add((ruta, numero))
        self.assertEqual(
            sorted(observado),
            sorted(esperado),
            "el barrido y el padron discrepan: un sitio declara la version sin estar en la tabla, o la tabla cita una linea que ya no la declara",
        )

    def test_p107d_ningun_sitio_sigue_publicando_la_version_anterior(self) -> None:
        """Un cambio de version a medias deja dos verdades; aqui se mide la de antes."""

        anteriores = [version for version in ("0.1.0", "0.1.1") if version != _VERSION_DEL_ARBOL]
        for ruta, numero, patron in _DECLARACIONES:
            visto = _declarado(ruta, numero, patron)
            with self.subTest(ruta=ruta, linea=numero):
                self.assertNotIn(visto, anteriores)

    def test_p107e_el_padron_cubre_las_seis_rutas_y_no_se_repite(self) -> None:
        rutas = {ruta for ruta, _, _ in _DECLARACIONES}
        self.assertEqual(len(rutas), 6)
        self.assertEqual(len(set(_DECLARACIONES)), len(_DECLARACIONES))
        self.assertEqual(len(_DECLARACIONES), 9)

    def test_p107f_el_sitio_canonico_es_el_del_paquete(self) -> None:
        """Los demas sitios citan; el paquete es el que un import lee."""

        self.assertIn(("src/protocol/__init__.py", 17), {(r, n) for r, n, _ in _DECLARACIONES})
        self.assertEqual(_declarado("src/protocol/__init__.py", 17, r'^__version__ = "([^"]+)"$'), _VERSION_DEL_ARBOL)


class TestElTagNoSeLeeDesdeDentro(_unittest.TestCase):
    def test_p107g_el_limite_esta_declarado_y_no_se_puede_medir_aqui(self) -> None:
        """El ancla de la version es un objeto de git: se mide fuera, no en el arbol."""

        metadatos: Dict[str, str] = {}
        for ruta, numero, patron in _DECLARACIONES:
            metadatos.setdefault(ruta, _declarado(ruta, numero, patron))
        self.assertTrue(all(valor == _VERSION_DEL_ARBOL for valor in metadatos.values()))
        self.assertNotIn(".git", _rastreados())
