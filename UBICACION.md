# UBICACION — adjudicar un manifiesto contra un árbol por contenido

Especificación del cuarto acto. Un tercero tiene que poder reimplementar lo que
está aquí **sin leer el código**: si la especificación no alcanza, lo que se
vende no es un estándar, es una caja negra.

El acto anterior ([PREDICADO.md](PREDICADO.md)) fija el formato del recibo. Este
fija **qué se mide** cuando el sujeto es un árbol de archivos y el testigo es un
manifiesto de digests.

## 1. La afirmación, y lo que no afirma

> Los artefactos que el manifiesto declara existen en este árbol, byte a byte.

**La ruta no forma parte de la afirmación.** Un artefacto con los bytes
correctos en otra ruta sigue cumpliendo la afirmación; un artefacto con los
bytes alterados no la cumple aunque su ruta no se haya movido. Las dos cosas
viajan en el recibo, separadas, porque confundirlas produce dos errores
distintos y los dos son caros:

- llamar **roto** a lo que sólo se movió (falso rojo: se re-sella sin necesidad,
  o se declara perdido un archivo que está a la vista);
- llamar **intacto** a lo que cambió de sitio ocupando el sitio de otro (falso
  verde: la reorganización pasa por mudanza limpia).

Caso medido que abre este documento: `SHA256SUMS_SELLO_A` de `platino-labs`
—14 filas, fecha cierta 2026-10-09— da **14/14 por hash y 10/14 por ruta**: el
sello está intacto y lo que envejeció fue el resolutor, que buscaba rutas.

## 2. Universo declarado

No se puede adjudicar contra "el árbol" en abstracto. El universo es una lista
de rutas, y **se publica con el recibo**, porque un veredicto sin denominador es
una opinión.

| fuente | qué es | ceguera declarada |
|---|---|---|
| `git ls-files` | lo versionado | no ve archivos presentes y no versionados |
| caminata con exclusiones enumeradas | lo que el árbol tiene | no ve lo que excluye; cuesta 130 s contra 0,8 s en un árbol de 83 690 archivos |

**La ceguera no se puede leer como ausencia.** Medido sobre el mismo árbol y el
mismo manifiesto: universo `git ls-files` ⇒ *0 conformes / 4 reubicados / 10
opacos*; universo de disco ⇒ *10 conformes / 4 reubicados / 0 opacos*. Las 10
rutas de la diferencia existen en disco y git no las versiona.

Regla: toda ruta declarada se **sondea en disco** aunque el universo no la
traiga. Si existe y el universo no la indexó, la fila es `OPACO` con motivo
`la ruta existe en disco y el universo declarado no la indexa` — nunca
`REUBICADO`. "Se movió" que sólo significa "no lo busqué" es un hallazgo falso.

### 2.1 El dialecto del manifiesto: una entrada, no un detalle de lectura

Un manifiesto sellado no es texto abstracto: es una gramática. Si el recibo no
declara cuál se leyó, dos verificadores honestos firman veredictos incomparables
sobre el mismo árbol — el mismo defecto que `GIT_INDEX_FILE` mete por el lado del
entorno, reintroducido por el lado de la evidencia.

Medido el 2026-11-24 contra cinco manifiestos públicos reales:

| manifiesto | dialecto | qué hace el lector |
|---|---|---|
| jq 1.7.1 `sha256sum.txt` | `sha256sum`, dos espacios | acepta 26 filas, `prefijadas = 0` |
| instalador de Debian `SHA256SUMS` | `sha256sum` con `./` explícito | acepta 640 filas, `prefijadas = 640` |
| OpenBSD 7.7 `SHA256` | BSD tradicional `SHA256 (ruta) = hex` | **rechaza** nombrando el dialecto |
| registro de npm | SRI base64 `sha512-…` | **rechaza** nombrando el dialecto |
| `digest ruta` con un solo espacio | `sha256sum` mal escrito | **rechaza** nombrando el dialecto |

Tres reglas, y cada una se publica:

1. **Un prefijo `./` explícito se normaliza y se cuenta.** `./x` y `x` denotan el
   mismo archivo: no hay dos sujetos que elegir. El recibo publica cuántas filas
   lo traían (`prefijadas`), porque una normalización que no se mide es una
   huella del lector convertida en dato del objeto.
2. **Un dialecto ajeno se nombra y se rechaza.** El nombre viaja en el error —
   `dialecto no admitido: BSD tradicional «SHA256 (ruta) = hex»` — para que el
   rechazo sea el mismo en cualquier implementación y diga qué convertir.
   Nombrar no es admitir: convertir el dialecto es un acto de quien aporta la
   evidencia, no del verificador.
3. **`./` no blanquea una salida del árbol.** `./../etc/passwd` sigue siendo
   `..` y se rechaza: la normalización es de ortografía, no de significado.

El dialecto leído y el borde de los no leídos viajan en `entorno.no_medido`.
Falsador: P-33.

## 3. Los cuatro estados

Sea `S: ruta ↦ digest` el índice del universo, y `(p, h)` una fila declarada.

| estado | condición | testigo que emite el recibo |
|---|---|---|
| `CONFORME` | `p ∈ dom(S)` y `S(p) = h` | la fila declarada, con `k = │{r : S(r) = h}│` |
| `REUBICADO` | `S(p) ≠ h` y existe `r ≠ p` con `S(r) = h` | `p -> r`, `k`, y si `p` quedó **vacía** |
| `DIVERGE` | `h` no está en el universo, o sólo consta en rutas que el manifiesto ya declaraba y `p` quedó sin bytes | `h` contra `S(p)` (o `ausente`), y el motivo |
| `OPACO` | la ruta está redactada, o existe en disco fuera del universo, o su lectura no cerró estable | el motivo, en texto |

Los cuatro son exhaustivos y mutuamente excluyentes sobre `(p, h, S)`.

**Multiplicidad.** `k = │{r : S(r) = h}│` se publica siempre. El recibo no puede
decir *cuál* copia es la buena; puede decir que hay `k`. Ocultar `k` convierte
una ambigüedad en una afirmación.

**La fibra declarada.** Un manifiesto puede declarar `k ≥ 2` rutas distintas con
el mismo digest —medido: jq 1.7.1 trae tres pares de binarios byte-idénticos—.
Ese conjunto es parte de lo declarado, y se conserva sólo si **cada** miembro
sigue midiendo `h`: un adjudicador que sólo compare multiconjuntos de hashes
llama limpio a la fibra que perdió un miembro, porque el digest sigue existiendo
en otro sitio. `INTACTA` exige entonces `∀ p declarada : S(p) = h`, y el recibo
publica la fibra con sus `k` rutas nombradas (`fibra | <digest> | k declaradas |
m conformes | p₁, …, p_k`).

Si un miembro de la fibra queda sin bytes y el digest no aparece en ninguna ruta
nueva, **nadie recibió nada**: no hay reubicación que declarar. La fila es
`DIVERGE` con el motivo `la ruta quedó sin bytes y el digest sólo consta en rutas
ya declaradas`, y el acto va a RC 1. Llamarlo `REUBICADA` afirmaría un movimiento
que no ocurrió y dejaría en verde un manifiesto con una copia declarada menos.
La relación es de **subconjunto**, no de igualdad: las copias que el manifiesto
no declara (`k_obs > k_decl`) no se acusan — no estaban declaradas.

### 3.0 La ley bipartita: `k_decl × k_obs`

Todo lo anterior se resume en un solo cuadro, y el cuadro no tiene casos
especiales. Sean `k_decl = │π_decl⁻¹(h)│` las rutas que el manifiesto declara con
el digest `h` y `k_obs = │π_obs⁻¹(h)│` las que el universo observado tiene:

| `k_decl` | `k_obs` | dónde viven | veredicto | qué certifica |
|---|---|---|---|---|
| 2 | 2 | las rutas declaradas | `INTACTA` | las `k` rutas declaradas conservan `h` **simultáneamente** (jq 1.7.1: binarios gemelos) |
| 1 | 14 | 1 declarada + 13 no declaradas | `REUBICADA` | los bytes están, en otra ruta; publica las 14 y no elige destino (Sello A: 13 `.worktrees/` + raíz) |
| 1 | 1 | ruta cruzada con otra fila | `INTERCAMBIADA` | el multiconjunto de hashes no cambió y la biyección de rutas sí |
| 1 | 0 | ninguna | `DIVERGE` | los bytes no están en el universo |

La fila 1×14 es la que fija la regla comercial del acto: **la multiplicidad se
publica, la unicidad no se inventa**. Un adjudicador que exija `k_obs = 1` para
adjudicar sólo funciona en el árbol donde se escribió el verificador.

### 3.0.1 La vía rápida: el universo es una continuación, no un peaje

`INTACTA` vive en la sub-σ-álgebra que generan las rutas declaradas: si las `N`
rutas del manifiesto miden su digest en su sitio, no hay nada que el barrido
pueda añadir salvo coste. Medido el 2026-11-24 sobre el Sello A de `platino-labs`
(14 filas, 87 817 caminos), tres veces sobre los mismos bytes:

| medición | `real` | estado de la máquina |
|---|---|---|
| 343,61 s | en paralelo con la suite | el reloj medía otra carga |
| 164,11 s | caché de página fría · `24,14 s` de CPU | cinco sextos son espera de I/O |
| 67,11 s | caché de página caliente | el mismo trabajo, ya leído |

**×5 sin que un byte cambie.** El coste del barrido no es una propiedad del acto:
es un estado de la máquina, y por eso no entra al recibo. Lo que sí es del objeto
son los contadores —`declaradas`, `barridas`, `hasheadas`—, y ésos son los que la
página publica. Un recibo que promete «verifica en segundos» afirma sobre el
lector, no sobre el artefacto.

Con las 14 rutas intactas el mismo acto se decide en milisegundos y lo declara:
`universo | 14 rutas | rutas declaradas (sin barrido) | 0 fuera del universo` y
`coste | 14 declaradas | 0 barridas | 14 hasheadas`.

La vía rápida **no puede** adjudicar nada más. Devuelve `None` —no un veredicto—
en cuanto una fila deja de sostenerse, porque sin universo no hay dónde mirar:

- ruta ausente o alterada ⇒ `None`. Contestar `DIVERGE` aquí sería acusar de una
  ausencia que el índice no midió; `REUBICADA` exige nombrar un destino.
- canje (`a ↔ b`) ⇒ `None`, y sólo el barrido lo nombra `INTERCAMBIADA`.
- una sola fila `OPACA`, o un manifiesto vacío ⇒ `None`. El vacío tampoco es
  `INTACTA`: `∀ p ∈ ∅` es verdadero y no certifica nada.
- una ruta que se resuelve fuera de `--raiz` (escape `..`, enlace externo) ⇒
  `None`: no se lee, y no se adjudica con lo que no se leyó.

**El régimen no puede cambiar el veredicto sobre los mismos bytes.** La vía
rápida sólo puede certificar `INTACTA` si el universo que *sería* barrido indexa
las `N` rutas declaradas; si el régimen las excluye, la fila sería `OPACO` en el
barrido y `INTACTA` por la puerta de atrás. La pertenencia se **pregunta** —un
segmento de `EXCLUSIONES` en modo caminata, `git ls-files` en modo git— nunca se
supone. Medido el 2026-11-24 con un `.git/configuracion` declarado en un
repositorio de una sola confirmación: antes del cierre, la misma materia daba
`2 conforme -> INTACTA` (`coste | 2 declaradas | 0 barridas`) por la vía rápida y
`1 opaco -> NO_MEDIDA` al forzar el barrido. Después, `__pycache__/x.pyc`
declarado da `1 opaco -> NO_MEDIDA` en los dos regímenes, y lo dice con la misma
línea de testigo: `opaco __pycache__/x.pyc (la ruta existe en disco y el
universo declarado no la indexa)`. Falsadores: P-45. Un veredicto que depende
del camino elegido no es un veredicto sobre el objeto.

Lo que la vía rápida **no publica** es `k_obs`. El recibo lo dice con una laguna
—`sin barrido del universo: … y k observado no se publica`— para que `INTACTA`
sin barrido no se lea como una afirmación sobre copias que nadie contó.

### 3.0.2 La redundancia se publica y no adjudica

La fibra es el mismo objeto visto desde el manifiesto (`k_decl`) y desde el árbol
(`k_obs`). Cuando `k_obs > k_decl` hay copias que **nadie declaró**:

```
redundancia | <digest> | 2 declaradas | 3 observadas | a.md, b.md, copia/c.md
```

La línea **no toca el veredicto**. La claim del acto es sobre los bytes
declarados, y un artefacto intacto que además vive en catorce sitios no está
roto. Pero dos copias idénticas hoy son dos candidatas a separarse mañana —la
duplicación es la fase latente de la divergencia— y un recibo que la calla deja
al lector sin el dato que más le importa cuando cinco agentes escriben en
paralelo sobre el mismo árbol.

Se emite sólo con el índice observado delante, y sólo para filas `CONFORME`: una
reubicación ya publica sus `k` caminos en el testigo, y bajo la vía rápida
`k_obs == k_decl` por construcción, de modo que la línea **no aparece**. Su
ausencia ahí no es un cero: es que nadie contó. Falsadores: P-46, tres casos,
uno de ellos probando que la copia de más ni rescata ni condena a la fila que
falta.

**`--completo` es la pregunta que la vía rápida no puede contestar.** «¿Siguen los
bytes declarados?» y «¿cuántas copias de estos bytes hay?» comparten sujeto y
necesitan universos distintos: la primera se decide con las rutas declaradas, la
segunda necesita el árbol, porque una copia que nadie declaró sólo existe fuera
del manifiesto. Con `--completo` el acto barre aunque la vía rápida bastara, y el
recibo publica en cuál de los dos regímenes se decidió (`universo | N rutas |
caminata con 6 exclusiones` frente a `rutas declaradas (sin barrido)`), así que el
modo nunca viaja implícito. El veredicto no cambia: en un árbol sano sigue siendo
`intacta`. Falsador: P-47, donde el mismo sujeto sin la bandera da `intacta` sin
recuento y con la bandera da `intacta` con `3 observadas`.

**La lectura inestable no es una divergencia.** Un digest calculado mientras otro
proceso escribía no es el digest de ningún estado del archivo: es un híbrido que
nunca existió entero en disco. Se mide `fstat` antes y después de leer y, si
cambia el tamaño, la fecha, el inodo o el dispositivo —o si los bytes leídos no
son los que el archivo declara tener—, la ruta va a `inestables` y la fila sale
`OPACO` con motivo `la lectura del archivo no cerró estable`. Emitir ese digest
acusaría al artefacto de una alteración ocurrida en el instrumento.

**El motivo del `OPACO` dice qué corregir**, y por eso la comprobación de la
laguna va **antes** de buscar candidatas: si la ruta no se midió, que su digest
aparezca o no en otro sitio no cambia que aquí no hay medición. Tres motivos, tres
arreglos distintos: `la ruta existe en disco y el universo declarado no la indexa`
(versionar, o cambiar de universo) · `la ruta es un enlace o un directorio: el
manifiesto mide bytes de archivo` (indexar el destino, no el enlace) · `la lectura
del archivo no cerró estable` (quiescencia del sujeto, no del lector).

### 3.1 Redacción

Una ruta que contiene los bytes `<` o `>` no es un nombre de archivo: es una
marca de que el manifiesto remite a un lugar que no escribe. Es `OPACO` por
construcción, y su digest no se busca. Un lector que ignore esta regla la
declara `DIVERGE`, y ese falso rojo es el que un manifiesto saneado produce en
masa.

## 4. El veredicto del acto: seis valores, con orden declarado

| veredicto | condición | ¿la afirmación se sostiene? |
|---|---|---|
| `DIVERGENTE` | alguna fila `DIVERGE` | no |
| `SUPLANTADA` | alguna fila `REUBICADO` cuya ruta declarada no quedó vacía y no la ocupa un digest declarado | no |
| `INTERCAMBIADA` | alguna fila `REUBICADO` cuya ruta declarada la ocupa el digest declarado de otra fila | no |
| `NO_MEDIDA` | hay filas y ninguna de las anteriores, pero hay `OPACO` | no se sabe |
| `REUBICADA` | hay `REUBICADO` y todas sus rutas declaradas quedaron vacías | **sí** |
| `INTACTA` | todas las filas son `CONFORME` | sí |

Un acto sin filas es `NO_MEDIDA`, no `INTACTA`: cero artefactos medidos no es
cero hallazgos.

**El código de salida se deriva del veredicto, no del número de filas.** En
medición (`--manifiesto … --raiz …`) el acto devuelve RC 0 sólo para `INTACTA` y
`REUBICADA`; RC 1 para los cuatro restantes, `NO_MEDIDA` incluida —un acto que no
pudo mirar no certifica, y salir en verde «porque no encontró nada» es el falso
verde en la dirección peligrosa—; RC 2 si la entrada no se puede leer. `--check`
conserva su contrato propio (§6). La línea del veredicto nombra cuál de los
cuatro fue: el RC agrupa, el tipo distingue.

El testigo de una reubicación nombra **todos** los caminos medidos, no el que el
lector prefiera: `p -> k caminos: a, b` cuando `k > 1`. Elegir uno cuando hay `k`
publica un destino que el índice no sostiene — medido sobre jq 1.7.1, que trae
tres pares de binarios byte-idénticos, el testigo nombraba el gemelo que nunca se
movió.

### 4.1 El canje, que un esquema de sólo contenido no ve

Si dos artefactos **intercambian** sus rutas, cada digest sigue apareciendo
**una sola vez** (`k = 1`) y cada ruta sigue ocupada. Un adjudicador que sólo
compare conjuntos de digests llama limpio a un canje; el canje es justo lo que
un sello existe para detectar, porque es el resultado de una reorganización que
nadie revisó.

El discriminador es **`vaciada`**: ¿la ruta declarada quedó sin archivo? En una
mudanza limpia, sí. En un canje, no: la ocupa el otro. De ahí que
`INTERCAMBIADA` exista y ordene por encima de `NO_MEDIDA` — es un hallazgo
positivo, no una laguna.

Un canje es **mutuo por construcción**, y no hay que postularlo: si `p1` lleva el
digest declarado de `p2`, la fila de `p2` tiene necesariamente su digest fuera de
su ruta. Lo que no es mutuo es un **intruso**: bytes que el manifiesto no declara
ocupando la ruta sellada mientras el artefacto verdadero vive en otra parte.
Eso es `SUPLANTADA`, y no se puede llamar `INTERCAMBIADA` sin afirmar un canje
que no ocurrió ni `REUBICADA` sin abrir un falso verde.

Caso real (jq 1.7.1, 2026-11-24): mutar un byte de `jq-linux64` deja su digest
vivo en su gemelo `jq-linux-amd64`, así que la fila no es pérdida. El acto
anterior lo llamaba `intercambiada`; el veredicto nuevo dice lo que pasó:
`reubicado jq-linux64 -> jq-linux-amd64 (ruta ocupada por bytes no declarados)`.

El testigo nombra el ocupante: `p -> r (ruta ocupada)` cuando el ocupante es un
digest declarado, `p -> r (ruta ocupada por bytes no declarados)` cuando no lo
es.

**El mismo acto físico, dos pérdidas distintas.** Un byte cambiado en una ruta
cuyo digest no vive en ningún otro sitio da `DIVERGENTE`: se perdió el
artefacto. El mismo byte, en una ruta cuyo digest sobrevive en un gemelo, da
`SUPLANTADA`: se perdió la ruta, el artefacto está. Un verificador que sólo
conozca la primera dice «se corrompió» de las dos, y manda a buscar un archivo
que existe.

## 5. Lo que este acto no hace

- **No sella.** Re-sellar es un acto externo con su propio pre-veredicto y su
  propia fecha cierta. Este acto mide un sello ya emitido.
- **No fecha.** No hay firma de tiempo; `entorno.no_medido` lo declara.
- **No decide qué copia es la buena** cuando `k > 1`: publica `k` y para.
- **No resuelve rutas redactadas** fuera de banda.
- **No sigue enlaces simbólicos ni lee directorios**: sus bytes no son los bytes
  del manifiesto. Se publican en `omitidas`.
- **No distingue un archivo que nunca existió de uno que desapareció entre
  `isfile` y la lectura.** Los dos son `OPACO` con motivo de instrumento: el
  lector no vio bytes, y afirmar cuál de los dos fue sería inventar.
- **No acusa las copias que el manifiesto no declara.** `INTACTA` es una
  relación de subconjunto (`∀ p declarada`), no de igualdad de multiconjuntos.
  Detectar una duplicación posterior es otro acto.
- **No publica `k` observado cuando decide por la vía rápida.** Si las rutas
  declaradas se sostienen, contesta `INTACTA` sin barrer el universo, y lo
  declara con la laguna `sin barrido del universo: … y k observado no se
  publica`. Un `INTACTA` sin barrido es una afirmación sobre las `N` filas
  declaradas, no sobre cuántas copias hay.
- **No cronometra dentro del recibo.** `coste | declaradas | barridas |
  hasheadas` son contadores y reproducen; la duración va al stream de medición.
- **No decide por su cuenta entre `RANCIO` y `REFUTA`.** El acto de contrafirma
  devuelve el `VeredictoDeAncla` en su línea y el código de salida lo traduce
  (§6.2); el sello no adivina el veredicto ajeno.

## 6. Reproducción

    python3 -B examples/verificar_sello.py --check

Lee `examples/predicado-sello.json`, recompone la página y la compara contra la
emitida con la escalera de §6.2: `REPRODUCE` (0), `REFUTA` (1), `RANCIO` (2),
`NO_MEDIDO` (3).

### 6.1 La única excepción es el entorno del acto, y son dos campos

`plataforma` y `runtime` son del observador, no del sujeto: el mismo árbol medido
con otro intérprete produce la misma salida y **otra** página. Compararla entera
convertiría esa diferencia en una condena del árbol, y el acto se volvería verde
sólo bajo el intérprete que lo firmó: un rojo por el entorno condena y un verde
por el entorno absuelve, y ninguno de los dos midió el árbol.

El acto normaliza esos dos campos y compara **el resto byte a byte**. Todo lo
demás condena: un digest movido en `entradas` es del árbol y sale `REFUTA`; una
fila borrada de `entorno.no_medido` también, porque la laguna es lo que el acto
confiesa y normalizarla le dejaría absolverse de su propia confesión.

La reproducción no elige identidad: publica las dos.

    MEDICION | pagina reproducida | True
    MEDICION | entorno del acto | firmada en darwin/CPython 3.9.6 | reproducida en darwin/CPython 3.12.13
    MEDICION | digest del acto declarado | <sha256 de la pagina firmada>
    MEDICION | digest de este acto | <sha256 de la pagina de esta corrida>
    REPRODUCE | <sha256 de la pagina firmada>

`REPRODUCE` nombra el acto **firmado**, no el de la corrida de turno: publicar el
nombre de quien reproduce daría dos identidades al mismo acto según la máquina.
Medido el 27-Nov-2026: la página sellada bajo `CPython 3.9.6` reproduce bajo
`CPython 3.12.13` con RC 0; el nombre firmado es `80bee69d…` y el de la corrida
`bfed7488…`, y el mismo archivo, sin reescribirse, sirve a los dos.
Falsadores: P-32 (el entorno no condena) y P-27 (el separador del archivo no
condena).

### 6.2 La escalera del código de salida, y por qué `RANCIO` no es `REFUTA`

Cuatro actos —`emitir_predicado.py`, `emitir_censo.py`, `verificar_sello.py`,
`contrafirmar_censo.py`— contestan con los mismos códigos, que viven en
`protocol.predicado.CodigoDeActo` y no en la prosa de cada uno:

| código | nombre | lo que prueba |
|---|---|---|
| 0 | `REPRODUCE` | la página nombra este árbol y este veredicto |
| 1 | `REFUTA` | el árbol es el mismo y la página miente sobre él: `salida`, `veredicto` o `no_medido` no cuadran |
| 2 | `RANCIO` | la página nombra **otro** árbol: sus `entradas` o su `codigo` no son los de hoy |
| 3 | `NO_MEDIDO` | no hay página previa, o el acto no pudo leer el sujeto |
| 64 | `CONTRATO` | la declaración del acto está mal formada |
| 65 | `OBSERVADOR` | el universo está sucio por un observador ajeno |

**El orden de las comparaciones es la regla.** Primero `entradas` y `codigo`;
sólo si cuadran se mira `salida`. Invertirlo convierte cada movimiento del árbol
en una acusación: tocar una fuente mueve los dos lados de la página, y llamar a
eso `REFUTA` sería condenar al árbol por haberse movido. `RANCIO` se repara
emitiendo de nuevo, y emitir de nuevo es gratis; `REFUTA` obliga a auditar quién
escribió la página.

**Una página forjada es `RANCIO` aquí y `REFUTA` en la contrafirma**, y por eso
existen los dos actos. El cotejo de página sólo puede probar que la página y el
árbol de hoy no se corresponden; probar que un árbol **existió** es del ancla,
que nombra un commit y no un archivo. Un cotejo que contestara `REFUTA` en los
dos casos estaría afirmando lo que no mide.

`REFUTA` conserva el `1` porque los consumidores que ya existen sólo conocían dos
códigos (`0` y «algo va mal»); `RANCIO` toma el `2` que antes significaba «no hay
página previa», y `NO_MEDIDO` se muda al `3`. `64`/`65` no son `4`/`5` porque
`sysexits.h` reserva `64`–`78` para el uso del acto y el `4` ya es el `grep` de
«no puedo leer».

**Un mismo acto puede tener dos gramáticas, y la elige el argumento.**
`verificar_sello.py` contesta dos preguntas distintas: sin `--check` pregunta por
el **sujeto** —`0` la afirmación se sostiene, `1` no se sostiene o no se pudo
medir, `2` la entrada no se puede usar— y con `--check` pregunta por la
**página**, que es la tabla de arriba. Las dos tablas no se mezclan: bajo
`--check` una entrada ilegible **no** sale `2`, porque ese `2` ya es `RANCIO` y
una errata de argumento disfrazada de página rancia manda a re-emitir lo que no
está rancio; sale `64`, que es lo que el defecto es —de quien llamó—. Por lo
mismo, lo que subía como `SystemExit("texto")` salía `1`, el código de
`REFUTA`: teclear mal el argumento mandaba a auditar un árbol sano. Falsador:
P-42b, que corre la misma entrada ausente en los dos modos y exige `(2, 64)`.

**La escalera no cubre `tools/verificar_etiqueta.py`**, que publica su propio
contrato —`0` todas coinciden · `1` alguna diverge · `2` NO_MEDIDO—. Ese acto no
coteja una página sino etiquetas contra la historia, y su `2` significa lo
contrario que aquí; migrarlo es un corte propio y hasta entonces dos actos del
mismo árbol hablan dialectos distintos, cosa que se declara en vez de
disimularse.

Falsadores: P-25 (las seis filas de la escalera), P-26 (el nombre publicado es el
del acto firmado), P-27 (el separador del archivo no condena la página), P-32 (un
árbol movido contesta `RANCIO`; una fila mentida, `REFUTA`), P-42b (la entrada
ilegible cambia de código con el modo) y t14_b (el universo sucio sale por `65`).

La fixture `examples/sello-de-muestra/` tiene un caso de cada estado y está
escrita a mano: los digests son los del sello y el árbol es el de hoy, y la
diferencia entre los dos **es** el acto. Un fixture que se regenera no puede
contradecir a su lector.

El sello real de `platino-labs` se mide por comando (`--manifiesto … --raiz …`)
y se reporta en prosa: una prueba que se salta cuando el árbol vecino no está
enseña a saltarse la puerta.
