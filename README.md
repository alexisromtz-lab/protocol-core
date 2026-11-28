# protocol-core

**Protocolo de Custodia Determinista y Reserva de Ranuras — Versión 0.3.0**

Almacenamiento atómico y auditoría determinista: sustitución atómica de archivos, aislamiento de
manifiestos por namespace, reserva determinista de ranuras y auditoría criptográfica **en frío** (sin
red, sin credenciales, sin re-sellar nada).

- **Versión**: `0.3.0` (congelada `2026-11-27T23:39:42Z`)
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
con los estados y veredictos de ubicación. Si el documento y el módulo discrepan, manda
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
python3 -B -m unittest discover -s tests -v                      # 321 pruebas (corrida local: stdlib unittest)
python3 -B examples/emitir_predicado.py                          # emite el recibo del acto: veredicto + página
python3 -B examples/emitir_censo.py                               # el censo: declarado vs observado
python3 -B examples/verificar_sello.py --manifiesto RUTA --raiz DIR --universo disco   # los seis veredictos
python3 -B examples/emitir_predicado.py --check                   # REPRODUCE (RC 0) · REFUTA (RC 1) · RANCIO (RC 2) · NO_MEDIDO (RC 3)
python3 -B examples/emitir_censo.py --check                       # REPRODUCE (RC 0) · REFUTA (RC 1) · RANCIO (RC 2) · NO_MEDIDO (RC 3)
python3 -B examples/verificar_sello.py --check                    # REPRODUCE (RC 0) · REFUTA (RC 1) · RANCIO (RC 2) · NO_MEDIDO (RC 3)
python3 -B examples/contrafirmar_censo.py --check                 # REPRODUCE (RC 0) · REFUTA (RC 1) · RANCIO (RC 2) · NO_MEDIDO (RC 3)
PYTHONPATH=src python3 -B -c "import protocol; print(protocol.__version__)"   # 0.3.0
python3 -B examples/emitir_recibo.py --tramo A=B --paginas A.txt,B.txt --salida RUTA   # el emisor: pliega los tramos en un /2
python3 -B examples/firmar_recibo.py --recibo RUTA --semilla ARCHIVO          # anillo 8: firma el /2 en RUTA.firma y RUTA.pub
python3 -B examples/verificar_recibo_externo.py RUTA --clave RUTA.pub --firma RUTA.firma   # el auditor coteja la firma
```

**Motor único: `unittest` de la biblioteca estándar.** Los 5 archivos de `tests/` hacen
`import unittest`; 0 de los 12 `.py` rastreados hacen `import pytest`. Lo que el aparato de CI corre es
esa misma suite con `python -m pytest -q --junitxml=/tmp/junit.xml`, donde `pytest` es el **colector**
y el productor del junitxml, no un segundo motor de aserciones. `pytest` lo instala el runner y este
repositorio lo declara como **extra de desarrollo** (`pip install -e .[dev]`), nunca como dependencia
de ejecución.
El veredicto (`Ran 100 tests` · `OK`) sale por **stderr**; las líneas `MEDICION |` de cada prueba salen
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
python3 -B examples/emitir_predicado.py --check   # REPRODUCE (RC 0) · REFUTA (RC 1) · RANCIO (RC 2) · NO_MEDIDO (RC 3)
```

El falsador se ve en un byte: se toca cualquier fuente, la suite **sigue verde**
—`salida reproducida | True`— y el acto contesta `RANCIO` (RC 2), porque el
árbol ya no es el que produjo ese veredicto. Un verde sin recibo es exactamente el falso
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
python3 -B examples/emitir_censo.py --check   # REPRODUCE (RC 0) · REFUTA (RC 1) · RANCIO (RC 2) · NO_MEDIDO (RC 3)
```

El lado declarado vive en `examples/censo-declarado.txt` y **lo escribe una
persona**: el programa no puede declarar contra sí mismo. Cambiar `declarado=6`
por `declarado=7` y volver a pasar `--check` da `REFUTA` (RC 1); emitir de nuevo
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
python3 -B examples/contrafirmar_censo.py --check   # REPRODUCE (RC 0) · REFUTA (RC 1) · RANCIO (RC 2) · NO_MEDIDO (RC 3)
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
   `VEREDICTO DE ANCLA | rancio` con RC 1 mientras el digest anclado sigue siendo
   el anterior.

**El veredicto de ancla, tipado.** El acto imprime una línea propia
—`VEREDICTO DE ANCLA | <v> | <detalle>`— con uno de cuatro valores:

| veredicto | condición | qué hacer |
|---|---|---|
| `VIGENTE` | la contrafirma cubre la página de enfrente y el ancla nombra el commit que la introdujo | nada |
| `RANCIO` | el ancla nombra otro árbol, o la página de enfrente cambió de digest | re-anclar |
| `REFUTA` | el ancla existe y la contrafirma no cubre este acto | investigar |
| `NO_MEDIDA` | falta la página, el ancla o el commit al que apunta | reunir el objeto |

RC 0 sólo para `VIGENTE`. El código de salida dice *si* el acto se sostiene; la
línea dice *por qué*, y sin ella «no está vigente» junta tres arreglos distintos
bajo el mismo 1. Es un eje propio —**¿el ancla sigue atando este acto?**— y no un
grado del veredicto de ubicación (**¿siguen juntos los bytes?**): un acto puede
estar `VIGENTE` sobre un sujeto `REUBICADO`, y ese es justamente el caso que el
ancla fue a buscar.

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

**La ruta declarada es una entrada, y se confina antes de abrirse.**
`ancla-declarada.txt` la escribe un humano, así que no se abre: se pasa por
`RutaRelativa`, se resuelve y se exige que caiga dentro de `RAIZ` y que sea
archivo. `../fuera.json`, una ruta absoluta o un enlace que salga del árbol
salen `OPACO | <ruta> | <motivo>` y el acto va a `NO_MEDIDA`; **no se lee**. Un
verificador que abre lo que le piden es un lector arbitrario del host que lo
ejecuta. Falsador: P-40, cinco vectores.

## El cuarto acto: la ubicación (los bytes, no las rutas)

Un manifiesto de sellado declara pares `(ruta, digest)`. La pregunta que contesta
este acto no es *¿existe ese archivo?* sino ***¿siguen juntos esos bytes?***. La
diferencia decide si una reorganización destruye la evidencia: `git mv` no
cambia un solo byte y, bajo una verificación indexada por ruta, invalida catorce
sellos con fecha cierta.

```
python3 -B examples/verificar_sello.py                    # la fixture; escribe su página
python3 -B examples/verificar_sello.py --manifiesto M --raiz D --universo disco
python3 -B examples/verificar_sello.py --check            # REPRODUCE (RC 0) · REFUTA (RC 1) · RANCIO (RC 2) · NO_MEDIDO (RC 3)
```

Cuatro estados por fila —`CONFORME`, `REUBICADO`, `DIVERGE`, `OPACO`— y seis
veredictos del acto, en orden de gravedad:

| veredicto | lo que prueba |
|---|---|
| `DIVERGENTE` | el digest declarado no aparece en el universo: pérdida real |
| `SUPLANTADA` | los bytes viven en otra ruta y la sellada la ocupan bytes no declarados |
| `INTERCAMBIADA` | el digest está donde se declaró el de **otra** entrada: canje |
| `NO_MEDIDA` | el universo no puede mirar en algún sitio declarado |
| `REUBICADA` | los bytes viven, la ruta cambió |
| `INTACTA` | cada ruta declarada tiene su digest declarado |

`INTERCAMBIADA` existe porque un esquema que sólo mire contenido **no puede ver un
intercambio**: cada digest sigue apareciendo exactamente una vez y el acto
devolvería `reubicada`. Es la laguna que el orden de los veredictos tapa, y la
publica `UBICACION.md` §4.1. `SUPLANTADA` existe porque el caso inverso también
miente: mutar un byte de un archivo que tiene un gemelo byte-idéntico deja el
digest vivo en el gemelo, y llamar «canje» a eso afirma un intercambio que no
ocurrió. Siempre se publica la multiplicidad `k` —cuántos caminos del universo
llevan ese digest, y cuáles—, porque el recibo no puede decidir cuál copia es la
buena, sólo cuántas hay.

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
   sobre `SHA256SUMS_SELLO_A` con `--universo disco` (83 654 rutas, 36 omitidas;
   más tarde ese mismo día 87 813 — el universo creció con tres `.worktrees/`
   nuevos, y por eso la cifra viaja con su hora): `10 conforme / 4 reubicado /
   0 divergente / 0 opaco -> reubicada`.

3. **El dialecto del manifiesto es una entrada, no un detalle de lectura.** Un
   manifiesto sellado es una gramática: si el recibo no declara cuál se leyó, dos
   verificadores honestos firman veredictos incomparables sobre el mismo árbol.
   Medidos cinco manifiestos públicos el 2026-11-24: jq 1.7.1 se lee tal cual (26
   filas); el instalador de Debian trae `./` explícito en sus 640 filas — se
   normaliza y se **cuenta** (`prefijadas`); OpenBSD (BSD tradicional), el registro
   de npm (SRI base64) y un `sha256sum` con un solo espacio se **rechazan nombrando
   el dialecto**. Publica `UBICACION.md` §2.1. Falsador: P-33.

4. **Una fibra declarada que pierde un miembro no se reubicó: divergió.** Si el
   manifiesto declara `k ≥ 2` rutas con el mismo digest (`jq` trae binarios
   gemelos), supervivencia del digest en cualquier ruta **no** basta: el estado es
   `DIVERGE` si alguna de las `k` rutas declaradas perdió sus bytes, porque
   entonces nadie recibió esa copia. Y una lectura que cambia bajo el hasher
   —`st_size`/`st_mtime_ns` distintos antes y después— es `OPACO`, nunca
   `DIVERGE`: un digest híbrido no es una mutación del sujeto, es un defecto de
   medición. Publica `UBICACION.md` §3. Falsadores: P-36, P-38.

**El código de salida del acto lo dice el veredicto, no el número de filas.**
Medir (`--manifiesto … --raiz …`) devuelve **RC 0 sólo si el veredicto es
`INTACTA` o `REUBICADA`** —la claim del acto es sobre bytes, no sobre rutas— y
**RC 1** para `DIVERGENTE`, `SUPLANTADA`, `INTERCAMBIADA` **y también** para
`NO_MEDIDA`: un acto que no pudo mirar no certifica, y salir en verde «porque no
encontró nada» es el falso verde en la dirección peligrosa. RC 2 queda para
entrada inválida. Un verificador que sale 0 con el sello roto no es un
instrumento: es el defecto que el instrumento existe para nombrar. Falsador:
P-41, dos casos por `subprocess` sobre un sujeto temporal.

**El universo es una continuación, no un peaje.** Si las rutas declaradas se
sostienen, el acto no barre: `INTACTA` vive en la σ-álgebra que generan esas
rutas y el barrido sólo añadiría coste. Medido el 2026-11-24 sobre el Sello A de
`platino-labs` —14 filas, 87 817 caminos— tres veces sobre los mismos bytes:
`343,61 s` en paralelo con la suite, `164,11 s` con caché fría y `67,11 s` con
caché caliente. **×5 sin que un byte cambie**: el coste es estado de la máquina,
no propiedad del acto, y por eso no entra al recibo. Con las 14 intactas el mismo
acto se decide en milisegundos. El recibo declara en cuál de los dos regímenes
decidió y lo que costó en contadores, no en segundos:

```
universo | 14 rutas | rutas declaradas (sin barrido) | 0 fuera del universo
coste | 14 declaradas | 0 barridas | 14 hasheadas
```

Un cronómetro no reproduce y la página tiene que reproducir bit a bit: la
duración viaja en el stream de medición (`MEDICION | reloj de duracion ms`).
La vía rápida **no adjudica nada más**: devuelve `None` —no un veredicto— en
cuanto una fila deja de sostenerse, porque sin universo no hay dónde mirar un
`REUBICADO` ni contra qué probar un `DIVERGE`. Un manifiesto vacío tampoco es
`INTACTA`: `∀ p ∈ ∅` es verdadero y no certifica nada. Publica `UBICACION.md`
§3.0.1. Falsadores: P-43, seis casos.

**El régimen no puede cambiar el veredicto.** La vía rápida sólo certifica si el
universo que *sería* barrido indexa las rutas declaradas; la pertenencia se
pregunta al régimen (segmento excluido, `git ls-files`), no se supone. Sin esa
pregunta, una ruta que el barrido llamaría `OPACO` pasaba `INTACTA` por la puerta
de atrás: medido, `2 conforme -> INTACTA` frente a `1 opaco -> NO_MEDIDA` sobre la
misma materia. Falsadores: P-44, P-45.

**La redundancia se publica y no adjudica.** Un digest puede vivir en más rutas
de las que el manifiesto declara. La línea `redundancia | <digest> | N
declaradas | M observadas | <caminos>` dice cuántas copias hay que nadie firmó, y
**no toca el veredicto**: la claim es sobre los bytes declarados. Dos copias
idénticas hoy son la divergencia de mañana, y con cinco agentes escribiendo en
paralelo ése es el dato que se quiere ver. Sólo aparece con el índice observado
delante —bajo la vía rápida no es un cero, es que nadie contó— y sólo para filas
`CONFORME`, porque una reubicación ya publica sus `k` caminos en el testigo.
Publica `UBICACION.md` §3.0.2. Falsadores: P-46, tres casos.

**`--completo` pide la segunda pregunta.** Contar copias exige barrer: la vía
rápida construye su índice con las rutas declaradas y no puede ver lo que el
manifiesto no nombra. La bandera fuerza el barrido sobre un sujeto sano y deja el
veredicto donde estaba (`intacta`), porque una copia no declarada ni rescata ni
condena. El recibo declara el régimen en su primera línea, así que el modo no
viaja implícito. Falsador: P-47.

**La ley bipartita `k_decl × k_obs`** cierra el cuadro sin casos especiales: `2×2`
en las mismas rutas ⇒ `INTACTA` (jq 1.7.1); `1×14` en otras ⇒ `REUBICADA` con las
14 publicadas (Sello A, 13 `.worktrees/` + la raíz); `1×1` cruzada ⇒
`INTERCAMBIADA`; `1×0` ⇒ `DIVERGENTE`. Publica `UBICACION.md` §3.0.

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

## Field notes

This repository belongs to an audit corpus whose measurements are published as
field notes. Two of them come from the same work:

- [El contador que sobrevive a su ventana](https://dev.to/alexisromtz7/el-contador-que-sobrevive-a-su-ventana-3p2)
- [El instrumento que se acusó a sí mismo: 28 hallazgos, 1 CRÍTICO y un mecanismo que no lo sostiene](https://dev.to/alexisromtz7/el-instrumento-que-se-acuso-a-si-mismo-28-hallazgos-1-critico-y-un-mecanismo-que-no-lo-sostiene-5fcf)
