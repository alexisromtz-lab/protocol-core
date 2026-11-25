# GUIONES — cinco piezas escritas antes de grabar

<!-- HUELLA-GUIONES-CON-RECIBO-20261124 -->

**Estado:** guiones cerrados · **frames renderizados: 0** · cifras medidas el 25-Nov-2026 sobre `protocol-core` y sobre el Sello A real ([`SHA256SUMS_SELLO_A`](../platino-labs/sellos-fecha-cierta-20261009/SHA256SUMS_SELLO_A)).

Este archivo no es publicidad: es **una página**, en el mismo sentido que `PREDICADO.md` y `UBICACION.md`. Todo número que un guion pone en pantalla se re-deriva con un comando que está aquí, y cada guion declara qué lo falsa. Un video que enseña una cifra que nadie puede reproducir contradice, en cámara, el producto que intenta vender.

---

## 0 · El contrato del guion — seis reglas

1. **Ninguna cifra en pantalla sin su comando.** Vale para `206 rutas` igual que para `RC 1`. La tabla [§8](#8--tabla-de-cifras) es la fuente; el guion la cita, no la recuerda.
2. **El guion no se transcribe: se convoca.** Las líneas que van a pantalla las imprime `examples/ensayo_escalera.py`, no un editor de texto. Si alguien reescribe una línea «para que se lea mejor», el video y el acto ya no son el mismo objeto.
3. **El guion se ensaya antes de grabarse.** `python3 -B examples/ensayo_escalera.py` ⇒ `ENSAYO | 7/7 | … | RC 0`. Ese RC es el falsador del guion: si el acto cambia, el ensayo lo grita **antes** que la cámara.
4. **La animación no adelanta.** Una línea aparece completa —como la imprime el acto— y después entra. Nunca se escribe carácter a carácter: escribir sugiere un proceso que el acto no tuvo.
5. **Al RC se le llama por su nombre.** `RC 0` significa *el acto no encontró ruptura*, no *está correcto*. En pantalla nunca se dice «correcto» ni «aprobado»; se dice el veredicto (`intacta`, `reubicada`, `divergente`, `intercambiada`, `no_medida`) y el código.
6. **La voz tiene presupuesto: 12 palabras cada 4 s, y la pieza se sostiene sin voz.** Lo que no cabe en la voz no se acelera: pasa a segunda línea en pantalla. La voz **no explica** lo que el recibo ya imprime; dice sólo lo que el recibo *no* puede decir (por qué importa).

---

## 1 · La materia prima (medida, no imaginada)

### 1.1 · El ensayo de la escalera

`python3 -B examples/ensayo_escalera.py` construye siete sujetos efímeros y corre el acto sobre cada uno. Salida literal, 25-Nov-2026, **RC 0**:

```
=== 1/7 · intacta — los bytes declarados estan en su ruta
    $ python3 -B <acto> --manifiesto <sujeto>/SHA256SUMS --raiz <sujeto> --universo disco
      universo | 2 rutas | rutas declaradas (sin barrido) | 0 fuera del universo
      2 conforme / 0 reubicado / 0 diverge / 0 opaco -> intacta
      coste | 2 declaradas | 0 barridas | 2 hasheadas
    RC 0 · esperado 0 · OK

=== 2/7 · reubicada — los mismos bytes, otra ruta
    $ python3 -B <acto> --manifiesto <sujeto>/SHA256SUMS --raiz <sujeto> --universo disco
      universo | 3 rutas | caminata con 6 exclusiones | 0 fuera del universo
      1 conforme / 1 reubicado / 0 diverge / 0 opaco -> reubicada
      reubicado a.md -> actas/a.md (ruta vaciada)
      coste | 2 declaradas | 3 barridas | 3 hasheadas
    RC 0 · esperado 0 · OK

=== 3/7 · intercambiada — mismo multiconjunto de digests, biyeccion de rutas rota
    $ python3 -B <acto> --manifiesto <sujeto>/SHA256SUMS --raiz <sujeto> --universo disco
      universo | 3 rutas | caminata con 6 exclusiones | 0 fuera del universo
      0 conforme / 2 reubicado / 0 diverge / 0 opaco -> intercambiada
      reubicado a.md -> b.md (ruta ocupada)
      reubicado b.md -> a.md (ruta ocupada)
      coste | 2 declaradas | 3 barridas | 3 hasheadas
    RC 1 · esperado 1 · OK

=== 4/7 · divergente — un byte de mas
    $ python3 -B <acto> --manifiesto <sujeto>/SHA256SUMS --raiz <sujeto> --universo disco
      universo | 3 rutas | caminata con 6 exclusiones | 0 fuera del universo
      1 conforme / 0 reubicado / 1 diverge / 0 opaco -> divergente
      diverge a.md (bytes alterados)
      coste | 2 declaradas | 3 barridas | 3 hasheadas
    RC 1 · esperado 1 · OK

=== 5/7 · entrada invalida — no hay manifiesto que adjudicar
    $ python3 -B <acto> --manifiesto <sujeto>/no-existe.txt --raiz <sujeto> --universo disco
      ENTRADA INVALIDA | <sujeto>/no-existe.txt | no se puede leer
    RC 2 · esperado 2 · OK

=== 6/7 · redundancia — los bytes estan, y ademas hay copias que nadie declaro
    $ python3 -B <acto> --manifiesto <sujeto>/SHA256SUMS --raiz <sujeto> --universo disco --completo
      universo | 4 rutas | caminata con 6 exclusiones | 0 fuera del universo
      2 conforme / 0 reubicado / 0 diverge / 0 opaco -> intacta
      redundancia | bbbff613b27d7f717f8e7bfce522186e0e2539efd86520ceac00ce62dab458c2 | 1 declaradas | 2 observadas | a.md, copia/a.md
      coste | 2 declaradas | 4 barridas | 4 hasheadas
    RC 0 · esperado 0 · OK

=== 7/7 · no_medida — el byte esta en disco y el universo del acto no lo indexa
    $ python3 -B <acto> --manifiesto <sujeto>/SHA256SUMS --raiz <sujeto> --universo disco
      universo | 3 rutas | caminata con 6 exclusiones | 1 fuera del universo
      2 conforme / 0 reubicado / 0 diverge / 1 opaco -> no_medida
      opaco __pycache__/x.pyc (la ruta existe en disco y el universo declarado no la indexa)
      coste | 3 declaradas | 3 barridas | 3 hasheadas
    RC 1 · esperado 1 · OK

ENSAYO | 7/7 | los 7 sujetos se comportaron como declara este archivo | RC 0
```

Los cinco primeros son la escalera de veredictos y su código de salida: **`0 / 0 / 1 / 1 / 2`**. Los dos últimos **no son veredictos**: el sexto es el dato que exige el barrido completo, y el séptimo es la laguna.

### 1.2 · El Sello A real

Mismo acto, sujeto ajeno a las fixtures: 14 filas firmadas de `platino-labs`, árbol de 87 819 rutas.

```
$ python3 -B examples/verificar_sello.py \
    --manifiesto ../platino-labs/sellos-fecha-cierta-20261009/SHA256SUMS_SELLO_A \
    --raiz ../platino-labs --universo disco

universo | 87819 rutas | caminata con 6 exclusiones | 0 fuera del universo
10 conforme / 4 reubicado / 0 diverge / 0 opaco -> reubicada
reubicado ACTA_DE_CIERRE_…_20261009.md -> 14 caminos: .worktrees/…, …
reubicado ACTA_DE_CONGELACION_…            -> 14 caminos: .worktrees/…, …
reubicado ACTA_GATE_DE_PROTOCOL_CORE_…     -> 14 caminos: .worktrees/…, …
reubicado ASIENTO_DE_RETIRO_EXPLICITO_…    -> 14 caminos: .worktrees/…, …
redundancia | 0d7cca0b97d597dd… | 1 declaradas | 15 observadas | …
… (14 líneas `redundancia`, una por digest declarado)
coste | 14 declaradas | 87855 barridas | 87819 hasheadas
```

Los `…` son elisiones de esta página, **no del acto**: las líneas `reubicado` y `redundancia` reales listan todas las rutas. Un video que recorte la lista tiene que decirlo en pantalla (§4, G4).

Agregado que usan los guiones, y su comando:

```
$ python3 -B examples/verificar_sello.py --manifiesto <…> --raiz ../platino-labs --universo disco \
    | grep '^redundancia' | awk -F'|' '{d++; n+=split($5,a,",")} END {print d" digests | "n" rutas"}'
14 digests | 206 rutas
```

### 1.3 · El sujeto ajeno — jq 1.7.1

Ni el Sello A ni las fixtures sirven para la mitad vendible de G4: los dos son míos. Sujeto con **bytes y manifiesto de un tercero**, descargado por HTTPS sin cooperación del autor, y con dos copias que el manifiesto oficial no declara:

```
$ curl -sL -o sha256sum.txt https://github.com/jqlang/jq/releases/download/jq-1.7.1/sha256sum.txt
$ grep 'jq-linux-amd64$' sha256sum.txt > SHA256SUMS_OFICIAL
$ cp jq-linux-amd64 vendor/…  # y otra copia en vendor/third_party/

$ python3 -B examples/verificar_sello.py --manifiesto /tmp/ajeno/SHA256SUMS_OFICIAL \
    --raiz /tmp/ajeno --universo disco --completo

universo | 5 rutas | caminata con 6 exclusiones | 0 fuera del universo
1 conforme / 0 reubicado / 0 diverge / 0 opaco -> intacta
redundancia | 5942c9b0934e510ee61eb3e30273f1b3fe2590df93933a93d7c58b81d19c8ff5 | 1 declaradas | 3 observadas | jq-linux-amd64, vendor/jq-linux-amd64, vendor/third_party/jq-linux-amd64
coste | 1 declaradas | 5 barridas | 5 hasheadas
RC 0
```

El digest es el que publica jq: cualquiera lo comprueba contra el release. Y el veredicto **no se movió** pese a las dos copias — la claim es sobre los bytes declarados, el resto es censo (ley 27).

El manifiesto original declara **26 filas** (`2129 B`); el sujeto declara **una**: esto mide una fila contra un árbol, no el release entero. Declararlo es la mitad del resultado, como el dialecto.

**Lo que esta medición no es:** los bytes y el manifiesto son de jq; la **topología de copias la construí yo**. Prueba que el acto cuenta copias no declaradas de bytes ajenos; no prueba cómo se duplica el árbol de un cliente. Eso sigue en §10.

El mismo acto tardó **11 ms** sobre 5 rutas y **264,35 s** sobre 87 819 (§1.2). La diferencia no es el acto: es el universo. Es la misma ley de §8 #8 vista desde el otro extremo.

---

## 2 · Reglas de cámara

- **Fondo** `#0B0E12` · **texto** `#E8EDF2` · **ámbar** `#E0A83C` = veredicto · **cian** `#4CC3D9` = dato · **gris** `#8A949E` = laguna.
- **Monoespaciada sin ligaduras** para el recibo. El recibo no se reescribe, no se alinea «bonito» y no se traduce: si en pantalla pone `-> reubicada`, el acto imprimió `-> reubicada`.
- **Un solo movimiento por línea**: opacidad 0→1 en 120 ms, sin rebote. El clímax no se anima.
- **Sin música de tensión.** Un pulso de 60 BPM como máximo, y sólo en los cierres.
- **El nombre del sujeto se tacha a `<sujeto>`** cuando es efímero (como hace el ensayo): no se enseña una ruta de `/tmp` que el espectador no puede tener.
- **Render determinista** (regla de `letras-video`): mismo `cues.ts` ⇒ mismo MP4 bit a bit. Si dos renders del mismo guion no dan el mismo SHA-256, la pieza no está terminada.

---

## 3 · G1 · «Catorce copias» — 15 s · teaser

**Tesis:** un árbol tiene muchos más originales de los que cree. El acto no elige por ti cuál es el bueno: los cuenta.

| t | pantalla | voz |
|---|---|---|
| 0,0–2,5 | `14 archivos firmados.` | «Catorce archivos firmados.» |
| 2,5–6,0 | `206 rutas.` (cian) | «Doscientas seis rutas con esos mismos bytes.» |
| 6,0–10,5 | `10 conforme / 4 reubicado / 0 diverge / 0 opaco -> reubicada` (ámbar en el veredicto) | «Diez siguen donde el recibo dijo. Cuatro se mudaron.» |
| 10,5–13,5 | `reubicado <acta> -> 14 caminos` + `RC 0` | «Y no elige un destino por ti: publica los catorce.» |
| 13,5–15,0 | `protocol-core` | — |

**Animación:** las 206 rutas no se dibujan; se colapsan en un contador. Un árbol de puntos es opcional **sólo** si cada punto es una ruta de la lista (no una ilustración).
**Cifras:** `206` ⇒ §8 #4 · `14/4/10` ⇒ §8 #3.
**Falsador:** el comando de §1.2 tiene que seguir dando `10 conforme / 4 reubicado`. Si mañana el Sello A se mueve, este guion no se re-graba: se re-mide.

---

## 4 · G2 · «La escalera» — 45 s · pieza principal

**Tesis:** el veredicto no es un semáforo. Son seis estados distinguibles, y dos de ellos existen precisamente porque un verificador ingenuo no los ve.

| t | pantalla | voz |
|---|---|---|
| 0,0–3,0 | `Un recibo. Siete sujetos.` | «Lo mismo, siete veces, con un byte de diferencia.» |
| 3,0–8,5 | bloque 1/7 completo | «Los bytes están en su ruta. Cero barridas.» |
| 8,5–14,5 | bloque 2/7 completo | «Los mismos bytes, otra ruta.» |
| 14,5–22,0 | bloque 3/7 completo + segunda línea `cada digest sigue apareciendo una vez` | «Cada digest sigue apareciendo una vez. Y aun así no es `intacta`.» |
| 22,0–28,0 | bloque 4/7 completo | «Un byte de más.» |
| 28,0–33,0 | bloque 5/7 completo | «Sin manifiesto no hay adjudicación. Código dos, no uno.» |
| 33,0–39,5 | bloque 6/7 completo | «Copias que nadie declaró: el veredicto no cambia, el dato aparece.» |
| 39,5–43,0 | bloque 7/7 completo | «Existe en disco y el universo no lo indexa. No es un cero: es `no_medida`.» |
| 43,0–45,0 | `ENSAYO | 7/7 | RC 0` | «Siete de siete.» |

**Animación:** cada bloque entra como entra en la consola —cabecera, comando, líneas, RC— y se queda 1,5 s antes del siguiente. El bloque anterior **no se borra**: se desplaza. La escalera tiene que verse acumulada.
**Voz:** el argumento del bloque 3 —que el multiconjunto de hashes es idéntico al declarado— **no cabe** en ocho segundos y no se recita: entra como segunda línea. Es la única frase de la serie que no se dice.
**Cifras:** todos los códigos y contadores vienen literalmente de §1.1; el único número que no es del recibo es `60 BPM` (§2).
**Falsador:** `examples/ensayo_escalera.py` RC 0. Si algún bloque cambia, la pieza queda obsoleta hasta re-ensayar.

---

## 5 · G3 · «Lo que no pudo ver» — 30 s

**Tesis:** el producto no es «detecto rupturas», es **publico lo que no miré**. Todo lo demás lo intenta cualquiera; esto es lo que ningún semáforo verde hace.

| t | pantalla | voz |
|---|---|---|
| 0,0–4,0 | `2 conforme / 0 reubicado / 0 diverge / 0 opaco -> intacta` + `coste | 2 declaradas | 0 barridas | 2 hasheadas` | «Este recibo dice `intacta` y no barrió nada. ¿Se fía usted?» |
| 4,0–10,0 | mismo sujeto, ahora con `--completo` ⇒ `coste | 2 declaradas | 4 barridas | 4 hasheadas` + `redundancia | bbbff613… | 1 declaradas | 2 observadas | a.md, copia/a.md` + segunda línea `la ausencia de esa línea no era un cero` | «Con el barrido pedido el veredicto no cambia. Y aparece una copia que nadie firmó.» |
| 10,0–17,0 | `universo | 3 rutas | caminata con 6 exclusiones | 1 fuera del universo` + `opaco __pycache__/x.pyc (…)` + `-> no_medida` | «Un byte declarado que el propio universo del acto excluye no se certifica: se declara opaco.» |
| 17,0–23,0 | `RC 1` | «No es un error del programa. Es el programa diciendo dónde dejó de mirar.» |
| 23,0–30,0 | `opaco` · `no_medida` · `redundancia` (los tres en cian) | «Un instrumento que declara su ceguera es el único que un tercero puede auditar.» |

**Animación:** las tres palabras finales entran una a una. Nada más se mueve en 7 s: es el cierre intelectual de la serie.
**Cifras:** §8 #2, #5, #6, #7.
**Falsador:** P-47 (`tests/test_ubicacion.py`) y P-44/P-45 —sin `--completo`, la línea `redundancia` **no puede** aparecer; con él, el veredicto no se mueve.

---

## 6 · G4 · «Copias que nadie firmó» — 25 s

**Tesis:** el dato que el cliente compra —cuántas copias de lo firmado hay en su árbol— y la honestidad de decir cuánto de eso **no** está medido.

| t | pantalla | voz |
|---|---|---|
| 0,0–6,0 | `$ curl -sL …/jq-1.7.1/sha256sum.txt` + `26 filas · 2129 B` (cian) | «Un manifiesto que no escribí yo.» |
| 6,0–13,0 | `redundancia | 5942c9b0… | 1 declaradas | 3 observadas | jq-linux-amd64, vendor/jq-linux-amd64, vendor/third_party/jq-linux-amd64` | «Un archivo firmado por jq. Tres rutas con esos bytes.» |
| 13,0–19,0 | `1 conforme / 0 reubicado / 0 diverge / 0 opaco -> intacta` + `RC 0` + segunda línea `la copia entra como dato, no como veredicto` (gris) | «El veredicto no se mueve. La copia entra como dato.» |
| 19,0–25,0 | `14 digests | 206 rutas` (ámbar) + segunda línea `esto sí es mi árbol` | «En el mío: doscientas seis rutas. Ese árbol es mío, no el suyo.» |

**Animación:** el contador sube de 3 a 206 una sola vez, monotónico, sin easing. La segunda línea en gris entra 800 ms después que su principal.
**Cifras:** §8 #4, #10.
**Falsador:** §1.3 (la línea `1 declaradas | 3 observadas` sobre jq 1.7.1) y el agregado §1.2.
**Aviso permanente, tercio inferior en gris, de 6,0 a 19,0:** `bytes y manifiesto: jq 1.7.1 · las copias: mías`. La voz no lo dice (no cabe) y la pieza no lo esconde. Ver §10.

---

## 7 · G5 · «Verifícalo sin creerme» — 45 s · cierre

**Tesis:** el producto entero cabe en una línea: *no te pido que me creas, te doy el acto*. La pieza no enseña conclusiones: enseña los comandos y su salida, y deja el teclado al espectador.

| t | pantalla | voz |
|---|---|---|
| 0,0–5,0 | `$ git clone …` + `Ran 119 tests` + `OK` | «Un clon público. La suite entera.» |
| 5,0–13,0 | `$ python3 -B examples/verificar_sello.py --manifiesto … --raiz … --check` ⇒ `REPRODUCE | <digest>` | «El sello se re-emite y se compara consigo mismo: si la página no describe este árbol, lo dice.» |
| 13,0–21,0 | cuatro líneas `real` (gris): `343,61 s` · `164,11 s` · `67,11 s` · `264,35 s` + segunda línea `el mismo acto sobre los mismos bytes` | «Cuatro corridas del mismo acto. Sesenta y siete segundos, o trescientos cuarenta. El coste es de la máquina.» |
| 21,0–29,0 | `coste | 14 declaradas | 87855 barridas | 87819 hasheadas` (cian) | «Por eso a la página sellada no entra el reloj. Entran los contadores: cuántas declaré, cuántas barrí, cuántas hasheé.» |
| 29,0–38,0 | `ENSAYO | 7/7 | … | RC 0` | «Todo lo que vio aquí se convoca con un comando: el ensayo construye los siete sujetos.» |
| 38,0–45,0 | `git clone` + `python3 -B examples/ensayo_escalera.py` (mono, quieto) | «Si mañana esto ya no es verdad, el ensayo falla antes de que nadie tenga que creerme.» |

**Animación:** los cuatro tiempos `real` aparecen como columnas de una misma tabla, no como una gráfica de mejora: no hay tendencia, hay dispersión.
**Cifras:** §8 #1, #3, #8, #9.
**Falsador:** los propios comandos, en cámara, desde un clon en frío (§9).

---

## 8 · Tabla de cifras

| # | cifra | comando que la produce | fecha |
|---|---|---|---|
| 1 | `ENSAYO 7/7 RC 0` | `python3 -B examples/ensayo_escalera.py` | 25-Nov-2026 |
| 2 | escalera `0 / 0 / 1 / 1 / 2` | idem, columna `RC n · esperado m` | 25-Nov-2026 |
| 3 | `10 conforme / 4 reubicado … -> reubicada` · `coste | 14 declaradas | 87855 barridas | 87819 hasheadas` | §1.2 | 25-Nov-2026 |
| 4 | `14 digests | 206 rutas` | agregado de §1.2 | 25-Nov-2026 |
| 5 | `coste | 2 declaradas | 0 barridas | 2 hasheadas` | ensayo, paso 1/7 | 25-Nov-2026 |
| 6 | `coste | 2 declaradas | 4 barridas | 4 hasheadas` | ensayo, paso 6/7 | 25-Nov-2026 |
| 7 | `1 fuera del universo` · `opaco __pycache__/x.pyc` | ensayo, paso 7/7 | 25-Nov-2026 |
| 8 | `343,61 / 164,11 / 67,11 / 264,35 s` | `/usr/bin/time -p` sobre el acto (§1.2), cuatro veces en cuatro estados de máquina | 24–25 Nov-2026 |
| 9 | `Ran 119 tests` · `OK` | `python3 -B -m unittest discover -s tests` | 25-Nov-2026 |
| 10 | `redundancia | 5942c9b0… | 1 declaradas | 3 observadas` · `coste | 1 declaradas | 5 barridas | 5 hasheadas` | §1.3 (jq 1.7.1, manifiesto oficial) | 25-Nov-2026 |

`87819` y `87855` cuentan cosas distintas (rutas del universo / rutas hasheadas, que incluyen las declaradas fuera de él); no se restan entre sí. `206` es suma de longitudes de listas impresas por el acto, no una resta.

---

## 9 · Falsadores de la serie

| pieza | qué la falsa | comando |
|---|---|---|
| G1, G4 | el Sello A o el sujeto jq cambian de veredicto o de multiplicidad | §1.2 · §1.3 |
| G2, G5 | un paso del ensayo deja de coincidir | `python3 -B examples/ensayo_escalera.py` (RC ≠ 0) |
| G3 | `--completo` deja de mover el contador o mueve el veredicto | `python3 -B -m unittest tests.test_ubicacion.TestRedundancia` |
| G5 | el acto no reproduce su sello / el ancla no está vigente | `--check` sobre el acto · `contrafirmar_censo.py --check` |
| todas | la suite cae | `python3 -B -m unittest discover -s tests` |

Un guion cuya cifra ya no la produce su comando **no se corrige**: se retira y se re-mide.

**Prerrequisito de grabación, medido el 25-Nov-2026:** el veredicto de ancla necesita **historia completa**. En un `--depth 1` el acto responde `CONTRATO | git no respondió: sin ancla no hay contrafirma` —no miente y no mide—, así que el clon de G5 se hace sin `--depth 1` si la pieza va a enseñar el ancla. La suite y el ensayo sí corren en un clon superficial (`Ran 119 tests` · `OK`, `ENSAYO 7/7 RC 0`).

---

## 10 · Lo que todavía no hay que grabar

Estas son las lagunas del producto, y por eso no tienen guion:

1. **La tasa de duplicación de un árbol de cliente: `NO_MEDIDA`.** Lo medido es el acto sobre bytes ajenos (jq 1.7.1: `1 declaradas | 3 observadas`, §1.3) con **topología propia**. Cuánto se duplica el repositorio de un cliente —la cifra que compraría— no existe todavía. `--completo` la hace **medible**, no medida. Los `k = 14` del Sello A son worktrees del mismo dueño.
2. **El coste de una máquina de cliente.** Cuatro medidas del mismo acto van de 67 a 344 s, todas en esta máquina. Ninguna es «el tiempo del acto».
3. **La precedencia entre `suplantada` e `intercambiada`** está fijada sólo en la fixture (P-28).
4. **La rama de fallo de `git ls-files`** se trata como «fuera del universo» y no tiene falsador propio (sería P-48).
5. **La escalera completa contra un árbol de terceros** (un release público con `SHA256SUMS` nativo) está hecha para `intacta`/`reubicada`/`suplantada`/`divergente`, no para los siete pasos.

Grabar cualquiera de estos cinco como si estuviera medido es el único error que este archivo no puede arreglar después.

---

## 11 · Puente con `letras-video`

Cada guion es ya una tabla `(t0, t1, texto, voz)`. El paso a `cues.ts` es mecánico:

```ts
// cues.ts — G2 «La escalera»
export const cues = [
  { t0: 0.0,  t1: 3.0,  texto: "Un recibo. Siete sujetos.",               voz: "g2_01" },
  { t0: 3.0,  t1: 8.5,  texto: "=== 1/7 · intacta — los bytes declarados estan en su ruta", voz: "g2_02" },
  { t0: 14.5, t1: 22.0, texto: "0 conforme / 2 reubicado / 0 diverge / 0 opaco -> intercambiada", voz: "g2_04" },
  // …
];
```

Dos condiciones de aceptación, las mismas que ya rigen `pintar-paneo`:

- **Determinismo bit a bit:** dos renders del mismo `cues.ts` dan el mismo SHA-256 del MP4.
- **El texto de `cues.ts` no se teclea:** se copia de la salida del ensayo (§1.1). Un `cues.ts` escrito a mano es una segunda fuente de verdad, y dos fuentes divergen.

Cuando llegue el día del render, lo primero no es grabar: es volver a correr `examples/ensayo_escalera.py` y comparar. Si difiere, el guion está rancio —no el acto— y se decide cuál de los dos manda.
