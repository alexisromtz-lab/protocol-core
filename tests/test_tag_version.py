"""test_tag_version.py — P-108: la etiqueta y su arbol, medidos desde fuera del arbol.

QUE MIDE. Que `tools/verificar_etiqueta.py` juzgue el par (nombre de la
etiqueta, version que declara **el arbol del commit apuntado**) y no otra cosa:
`COINCIDE` cuando coinciden, `DIVERGE` cuando no, `NO_MEDIDO` —nunca `0`—
cuando el arbol apuntado no declara version; que lea el objeto de git y no el
directorio de trabajo; que un push de ramas no quede bloqueado; y que la lapida
de una etiqueta retirada se vuelva a medir en cada corrida.

POR QUE VIVE AQUI Y NO EN EL ARBOL. Una etiqueta es un objeto de git: ningun
archivo del arbol puede declararla ni comprobarla sin mentir. `test_version.py`
mide las nueve lineas del arbol entre si y declara ese hueco como NO CUBIERTO;
esta es la prueba que lo cubre desde fuera, montando repositorios de usar y
tirar para poder fabricar el defecto en vez de esperar a que ocurra.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_HERRAMIENTA = os.path.join(_RAIZ, "tools", "verificar_etiqueta.py")
_CEROS = "0" * 40


def _git(raiz, *argumentos):
    return subprocess.run(
        ["git"] + list(argumentos),
        cwd=raiz,
        capture_output=True,
        text=True,
    )


def _escribir(ruta, texto):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as maneja:
        maneja.write(texto)


class _Base(unittest.TestCase):
    def repo(self, version=None, en_pyproject=None):
        """Un repositorio desechable cuyo arbol declara lo que se le pida."""

        raiz = tempfile.mkdtemp(prefix="protocol-etiqueta-")
        self.addCleanup(shutil.rmtree, raiz, True)
        _git(raiz, "init", "-q")
        _git(raiz, "config", "user.email", "prueba@protocol.invalid")
        _git(raiz, "config", "user.name", "prueba")
        if version is None and en_pyproject is None:
            _escribir(os.path.join(raiz, "README.md"), "# arbol sin version declarada\n")
        if version is not None:
            _escribir(
                os.path.join(raiz, "src", "protocol", "__init__.py"),
                '__version__ = "%s"\n' % version,
            )
        if en_pyproject is not None:
            _escribir(
                os.path.join(raiz, "pyproject.toml"),
                '[project]\nname = "protocol-core"\nversion = "%s"\n' % en_pyproject,
            )
        _git(raiz, "add", "-A")
        _git(raiz, "commit", "-q", "-m", "base")
        return raiz

    def correr(self, raiz, *argumentos, entrada=""):
        proceso = subprocess.run(
            [sys.executable, "-B", _HERRAMIENTA] + list(argumentos) + ["--raiz", raiz],
            capture_output=True,
            text=True,
            input=entrada,
        )
        return proceso.returncode, proceso.stdout

    def retirar(self, raiz, etiqueta, declara):
        """Fabrica una retirada bien hecha: nombre fuera, objeto fuera de refs/tags/."""

        objeto = _git(raiz, "rev-parse", etiqueta).stdout.strip()
        commit = _git(raiz, "rev-parse", etiqueta + "^{commit}").stdout.strip()
        _git(raiz, "tag", "-d", etiqueta)
        _git(raiz, "update-ref", "refs/tags-retirados/" + etiqueta, objeto)
        registro = {
            "retiradas": [
                {
                    "etiqueta": etiqueta,
                    "objeto": objeto,
                    "commit": commit,
                    "declara_en_su_arbol": declara,
                    "retirada": "2026-11-27",
                    "por_que": "prueba",
                }
            ]
        }
        _escribir(os.path.join(raiz, "examples", "etiquetas-retiradas.json"), json.dumps(registro))
        return objeto


class TestElParEtiquetaArbol(_Base):
    def test_p108a_este_repositorio_no_tiene_etiquetas_contradichas(self):
        """El censo real: ninguna etiqueta publicada contradice a su arbol."""

        codigo, salida = self.correr(_RAIZ, "--todas", "--json")
        datos = json.loads(salida)
        graves = [fila for fila in datos["filas"] if fila["veredicto"] in ("DIVERGE", "REAPARECIDA", "RETIRADA_RANCIA")]
        self.assertEqual(graves, [], "etiquetas contradichas: %r" % (graves,))
        self.assertEqual(codigo, 0)
        self.assertTrue(
            [fila for fila in datos["filas"] if fila["veredicto"] == "COINCIDE"],
            "un censo sin ninguna coincidencia no mide nada",
        )

    def test_p108b_la_etiqueta_que_coincide_coincide(self):
        raiz = self.repo(version="2.0.0")
        _git(raiz, "tag", "v2.0.0")
        codigo, salida = self.correr(raiz, "--todas")
        self.assertEqual(codigo, 0, salida)
        self.assertIn("COINCIDE", salida)
        self.assertIn("declara=2.0.0", salida)

    def test_p108c_la_etiqueta_que_no_coincide_diverge_y_nombra_las_dos(self):
        raiz = self.repo(version="2.0.0")
        _git(raiz, "tag", "v9.9.9")
        codigo, salida = self.correr(raiz, "--todas")
        self.assertEqual(codigo, 1, salida)
        self.assertIn("DIVERGE", salida)
        self.assertIn("la etiqueta dice 9.9.9 y el arbol declara 2.0.0", salida)

    def test_p108d_sin_version_declarada_es_no_medido_y_nunca_cero(self):
        raiz = self.repo()
        _git(raiz, "tag", "v1.0.0")
        codigo, salida = self.correr(raiz, "--todas")
        self.assertEqual(codigo, 2, salida)
        self.assertIn("NO_MEDIDO", salida)
        self.assertIn("no declara la version", salida)

    def test_p108e_lee_el_objeto_y_no_el_directorio_de_trabajo(self):
        """El falsificador del atajo: el disco dice otra cosa y el veredicto no cambia."""

        raiz = self.repo(version="2.0.0")
        _git(raiz, "tag", "v2.0.0")
        _escribir(os.path.join(raiz, "src", "protocol", "__init__.py"), '__version__ = "7.7.7"\n')
        codigo, salida = self.correr(raiz, "--todas")
        self.assertEqual(codigo, 0, salida)
        self.assertIn("declara=2.0.0", salida)
        self.assertNotIn("7.7.7", salida)

    def test_p108f_el_ancla_ausente_no_es_un_cero(self):
        """Sin etiquetas no hay universo: NO_MEDIDO, y se dice."""

        raiz = self.repo(version="2.0.0")
        codigo, salida = self.correr(raiz, "--todas")
        self.assertEqual(codigo, 2, salida)
        self.assertEqual(salida.strip(), "RESUMEN: 0 etiquetas ·  · RC 2")


class TestElHookNoBloqueaLoQueNoMide(_Base):
    def test_p108g_un_push_de_ramas_no_se_bloquea(self):
        raiz = self.repo(version="2.0.0")
        linea = "refs/heads/main %s refs/heads/main %s\n" % (_CEROS[:7], _CEROS)
        codigo, salida = self.correr(raiz, "--pre-push", entrada=linea)
        self.assertEqual(codigo, 0, salida)
        self.assertIn("SIN ETIQUETAS EN ESTE PUSH", salida)

    def test_p108h_un_borrado_de_etiqueta_no_se_juzga(self):
        raiz = self.repo(version="2.0.0")
        linea = "(delete) %s refs/tags/v2.0.0 %s\n" % (_CEROS, _CEROS)
        codigo, salida = self.correr(raiz, "--pre-push", entrada=linea)
        self.assertEqual(codigo, 0, salida)

    def test_p108i_la_etiqueta_discordante_del_push_se_rechaza(self):
        raiz = self.repo(version="2.0.0")
        _git(raiz, "tag", "v3.0.0")
        oid = _git(raiz, "rev-parse", "v3.0.0").stdout.strip()
        linea = "refs/tags/v3.0.0 %s refs/tags/v3.0.0 %s\n" % (oid, _CEROS)
        codigo, salida = self.correr(raiz, "--pre-push", entrada=linea)
        self.assertEqual(codigo, 1, salida)
        self.assertIn("DIVERGE", salida)


class TestLaLapidaSeVuelveAMedir(_Base):
    def test_p108j_la_retirada_bien_hecha_sale_retirada(self):
        raiz = self.repo(version="1.0.0")
        _git(raiz, "tag", "v1.0.0")
        self.retirar(raiz, "v1.0.0", "1.0.0")
        codigo, salida = self.correr(raiz, "--todas")
        self.assertEqual(codigo, 0, salida)
        self.assertIn("RETIRADA ", salida)
        self.assertIn("declara=1.0.0", salida)

    def test_p108k_si_el_nombre_reaparece_la_lapida_acusa(self):
        raiz = self.repo(version="1.0.0")
        _git(raiz, "tag", "v1.0.0")
        objeto = _git(raiz, "rev-parse", "v1.0.0").stdout.strip()
        _escribir(
            os.path.join(raiz, "examples", "etiquetas-retiradas.json"),
            json.dumps({"retiradas": [{"etiqueta": "v1.0.0", "objeto": objeto, "declara_en_su_arbol": "1.0.0"}]}),
        )
        codigo, salida = self.correr(raiz, "--todas")
        self.assertEqual(codigo, 1, salida)
        self.assertIn("REAPARECIDA", salida)

    def test_p108l_si_el_registro_miente_la_lapida_acusa(self):
        raiz = self.repo(version="1.0.0")
        _git(raiz, "tag", "v1.0.0")
        self.retirar(raiz, "v1.0.0", "8.8.8")
        codigo, salida = self.correr(raiz, "--todas")
        self.assertEqual(codigo, 1, salida)
        self.assertIn("RETIRADA_RANCIA", salida)
        self.assertIn("la retirada registra 8.8.8 y su arbol declara 1.0.0", salida)
