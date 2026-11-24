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
- **No decide entre `RANCIO` y `REFUTA` con el código de salida.** El acto de
  contrafirma (`contrafirmar_censo.py`) devuelve `VeredictoDeAncla` —`vigente`,
  `rancio`, `refuta`, `no_medida`— en su propia línea; RC 1 agrupa los tres que
  no están vigentes.

## 6. Reproducción

    python3 -B examples/verificar_sello.py --check

Lee `examples/predicado-sello.json`, recompone la página y la compara **entera**
contra la emitida. RC 0 = reproduce; RC 1 = diverge; RC 2 = no hay página previa.

La fixture `examples/sello-de-muestra/` tiene un caso de cada estado y está
escrita a mano: los digests son los del sello y el árbol es el de hoy, y la
diferencia entre los dos **es** el acto. Un fixture que se regenera no puede
contradecir a su lector.

El sello real de `platino-labs` se mide por comando (`--manifiesto … --raiz …`)
y se reporta en prosa: una prueba que se salta cuando el árbol vecino no está
enseña a saltarse la puerta.
