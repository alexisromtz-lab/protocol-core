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

## Las 17 piezas

```
SPEC.md                  PREDICADO.md             pyproject.toml
src/protocol/__init__.py src/protocol/atomic.py   src/protocol/audit.py
src/protocol/metrics.py  src/protocol/types.py    src/protocol/predicado.py
src/protocol/ubicacion.py
tests/test_atomic.py     tests/test_audit.py      tests/test_metrics.py
tests/test_predicado.py  tests/test_ubicacion.py
examples/emitir_predicado.py + los dos artefactos que emite
examples/emitir_censo.py + censo-declarado.txt y los dos que emite
examples/contrafirmar_censo.py + ancla-declarada.txt y contrafirma-censo.json
examples/verificar_sello.py + sello-de-muestra/ y los dos que emite
```

`PREDICADO.md` es la especificación del Anillo 0 y existe para que un tercero
reimplemente la verificación **sin leer el código**. `UBICACION.md` hace lo mismo
con los cuatro estados de ubicación. Si el documento y el módulo discrepan, manda
el documento. `SPEC.md` no se toca: está sellado con fecha cierta y una sección
nueva invalidaría el sello.

## Invariantes (SPEC §3)

`INV_EXCL` (exclusividad en la apertura) · `INV_SPLIT` (partición determinista) · `INV_SELF` (resta
endógena de auto-conteo) · `INV_ISOL` (aislamiento de manifiestos) · `INV_TIME` (validez temporal
acoplada) · y las extensiones declaradas `INV-6` (ficha fuera de banda), `INV-7` (portabilidad de
`T₀`), `INV-8` (lectura no rasgada). El enunciado completo vive en `SPEC.md`.

## Uso

Los comandos se corren **desde la raíz de este repositorio**:

```
python3 -B -m unittest discover -s tests -v                      # 85 pruebas (corrida local: stdlib unittest)
python3 -B examples/emitir_predicado.py                          # emite el recibo del acto: veredicto + página
python3 -B examples/emitir_censo.py                               # el censo: declarado vs observado
python3 -B examples/verificar_sello.py --manifiesto RUTA --raiz DIR --universo disco   # los cuatro estados
python3 -B examples/emitir_predicado.py --check                   # REPRODUCE (RC 0) o DIVERGE (RC 1)
python3 -B examples/emitir_censo.py --check                       # REPRODUCE (RC 0) o RANCIO (RC 1)
python3 -B examples/verificar_sello.py --check                    # REPRODUCE (RC 0) o RANCIO (RC 1)
python3 -B examples/contrafirmar_censo.py --check                 # CONFIRMA (RC 0) o RANCIO (RC 1)
PYTHONPATH=src python3 -B -c "import protocol; print(protocol.__version__)"   # 0.1.0
```

**Motor único: `unittest` de la biblioteca estándar.** Los 5 archivos de `tests/` hacen
`import unittest`; 0 de los 12 `.py` rastreados hacen `import pytest`. Lo que el aparato de CI corre es
esa misma suite con `python -m pytest -q --junitxml=/tmp/junit.xml`, donde `pytest` es el **colector**
y el productor del junitxml, no un segundo motor de aserciones. `pytest` lo instala el runner y este
repositorio lo declara como **extra de desarrollo** (`pip install -e .[dev]`), nunca como dependencia
de ejecución.
El veredicto (`Ran 85 tests` · `OK`) sale por **stderr**; las líneas `MEDICION |` de cada prueba salen
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

**El contrato se midió contra un tercero.** Una implementación independiente
—escrita sin acceso al código, sólo con `PREDICADO.md` y la página emitida en
`8bcb6b4` (`f7000a8c…`)— reprodujo ese digest **bit a bit** por tres caminos
distintos (serializador propio en Node, `json.dumps` con los mismos argumentos,
y `openssl dgst -sha256`) y aprobó la página con 0 hallazgos. Encontró además
**cuatro** puntos donde un tercero razonable obtiene otro digest sin violar el
texto —salto final, orden de listas, orden de llaves anidadas y `h_prev` ausente
frente a `null`— más un error de alcance en la regla de rutas. Los cinco están
cerrados en §2 del documento y vigilados por las pruebas P-19 y P-20. El riesgo
residual se declara: el revisor no fue una persona distinta sino un modelo de la
misma familia, así que la prueba mide *legibilidad del contrato*, no
independencia de criterio.

**Lo que este módulo no hace:** no firma, no mide el sistema de archivos y no
adjudica. No se simula una firma que no se verifica.

## El segundo acto: el censo (Anillo 2)

La cifra honesta de un corpus no es «cuántos hay»: es el par `declarado −
observado`. Este acto publica los **tres** números —declarado, observado y
discrepancia— porque publicar dos es publicar una cifra que nadie puede
refutar.

```
python3 -B examples/emitir_censo.py           # observa, resta y sella la página
python3 -B examples/emitir_censo.py --check   # REPRODUCE (RC 0) · DIVERGE (RC 1)
```

El lado declarado vive en `examples/censo-declarado.txt` y **lo escribe una
persona**: el programa no puede declarar contra sí mismo. Cambiar `declarado=6`
por `declarado=7` y volver a pasar `--check` da `DIVERGE` (RC 1); emitir de nuevo
publica `discrepancia=-1` y `veredicto=no_conforme`. Una declaración falsa no se
discute: se resta, y el signo dice de qué lado se equivocó quien declaró.

Tres límites que el acto declara en vez de esconder:

1. El instrumento **vive dentro del universo contado** (`audit.py` está en
   `src/protocol`), así que el censo no descuenta su propio pie. Restarlo sin
   enumerarlo sería el doble descuento de `SPEC` §3.c; se declara en
   `entorno.no_medido`.
2. El acto **no lleva reloj**. El predicado prueba *qué*; la fecha cierta la
   aporta el ancla. Un `t_utc` de pared haría irreproducible la página y un
   `--check` que lo saltara sería un falso verde.
3. Si el universo contiene bytecode del intérprete (`__pycache__`, `*.pyc`), el
   acto **se para y no borra nada**: contarlos ataría el número a quién ejecutó
   Python antes en esa máquina.

## El tercer acto: la contrafirma (la frontera)

El censo prueba **qué** se contó. La contrafirma prueba **que ese recibo existía
en un punto que su autor no controla**. Sin ella el predicado es un sistema
cerrado: quien reescribe los siete campos y recalcula el digest obtiene un acto
internamente consistente y sin autoría.

```
python3 -B examples/contrafirmar_censo.py           # adjudica y emite contrafirma-censo.json
python3 -B examples/contrafirmar_censo.py --check   # CONFIRMA (RC 0) · RANCIO (RC 1)
```

La frontera es un solo archivo que **edita una persona**:
`examples/ancla-declarada.txt` nombra `repositorio`, `ancla` (el commit) y
`ruta` (la página). La fecha **no se declara ahí**: se mide con `git show` sobre
la propia ancla, porque una fecha escrita a mano es una afirmación más.

Cuatro reglas que el acto cumple, y el falsador de cada una:

1. **Se contrafirma la página tal como existe en el ancla, no en el árbol de
   trabajo.** Si se leyera el árbol local, una página manipulada emitiría su
   propia contrafirma y el acto se absolvería a sí mismo.
2. **El verificador no figura en `codigo`.** Si figurara, mejorarlo cambiaría la
   página que verifica y el ancla quedaría inservible para siempre: un guardián
   no puede guardarse a sí mismo. Su digest vive en la contrafirma, que es un
   objeto distinto del acto.
3. **El ancla nombra un commit anterior.** Levantar el acto produce dos commits:
   el primero crea las páginas, el segundo nombra su SHA y trae la contrafirma.
4. **Dos divergencias no se confunden.** `RANCIO` = el ancla describe otro árbol
   (hay que re-anclar). `REFUTA` = la contrafirma no cubre este acto (hay que
   investigar). Falsador medido el 2026-11-24: un byte movido en
   `predicado-censo.json` (`conforme` → `no_conforme`) y `--check` devuelve
   `RANCIO` con RC 1 mientras el digest anclado sigue siendo el anterior.

**El clon tiene que traer historia.** La contrafirma se adjudica contra el
commit que nombra el ancla, así que un clon superficial (`--depth 1`) no puede
cerrarla: `git clone` normal, o `git fetch --unshallow`, o falla con
`CONTRATO | git no respondió: sin ancla no hay contrafirma`. Falla cerrado a
propósito — un ancla ausente no se lee como un ancla confirmada. Medido el
2026-11-24 en `/tmp`, mismo commit, dos clones: superficial ⇒ RC 1, completo ⇒
`CONFIRMA`.

**La inversa es parte del contrato.** `desde_cuerpo` levanta el acto desde la
página publicada —diccionario, texto o bytes UTF-8—, exige las **siete** llaves
y ninguna otra y no consulta al emisor. Sin esa inversa un tercero sólo puede
comparar un digest que no sabe calcular, que es confiar, no verificar.

## El cuarto acto: la ubicación (los bytes, no las rutas)

Un manifiesto de sellado declara pares `(ruta, digest)`. La pregunta que contesta
este acto no es *¿existe ese archivo?* sino ***¿siguen juntos esos bytes?***. La
diferencia decide si una reorganización destruye la evidencia: `git mv` no
cambia un solo byte y, bajo una verificación indexada por ruta, invalida catorce
sellos con fecha cierta.

```
python3 -B examples/verificar_sello.py                    # la fixture; escribe su página
python3 -B examples/verificar_sello.py --manifiesto M --raiz D --universo disco
python3 -B examples/verificar_sello.py --check            # REPRODUCE (RC 0) · RANCIO (RC 1)
```

Cuatro estados, mutuamente excluyentes, y un quinto veredicto del acto:

| estado | condición | lo que prueba |
|---|---|---|
| `INTACTA` | la ruta declarada tiene el digest declarado | bytes intactos en su ruta |
| `REUBICADA` | otro camino del universo tiene ese digest | los bytes viven, la ruta cambió |
| `INTERCAMBIADA` | el digest está donde se declaró el de **otra** entrada | dos entradas permutadas |
| `DIVERGENTE` | el digest no aparece en el universo | alteración real o pérdida |
| `OPACO` | el universo no puede mirar ahí | el tercero no puede cerrar la cadena |

`INTERCAMBIADA` existe porque un esquema que sólo mire contenido **no puede ver un
intercambio**: cada digest sigue apareciendo exactamente una vez y el acto
devolvería `reubicada`. Es la laguna que el orden de los estados tapa, y la
publica `UBICACION.md` §4.1. Siempre se publica la multiplicidad `k` —cuántos
caminos del universo llevan ese digest—, porque el recibo no puede decidir cuál
copia es la buena, sólo cuántas hay.

Dos reglas que costaron una medición cada una:

1. **Un universo ciego produce lagunas, no reubicaciones.** Si la ruta declarada
   existe en disco y el universo declarado no la indexa, el estado es `OPACO`,
   nunca `REUBICADA`. Decir «se movió» cuando sólo significa «no lo busqué» es
   un falso hallazgo en la dirección peligrosa. Falsador: el sello A sobre
   `--universo git` da `0 conforme / 4 reubicado / 10 opaco`, y las diez son
   `platino-labs/protocol-core/*`, **no rastreado** aunque presente en disco.
2. **El veredicto de la página se deriva, no se escribe.** Una página que declare
   `conforme` mientras su propia salida dice `divergente` es exactamente el falso
   verde que el acto existe para impedir. El caso real, medido el 2026-11-24
   sobre `SHA256SUMS_SELLO_A` con `--universo disco` (83 654 rutas, 36 omitidas):
   `10 conforme / 4 reubicado / 0 divergente / 0 opaco -> reubicada`.

3. **El dialecto del manifiesto es una entrada, no un detalle de lectura.** Un
   manifiesto sellado es una gramática: si el recibo no declara cuál se leyó, dos
   verificadores honestos firman veredictos incomparables sobre el mismo árbol.
   Medidos cinco manifiestos públicos el 2026-11-24: jq 1.7.1 se lee tal cual (26
   filas); el instalador de Debian trae `./` explícito en sus 640 filas — se
   normaliza y se **cuenta** (`prefijadas`); OpenBSD (BSD tradicional), el registro
   de npm (SRI base64) y un `sha256sum` con un solo espacio se **rechazan nombrando
   el dialecto**. Publica `UBICACION.md` §2.1. Falsador: P-33.

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
