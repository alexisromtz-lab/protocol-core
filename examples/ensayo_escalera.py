"""examples/ensayo_escalera.py — ensaya la escalera de estados que un guion graba.

Un guion que pone un numero en pantalla y no dice de donde sale es una claim sin
ancla, y este producto se vende precisamente porque sus claims la tienen. Asi que
el guion no transcribe el acto: lo **convoca**. Este ensayo construye sujetos
efimeros y corre `verificar_sello.py` sobre cada uno, de modo que las lineas que
el video muestra son las que imprime este archivo, no las que alguien recordo.

Siete sujetos, cada uno un escalon mas lejos de la verdad:

    intacta          los bytes declarados estan en su ruta
    reubicada        los mismos bytes, otra ruta
    intercambiada    cada digest sigue apareciendo una vez, en la ruta del otro
    divergente       un byte de mas
    entrada invalida no hay manifiesto que adjudicar
    redundancia      los bytes estan y ademas hay copias que nadie declaro
    no_medida        el byte esta en disco y el universo del acto no lo indexa

Los cinco primeros recorren la escalera de veredictos y su codigo de salida
(0 / 0 / 1 / 1 / 2). Los dos ultimos no son veredictos: el sexto es el dato que
exige el barrido completo —cuanto de esto es copia, la pregunta que trae el
cliente— y el septimo es la laguna, un byte que existe en disco y que el universo
del acto declara no indexar.

Uso:

    python3 -B examples/ensayo_escalera.py

RC 0 si los siete sujetos se comportaron como este archivo declara, RC 1 si alguno
no. Ese RC es el falsador del guion: si el acto cambia, el ensayo lo grita antes
que la camara.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ACTO = os.path.join(RAIZ, "examples", "verificar_sello.py")
ALFA = b"alfa\n"
BETA = b"beta\n"
ETIQUETA_SUJETO = "<sujeto>"


def _sha(datos: bytes) -> str:
    return hashlib.sha256(datos).hexdigest()


class Sujeto:
    """Un arbol y su manifiesto, en un directorio que se borra al terminar."""

    def __init__(self, raiz: str) -> None:
        self.raiz = raiz
        os.makedirs(raiz)
        self.manifiesto = os.path.join(raiz, "SHA256SUMS")

    def escribir(self, ruta: str, datos: bytes) -> None:
        destino = os.path.join(self.raiz, ruta)
        carpeta = os.path.dirname(destino)
        if carpeta != self.raiz:
            os.makedirs(carpeta, exist_ok=True)
        with open(destino, "wb") as flujo:
            flujo.write(datos)

    def declarar(self, filas: tuple) -> None:
        with open(self.manifiesto, "w", encoding="utf-8") as flujo:
            for ruta, datos in filas:
                flujo.write("%s  %s\n" % (_sha(datos), ruta))

    def orden(self, manifiesto: str, extra: tuple) -> list:
        return [
            sys.executable,
            "-B",
            ACTO,
            "--manifiesto",
            manifiesto,
            "--raiz",
            self.raiz,
            "--universo",
            "disco",
        ] + list(extra)

    def correr(self, manifiesto: str, extra: tuple) -> tuple:
        corrida = subprocess.run(
            self.orden(manifiesto, extra),
            cwd=RAIZ,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        texto = corrida.stdout.decode("utf-8", "replace")
        # El recibo es lo que va a pantalla; el stream de medicion es del lector.
        recibo = [linea for linea in texto.splitlines() if not linea.startswith("MEDICION |")]
        return corrida.returncode, recibo


def _comando(sujeto: Sujeto, manifiesto: str, extra: tuple) -> str:
    orden = sujeto.orden(manifiesto, extra)
    return " ".join(
        "<acto>" if parte == ACTO else parte.replace(sujeto.raiz, ETIQUETA_SUJETO) for parte in orden[2:]
    )


def _paso(numero: int, total: int, nombre: str, tesis: str, preparar, esperado_rc: int, agujas: tuple) -> bool:
    raiz = tempfile.mkdtemp(prefix="ensayo-%d-" % numero)
    try:
        sujeto, manifiesto, extra = preparar(raiz)
        rc, recibo = sujeto.correr(manifiesto, extra)
        conforme = rc == esperado_rc and all(aguja in "\n".join(recibo) for aguja in agujas)
        print("=== %d/%d · %s — %s" % (numero, total, nombre, tesis))
        print("    $ python3 -B %s" % _comando(sujeto, manifiesto, extra))
        for linea in recibo:
            print("      %s" % linea.replace(sujeto.raiz, ETIQUETA_SUJETO))
        print(
            "    RC %d · esperado %d · %s"
            % (rc, esperado_rc, "OK" if conforme else "NO COINCIDE")
        )
        print("")
        return conforme
    finally:
        shutil.rmtree(raiz, True)


def _sembrar(sujeto: Sujeto) -> None:
    sujeto.escribir("a.md", ALFA)
    sujeto.escribir("b.md", BETA)
    sujeto.declarar((("a.md", ALFA), ("b.md", BETA)))


def _intacta(raiz: str) -> tuple:
    sujeto = Sujeto(os.path.join(raiz, "intacta"))
    _sembrar(sujeto)
    return sujeto, sujeto.manifiesto, ()


def _reubicada(raiz: str) -> tuple:
    sujeto = Sujeto(os.path.join(raiz, "reubicada"))
    _sembrar(sujeto)
    destino = os.path.join(sujeto.raiz, "actas")
    os.makedirs(destino)
    os.rename(os.path.join(sujeto.raiz, "a.md"), os.path.join(destino, "a.md"))
    return sujeto, sujeto.manifiesto, ()


def _intercambiada(raiz: str) -> tuple:
    sujeto = Sujeto(os.path.join(raiz, "intercambiada"))
    _sembrar(sujeto)
    sujeto.escribir("a.md", BETA)
    sujeto.escribir("b.md", ALFA)
    return sujeto, sujeto.manifiesto, ()


def _divergente(raiz: str) -> tuple:
    sujeto = Sujeto(os.path.join(raiz, "divergente"))
    _sembrar(sujeto)
    sujeto.escribir("a.md", ALFA + b".")
    return sujeto, sujeto.manifiesto, ()


def _invalida(raiz: str) -> tuple:
    sujeto = Sujeto(os.path.join(raiz, "invalida"))
    _sembrar(sujeto)
    return sujeto, os.path.join(sujeto.raiz, "no-existe.txt"), ()


def _redundancia(raiz: str) -> tuple:
    sujeto = Sujeto(os.path.join(raiz, "redundancia"))
    _sembrar(sujeto)
    sujeto.escribir("copia/a.md", ALFA)
    return sujeto, sujeto.manifiesto, ("--completo",)


def _no_medida(raiz: str) -> tuple:
    sujeto = Sujeto(os.path.join(raiz, "no_medida"))
    sujeto.escribir("a.md", ALFA)
    sujeto.escribir("b.md", BETA)
    # El byte esta en disco y el universo del acto no lo indexa: `__pycache__`
    # esta en la lista de exclusiones de la caminata. Certificarlo seria firmar
    # sobre lo que el propio instrumento declara no haber mirado.
    sujeto.escribir("__pycache__/x.pyc", b"pyc\n")
    sujeto.declarar((("a.md", ALFA), ("b.md", BETA), ("__pycache__/x.pyc", b"pyc\n")))
    return sujeto, sujeto.manifiesto, ()


PASOS = (
    (
        "intacta",
        "los bytes declarados estan en su ruta",
        _intacta,
        0,
        ("-> intacta", "coste | 2 declaradas | 0 barridas | 2 hasheadas"),
    ),
    (
        "reubicada",
        "los mismos bytes, otra ruta",
        _reubicada,
        0,
        ("-> reubicada", "reubicado a.md -> actas/a.md"),
    ),
    (
        "intercambiada",
        "mismo multiconjunto de digests, biyeccion de rutas rota",
        _intercambiada,
        1,
        ("-> intercambiada", "(ruta ocupada)"),
    ),
    (
        "divergente",
        "un byte de mas",
        _divergente,
        1,
        ("-> divergente", "diverge a.md (bytes alterados)"),
    ),
    (
        "entrada invalida",
        "no hay manifiesto que adjudicar",
        _invalida,
        2,
        ("ENTRADA INVALIDA", "no se puede leer"),
    ),
    (
        "redundancia",
        "los bytes estan, y ademas hay copias que nadie declaro",
        _redundancia,
        0,
        ("-> intacta", "redundancia | %s | 1 declaradas | 2 observadas | a.md, copia/a.md" % _sha(ALFA)),
    ),
    (
        "no_medida",
        "el byte esta en disco y el universo del acto no lo indexa",
        _no_medida,
        1,
        ("-> no_medida", "1 fuera del universo"),
    ),
)


def main(argv: tuple) -> int:
    if argv:
        print("USO | python3 -B examples/ensayo_escalera.py  (sin argumentos)")
        return 2
    total = len(PASOS)
    fallos = []
    for numero, (nombre, tesis, preparar, esperado_rc, agujas) in enumerate(PASOS, start=1):
        if not _paso(numero, total, nombre, tesis, preparar, esperado_rc, agujas):
            fallos.append(nombre)
    if fallos:
        print("ENSAYO | %d/%d | no coinciden: %s | RC 1" % (total - len(fallos), total, ", ".join(fallos)))
        return 1
    print("ENSAYO | %d/%d | los %d sujetos se comportaron como declara este archivo | RC 0" % (total, total, total))
    return 0


if __name__ == "__main__":
    sys.exit(main(tuple(sys.argv[1:])))
