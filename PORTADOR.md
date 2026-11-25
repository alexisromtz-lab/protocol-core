# El portador — lo único que el cliente trae

Un recibo vale lo que vale la lectura de su manifiesto. Hasta el anillo 4 este
protocolo sabía leer **un** formato —`hash` + dos espacios + ruta— y llamaba
«sin dos columnas» a todo lo demás. Eso no era un límite del protocolo: era el
protocolo confundiendo **su** dialecto con el archivo del cliente. Este documento
fija las gramáticas que se admiten, por qué son cuatro y no una lista de
prioridades, y qué se publica cuando el archivo no entra en ninguna.

El código vive en [`src/protocol/portador.py`](src/protocol/portador.py); los
falsadores, en [`tests/test_portador.py`](tests/test_portador.py); los
artefactos de terceros con su procedencia, en
[`examples/portadores/`](examples/portadores/) y su `FUENTES.txt`.

## 0. Qué certifica una lectura

> El archivo que el tercero publicó se leyó **tal como lo escribió**, y lo que el
> lector no entendió se cuenta.

Una lectura **no** certifica que el manifiesto sea auténtico —eso es la firma,
que aquí se salta y se declara saltada—, ni que las rutas existan, ni que los
digests correspondan a bytes reales: eso lo mide el acto de adjudicación. La
lectura es el paso 0 de la cadena y su único producto es un par
`(portador, pares)` reproducible.

## 1. La medición que abrió el anillo — 2026-11-25

Cinco portadores realmente publicados, de cuatro familias, descargados y medidos:
`sha256sum.txt` de jq 1.7.1, `SHASUMS256.txt` de Node v22.11.0,
`gh_2.62.0_checksums.txt`, `CHECKSUM` de Fedora 41 y `Release` de Debian 12.15,
más un sexto sintético —`deb822-pequeno.txt`, dos filas `deb822`— que reproduce
en 191 bytes la estructura de una sección del `Release`. El lector de entonces
—el del verificador externo, que era el único que había— los trató así:

| portador | filas | qué hizo el lector de un solo dialecto | RC |
|---|---|---|---|
| `sha256sum.txt` de jq 1.7.1 | 26 | lo leyó | 0 |
| `SHASUMS256.txt` de Node v22.11.0 | 41 | lo leyó, **en el orden del archivo** | 0 |
| `gh_2.62.0_checksums.txt` | 20 | lo leyó | 0 |
| `CHECKSUM` de Fedora 41 (PGP en claro) | 1 | lo rechazó | 2 |
| `Release` de Debian 12.15 (`deb822`) | 772 | no encontró una sola fila en su dialecto | 2 |
| `deb822-pequeno.txt` (sintético) | 2 | **acusó de alterado un archivo intacto** | 1 |

Dos de seis leídos, tres rechazados y **una falsa acusación**. El falso rojo es
el hallazgo, no el rechazo: rechazar es honesto —el lector dice que no sabe—,
acusar es afirmar. En los dos casos `deb822` el lector viejo leyó **cero filas**;
el mismo cero se convirtió en rechazo para el `Release` y en acusación para el
pequeño, según qué digest se comparara. `881cba55a9d2` es el `sha256` del propio
archivo acusado; el verificador comparaba ese digest contra el de las filas que
había conseguido leer, y la diferencia era suya.

**Regla que se sigue de aquí: un lector que sólo conoce un dialecto no mide
manifiestos, mide su propio dialecto.** Un archivo ajeno que se lee mal produce
un veredicto con la misma forma que uno verdadero.

## 2. Cuatro gramáticas, disjuntas por construcción

| gramática | forma | separador | quién la escribe |
|---|---|---|---|
| `coreutils` | `<64 hex>  <ruta>` | columna 65, sin espacio delante | `sha256sum`, jq, Node, gh |
| `bsd` | `SHA256 (<ruta>) = <64 hex>` | paréntesis y `=` | Fedora, \*BSD |
| `deb822` | ` <64 hex>  <tamaño> <ruta>` | un espacio delante | Debian, Ubuntu |
| `suelto` | `<64 hex>` | nada: el archivo **es** el digest | Go, `*.sha256` |

No hay una lista de prioridades. Hay cuatro patrones que **no pueden encajar a
la vez**, y la razón es geométrica:

- `coreutils` exige que el digest empiece en la columna 1 y que la columna 65 sea
  el separador, con la ruta inmediatamente después.
- `deb822` exige un espacio en la columna 1; por tanto su digest empieza en la 2
  y su columna 65 **no** es el separador, sino el relleno del tamaño.
- `bsd` exige la palabra `SHA256` y un paréntesis donde los otros exigen un
  hexadecimal.
- `suelto` exige que la línea entera sea el digest, y los otros tres escriben una
  ruta.

De ahí que `detectar` sea una **función** y no una elección (P-86), y que un
archivo explicable por dos gramáticas no se lea: se publique (P-87). Elegir en
silencio es publicar una lectura como si fuera el archivo.

El caso `coreutils` admite el marcador de modo: `sha256sum -b` escribe `*` donde
`sha256sum -t` escribe un espacio, y son la misma familia. La convención de
escape de `coreutils` (`\ruta`) **no** se admite: se rechaza, y se nombra.

## 3. El recorte: el testigo que el anillo necesitaba

El `Release` de Debian pasa de 1 500 líneas y sus secciones van **encadenadas sin
línea en blanco**: `MD5Sum:`, `SHA1:` y `SHA256:` se suceden con sus filas
detrás. La cabecera `SHA256:` está en la línea 786 de 1 558.

De sus 772 filas, **58 traen un tamaño que llena el campo entero** —8 o más
dígitos, 47 y 11 respectivamente—, y son las únicas en que el relleno no deja un
espacio pegado tras el separador. Las otras 714 escriben relleno y una ruta que
empieza por un espacio. Esas 58 son lo que impide que el archivo completo se
pueda leer también como `coreutils`.

Sobre un **extracto** de 12 filas, en cambio, los tamaños son de 5, 6 y 7
dígitos —todos con relleno—: quitar el espacio inicial convierte las 12 líneas
en columnas válidas de `coreutils` cuyas rutas empiezan por el tamaño. Mismo
archivo, dos lecturas, dos digests:

| lectura | digest | rutas |
|---|---|---|
| `deb822` | `04f72099f9bc` | `contrib/Contents-all` |
| `coreutils` (tras recortar el espacio) | `ef481308e7cf` | `1484322 contrib/Contents-all` |

**El archivo completo no es ambiguo y el extracto sí.** Eso es lo que el
testigo mide: la ambigüedad no es una propiedad del formato sino del **ejemplo**
que se publica. Un extracto cómodo de un archivo verificable puede ser un
archivo que no verifica nada. Por eso el acto lo publica: `recortes()` devuelve
las segundas lecturas, y `leer_sin_declarar` **se niega** a elegir entre ellas
publicando los dos digests (P-87, `RecorteAmbiguo`).

## 4. Lo que la lectura publica

Cada `Lectura` emite tres clases de línea, y ninguna es decorativa:

```
portador | deb822 | 772 filas | canonico | digest c0dc59762595
envoltura | mensaje firmado PGP | firma no verificada
normalizado | 2 prefijos ./ | 2 fines de linea CR
```

- `canonico` o `reordenado`: si las filas venían ordenadas por bytes de ruta. Un
  digest canónico de un archivo reordenado **no** es el `sha256` del archivo, y
  el portador dice cuál de los dos está publicando. El de Node es el caso: de 41
  filas, 11 no están en su sitio, y el digest canónico `23aaeb143953` no es el
  `sha256` del archivo `dddf2b497e71`.
- `envoltura … firma no verificada`: el mensaje firmado en claro de Fedora se
  salta, y se dice. Lo que se atestigua es la **línea**, no el autor.
- `normalizado …`: prefijos `./` retirados y fines de línea CR contados. Se
  normaliza lo que no cambia el sujeto, y se cuenta lo normalizado.

`ignoradas` cuenta **bloques** (cabeceras de sección, campos del preámbulo,
otras secciones) en el módulo, y **líneas** en el verificador externo. Son dos
unidades distintas y cada una va nombrada: 13 bloques y 786 líneas son el mismo
`Release`, y una cifra sin unidad no es una medición.

## 5. Lo que este objeto no hace — lista cerrada

1. **No verifica la firma PGP, y desde el anillo 6 tampoco la salta a ciegas.**
   El sobre se desenvuelve en [`sobre.py`](src/protocol/sobre.py) y se publica
   `firma no verificada` **con su número de bytes** —o `0 bytes de firma` cuando
   el artefacto no trae ninguna—. Firma, topologías y falsadores:
   [`SOBRE.md`](SOBRE.md).
2. **No admite la convención de escape de `coreutils`** (`\ruta`): la rechaza y
   la nombra. Admitirla obligaría a decidir qué significa una barra invertida en
   una ruta con barra invertida.
3. **No admite SRI en base64** (`sha256-…=`). Rechazo con nombre, no con silencio.
4. **No adivina el nombre del archivo en `suelto`.** Sin nombre, el portador está
   **incompleto** (`PortadorIncompleto`): el digest no dice a qué ruta pertenece,
   y suponerlo sería inventar el sujeto.
5. **No unifica dos gramáticas en una lectura.** Si un archivo abre dos, no hay
   lectura: hay dos, y se publican las dos.

## 6. Falsadores

| id | qué falsa |
|---|---|
| P-85a–d | los artefactos reales se leen, y con el digest medido |
| P-86a–d | la gramática no se elige; declarar una que no encaja se rechaza en la línea donde deja de encajar, nombrando la que sí encaja |
| P-87a–c | el recorte abre una segunda lectura, el completo no, y sin declarar no se elige |
| P-88, P-88b | los mismos pares en cuatro portadores dan el mismo digest; el orden del portador no es el del digest, y se publica cuál |
| P-89, P-89b | lo que el portador no escribe (nombre de `suelto`) se rechaza en vez de suponerse |
| P-90a, P-90b | la envoltura no es el contenido: el `CHECKSUM` de Fedora se lee sin su firma, y el `Release` encadena secciones sin línea en blanco |
| P-91a, P-91b | el verificador externo, que **no importa** `protocol`, llega al mismo digest sobre los ocho artefactos, y rechaza lo que no encaja |
| P-92, P-92b | prefijos y CR se cuentan; cero filas no es una lectura |

## 7. Cómo volver a medirlo

```
python3 -B -m unittest tests.test_portador
python3 -B examples/verificar_recibo_externo.py --recibo RECIBO.json \
    --manifiesto examples/portadores/debian-12.15-Release \
    --ausente contrib/Contents-riscv64 --portador auto
```

La segunda orden cierra con RC 0 sobre el `Release` de Debian, publica
`portador | deb822 | 772 filas | 786 lineas fuera de la gramatica` y prueba en
`O(1)` que `contrib/Contents-riscv64` no está, con sus dos vecinos adyacentes:
`contrib/Contents-ppc64el.gz < contrib/Contents-riscv64 < contrib/Contents-s390x`.
Un tercero puede repetirlo sin instalar nada y sin confiar en el generador.
