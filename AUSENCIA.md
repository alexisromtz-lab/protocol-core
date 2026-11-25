# AUSENCIA — el anillo 3: probar que algo **no** está

> Un verificador de hashes certifica lo que el manifiesto declara. No puede
> decir nada de lo que no declara, porque su universo es la lista de filas. La
> pregunta que un auditor hace primero —«¿este archivo estaba fuera del
> paquete?»— no tiene respuesta en ese formato. Este anillo la construye.

Acto: [`examples/verificar_ausencia.py`](examples/verificar_ausencia.py) ·
Módulo: [`src/protocol/ausencia.py`](src/protocol/ausencia.py) ·
Falsadores: [`tests/test_ausencia.py`](tests/test_ausencia.py) (P-48 … P-60).

---

## §0 · La pregunta, y por qué no es la negación de la anterior

`verificar_sello` pregunta **¿siguen estos bytes en algún sitio?** Su sujeto es
el árbol. `verificar_ausencia` pregunta **¿puedes probar que esta ruta no está
declarada?** Su sujeto es la página —el manifiesto ordenado—, y sólo
secundariamente el árbol.

La diferencia no es de signo, es de cuantificador. Una presencia se decide con
un testigo («aquí están los bytes, y el digest coincide»). Una ausencia se
decide agotando el conjunto: `¬∃p ∈ M : p = q` sólo se sostiene si se conoce
`M`. De ahí las tres tesis del anillo.

| anillo | pregunta | sujeto | veredicto |
|---|---|---|---|
| 0 · `predicado` | ¿el recibo emitido conserva su identidad? | la página del acto | `ACEPTA` / `REFUTA` |
| 1 · `ancla` | ¿la contrafirma y el ancla siguen vigentes? | la historia del repo | `VIGENTE` / `RANCIO` / `REFUTA` |
| 2 · `ubicacion` | ¿siguen juntos los mismos bytes en el árbol? | el árbol | `intacta` … `no_medida` |
| **3 · `ausencia`** | **¿puedes probar que `q` no está?** | **el orden** | **`ausente` / `presente` / `no_medida`** |

---

## §1 · El orden es el testigo

Un intervalo cualquiera no prueba nada: para cualquier `q` siempre hay una fila
menor y una mayor. Lo que prueba es la **adyacencia** — dos filas consecutivas
de la secuencia, sin nada en medio:

```
a.md · b.md · d.md          q = c.md
                ↑
        b.md < c.md < d.md  y son adyacentes  ⇒  c.md ∉ M
```

Entre `b.md` y `d.md` no cabe ninguna fila de `M`, luego la afirmación «`c.md`
no es una fila» se sostiene **sin recorrer el resto**. Si el testigo dijera
`a.md < c.md < d.md`, también sería cierto y no probaría nada: `b.md` cae dentro.

Los extremos llevan un solo vecino y siguen siendo prueba: `⊥ < a.md < "m.md"`
prueba que no hay nada antes de la primera fila.

Formalmente, el testigo es una tupla

```
(q, estado, i, fila[i-1], fila[i], digest_pagina)
```

con `clave(fila[i-1]) < clave(q) < clave(fila[i])` y `i` el índice de inserción
en la secuencia canónica.

### §1.1 · El orden se declara, no se hereda

`ORDEN_DECLARADO = "colacion C sobre bytes UTF-8 (alfabeto §2.1: NFC es la
identidad)"`. La colación C compara bytes, así que `Z` < `a` y `a.md` < `a/b.md`
no se decide por convención humana.

El alfabeto del protocolo es ASCII (`types.py:ALFABETO`), y eso vuelve
**degenerada** la trampa Unicode: no hay dos cadenas distintas con la misma
forma NFC, porque toda ruta ya está en NFC y el alfabeto no admite caracteres
combinables. El orden declarado es total y no necesita desempates por longitud o
por normalización.

La trampa que sí muerde no es Unicode: es **el caso**. En APFS `a.txt` y `A.txt`
son el mismo archivo y dos filas distintas del orden declarado. Ver §4.2.

### §1.2 · El orden es de la página, no del archivo

El manifiesto puede venir desordenado (`SHA256SUMS` no exige orden). La página se
reordena siempre, y `desordenada` se publica porque el testigo lleva **índices de
la secuencia ordenada**: un tercero que compruebe `i` contra su copia del archivo
comprobaría otra cosa. P-51 mide que la misma consulta contra el mismo conjunto
desordenado da el mismo intervalo y el mismo digest.

---

## §2 · Los dos dialectos de testigo, y el coste que cada uno declara

La corrección a la formulación habitual de este operador: **el testigo no cuesta
O(1)**. Cuesta O(1) *por consulta* una vez que el verificador ya tiene la página
autenticada, y autenticarla cuesta O(n) la primera vez. Ese O(n) no es gratis ni
invisible: es la diferencia entre verificar y creer.

| dialecto | qué necesita el verificador | prueba | entrega |
|---|---|---|---|
| **página** | la página entera (n filas) y su digest | índice + adyacencia, O(1) por consulta | el inventario completo |
| **Merkle** (`--merkle`) | una raíz de 32 bytes y su tamaño; **no** la página | dos caminos de inclusión, O(log n) | nada del inventario |

### §2.1 · Merkle: por qué ata la secuencia y no el conjunto

Un árbol de Merkle sobre un conjunto ordenado compromete la **secuencia**, y eso
es justo lo que hace falta: dos hojas en las posiciones `i` e `i+1` no admiten
nada entre ellas, porque insertar algo entre `i` e `i+1` cambiaría todas las
posiciones siguientes y la raíz.

El esquema es RFC 6962, sin inventar:

```
hoja  = sha256(0x00 ‖ ruta ‖ 0x00 ‖ digest_hex)
nodo  = sha256(0x01 ‖ izq ‖ der)
```

Los prefijos de dominio no son cosmética: sin `0x00`/`0x01` una hoja puede
reenviarse como nodo interno y el compromiso deja de atar la forma del árbol. El
corte se hace en la mayor potencia de dos menor que `n`, que es lo que mantiene
el árbol equilibrado con cualquier número de hojas.

P-55 mide las cuatro cosas que pueden fallar: el camino llega a la raíz, una hoja
alterada no llega, una raíz ajena no vale, y —la que más importa— un testigo de
**presencia** pasado como ausencia se rechaza.

### §2.2 · Qué verifica cada dialecto, en una línea

- El dialecto **página** prueba «`q` no está en `M`» a quien tenga `M`.
- El dialecto **Merkle** prueba lo mismo a quien **no** tenga `M`, y por eso es
  el único que se puede vender a un tercero con confidencialidad.

---

## §3 · Las tres trampas del manifiesto adversarial

Cada una da verde en un verificador ingenuo. Aquí están cerradas con coste de
código mínimo porque son exactamente los tres vectores de un manifiesto hostil.

| vector | cómo engaña | cierre | falsador |
|---|---|---|---|
| página vacía | `∀p ∈ ∅` es cierto ⇒ «ausente» para toda consulta | el lector ya rechaza un manifiesto sin filas; la página, también | P-54 |
| fila redactada (`<…>`) | hay un agujero en el orden y `q` puede caer dentro | toda consulta → `no_medida`, con el motivo | P-53 |
| nombre que es directorio | `vendor` no es una fila y el árbol lo tiene | `no_medida`: la página declara rutas, no prefijos | P-56 |

El escape de raíz (`../`) y el symlink externo no llegan aquí: la consulta pasa
por `RutaRelativa`, que rechaza `..` y `/` inicial, y el acto no sigue enlaces
(el árbol se sondea con `lexists` y el universo por caminata, que no resuelve
enlaces fuera de la raíz). Una consulta fuera del alfabeto es **entrada
inválida**, no un veredicto: RC 2.

La mutación en vuelo (TOCTOU) tampoco: este acto **no hashea bytes del árbol**.
Su sujeto es el orden de un manifiesto, y el manifiesto se lee una vez.

---

## §4 · La ley de proyección, tercera instancia

### §4.1 · El teorema compuesto

```
AUSENTE(página) ∧ ¬OPACO(q) ⇒ AUSENTE(árbol)
```

se sostiene sobre el universo que el árbol indexa, y **sólo** sobre él. Si `q`
cae fuera de ese universo, la composición es `no_medida`, no `ausente`.

Es el mismo defecto que apareció tres veces en tres actos distintos —qué
subconjunto decide y qué se afirma de lo que quedó fuera—: en el **régimen** de
la vía rápida (§3.0.1 de `UBICACION.md`), en la **redundancia** (§3.0.2) y aquí.

### §4.2 · El caso como entrada declarada

El acto **mide** si el volumen pliega mayúsculas, en vez de suponerlo: voltea la
caja de una ruta que ya existe y compara inodos. Mismo inodo ⇒ colapsa; inodo
distinto ⇒ distingue; no resuelve ⇒ distingue. No escribe nada.

```
caso | colapsa-el-caso | sonda protocol-core/SPEC.md -> Protocol-core/SPEC.md es el mismo inodo
caso-choque | jq-linux-amd64 | la pagina prueba JQ-LINUX-AMD64 y el volumen no distingue jq-linux-amd64
```

Donde colapsa, la página prueba `JQ-LINUX-AMD64 ∉ M` y el árbol tiene esos mismos
bytes bajo `jq-linux-amd64`: dos filas del orden, un solo archivo. El acto publica
el choque y **no elige**. P-57 lo falsifica de forma portable: afirma que el
recibo nombra el régimen que el volumen realmente tiene, de modo que pasa en un
CI sensible al caso y en un macOS que lo pliega.

### §4.3 · El universo por omisión no es el del acto de sello

`verificar_sello` resuelve `--universo auto` a `git ls-files` porque busca
artefactos **declarados**, y lo declarado está versionado por definición.

La ausencia pregunta por lo **no** declarado, y esa mitad —secretos, salidas de
build, dependencias copiadas a mano— no se versiona nunca. Un universo git no
puede probar su ausencia por construcción:

```
$ verificar_ausencia.py --raiz … --universo git --ausente tools/x.sh
arbol | git | git ls-files no lo versiona
arbol-ausencia | no_medida | git ls-files no lo versiona
-> no_medida                                                          (RC 3)
```

Por eso `auto` resuelve a **disco** aquí. No es una inconsistencia entre actos:
es que cada acto resuelve `auto` hacia el universo de *su* pregunta. P-59 mide
las dos ramas sobre el mismo árbol.

### §4.4 · La proyección la firma el cliente, no el módulo

Fuera de un árbol de software la pregunta por la ausencia deja de tener rutas y
pasa a tener **claves**: `Ávila-cita-09-30` y `avila-cita-09-30` son la misma
cita. El módulo no decide eso. Acepta una sola proyección declarada —`A-Za-z0-9._-`,
sin normalizar en silencio— y **rechaza** lo que no encaja en ella, porque una
tilde borrada a escondidas es una fila que desaparece del inventario:

```
ENTRADA INVALIDA | avila-cita-09-30-sillon1 | componente no admisible como slug   (RC 2)
```

La proyección `π(k)` es, entonces, **entrada del cliente aplicada antes de que la
página exista**: el exportador pliega tildes, caja y separadores, y firma el
resultado. De ahí la frontera que el módulo no puede verificar por él: si dos
registros **distintos** colapsan bajo el mismo `π`, la página tendría dos filas
con una sola clave y el testigo de vecinos dejaría de acotar. El módulo lo corta
donde puede —`Pagina` exige filas estrictamente crecientes, así que el choque es
violación de contrato (RC 2)— y el exportador lo corta antes, en el origen:

```
CONTRATO | colapsa-el-caso: 'Ávila-cita-09-00-sillon1' y 'AVILA-CITA-09-00-SILLON1'
           proyectan a la misma clave 'avila-cita-09-00-sillon1'                 (RC 1)
-> no se emite: una clave que colapsa se resuelve, no se sella
```

Elegir cuál de los dos registros es el bueno es una decisión del dueño de los
datos; el instrumento sólo puede negarse a sellar la ambigüedad. Por eso este
§4.4 es una **frontera declarada** y no un control: P-75 prueba que el
exportador se detiene, P-73 que la proyección es una sola definición y P-78 que
el orden de bytes del archivo no es el orden de la página.

---

## §5 · Escalera de códigos de salida

`0/0/1/1/2` del acto de sello no distingue «bloqueado» de «no se sabe». Una
compuerta de CI **sí** tiene que distinguirlos, así que este acto usa cuatro:

| RC | veredicto | qué significa para la compuerta |
|---|---|---|
| `0` | `ausente` | la afirmación se sostiene: no está, y se probó |
| `1` | `presente` | no se sostiene: la página lo declara, o el árbol lo tiene |
| `2` | — | la entrada no se puede leer (manifiesto ilegible, consulta fuera del alfabeto) |
| `3` | `no_medida` | **no se pudo medir**: página con huecos, ruta fuera del universo, nombre que es directorio |

`3` no es `0`. Un `3` que se lea como verde convierte el único instrumento
auditable en uno más que vende palomas.

---

## §6 · El recibo, y lo que no hace

```
ausencia | c.md | ausente | entre las filas 1 y 2
orden | colacion C sobre bytes UTF-8 (alfabeto §2.1: NFC es la identidad)
pagina | 3 filas | canonica | 0 redactadas | digest 6730fafa…
testigo | "b.md" < c.md < "d.md" | posicion 2
verificado | si | O(1) contra la pagina autenticada
autenticacion | si | O(n) una vez | 3 filas
caso | colapsa-el-caso | sonda a.md -> A.md es el mismo inodo
arbol | disco | la caminata no lo excluye
arbol-ausencia | ausente | el universo lo indexa y no esta
-> ausente
coste | 3 declaradas | 3 autenticadas | sin merkle
```

Dos capas, dos respuestas, las dos publicadas. Cuando la página prueba ausencia y
el árbol la refuta, el recibo **no** borra la primera: escribe las dos y adjudica
en `->`. Así el cliente ve *por qué* su manifiesto no era suficiente.

**Lo que este acto no hace**, y se publica para que no se lea como hueco:

1. **No fecha.** No emite ni verifica firmas de tiempo; mide un manifiesto ya
   emitido.
2. **No cuenta el reloj como umbral.** La duración va a `MEDICION`, nunca al
   recibo: la página tiene que reproducir bit a bit y un cronómetro no reproduce.
3. **No prueba ausencia en un árbol que no indexa.** Responde `no_medida` (ley
   §4.1), y por eso la respuesta correcta a «¿no está?» depende de qué universo
   se declaró.
4. **No entrega el inventario con `--merkle`.** Entrega dos caminos y una raíz;
   el resto del manifiesto no viaja.
5. **No decide qué significa «suficiente».** Si el cliente quiere saber si su
   paquete lleva un archivo de más, el acto contesta por ruta; el juicio sobre
   qué rutas importan es del cliente.
