# GUIONES — nueve piezas escritas antes de grabar

<!-- HUELLA-GUIONES-CON-RECIBO-20261124 --><!-- HUELLA-GUIONES-G6-AUSENCIA-20261125 -->

**Estado:** guiones cerrados · **frames renderizados: 0** · cifras medidas el 25-Nov-2026 sobre `protocol-core` y sobre el Sello A real ([`SHA256SUMS_SELLO_A`](../platino-labs/sellos-fecha-cierta-20261009/SHA256SUMS_SELLO_A)).

Este archivo no es publicidad: es **una página**, en el mismo sentido que `PREDICADO.md` y `UBICACION.md`. Todo número que un guion pone en pantalla se re-deriva con un comando que está aquí, y cada guion declara qué lo falsa. Un video que enseña una cifra que nadie puede reproducir contradice, en cámara, el producto que intenta vender.

---

## 0 · El contrato del guion — seis reglas

1. **Ninguna cifra en pantalla sin su comando.** Vale para `206 rutas` igual que para `RC 1`. La tabla [§14](#14--tabla-de-cifras) es la fuente; el guion la cita, no la recuerda.
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

**Lo que esta medición no es:** los bytes y el manifiesto son de jq; la **topología de copias la construí yo**. Prueba que el acto cuenta copias no declaradas de bytes ajenos; no prueba cómo se duplica el árbol de un cliente. Eso sigue en §16.

El mismo acto tardó **11 ms** sobre 5 rutas y **264,35 s** sobre 87 819 (§1.2). La diferencia no es el acto: es el universo. Es la misma ley de §14 #8 vista desde el otro extremo.

### 1.4 · El acto de ausencia — Sello A y jq 1.7.1

G6 no se puede grabar con un `grep`. Lo que prueba ausencia es el **orden** de la página: si dos filas adyacentes dejan a la consulta en medio, la página certifica que no está sin revelar el resto del inventario. Recibos literales, sobre el Sello A real:

```
$ python3 -B examples/verificar_ausencia.py \
    --manifiesto ../platino-labs/sellos-fecha-cierta-20261009/SHA256SUMS_SELLO_A \
    --ausente .env --raiz ../platino-labs

ausencia | .env | ausente | antes de la primera fila
pagina | 14 filas | canonica | 0 redactadas | digest ad67ece0…
testigo | ⊥ < .env < "ACTA_DE_CIERRE_DEL_BARRIDO_COGNITIVO_NULOS_EN_FRIO_20261009.md" | posicion 0
verificado | si | O(1) contra la pagina autenticada
autenticacion | si | O(n) una vez | 14 filas
caso | colapsa-el-caso | sonda protocol-core/SPEC.md -> Protocol-core/SPEC.md es el mismo inodo
arbol-ausencia | ausente | el universo lo indexa y no esta
-> ausente
RC 0
```

```
$ … --ausente AGENTS.md --raiz ../platino-labs

ausencia | AGENTS.md | ausente | entre las filas 2 y 3
testigo | "ACTA_GATE_DE_PROTOCOL_CORE_26_PRUEBAS_RC0_20261009.md" < AGENTS.md < "ASIENTO_DE_RETIRO_EXPLICITO_DEL_FRENTE_DE_PATENTES_20261009.md" | posicion 3
arbol-ausencia | presente | el arbol lo tiene y la pagina no lo declara
-> presente
RC 1
```

Los dos nombres dan `grep -c … → 0` sobre el mismo manifiesto (`probes`: `grep` RC 1 en ambos). **El mismo cero significa dos cosas distintas** y sólo el árbol dice cuál: `.env` no está en ninguna parte; `AGENTS.md` está en el árbol y el manifiesto no lo declara. Un verificador que respondiera con el `grep` habría acertado una vez y fallado la otra con la misma salida.

La tercera medición es la trampa del volumen: sobre jq 1.7.1, con el nombre en mayúsculas, un `grep`/`sha256sum -c` imprimiría verde en APFS porque el sistema de archivos no distingue el caso. El acto lo detecta y lo publica:

```
$ … --manifiesto /tmp/ajeno/SHA256SUMS_OFICIAL --ausente JQ-LINUX-AMD64 --raiz /tmp/ajeno

ausencia | JQ-LINUX-AMD64 | ausente | antes de la primera fila
testigo | ⊥ < JQ-LINUX-AMD64 < "jq-linux-amd64" | posicion 0
caso | colapsa-el-caso | sonda jq-linux-amd64 -> Jq-linux-amd64 es el mismo inodo
caso-choque | jq-linux-amd64 | la pagina prueba JQ-LINUX-AMD64 y el volumen no distingue jq-linux-amd64
arbol-ausencia | presente | el arbol lo tiene y la pagina no lo declara
-> presente
RC 1
```

**Lo que estas mediciones no son:** el Sello A y jq son sujetos reales, pero el árbol de jq lo construí yo (dos copias en `vendor/`); el caso de `.env` y `AGENTS.md` es el árbol real de `platino-labs` sin tocar un byte. Ninguna de las tres prueba cómo declara ausencias el manifiesto de un cliente: prueba que el acto **distingue los tres estados con el mismo cero delante**.

---

### 1.5 · El sujeto de negocio — una agenda, no un árbol

El anillo 3 no pide un árbol de código: pide una **página**. `examples/manifiesto-negocio.py` construye una agenda de citas y un libro de movimientos con nombres en español, acentos incluidos, y declara la pieza que el álgebra exige y que ningún dominio trae puesta: la proyección `pi(k)` —plegado de diacríticos, minúsculas, separadores colapsados a `-`—.

```
ausencia | avila-cita-09-30-sillon1.tsv | ausente | entre las filas 0 y 1
orden | colacion C sobre bytes UTF-8 (alfabeto §2.1: NFC es la identidad)
pagina | 7 filas | canonica | 0 redactadas | digest f6d1b10923c9563ebe40dec7a3af09224adf1a1e2ebd10ff5753b326b463a912
testigo | "avila-cita-09-00-sillon1.tsv" < avila-cita-09-30-sillon1.tsv < "montes-cita-11-15-sillon3.tsv" | posicion 1
verificado | si | O(1) contra la pagina autenticada
autenticacion | si | O(n) una vez | 7 filas
coste | 7 declaradas | 7 autenticadas | sin merkle
-> ausente
```

Tres cosas que esta agenda mide y un `grep` de exportador no:

- **El orden del exportador no es el objeto.** El mismo conjunto de siete filas escrito en dos órdenes de archivo —uno por la clave canónica, otro por el nombre original, donde `Á` empieza en `0xC3` y cae detrás de toda la ASCII— da **el mismo** `digest f6d1b109…`, el mismo testigo y el mismo `-> ausente`. Lo único que cambia es la bandera: `| canonica |` contra `| desordenada |`. El acto ordena y publica que ordenó.
- **`pi` se aplica antes de que la página exista.** Una ruta con un byte fuera de `A-Za-z0-9._-` no se normaliza a la callada: `ENTRADA INVALIDA | … | componente no admisible como slug`, RC 2. Un acento que se cae sin decirlo es una fila que desaparece.
- **Dos clientes con la misma `pi` son un cliente.** `Ávila-cita-09-00-sillon1` y `AVILA-CITA-09-00-SILLON1` proyectan a la misma clave y el acto **no sella**: `CONTRATO | colapsa-el-caso: … proyectan a la misma clave 'avila-cita-09-00-sillon1'` · `-> no se emite: una clave que colapsa se resuelve, no se sella` · RC 1. Adivinar cuál de los dos es el bueno sería inventar la respuesta del dueño.

**Lo que esta medición no es:** el manifiesto lo escribimos nosotros. Prueba que el álgebra funciona fuera de un árbol de software; **no** prueba que un manifiesto firmado por un cliente se comporte igual. Eso sigue en §16.

---

### 1.6 · La cadena — dos recibos que se componen

El anillo 4 no mide un salto: mide la **composición** de dos, `R_AB ∘ R_BC`, y el objeto que produce tiene que servirle a un auditor que nunca vio B. Sobre la misma agenda de §1.5, con B releyendo el libro y C recibiendo el paquete de B:

```
cadena | A -325c7ca8fb07-> B -325c7ca8fb07-> C
tramos | 2 | peor | reubicada
ausencia vigente | avila-cita-09-30-sillon1.tsv | "avila-cita-09-00-sillon1.tsv" < avila-cita-09-30-sillon1.tsv < "montes-cita-11-15-sillon3.tsv"
-> reubicada
```

Y el mismo par de saltos con la frontera rota —B firmó una página y C leyó otra—:

```
cadena | A -325c7ca8fb07-> B -325c7ca8fb07-> C
tramos | 2 | peor | frontera_rota
frontera | rota | el tramo anterior dejo 325c7ca8fb07 y el siguiente leyo 196b31a91400
ausencia sin transito | avila-cita-09-30-sillon1.tsv | probada contra la pagina final y la cadena no sostiene
-> frontera_rota
```

El tercer objeto es el que hace la cadena auditable desde fuera. `examples/verificar_recibo_externo.py` recibe **sólo** el manifiesto y el JSON del recibo —no importa `protocol`, no ve el generador— y recomputa todo:

```
tramo | A->B | intacta | 7 filas | 325c7ca8fb07
testigo | avila-cita-09-30-sillon1.tsv | ausente | avila-cita-09-00-sillon1.tsv < consulta < montes-cita-11-15-sillon3.tsv
tramo | B->C | reubicada | 7 filas | 325c7ca8fb07
veredicto | reubicada | recalculado sobre 2 tramos | sostiene si
manifiesto | 7 filas | 325c7ca8fb07 | archivo ya canonico
limite | el verificador comprueba que las paginas encadenadas son las mismas; no que B hiciera su trabajo
-> cierra
```

Cuatro cosas que esta cadena mide y que dos recibos sueltos no dicen:

- **El orden no se inventa dos veces.** El veredicto compuesto es el **peor** de los tramos, y «peor» usa el orden que ya publicaba [`UBICACION.md` §4](UBICACION.md): el mismo que decide el RC de un acto simple. Con dos órdenes, la misma cadena daría dos certificados según quién la leyera.
- **El neutro se absorbe.** `R_AB ∘ Id_B = R_AB` con el mismo veredicto, la misma cadena y los mismos testigos: un tramo de identidad que sobreviviera haría crecer la traza con saltos que no existieron. Y una identidad **enferma** —`B -> B` en `no_medida`— no se absorbe: un neutro que no certifica nada es un hueco con forma de neutro.
- **El testigo tiene tres estados, no dos.** `ausencia vigente` (la página que lo prueba es la que llega **y** la cadena sostiene), `ausencia historica` (se probó contra otra página: envejeció el testigo) y `ausencia sin transito` (el testigo no envejeció; lo que falta es el camino). La tercera impide el atajo: con la frontera rota, C puede leer una página cuyo digest coincide con el de A y el testigo encaja por digest mientras la cadena no une los extremos.
- **`FRONTERA_ROTA` ordena por encima de `divergente`.** Un tramo `divergente` dice que algo cambió; una frontera rota dice que los dos tramos no hablan del mismo objeto, y con eso no hay cadena que componer.

**Lo que esta medición no es:** certifica **continuidad de bytes entre saltos**, no que B aplicara la regla acordada. Un recibo de integridad leído como recibo de corrección es el falso verde con firma. Y la cadena no se abarata por componerla: verificar un salto sigue costando O(página).

### 1.7 · El portador — el archivo que trae el cliente

Todo lo anterior supone que el manifiesto se puede leer. Medido el 25-Nov-2026 sobre cinco portadores realmente publicados (jq 1.7.1, Node v22.11.0, gh 2.62.0, Fedora 41 y el `Release` de Debian 12.15) más uno sintético de dos filas: el lector de un solo dialecto leyó **dos**, rechazó tres y **acusó de alterado un archivo intacto**. El portador de Debian, con sus 772 filas intactas:

```
portador | deb822 | 772 filas | canonico | digest c0dc59762595
sobre | ninguno | 0 bytes de firma | no habia nada que verificar
envoltura | seccion SHA256 | 13 bloques ignorados
```

El de Node, que trae las filas en otro orden, publica las dos cosas a la vez —que lo leyó y que lo reordenó—:

```
portador | coreutils | 41 filas | reordenado | digest 23aaeb143953
sobre | ninguno | 0 bytes de firma | no habia nada que verificar
envoltura | ninguna | 0 normalizaciones
```

El de Fedora viene dentro de un mensaje firmado en claro. Desde el anillo 6 el sobre se **desenvuelve**, y se dice cuánto no se comprobó:

```
portador | bsd | 1 filas | canonico | digest 9bc34ed33916
sobre | firmado_en_claro | 832 bytes de firma | carga bc3ba445957b | sobre f482e55b35f5 | firma no verificada
envoltura | ninguna | 0 normalizaciones
```

**Corrección de esta misma página.** Hasta el anillo 6, las dos primeras salidas de arriba decían `envoltura | … | firma no verificada`, y el `Release` de Debian no tiene **ni un byte** de PGP. La nota del censo que lo justificaba —«la firma PGP final no se verifica»— describía un artefacto que no era el vendoreizado. Un punto ciego inventado es tan grave como un verde falso: al auditor le impide distinguir «no pude verificarlo» de «no había nada que verificar». Las dos líneas se re-midieron y se publican como estaban medidas (§1.8).

Y el testigo del anillo: el mismo archivo de dos filas, dos lecturas, dos digests. El `Release` de Debian es `deb822` **por su espacio inicial**; quitarlo lo convierte en un archivo de `coreutils` cuyas rutas empiezan por el tamaño:

```
portador | deb822 | 2 filas | canonico | digest 7674c4bedf05
portador | coreutils | 2 filas | canonico | recorte | digest f2ba089a097c
  (' 840868 contrib/Contents-amd64', 'd6c9c82f4e61…')
```

Sobre el archivo completo esa segunda lectura **no existe**: 58 de sus 772 filas llenan el campo del tamaño y rompen la alineación de `coreutils`. Sobre un extracto de 12 filas, las doce encajan. La ambigüedad no es del formato: es del **ejemplo** que se publica.

**Lo que esta medición no es:** no verifica la firma PGP (`firma no verificada`, y se publica así), no admite la convención de escape `\ruta` de `coreutils`, no acepta SRI en base64, no adivina el nombre de un portador `suelto` y no elige entre dos lecturas: las publica. Atestigua la **línea**, no al autor.

### 1.8 · El sobre — el archivo no es el objeto

El mismo autor, el mismo contenido, tres artefactos descargados de `deb.debian.org` el 25-Nov-2026 a las `19:31:13Z`:

| archivo | bytes | topología | antes del anillo 6 |
|---|---|---|---|
| `debian-12.15-Release` | 149 266 | `sin_sobre` | 772 filas, `c0dc59762595` |
| `debian-12.15-InRelease` | 151 075 | `firmado_en_claro` | **rechazado**: `linea 4: 'Origin: Debian'` |
| `debian-12.15-Release.gpg` | 1 760 | `firma_pegada` | **0 filas, en silencio** |

Quitado el sobre, el `InRelease` **es** el `Release`: 149 266 bytes cuyo `sha256` es `abcf5882746e0f68…`, el que publica Debian. Las tres topologías, leídas hoy:

```
sobre | firmado_en_claro | 1759 bytes de firma | carga abcf5882746e | sobre 77737fa4b34f | firma no verificada
sobre | ninguno | 0 bytes de firma | no habia nada que verificar
SobreSinCarga: firma pegada de 1759 bytes, sin carga: el manifiesto esta en otro archivo y su nombre no viaja dentro de este
```

Y las dos vías del mismo objeto publican **la misma página**, que es lo que el cliente compra:

```
portador | deb822 | 772 filas | canonico | digest c0dc59762595     (Release)
portador | deb822 | 772 filas | canonico | digest c0dc59762595     (InRelease)
```

El error que costó una corrida: reconstruir la carga perdiendo el salto de línea final da `149265` bytes y `c8394efad1f4` en vez de `149266` y `abcf5882746e`. Un byte de separador entre la carga y el bloque de firma, y el digest del objeto deja de ser el del autor.

**Lo que esta medición no es:** no verifica la firma —no hay clave pública en este anillo— y por eso `firma no verificada` viaja **con su número de bytes**: 3 de los 10 artefactos del censo tienen firma y 7 publican `0 bytes de firma`. La frecuencia del escape `- ` de RFC 4880 en lo publicado es `0` de `10` y se declara `no_medida`; la transformación se mide por testigo sintético. Detalle: [`SOBRE.md`](SOBRE.md).

---

### 1.9 · La conservación — la magnitud que sobrevive

El sobre (§1.8) separa archivo de objeto, y ninguno de los dos pregunta si lo que va **dentro** de la página está bien calculado. La cadena de §1.6 hereda esa misma ceguera: dos saltos `intactas` dan un recibo `intacto` aunque el nodo de en medio haya recalculado sus tres filas. La conservación es la primera medida de la serie que **no mira bytes**: el cliente declara una magnitud sobre la página, y la cadena comprueba que se lee igual en los dos extremos.

Dos medidas declaradas, la misma cadena de tres nodos, dos veredictos:

```
conservacion | A -> B -> C
medida | filas | declarada por el cliente
salto | A->B | filas | filas=3 -> filas=3 | conservada
salto | B->C | filas | filas=3 -> filas=3 | conservada
limite | conserva el transporte, no el calculo: la magnitud elegida puede sobrevivir a un valor mal calculado
-> conservada
```

```
conservacion | A -> B -> C
medida | claves | declarada por el cliente
salto | A->B | claves | claves=17849efefd40 -> claves=17849efefd40 | conservada
salto | B->C | claves | claves=17849efefd40 -> claves=37cc1abd699d | no_conservada
degradado | B->C | no_conservada
limite | conserva el transporte, no el calculo: la magnitud elegida puede sobrevivir a un valor mal calculado
-> no_conservada
```

La misma cadena, las mismas páginas, dos veredictos opuestos. No es una contradicción: es la única lección que la pieza tiene. `filas=3` cuenta entradas y no ve que `B` recalculó sus tres digests; `claves` autentica el **conjunto de rutas** —descartando los digests a propósito— y por eso tampoco ve el recálculo, pero sí ve que `C` movió una cita del sillón 2 al 4. Una medida más fina implica la más gruesa y no al revés (P-100e), y **ninguna de las dos mira el valor de la fila**.

**Lo que esta medición no es:** la conservación *no* certifica que `B` calculara bien. Una cadena `conservada` dice que la magnitud que el cliente eligió sobrevivió el transporte; si `B` suma mal y su página conserva la cuenta, la cadena no tiene con qué acusarlo. Por eso la línea `limite` viaja en las dos salidas, también en la verde: un `conservada` sin esa línea se leería como una certificación aritmética que este anillo no hace. Álgebra, cadena de refinamiento y los 29 falsadores P-99…P-106: [`CONSERVACION.md`](CONSERVACION.md).

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
**Cifras:** `206` ⇒ §14 #4 · `14/4/10` ⇒ §14 #3.
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
| 39,5–43,0 | bloque 7/7 completo | «En disco, fuera del universo: `no_medida`.» |
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
**Cifras:** §14 #2, #5, #6, #7.
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
**Cifras:** §14 #4, #10.
**Falsador:** §1.3 (la línea `1 declaradas | 3 observadas` sobre jq 1.7.1) y el agregado §1.2.
**Aviso permanente, tercio inferior en gris, de 6,0 a 19,0:** `bytes y manifiesto: jq 1.7.1 · las copias: mías`. La voz no lo dice (no cabe) y la pieza no lo esconde. Ver §14.

---

## 7 · G6 · «Lo que no está» — 30 s

**Tesis:** la mitad del trabajo de un auditor no es probar lo que hay, es probar lo que **no** hay: que el lote no lleva la clave privada, que el expediente no incluye el registro borrado. Un `grep` no prueba ausencia — prueba que buscó. Lo que prueba ausencia es un **testigo de orden**: dos filas adyacentes que dejan a la consulta en medio.

| t | pantalla | voz |
|---|---|---|
| 0,0–5,0 | `$ grep -c '\.env' SHA256SUMS_SELLO_A` → `0` · `$ grep -c 'AGENTS.md' …` → `0` (gris) | «El mismo cero para los dos nombres. Un cero no distingue dos verdades.» |
| 5,0–13,0 | `testigo | ⊥ < .env < "ACTA_DE_CIERRE…md" | posicion 0` + `verificado | si | O(1) contra la pagina autenticada` + `-> ausente` `RC 0` | «Éste sí falta, y la página lo prueba por sus vecinos: entre el principio y la primera fila no cabe nada. Una consulta.» |
| 13,0–21,0 | `testigo | "ACTA_GATE…md" < AGENTS.md < "ASIENTO_DE_RETIRO…md" | posicion 3` + `arbol-ausencia | presente | el arbol lo tiene y la pagina no lo declara` + `-> presente` `RC 1` | «Éste está: el manifiesto no lo declara y el árbol lo tiene. Mismo cero, otra verdad.» |
| 21,0–27,0 | `caso | colapsa-el-caso` + `caso-choque | jq-linux-amd64 | la pagina prueba JQ-LINUX-AMD64 y el volumen no distingue jq-linux-amd64` + `-> presente` `RC 1` | «Y en un volumen que ignora mayúsculas, preguntar por `JQ-LINUX-AMD64` devolvería un verde. Devuelve `presente`.» |
| 27,0–30,0 | `ausente` · `presente` · `no_medida` (los tres en cian) | «Ausencia probada. Presencia declarada. Lo no mirado, dicho.» |

**Animación:** las tres palabras del cierre entran igual que en G3: la serie tiene un solo final visual y no inventa gramática nueva.
**Cifras:** §14 #11, #12, #13.
**Falsador:** `python3 -B -m unittest tests.test_ausencia` (27 pruebas) y los recibos de §1.4.
**Aviso permanente, tercio inferior en gris, mientras dura la fila 21,0–27,0:** `volumen APFS sin distinción de mayúsculas · sonda escribe 0 bytes`.

---

## 8 · G7 · «La cita que no existió» — 30 s · pieza de dominio

**Tesis:** el mismo testigo de orden que prueba que un `.env` no está en un lote prueba que una cita no está en una agenda — y lo prueba **sin enseñar las otras citas**. Ahí el producto sale del software: un estudio, una clínica o un banco pueden atestiguar la ausencia de un registro sin entregar el libro.

| t | pantalla | voz |
|---|---|---|
| 0,0–5,0 | `pagina | 7 filas | canonica | digest f6d1b109…` (cian) | «Siete citas firmadas. Ninguna es la de las nueve y media.» |
| 5,0–13,0 | `testigo | "avila-cita-09-00-sillon1.tsv" < avila-cita-09-30-sillon1.tsv < "montes-cita-11-15-sillon3.tsv" | posicion 1` + `verificado | si | O(1) contra la pagina autenticada` + `-> ausente` `RC 0` (ámbar en el veredicto) | «Entre las nueve y las once y cuarto no cabe nada. Una consulta lo prueba.» |
| 13,0–21,0 | `pagina | 7 filas | canonica | … digest f6d1b109…` arriba · `pagina | 7 filas | desordenada | … digest f6d1b109…` abajo (mismo digest, en cian los dos) | «Dos exportadores, dos órdenes. El mismo sello: el orden no era el objeto.» |
| 21,0–27,0 | `CONTRATO | colapsa-el-caso: 'Ávila-cita-09-00-sillon1' y 'AVILA-CITA-09-00-SILLON1' proyectan a la misma clave` + `-> no se emite: una clave que colapsa se resuelve, no se sella` `RC 1` (ámbar) | «Ávila y AVILA son el mismo cliente. El acto no adivina: se detiene.» |
| 27,0–30,0 | `ausente` · `presente` · `no_medida` (los tres en cian) | «Ausencia probada. Presencia declarada. Lo demás, no mirado.» |

**Animación:** la de G3 y G6 —la serie tiene un solo final visual y no inventa gramática nueva.
**Cifras:** §14 #14, #15.
**Falsador:** `python3 -B -m unittest tests.test_negocio` (13 pruebas) y los recibos de §1.5.
**Aviso permanente, tercio inferior en gris, mientras dura la fila 21,0–27,0:** `los nombres son de un sujeto escrito por nosotros · ningún cliente ha firmado este manifiesto`.

---

## 9 · G8 · «La cadena que no se rompe» — 30 s · pieza de composición

**Tesis:** cuando el paquete pasa por manos que no son las del dueño, no basta con dos recibos: hace falta un **recibo compuesto** que nombre a la vez lo que viajó y el punto donde la cadena dejó de hablar del mismo objeto. Es la pieza para quien ya tiene el dato repartido entre un exportador, un worker y un auditor.

| t | pantalla | voz |
|---|---|---|
| 0,0–5,0 | `cadena \| A -325c7ca8fb07-> B -325c7ca8fb07-> C` (cian) | «Dos saltos. Un solo objeto.» |
| 5,0–13,0 | `tramos \| 2 \| peor \| reubicada` + `ausencia vigente \| avila-cita-09-30-sillon1.tsv \| "…09-00…" < … < "montes…"` + `-> reubicada` (ámbar) | «La cita sigue ausente tres nodos después. El testigo viaja con la cadena.» |
| 13,0–21,0 | `frontera \| rota \| el tramo anterior dejo 325c7ca8fb07 y el siguiente leyo 196b31a91400` + `-> frontera_rota` (ámbar) | «El nodo intermedio cambió el libro. La cadena no cierra, y sin cadena no hay recibo.» |
| 21,0–27,0 | `ausencia sin transito \| … \| probada contra la pagina final y la cadena no sostiene` + `veredicto \| reubicada \| recalculado sobre 2 tramos \| sostiene si` + `limite \| … no que B hiciera su trabajo` (gris) | «Ni vigente ni histórica: el testigo es el mismo y el camino no.» |
| 27,0–30,0 | `reubicada` · `frontera_rota` · `no_medida` (los tres en cian) | «Lo que viajó. Lo que se rompió.» |

**Animación:** la de G3, G6 y G7 —tres palabras al cierre, mismo movimiento, misma opacidad—; lo nuevo es el empalme: la línea `frontera` entra **entre** los dos digests, no encima.
**Cifras:** §14 #16, #17.
**Falsador:** `python3 -B -m unittest tests.test_composicion` (22 pruebas) y los recibos de §1.6.
**Aviso permanente, tercio inferior en gris, mientras dura la fila 13,0–21,0:** `continuidad de bytes entre saltos · no que el nodo intermedio hiciera su trabajo`.

---

## 10 · G9 · «Tu manifiesto, no el mío» — 30 s · pieza de portador

**Tesis:** el cliente no nos entrega un árbol limpio: nos entrega el archivo que su herramienta escribió. La pieza enseña el mismo recibo naciendo sobre cinco portadores distintos y, sobre todo, enseña el archivo que el lector viejo **acusó** de estar alterado cuando estaba intacto. Es la pieza para quien ya intentó verificar un release ajeno y se topó con un «OK» que no miraba lo que decía mirar.

| t | pantalla | voz |
|---|---|---|
| 0,0–5,0 | `portador \| coreutils \| 26 filas \| canonico \| digest f1f692fe9f92` (cian) | «El manifiesto de jq. Veintiséis filas.» |
| 5,0–13,0 | `portador \| bsd \| 1 filas …` + `envoltura \| pgp \| firma no verificada` + `portador \| deb822 \| 772 filas \| canonico \| digest c0dc59762595` (cian, tres columnas) | «Fedora lo firma. Debian lo pagina en setecientas setenta y dos filas. El mismo recibo, tres archivos.» |
| 13,0–21,0 | `portador \| coreutils \| 41 filas \| reordenado \| digest 23aaeb143953` (ámbar) + `dddf2b497e71` en gris debajo | «Node lo escribió en otro orden. Lo leí, lo dije, y publiqué los dos digests.» |
| 21,0–27,0 | `portador \| deb822 \| 2 filas \| canonico \| digest 7674c4bedf05` + `portador \| coreutils \| 2 filas \| … recorte \| digest f2ba089a097c` + `881cba55a9d2` en rojo tachado | «El archivo estaba intacto. El lector de un solo dialecto lo llamó alterado.» |
| 27,0–30,0 | `coreutils` · `bsd` · `deb822` · `suelto` (los cuatro en cian) | «Cuatro gramáticas. Ninguna elegida a ciegas.» |

**Animación:** las tres primeras columnas entran con el movimiento de siempre; lo nuevo es el **tachado** de `881cba55a9d2` en 21,0–27,0 —una sola línea roja que cruza el digest, 200 ms, sin rebote—, porque lo que se retira es una acusación, no un dato.
**Cifras:** §14 #18, #19.
**Falsador:** `python3 -B -m unittest tests.test_portador` (21 pruebas) y los ocho artefactos de `examples/portadores/` con su `FUENTES.txt`.
**Aviso permanente, tercio inferior en gris, mientras dura la fila 21,0–27,0:** `la firma no se verifica · se atestigua la linea, no al autor`.

---

## 11 · G10 · «El archivo no es el objeto» — 30 s · pieza de sobre

**Tesis:** dos archivos del mismo autor, con los mismos 149 266 bytes dentro, dan **dos digests** —el del archivo y el del objeto— y el cliente paga precisamente por esa distinción. La pieza enseña el `InRelease` de Debian que el lector viejo rechazaba culpando a su contenido, y la firma pegada que se leía como un manifiesto de cero filas.

| t | pantalla | voz |
|---|---|---|
| 0,0–5,0 | `sobre \| firmado_en_claro \| 1759 bytes de firma` + `carga abcf5882746e` y `sobre 77737fa4b34f` (cian, dos columnas) | «El mismo archivo. Dos digests.» |
| 5,0–12,0 | `sobre \| ninguno \| 0 bytes de firma \| no habia nada que verificar` (gris) | «Debian también publica el archivo sin firmar. Digo cuál tengo.» |
| 12,0–20,0 | `sobre \| firma_pegada \| 1759 bytes de firma \| carga -` + `SobreSinCarga` (ámbar) | «La firma pegada no trae el objeto. Su vínculo es el nombre.» |
| 20,0–26,0 | `portador \| deb822 \| 772 filas \| canonico \| digest c0dc59762595` dos veces, columnas idénticas | «Dos archivos, una página: setecientas setenta y dos filas.» |
| 26,0–30,0 | `firma no verificada` (ámbar) + `0 bytes de firma` (gris) | «Lo que no comprobé, con su número de bytes.» |

**Animación:** las dos columnas de 20,0–26,0 se dibujan **a la vez y con el mismo movimiento**, y las dos cifras finales quedan alineadas al carácter; el único remarcado es el `-` de `carga -` en 12,0–20,0, que late una vez y se queda quieto, porque nombra una ausencia y no un error.
**Cifras:** §14 #20, #21.
**Falsador:** `python3 -B -m unittest tests.test_sobre` (13 pruebas) y los tres artefactos de Debian en `examples/portadores/`.
**Aviso permanente, tercio inferior en gris, desde 26,0:** `la firma no se verifica · se mide cuánto no se verificó`.

---

## 12 · G11 · «La cuenta sobrevive, el cálculo no» — 30 s · pieza de conservación

**Tesis:** la cadena de G8 dice que los bytes llegaron; no dice que lo que el nodo de en medio puso dentro esté bien sumado. La conservación es la primera medida de la serie que **no es un byte**: el cliente declara una magnitud —cuántas filas, qué claves— y la cadena comprueba que se lee igual en los dos extremos. La pieza enseña el mismo trío de nodos dando **dos veredictos opuestos** según la medida declarada, y la línea de límite que acompaña a los dos.

| t | pantalla | voz |
|---|---|---|
| 0,0–6,0 | `medida \| filas \| declarada por el cliente` + `filas=3 -> filas=3` (cian) | «Tres citas entran. Tres citas salen.» |
| 6,0–13,0 | `salto \| A->B \| filas \| filas=3 -> filas=3 \| conservada` y `salto \| B->C \| filas \| … \| conservada` | «La cuenta se conserva aunque los bytes cambien todos.» |
| 13,0–20,0 | `manifiesto B: las tres filas, recalculadas` (gris) + `salto \| A->B \| claves \| … \| conservada` (ámbar) | «B recalculó las tres filas. Ninguna de las dos medidas lo vio.» |
| 20,0–26,0 | `salto \| B->C \| claves \| claves=17849efefd40 -> claves=37cc1abd699d \| no_conservada` + `degradado \| B->C \| no_conservada` | «C movió una cita de sillón, y ahí sí acusa.» |
| 26,0–30,0 | `limite \| conserva el transporte, no el calculo: …` (ámbar, tercio inferior) | «Conserva el transporte. Del cálculo no responde.» |

**Animación:** las dos corridas del acto se dibujan **una después de la otra sobre el mismo trío de nodos**, sin mover cajas: lo único que cambia entre 6,0–13,0 y 20,0–26,0 es la palabra `filas` por `claves`. La línea `limite` no se anima: aparece completa y se queda, porque es la condición de lectura de todo lo anterior.
**Cifras:** §14 #22, #23.
**Falsador:** `python3 -B -m unittest tests.test_conservacion` (26 pruebas) y el acto de tercero `python3 -B examples/verificar_conservacion.py --demo` (§1.9).
**Aviso permanente, tercio inferior en gris, desde 26,0:** `la conservación mide el transporte · el cálculo queda fuera`.

---

## 13 · G5 · «Verifícalo sin creerme» — 45 s · cierre

**Tesis:** el producto entero cabe en una línea: *no te pido que me creas, te doy el acto*. La pieza no enseña conclusiones: enseña los comandos y su salida, y deja el teclado al espectador.

| t | pantalla | voz |
|---|---|---|
| 0,0–5,0 | `$ git clone …` + `Ran 299 tests` + `OK` | «Un clon público. La suite entera.» |
| 5,0–13,0 | `$ python3 -B examples/verificar_sello.py --manifiesto … --raiz … --check` ⇒ `REPRODUCE | <digest>` | «El sello se re-emite y se compara consigo mismo: si la página no describe este árbol, lo dice.» |
| 13,0–21,0 | cuatro líneas `real` (gris): `343,61 s` · `164,11 s` · `67,11 s` · `264,35 s` + segunda línea `el mismo acto sobre los mismos bytes` | «Cuatro corridas del mismo acto. Sesenta y siete segundos, o trescientos cuarenta. El coste es de la máquina.» |
| 21,0–29,0 | `coste | 14 declaradas | 87855 barridas | 87819 hasheadas` (cian) | «Por eso a la página sellada no entra el reloj. Entran los contadores: cuántas declaré, cuántas barrí, cuántas hasheé.» |
| 29,0–38,0 | `ENSAYO | 7/7 | … | RC 0` | «Todo lo que vio aquí se convoca con un comando: el ensayo construye los siete sujetos.» |
| 38,0–45,0 | `git clone` + `python3 -B examples/ensayo_escalera.py` (mono, quieto) | «Si mañana esto ya no es verdad, el ensayo falla antes de que nadie tenga que creerme.» |

**Animación:** los cuatro tiempos `real` aparecen como columnas de una misma tabla, no como una gráfica de mejora: no hay tendencia, hay dispersión.
**Cifras:** §14 #1, #3, #8, #9.
**Falsador:** los propios comandos, en cámara, desde un clon en frío (§15).

---

## 14 · Tabla de cifras

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
| 9 | `Ran 299 tests` · `OK` | `python3 -B -m unittest discover -s tests` | 27-Nov-2026 |
| 10 | `redundancia | 5942c9b0… | 1 declaradas | 3 observadas` · `coste | 1 declaradas | 5 barridas | 5 hasheadas` | §1.3 (jq 1.7.1, manifiesto oficial) | 25-Nov-2026 |
| 11 | `ausencia | .env | ausente` · `testigo | ⊥ < .env < …` · `RC 0` | §1.4 | 25-Nov-2026 |
| 12 | `ausencia | AGENTS.md | ausente` · `arbol-ausencia | presente` · `-> presente` · `RC 1` | §1.4 | 25-Nov-2026 |
| 13 | `caso-choque | jq-linux-amd64 | …` · `caso | colapsa-el-caso` · `RC 1` | §1.4 (sujeto jq 1.7.1) | 25-Nov-2026 |
| 14 | `pagina | 7 filas | canonica` y `… | desordenada` · **mismo** `digest f6d1b109…` | §1.5 | 25-Nov-2026 |
| 15 | `ausencia | avila-cita-09-30-sillon1.tsv | ausente` · `testigo | "…09-00…" < … < "montes…"` · `coste | 7 declaradas | 7 autenticadas` | §1.5 | 25-Nov-2026 |
| 16 | `cadena | A -325c7ca8fb07-> B -325c7ca8fb07-> C` · `tramos | 2 | peor | reubicada` · `ausencia vigente | …` | §1.6 | 25-Nov-2026 |
| 17 | `frontera | rota | … 325c7ca8fb07 … 196b31a91400` · `ausencia sin transito | …` · `veredicto | reubicada | recalculado sobre 2 tramos` | §1.6 | 25-Nov-2026 |
| 18 | `portador | deb822 | 772 filas | canonico | digest c0dc59762595` · `portador | bsd | 1 filas …` · `portador | coreutils | 41 filas | reordenado | digest 23aaeb143953` | §1.7 · `tests.test_portador` | 25-Nov-2026 |
| 19 | `deb822 2 filas 7674c4bedf05` y `coreutils 2 filas … recorte f2ba089a097c` sobre **el mismo archivo** · el acusado `881cba55a9d2` | §1.7 | 25-Nov-2026 |
| 20 | `sobre \| firmado_en_claro \| 1759 bytes de firma \| carga abcf5882746e \| sobre 77737fa4b34f` · `sobre \| ninguno \| 0 bytes de firma` · `SobreSinCarga` sobre `firma_pegada` | §1.8 · `tests.test_sobre` | 25-Nov-2026 |
| 21 | las dos vías del mismo objeto: `carga 149266 B abcf5882746e` por `Release` y por `InRelease` · el error medido: `149265 B c8394efad1f4` al perder el salto final | §1.8 · §7 de [`SOBRE.md`](SOBRE.md) | 25-Nov-2026 |
| 22 | `conservacion \| A -> B -> C` · `medida \| filas` · `salto \| A->B \| filas \| filas=3 -> filas=3 \| conservada` · `-> conservada` | §1.9 · `examples/verificar_conservacion.py --demo` | 27-Nov-2026 |
| 23 | la misma cadena con `medida \| claves`: `claves=17849efefd40 -> claves=37cc1abd699d` · `degradado \| B->C \| no_conservada` · `-> no_conservada` | §1.9 · `--demo --medida claves` | 27-Nov-2026 |

`87819` y `87855` cuentan cosas distintas (rutas del universo / rutas hasheadas, que incluyen las declaradas fuera de él); no se restan entre sí. `206` es suma de longitudes de listas impresas por el acto, no una resta.

La cifra 9 **no se copia al grabar**: la suite crece y el recibo en pantalla es el que vale. Va respaldada por `tests/test_guiones.py`, que compara el número de esta tabla con `unittest.defaultTestLoader.discover('tests').countTestCases()`; si la suite cambia y la tabla no, la prueba cae. Una cifra de guion sin lector envejece en la copia (A0.7).

---

## 15 · Falsadores de la serie

| pieza | qué la falsa | comando |
|---|---|---|
| G1, G4 | el Sello A o el sujeto jq cambian de veredicto o de multiplicidad | §1.2 · §1.3 |
| G2, G5 | un paso del ensayo deja de coincidir | `python3 -B examples/ensayo_escalera.py` (RC ≠ 0) |
| G3 | `--completo` deja de mover el contador o mueve el veredicto | `python3 -B -m unittest tests.test_ubicacion.TestRedundancia` |
| G5 | el acto no reproduce su sello / el ancla no está vigente | `--check` sobre el acto · `contrafirmar_censo.py --check` |
| G6 | el mismo `grep` vuelve a distinguir dos verdades, o el caso 21,0–27,0 deja de dar `presente` | `python3 -B -m unittest tests.test_ausencia` · §1.4 |
| G7 | la cita ausente deja de dar `ausente` RC 0, dos órdenes dejan de dar el mismo digest, o un choque de `pi` deja de detener el acto | `python3 -B -m unittest tests.test_negocio` · §1.5 |
| G8 | la cadena deja de nombrar el tramo degradado, el neutro deja de absorberse, o una frontera rota vuelve a heredar la ausencia | `python3 -B -m unittest tests.test_composicion` · §1.6 |
| G9 | un portador real deja de leerse, el archivo intacto vuelve a ser acusado, o un extracto deja de abrir dos lecturas | `python3 -B -m unittest tests.test_portador` · §1.7 |
| G10 | el sobre deja de dar el `sha256` del `Release`, una `firma_pegada` vuelve a leerse como manifiesto de cero filas, o `firma no verificada` aparece sobre un archivo sin firma | `python3 -B -m unittest tests.test_sobre` · §1.8 |
| G11 | la misma cadena deja de dar dos veredictos distintos según la medida, o una medida ausente deja de dar `sin_medida` | `python3 -B -m unittest tests.test_conservacion` · §1.9 |
| todas | la suite cae | `python3 -B -m unittest discover -s tests` |

Un guion cuya cifra ya no la produce su comando **no se corrige**: se retira y se re-mide.

**Prerrequisito de grabación, medido el 25-Nov-2026:** el veredicto de ancla necesita **historia completa**. En un `--depth 1` el acto responde `CONTRATO | git no respondió: sin ancla no hay contrafirma` —no miente y no mide—, así que el clon de G5 se hace sin `--depth 1` si la pieza va a enseñar el ancla. El ensayo sí corre en un clon superficial (`ENSAYO | 7/7 | … | RC 0`, re-medido el 27-Nov-2026); la suite no: su censo de etiquetas exige las etiquetas publicadas, un `--depth 1` sólo trae las que apuntan a la punta, y el censo sin universo acusa la ausencia en vez de dar un verde vacío.

---

## 16 · Lo que todavía no hay que grabar

Estas son las lagunas del producto, y por eso no tienen guion:

1. **La tasa de duplicación de un árbol de cliente: `NO_MEDIDA`.** Lo medido es el acto sobre bytes ajenos (jq 1.7.1: `1 declaradas | 3 observadas`, §1.3) con **topología propia**. Cuánto se duplica el repositorio de un cliente —la cifra que compraría— no existe todavía. `--completo` la hace **medible**, no medida. Los `k = 14` del Sello A son worktrees del mismo dueño.
2. **El coste de una máquina de cliente.** Cuatro medidas del mismo acto van de 67 a 344 s, todas en esta máquina. Ninguna es «el tiempo del acto».
3. **La precedencia entre `suplantada` e `intercambiada`** está fijada sólo en la fixture (P-28).
4. **La ausencia dentro del universo del cliente.** El acto prueba ausencia sobre la página y la comprueba contra un árbol que recorre con **seis exclusiones declaradas**; un manifiesto de cliente con exclusiones propias cambia el universo del testigo y sólo está medido sobre el Sello A y jq (`resuelto en` P-60 la mitad del instrumento: `git ls-files` que falla degrada a `no_medida`).
5. **El sujeto de negocio lo escribimos nosotros.** La agenda de §1.5 es una fixture propia: prueba que el álgebra funciona fuera de un árbol de software, **no** que un manifiesto firmado por un cliente se comporte igual. La proyección `π(k)` es una frontera declarada que el cliente firma ([`AUSENCIA.md` §4.4](AUSENCIA.md)); nadie nos ha firmado una todavía.
6. **La escalera completa contra un árbol de terceros** (un release público con `SHA256SUMS` nativo) está hecha para `intacta`/`reubicada`/`suplantada`/`divergente`, no para los siete pasos.
7. **La cadena de un cliente.** La composición se mide entre nodos del mismo dueño y sobre una agenda escrita por nosotros; ninguna cadena real de tres manos ha pasado por `componer`. Y componer no abarata verificar: la cadena de `n` saltos sigue costando O(página) por salto que alguien tenga que rehashear.
8. **La corrección aritmética del nodo de en medio: `NO_MEDIDA`.** La conservación dice que la magnitud declarada sobrevivió el transporte; no dice que `B` calculara bien. Si `B` suma mal **y** su página conserva la cuenta que declaró, la cadena no tiene con qué acusarlo (P-103). Lo medido es otra cosa: que la cadena se calla cuando la medida no está —`sin_medida`, peor que `conservada` y mejor que `no_conservada`— y que dos medidas de la misma cadena dan veredictos distintos (P-102).

Grabar cualquiera de estos ocho como si estuviera medido es el único error que este archivo no puede arreglar después.

---

## 17 · Puente con `letras-video`

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
