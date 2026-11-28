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

import importlib.util
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

_SRC = os.path.join(_RAIZ, "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from protocol.predicado import CodigoDeActo  # noqa: E402  (después del ajuste de `sys.path`)


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


def _registro(raiz):
    """Las filas de la lapida real, para saber que commit deberia viajar."""

    with open(os.path.join(raiz, "examples", "etiquetas-retiradas.json"), encoding="utf-8") as flujo:
        return json.load(flujo)["retiradas"]


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
        """El censo real: ninguna etiqueta publicada contradice a su arbol.

        El censo exige el sujeto entero, y un `--depth 1` no lo trae: el commit
        de la lapida no viaja, la lapida sale `RETIRADA_NO_MEDIDA` (RC 3, el
        `NO_MEDIDO` de la escalera del nucleo) y el censo no puede dar `0`. Ese
        3 se acepta **solo** cuando el commit declarado falta de verdad,
        comprobado aqui con `git rev-parse`; si el commit esta en el ODB y el
        censo aun responde 3, el test cae. Un clon que no trae el sujeto no
        hereda un rojo, pero tampoco se disfraza de cero: la distincion es la
        misma que hace el verificador.
        """

        codigo, salida = self.correr(_RAIZ, "--todas", "--json")
        datos = json.loads(salida)
        graves = [fila for fila in datos["filas"] if fila["veredicto"] in ("DIVERGE", "REAPARECIDA", "RETIRADA_RANCIA")]
        self.assertEqual(graves, [], "etiquetas contradichas: %r" % (graves,))
        faltan = [
            entrada["commit"]
            for entrada in _registro(_RAIZ)
            if _git(_RAIZ, "rev-parse", "--verify", "--quiet", str(entrada["commit"]) + "^{commit}").returncode != 0
        ]
        self.assertEqual(
            codigo,
            int(CodigoDeActo.NO_MEDIDO) if faltan else int(CodigoDeActo.REPRODUCE),
            "%s\ncommits de lapida ausentes: %r" % (salida, faltan),
        )
        self.assertTrue(
            [fila for fila in datos["filas"] if fila["veredicto"] == "COINCIDE"],
            "un censo sin ninguna coincidencia no mide nada: este clon no trae las "
            "etiquetas publicadas —`--depth 1` solo viaja con las que apuntan a la "
            "punta—, asi que el universo del censo es vacio y no hay verde que dar; "
            "se mide con un `git clone` completo",
        )

    def test_p108b_la_etiqueta_que_coincide_coincide(self):
        raiz = self.repo(version="2.0.0")
        _git(raiz, "tag", "v2.0.0")
        codigo, salida = self.correr(raiz, "--todas")
        self.assertEqual(codigo, int(CodigoDeActo.REPRODUCE), salida)
        self.assertIn("COINCIDE", salida)
        self.assertIn("declara=2.0.0", salida)

    def test_p108c_la_etiqueta_que_no_coincide_diverge_y_nombra_las_dos(self):
        """`REFUTA`: la identidad publicada es falsa, y re-emitir no la arregla.

        Par con P-108l: alli lo que no cuadra es el **registro** contra el objeto
        que sostiene, y eso se re-emite; aqui lo que no cuadra es el nombre
        contra el arbol, y eso se audita. Los dos codigos no se confunden.
        """

        raiz = self.repo(version="2.0.0")
        _git(raiz, "tag", "v9.9.9")
        codigo, salida = self.correr(raiz, "--todas")
        self.assertEqual(codigo, int(CodigoDeActo.REFUTA), salida)
        self.assertIn("DIVERGE", salida)
        self.assertIn("la etiqueta dice 9.9.9 y el arbol declara 2.0.0", salida)

    def test_p108d_sin_version_declarada_es_no_medido_y_nunca_cero(self):
        raiz = self.repo()
        _git(raiz, "tag", "v1.0.0")
        codigo, salida = self.correr(raiz, "--todas")
        self.assertEqual(codigo, int(CodigoDeActo.NO_MEDIDO), salida)
        self.assertIn("NO_MEDIDO", salida)
        self.assertIn("no declara la version", salida)

    def test_p108e_lee_el_objeto_y_no_el_directorio_de_trabajo(self):
        """El falsificador del atajo: el disco dice otra cosa y el veredicto no cambia."""

        raiz = self.repo(version="2.0.0")
        _git(raiz, "tag", "v2.0.0")
        _escribir(os.path.join(raiz, "src", "protocol", "__init__.py"), '__version__ = "7.7.7"\n')
        codigo, salida = self.correr(raiz, "--todas")
        self.assertEqual(codigo, int(CodigoDeActo.REPRODUCE), salida)
        self.assertIn("declara=2.0.0", salida)
        self.assertNotIn("7.7.7", salida)

    def test_p108f_el_ancla_ausente_no_es_un_cero(self):
        """Sin etiquetas no hay universo: NO_MEDIDO, y se dice."""

        raiz = self.repo(version="2.0.0")
        codigo, salida = self.correr(raiz, "--todas")
        self.assertEqual(codigo, int(CodigoDeActo.NO_MEDIDO), salida)
        self.assertEqual(salida.strip(), "RESUMEN: 0 etiquetas ·  · RC 3")


class TestElHookNoBloqueaLoQueNoMide(_Base):
    def test_p108g_un_push_de_ramas_no_se_bloquea(self):
        raiz = self.repo(version="2.0.0")
        linea = "refs/heads/main %s refs/heads/main %s\n" % (_CEROS[:7], _CEROS)
        codigo, salida = self.correr(raiz, "--pre-push", entrada=linea)
        self.assertEqual(codigo, int(CodigoDeActo.REPRODUCE), salida)
        self.assertIn("SIN ETIQUETAS EN ESTE PUSH", salida)

    def test_p108h_un_borrado_de_etiqueta_no_se_juzga(self):
        raiz = self.repo(version="2.0.0")
        linea = "(delete) %s refs/tags/v2.0.0 %s\n" % (_CEROS, _CEROS)
        codigo, salida = self.correr(raiz, "--pre-push", entrada=linea)
        self.assertEqual(codigo, int(CodigoDeActo.REPRODUCE), salida)

    def test_p108i_la_etiqueta_discordante_del_push_se_rechaza(self):
        raiz = self.repo(version="2.0.0")
        _git(raiz, "tag", "v3.0.0")
        oid = _git(raiz, "rev-parse", "v3.0.0").stdout.strip()
        linea = "refs/tags/v3.0.0 %s refs/tags/v3.0.0 %s\n" % (oid, _CEROS)
        codigo, salida = self.correr(raiz, "--pre-push", entrada=linea)
        self.assertEqual(codigo, int(CodigoDeActo.REFUTA), salida)
        self.assertIn("DIVERGE", salida)


class TestLaLapidaSeVuelveAMedir(_Base):
    def test_p108j_la_retirada_bien_hecha_sale_retirada(self):
        raiz = self.repo(version="1.0.0")
        _git(raiz, "tag", "v1.0.0")
        self.retirar(raiz, "v1.0.0", "1.0.0")
        codigo, salida = self.correr(raiz, "--todas")
        self.assertEqual(codigo, int(CodigoDeActo.REPRODUCE), salida)
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
        self.assertEqual(codigo, int(CodigoDeActo.REFUTA), salida)
        self.assertIn("REAPARECIDA", salida)

    def test_p108l_si_el_registro_miente_la_lapida_acusa(self):
        """`RANCIO`: el registro describe otro objeto, y el registro se re-emite.

        La lapida registra `8.8.8` y el arbol que sostiene declara `1.0.0`. Quien
        arregla esto es quien tiene el registro, no quien tiene el arbol: por eso
        `RANCIO` (2) y no `REFUTA` (1), que es lo que publica P-108c cuando el
        nombre vivo contradice a su arbol.
        """

        raiz = self.repo(version="1.0.0")
        _git(raiz, "tag", "v1.0.0")
        self.retirar(raiz, "v1.0.0", "8.8.8")
        codigo, salida = self.correr(raiz, "--todas")
        self.assertEqual(codigo, int(CodigoDeActo.RANCIO), salida)
        self.assertIn("RETIRADA_RANCIA", salida)
        self.assertIn("la retirada registra 8.8.8 y su arbol declara 1.0.0", salida)


class TestLaLapidaEnUnClonQueNoTraeElRefDeFueraDeBanda(_Base):
    """El tercer escalon: `git clone` no transporta `refs/tags-retirados/`.

    Medido en un clon frio por HTTPS: el ref de fuera de banda no llega, el
    commit si (esta en la historia), y la primera version del verificador
    publico `RETIRADA_RANCIA` —RC 1— sobre un arbol intacto. Era un rojo
    heredado de no haber traido el sujeto, no de haberlo medido.
    """

    def test_p108m_sin_el_ref_pero_con_el_commit_la_retirada_se_mide(self):
        """Escalon 2: el commit viaja, y basta para no mentir sobre la version."""

        raiz = self.repo(version="1.0.0")
        _git(raiz, "tag", "-a", "v1.0.0", "-m", "etiqueta anotada, como la real")
        self.retirar(raiz, "v1.0.0", "1.0.0")
        _git(raiz, "add", "-A")
        _git(raiz, "commit", "-q", "-m", "lapida")
        clon = tempfile.mkdtemp(prefix="protocol-etiqueta-clon-")
        self.addCleanup(shutil.rmtree, clon, True)
        # `--no-local` fuerza el camino de transporte: un clon por defecto solo
        # lleva refs/heads/* y refs/tags/*, asi que el ref de fuera de banda y
        # el objeto anotado (que solo el sostenia) no llegan.
        _git(clon, "clone", "-q", "--no-local", raiz, os.path.join(clon, "frio"))
        frio = os.path.join(clon, "frio")
        self.assertNotEqual(
            _git(frio, "show-ref", "--verify", "--quiet", "refs/tags-retirados/v1.0.0").returncode, 0
        )
        self.assertNotEqual(_git(frio, "rev-parse", "--verify", "--quiet", "v1.0.0").returncode, 0)
        codigo, salida = self.correr(frio, "--todas")
        self.assertEqual(codigo, int(CodigoDeActo.REPRODUCE), salida)
        self.assertIn("RETIRADA ", salida)
        self.assertIn("declara=1.0.0", salida)
        self.assertIn("sin refs/tags-retirados/v1.0.0 en este clon", salida)
        self.assertNotIn("RETIRADA_RANCIA", salida)

    def test_p108n_sin_el_ref_ni_el_commit_es_no_medido_y_nunca_rancia(self):
        """Escalon 3: no medir no es defecto, y no se disfraza de cero."""

        raiz = self.repo(version="1.0.0")
        _escribir(
            os.path.join(raiz, "examples", "etiquetas-retiradas.json"),
            json.dumps(
                {
                    "retiradas": [
                        {
                            "etiqueta": "v1.0.0",
                            "objeto": "1" * 40,
                            "commit": "2" * 40,
                            "declara_en_su_arbol": "1.0.0",
                            "retirada": "2026-11-27",
                            "por_que": "prueba",
                        }
                    ]
                }
            ),
        )
        codigo, salida = self.correr(raiz, "--todas")
        self.assertEqual(codigo, int(CodigoDeActo.NO_MEDIDO), salida)
        self.assertIn("RETIRADA_NO_MEDIDA", salida)
        self.assertIn("git fetch origin", salida)
        self.assertNotIn("RETIRADA_RANCIA", salida)


class TestLaEscaleraEsLaDelNucleo(unittest.TestCase):
    """P-109 — el acto no publica su propio dialecto: lee la escalera del nucleo.

    Medido el 27-Nov-2026, `UBICACION.md` §6.2 declaraba la deuda: este acto y
    los cuatro `--check` hablaban idiomas distintos, y el `2` de aqui
    (`NO_MEDIDO`) significaba lo contrario que el `2` del nucleo (`RANCIO`). Un
    consumidor que solo recibe el entero no podia saber si re-emitir o auditar.
    La cura no es una tabla nueva: es importar la que ya existe, y decirlo.
    """

    def herramienta(self):
        """La herramienta **real**, cargada como modulo y sin ejecutar su `main`."""

        especificacion = importlib.util.spec_from_file_location("etiqueta_bajo_prueba", _HERRAMIENTA)
        modulo = importlib.util.module_from_spec(especificacion)
        previo = sys.dont_write_bytecode
        sys.dont_write_bytecode = True
        self.addCleanup(setattr, sys, "dont_write_bytecode", previo)
        especificacion.loader.exec_module(modulo)
        return modulo

    def test_p109_la_tabla_es_la_del_nucleo_y_cubre_los_ocho_veredictos(self):
        modulo = self.herramienta()
        # El objeto es el mismo, no uno igual: una copia con los mismos numeros
        # vuelve a divergir el dia que el nucleo gane un codigo.
        self.assertIs(modulo.CodigoDeActo, CodigoDeActo)
        self.assertEqual(
            set(modulo._DEL_VEREDICTO),
            set(modulo._VEREDICTOS),
            "un veredicto sin fila en la tabla caeria a `NO_MEDIDO` en silencio",
        )
        esperado = {
            "COINCIDE": 0,
            "RETIRADA": 0,
            "DIVERGE": 1,
            "REAPARECIDA": 1,
            "RETIRADA_RANCIA": 2,
            "IGNORADA": 3,
            "NO_MEDIDO": 3,
            "RETIRADA_NO_MEDIDA": 3,
        }
        self.assertEqual(
            {clave: int(valor) for clave, valor in modulo._DEL_VEREDICTO.items()}, esperado
        )
        # Sin universo no hay verde, y la precedencia no se deja tapar: un censo
        # con una etiqueta refutada y otra sin medir esta refutado.
        self.assertEqual(int(modulo._codigo([])), int(CodigoDeActo.NO_MEDIDO))
        self.assertEqual(
            int(modulo._codigo([{"veredicto": "DIVERGE"}, {"veredicto": "RETIRADA_RANCIA"}])),
            int(CodigoDeActo.REFUTA),
        )
        self.assertEqual(
            int(modulo._codigo([{"veredicto": "RETIRADA_RANCIA"}, {"veredicto": "NO_MEDIDO"}])),
            int(CodigoDeActo.RANCIO),
        )
        self.assertEqual(
            int(modulo._codigo([{"veredicto": "COINCIDE"}, {"veredicto": "RETIRADA"}])),
            int(CodigoDeActo.REPRODUCE),
        )

    def test_p109b_el_acto_no_deja_bytecode_en_el_universo_que_mide(self):
        """Un instrumento que importa el nucleo no puede ensuciarlo al correr.

        El acto de censo cuenta `__pycache__` como entrada de directorio y se
        para con `OBSERVADOR` (65). Se corre la herramienta **sin `-B`** y sin
        `PYTHONDONTWRITEBYTECODE` en el entorno —el caso de quien teclea
        `python3 tools/verificar_etiqueta.py --todas`— sobre un arbol copiado:
        lo que se mira es el arbol copiado, no el del repositorio.

        El prefijo de cache se fija **dentro** de la copia a proposito: el
        Python del sistema en macOS trae `sys.pycache_prefix` apuntando a
        `~/Library/Caches` y sin esta linea la prueba mediria el default del
        interprete —y saldria verde con la guarda quitada—. Con el prefijo
        dentro de la copia, cualquier bytecode del nucleo copiado cae donde se
        busca, en macOS y en Linux.
        """

        copia = tempfile.mkdtemp(prefix="protocol-etiqueta-copia-")
        self.addCleanup(shutil.rmtree, copia, True)
        ignorar = shutil.ignore_patterns("__pycache__", "*.pyc")
        shutil.copytree(os.path.join(_RAIZ, "tools"), os.path.join(copia, "tools"), ignore=ignorar)
        shutil.copytree(os.path.join(_RAIZ, "src"), os.path.join(copia, "src"), ignore=ignorar)
        entorno = dict(os.environ)
        entorno.pop("PYTHONDONTWRITEBYTECODE", None)
        entorno["PYTHONPYCACHEPREFIX"] = os.path.join(copia, ".observador")
        proceso = subprocess.run(
            [
                sys.executable,
                os.path.join(copia, "tools", "verificar_etiqueta.py"),
                "--todas",
                "--raiz",
                _RAIZ,
            ],
            capture_output=True,
            text=True,
            env=entorno,
        )
        self.assertEqual(
            proceso.returncode, int(CodigoDeActo.REPRODUCE), proceso.stdout + proceso.stderr
        )
        # Bytecode de los modulos de la copia, este donde este el prefijo: la
        # biblioteca estandar escriba la suya y no es universo del acto.
        del_acto = [
            os.path.relpath(os.path.join(directorio, nombre), copia)
            for directorio, _, archivos in os.walk(copia)
            for nombre in archivos
            if nombre.endswith(".pyc") and os.sep + "src" + os.sep in os.path.join(directorio, nombre)
        ]
        del_acto += [
            os.path.relpath(os.path.join(directorio, nombre), copia)
            for directorio, subdirectorios, _ in os.walk(copia)
            for nombre in subdirectorios
            if nombre == "__pycache__"
            and os.sep + "src" + os.sep in os.path.join(directorio, nombre)
        ]
        self.assertEqual(
            del_acto, [], "el acto dejo bytecode de su propio nucleo: %r" % (del_acto,)
        )
