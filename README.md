# protocol-core

**Protocolo de Custodia Determinista y Reserva de Ranuras — Versión 0.1.0**

Almacenamiento atómico y auditoría determinista: sustitución atómica de archivos, aislamiento de
manifiestos por namespace, reserva determinista de ranuras y auditoría criptográfica **en frío** (sin
red, sin credenciales, sin re-sellar nada).

- **Versión**: `0.1.0` (congelada `2026-10-09T18:39:38Z`)
- **Python**: `>= 3.11` · **dependencias de ejecución**: ninguna
- **Licencia dual**: el **código** bajo **AGPL-3.0** (`LICENSE`); el **SPEC** bajo
  **CC BY 4.0** (`LICENSE_SPEC_CC-BY-4.0.txt`). Resumen y terceros: `NOTICE`, en este repositorio.
  El acta de la declaración dual vive **fuera** del repositorio, en el expediente de la bóveda:
  `<expediente-de-custodia>/DECLARACION_DE_LICENCIA_DUAL_20261009.md`
  (85 líneas · 3 704 B · sha256 `48252c8b92e17d421a13e8a5a06ab2649250a4ad0c417623ad38ab77f9c17594`).

## Las 13 piezas

```
SPEC.md                  PREDICADO.md             pyproject.toml
src/protocol/__init__.py src/protocol/atomic.py   src/protocol/audit.py
src/protocol/metrics.py  src/protocol/types.py    src/protocol/predicado.py
tests/test_atomic.py     tests/test_audit.py      tests/test_metrics.py
tests/test_predicado.py
examples/emitir_predicado.py + los dos artefactos que emite
```

`PREDICADO.md` es la especificación del Anillo 0 y existe para que un tercero
reimplemente la verificación **sin leer el código**. Si el documento y el módulo
discrepan, manda el documento. `SPEC.md` no se toca: está sellado con fecha
cierta y una sección nueva invalidaría el sello.

## Invariantes (SPEC §3)

`INV_EXCL` (exclusividad en la apertura) · `INV_SPLIT` (partición determinista) · `INV_SELF` (resta
endógena de auto-conteo) · `INV_ISOL` (aislamiento de manifiestos) · `INV_TIME` (validez temporal
acoplada) · y las extensiones declaradas `INV-6` (ficha fuera de banda), `INV-7` (portabilidad de
`T₀`), `INV-8` (lectura no rasgada). El enunciado completo vive en `SPEC.md`.

## Uso

Los comandos se corren **desde la raíz de este repositorio**:

```
python3 -B -m unittest discover -s tests -v                      # 44 pruebas (corrida local: stdlib unittest)
python3 -B examples/emitir_predicado.py                          # emite el recibo del acto: veredicto + página
python3 -B examples/emitir_predicado.py --check                   # REPRODUCE (RC 0) o DIVERGE (RC 1)
PYTHONPATH=src python3 -B -c "import protocol; print(protocol.__version__)"   # 0.1.0
```

**Motor único: `unittest` de la biblioteca estándar.** Los 4 archivos de `tests/` hacen
`import unittest`; 0 de los 11 `.py` rastreados hacen `import pytest`. Lo que el aparato de CI corre es
esa misma suite con `python -m pytest -q --junitxml=/tmp/junit.xml`, donde `pytest` es el **colector**
y el productor del junitxml, no un segundo motor de aserciones. `pytest` lo instala el runner y este
repositorio lo declara como **extra de desarrollo** (`pip install -e .[dev]`), nunca como dependencia
de ejecución.
El veredicto (`Ran 44 tests` · `OK`) sale por **stderr**; las líneas `MEDICION |` de cada prueba salen
por **stdout**.

**Plataformas certificadas de la suite:** linux (CI) y darwin. Medido el 2026-11-24: `os.mkfifo` no
admite `dir_fd` en darwin —`os.supports_dir_fd` no lo lista—, así que el caso T-10(d) crea el FIFO por
la ruta de la raíz efímera y sigue midiendo la barrera del instrumento (`MEDICION | T-10 barrera fifo |
ELOOP`). Sin esa corrección la corrida en darwin terminaba en `FAILED (errors=1)` por una limitación
del fixture, no del motor. Tercera plataforma: `NO_MEDIDO`.

<!-- HUELLA-PROTOCOL-CORE-PYTEST-DEPENDENCIA-DECLARADA-20261020 -->

## El recibo de un acto (Anillo 0)

`src/protocol/predicado.py` compone el enunciado que hace verificable un acto:
**afirmación · entradas · código · entorno · salida · veredicto · eslabón
anterior**, en una página de 61 líneas y 1 881 bytes. El contrato, escrito para
que un tercero lo reimplemente sin leer el código, vive en `PREDICADO.md`; la
proyección a in-toto Statement v1 hace que cualquier pipeline que ya entienda
SLSA/Sigstore lea el `subject` y el `predicateType` sin conversión.

`veredicto` es lo que el productor **reclama**. La adjudicación es otro objeto
—la contrafirma— y es la única que vale ante un tercero. Y una cadena de
digests **sin ancla** prueba coherencia, no autoría: quien reescribe todos los
eslabones recalcula la cadena entera y cuadra. Ese límite está en el contrato y
en una prueba que lo afirma como resultado negativo, no escondido en un README.

El ejemplo es el acto real de este repositorio, no una simulación:

```
python3 -B examples/emitir_predicado.py          # corre la suite, reduce, emite la página
python3 -B examples/emitir_predicado.py --check   # REPRODUCE (RC 0) · DIVERGE (RC 1)
```

El falsador se ve en un byte: se toca cualquier fuente, la suite **sigue verde**
—`salida reproducida | True`— y la página declara `DIVERGE`, porque el árbol ya
no es el que produjo ese veredicto. Un verde sin recibo es exactamente el falso
verde que el recibo existe para nombrar.

**Lo que este módulo no hace:** no firma, no mide el sistema de archivos y no
adjudica. No se simula una firma que no se verifica.

## Sellos de fe pública

Los dos sellos son **externos a este repositorio** y se verifican **en frío**:

| sello | objeto | sha256 | autoridades |
|---|---|---|---|
| A | 14 rutas del núcleo | `ad67ece0099f6a030cbcaedd3a2dc9bc7bcfcf2d448d830c78e608ace24d75ce` | RFC 3161 + OpenTimestamps |
| B | 12 rutas del expediente | `866fda13c41e771ced5f2d2f775398c4ce7c168da17eb6d8e3a6c44e4f508b60` | FreeTSA · Apple · DigiCert · Sectigo + OpenTimestamps |

Llaves de verificación (bóveda canónica de custodia):

```
<expediente-de-sellos>/VERIFICAR_SELLO_A.sh
<expediente-de-sellos>/VERIFICAR_SELLO_B.sh
```

Ninguna de las dos usa internet (salvo la mitad Bitcoin del `.ots`), credenciales ni este archivo:
**el sello prueba CUÁNDO existía el hash**; reproduce el árbol, no la confianza de quien lo firma.

## Regla de custodia

**Ninguna cifra empírica viaja sin su comando, su universo declarado y su hora.** Toda cifra de conteo
caduca al escribirse: su hora es parte de la cifra.
