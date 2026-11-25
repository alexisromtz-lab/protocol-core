# Predicado v1

El enunciado verificable de una página.

Tipo: `https://github.com/alexisromtz-lab/protocol-core/blob/main/PREDICADO.md#predicado-v1`

Este documento es la **especificación** del objeto que emite
`src/protocol/predicado.py`. Su razón de existir es que un tercero pueda
reimplementar la verificación **sin leer el código**, en cualquier lenguaje, con
la biblioteca estándar. Si la especificación y el código discrepan, manda la
especificación y el código es el defectuoso.

No cubre `SPEC.md`: el SPEC está sellado con fecha cierta (`ad67ece0…`) y una
sección nueva lo invalidaría. Este documento se versiona con git, y su historia
es su sello.

## 1. Los siete campos

Un predicado ata, en un solo objeto, lo que hace verificable un acto:

| campo | qué declara | obligatorio |
|---|---|---|
| `afirmacion` | qué se afirma, en una frase | sí, no vacío |
| `entradas` | las fuentes medidas: ruta y hash | sí, conjunto ordenado |
| `codigo` | el código que produjo la salida: ruta y hash | sí, conjunto ordenado |
| `entorno` | plataforma, runtime y lo que **no** se midió | sí, con `no_medido` explícito |
| `salida` | el artefacto: **una** ruta y su hash | sí, uno nombrado |
| `veredicto` | lo que el productor **reclama** | sí, del vocabulario cerrado |
| `h_prev` | el digest del eslabón anterior | no: `null` es el génesis |

**`veredicto` es reclamado, no adjudicado.** Quien produce el artefacto declara
`conforme` / `no_conforme` / `no_medido` sobre su propio trabajo. La adjudicación
es un objeto distinto, la **contrafirma** (§5), y es la única que vale como
prueba ante un tercero. Un objeto que mezcle las dos no puede sostener la
segunda: sería la primera repetida.

`entorno.no_medido` es una lista **declarada**. `[]` afirma "no quedó nada sin
medir"; una lista con elementos nombra cada hueco. El vacío silencioso —una
clave ausente— no es válido: es un cero no medido disfrazado de cero.

**Un mismo objeto puede figurar a la vez en `entradas` y en `codigo`.** Medido y
ejecutado no son excluyentes: cuando el acto mide un universo que contiene al
instrumento —un censo del árbol donde vive el propio censo—, el archivo es fuente
y es código. Sobredeclarar `codigo` no es mentir; omitir un módulo que corrió sí.
La regla es de dirección única: la lista puede ser más larga que la verdad, nunca
más corta.

## 2. La forma canónica

El digest se calcula **sólo** sobre la forma canónica. Una implementación que no
produzca bytes idénticos a estos no verifica:

1. **Texto**: toda cadena, en cualquier profundidad, se normaliza a NFC (Unicode
   Normalization Form C). APFS entrega NFD donde Linux entrega NFC; sin esto el
   mismo acto daría dos digests y el digest mediría la máquina. La normalización
   es del valor **antes** de serializar, no del serializado.
2. **Claves**: ordenadas por bytes UTF-8, ascendente, **en toda profundidad**
   (`sort_keys` recursivo), incluidos los objetos dentro de listas. Ordenar sólo
   el nivel superior da otro digest.
3. **Separadores**: `,` y `:` sin espacios.
4. **No-ASCII**: se emite tal cual, en UTF-8 (`ensure_ascii=false`), nunca como
   `\uXXXX`. La forma escapada y la literal son el mismo texto y no deben poder
   producir dos digests.
5. **Números**: se **rechazan** los flotantes. Su representación decimal no es
   portable y cualquier redondeo introduce una decisión no declarada. Un entero
   es un entero en toda plataforma; un flotante es una promesa.
6. **Nulos**: `null` es un valor y se admite. La clave **está siempre presente**:
   `h_prev: null` es el génesis, y omitir la clave no es lo mismo que dejarla
   nula —son dos objetos distintos y dan dos digests distintos—.
7. **Listas**: conservan su orden, y ese orden entra al digest. En `entradas` y
   `codigo` el orden **exige** que las rutas vayan ascendentes por bytes UTF-8,
   sin repetir: una lista desordenada no se canoniza, se rechaza. Una lista no
   es un conjunto: reordenarla cambia el digest aunque los elementos sean los
   mismos.
8. **Sin salto de línea final**: la forma canónica termina en `}`. La página
   (§3) sí puede llevar `\n` final, porque un archivo de texto que no termina en
   salto es incómodo de leer; el digest se calcula sobre los bytes sin él.

Un objeto con campos de más **no se canoniza**: se rechaza (§7.2). El cuerpo
tiene exactamente las siete claves del §1, y un verificador que las ignore y
siga adelante ha hasheado un objeto que no es el que recibió.

Ninguna **ruta** —las de `entradas`, `codigo` y `salida`— puede ser absoluta ni
contener un componente `..` ni NUL; la regla es de las rutas, no del texto
libre: una `afirmacion` que mencione `..` es prosa válida. Ningún hash puede
estar truncado, y el hexadecimal es minúscula: **una identidad truncada no es
una identidad**, y una mayúscula no es otra grafía del mismo hash, es un valor
no canónico.

## 3. Los dos nombres del acto

- `digest = sha256(canon(cuerpo))`, en hexadecimal minúscula de 64 caracteres,
  donde `cuerpo` es la forma canónica de los siete campos.
- `h_prev` viaja **dentro** del cuerpo, de modo que el digest de un eslabón
  cubre su enlace. Mover el enlace fuera del cuerpo permitiría reordenar la
  cadena sin cambiar ningún digest.

## 4. La cadena, y su límite

`verificar_cadena(cadena)` comprueba dos cosas: que cada `h_prev` sea el digest
del eslabón anterior, y que `h_prev` del primero sea `null`.

**Límite declarado, y es el corazón del producto:** una cadena sin ancla externa
**no prueba autoría**. Quien reescribe todos los eslabones y recalcula todos los
digests obtiene una cadena que cuadra. La coherencia interna detecta la edición
parcial, no la reescritura completa. Lo único que detecta la reescritura es un
ancla fuera del control del productor: un commit, un DOI con fecha cierta, un
registro de transparencia. Por eso el ancla es obligatoria para vender el
veredicto y no es parte del predicado: el predicado prueba *qué*, el ancla
prueba *cuándo* y *quién*.

## 5. La contrafirma

```json
{
  "verificador": "quién adjudica",
  "digest_del_predicado": "los 64 hex del acto adjudicado",
  "veredicto": "confirma | refuta | no_medido",
  "ancla": "dónde vive la prueba (DOI, commit, registro) o null"
}
```

La contrafirma nombra el acto por su digest, nunca por su contenido: así no hay
dos formas de citar el mismo acto. `ancla: null` significa "adjudico sin prueba
externa", que es exactamente lo que vale una contrafirma sin ancla. Este
documento **no** define criptografía: no se simula una firma que no se verifica.

## 5.bis Levantar el acto desde la página

`desde_cuerpo(pagina)` es la inversa de `cuerpo()` y de `pagina()`. Es parte del
contrato, no una comodidad de la biblioteca: sin ella la contrafirma cubre un
digest que sólo su autor sabe reproducir, y entonces el verificador no puede
divergir de nada.

Reglas de la inversa, todas falsables:

- Acepta el cuerpo como diccionario **o** como el texto/bytes UTF-8 publicado:
  quien verifica tiene un archivo, no un objeto vivo.
- Exige **las siete llaves y ninguna otra**. Una llave de menos es una laguna no
  declarada: `h_prev` ausente no es el origen, es un eslabón sin enlace. Una de
  más es un acto distinto que se leería con el vocabulario viejo.
- Exige `entorno.no_medido` **presente**, aunque sea `[]`. Rellenarlo por omisión
  afirmaría que no queda nada sin medir sin haberlo escrito.
- Rechaza lo que el constructor rechaza: rutas desordenadas, hashes truncados,
  veredicto fuera del vocabulario.

## 5.ter El ciclo del ancla: dos commits

El ancla nombra un commit **anterior**: el que contiene la página. Por eso cada
acto anclado se publica en dos tiempos —primero el acto, después la contrafirma
que lo nombra— y el segundo commit no cambia la página, sólo `ancla-declarada.txt`
y `contrafirma-censo.json`, que ningún acto incluye en `codigo`.

Dos consecuencias que se declaran porque un tercero las va a encontrar:

- **El verificador no figura en `codigo`.** `examples/contrafirmar_censo.py` no
  entra en el conjunto que el censo hashea: si el verificador se verificara a sí
  mismo, cambiar el verificador cambiaría la página que verifica y el ancla sería
  imposible de fijar. Un guardián no puede guardarse a sí mismo.
- **Toda edición del código verificado produce una página nueva y deja el ancla
  rancia.** No es un defecto: es la prueba de que la página ata los bytes. El
  acto que la emite informa `RANCIO` y devuelve RC 1 hasta que se re-ancle; un
  acto que lo callara sería el falso verde que este formato existe para impedir.

## 5.quater El acto es su propio punto fijo: dos pasadas

`examples/emitir_predicado.py` corre la suite y hashea `tests/` y `src/protocol/`
para escribir `examples/predicado-suite.json`. La página que escribe está dentro
del universo que hashea: es **entrada** del acto que la emite. De ahí que una
sola pasada no pueda certificar nada:

1. La primera pasada corre la suite cuando la página todavía describe el árbol
   anterior. La suite lo acusa —una prueba compara la página con la
   reconstrucción— y el veredicto reducido sale rojo **por su propia causa**.
2. La segunda pasada corre sobre la página que la primera dejó. Ya no hay
   desfase, la suite sale verde y el veredicto reducido que se publica es el de
   esta corrida.

Se publica el digest de la segunda. El de la primera no se esconde: es la página
que midió el desfase, y su digest se nombra en el acta. Un acto que se emitiera
una sola vez publicaría un veredicto sobre un árbol que ya no es el que describe,
que es la definición de un falso verde en la dirección peligrosa.

**Por qué esto no es «re-emitir hasta que salga verde».** El criterio de parada
no es el color: es la reproducción. `--check` vuelve a correr el acto entero y
compara la página byte a byte; si el árbol cambió desde la emisión, diverge y
devuelve RC 1 aunque el veredicto fuera verde. Un acto que se repitiera hasta
coincidir con una cifra deseada no mediría nada; éste se repite hasta que la
página y el árbol son el mismo objeto, y el segundo término no lo elige quien
emite.

## 6. Proyección a in-toto Statement v1

El predicado no compite con el estándar; se monta encima. La proyección es
literal y no pierde nada:

```json
{
  "_type": "https://in-toto.io/Statement/v1",
  "subject": [ { "name": "<salida.ruta>", "digest": { "sha256": "<salida.sha256>" } } ],
  "predicateType": "https://github.com/alexisromtz-lab/protocol-core/blob/main/PREDICADO.md#predicado-v1",
  "predicate": { "afirmacion": "...", "entradas": [...], "codigo": [...],
                 "entorno": {...}, "veredicto": "...", "h_prev": null }
}
```

`salida` se proyecta a `subject` **y se excluye** de `predicate`: es el único
campo con dos sitios posibles, y tenerlo en los dos haría que la proyección
dejara de ser inyectiva. La ida y vuelta (`desde_in_toto(p.a_in_toto()) == p`)
es el falsador de que la proyección no pierde información.

## 7. Lo que un verificador tiene que poder hacer

1. Recalcular el digest desde el JSON recibido, sin confiar en el que trae.
2. Rechazar: flotantes, hashes truncados, rutas absolutas, `..`, NUL, entorno
   sin `no_medido`, veredicto fuera del vocabulario, campos faltantes o de más.
3. Recorrer una cadena y nombrar el eslabón que rompe.
4. Decir explícitamente que **sin ancla** la cadena sólo prueba coherencia.
5. Levantar el predicado desde la página publicada y recomputar su digest **sin
   el emisor** (`§5.bis`). Un verificador que necesite el proceso que emitió no
   verifica: repite.
6. Nombrar por separado las dos divergencias que no son la misma: `RANCIO`, la
   página de la mesa no es la del ancla —el ancla describe otro árbol— y
   `REFUTA`, la contrafirma no cubre el acto de enfrente. Mezclarlas deja al
   auditor sin saber si re-ancorar o investigar. El vocabulario es
   `VeredictoDeAncla` = `VIGENTE` · `RANCIO` · `REFUTA` · `NO_MEDIDA` (falta el
   ancla, la página o el commit al que apunta); los tres últimos comparten RC 1,
   así que la diferencia tiene que viajar en texto, no en el código de salida.

Un verificador que acepte cualquiera de (2) con un `warning` y siga no ha
verificado: ha saludado.
