# El sobre — el archivo no es el objeto

Anillo 6 de `protocol-core`. Cierra el punto ciego más caro que quedaba abierto:
el portador leía manifiestos firmados **mal o de casualidad**, y el censo de
portadores declaraba un punto ciego que en un caso no existía.

Medido el 2026-11-25 sobre `Debian 12.15` y los ocho portadores anteriores.
Cero dependencias; el módulo es [`src/protocol/sobre.py`](src/protocol/sobre.py),
los artefactos viven en [`examples/portadores/`](examples/portadores/) con su
[`FUENTES.txt`](examples/portadores/FUENTES.txt), y los falsadores son
[`tests/test_sobre.py`](tests/test_sobre.py).

## 0. Qué certifica un sobre

Un sobre no cambia **qué** bytes hay: cambia **dónde** están y qué digest
corresponde a qué. Hasta el anillo 6, `leer()` trataba la envoltura como ruido
—una línea más fuera de la gramática— y publicaba un digest sin poder decir si
era el del archivo o el del objeto.

El sobre obliga a partir el hecho en dos:

| digest | qué identifica | cómo se obtiene |
|---|---|---|
| `sobre_digest` | **el archivo** que el cliente descargó | `sha256` de los bytes tal cual |
| `carga_digest` | **el objeto** que el autor firmó | `sha256` de los bytes sin el sobre |

Sin sobre los dos son el mismo número, y el módulo lo publica como el mismo
número, no como dos coincidencias (P-97).

## 1. La medición que abrió el anillo — 2026-11-25

El mismo autor, el mismo contenido, tres artefactos. Los tres se descargaron de
`deb.debian.org` a las `19:31:13Z`:

| archivo | bytes | topología | lo que publicaba el lector antes |
|---|---|---|---|
| `debian-12.15-Release` | 149 266 | `sin_sobre` | 772 filas, `c0dc59762595` |
| `debian-12.15-InRelease` | 151 075 | `firmado_en_claro` | **rechazado** |
| `debian-12.15-Release.gpg` | 1 760 | `firma_pegada` | **0 filas, en silencio** |

Dos defectos distintos, y el segundo es el grave:

1. **`InRelease` no se leía.** `facultades()` devolvía `()` y `detectar()`
   acusaba a la carga: `linea 4: 'Origin: Debian'`. La línea 4 era correcta; lo
   que el lector no sabía era que las tres primeras líneas no eran del objeto.
   Un rechazo con causa falsa es peor que un rechazo: manda a arreglar lo que
   está bien.
2. **`Release.gpg` se leía como un manifiesto vacío.** No tiene filas porque no
   es un manifiesto: es una firma sobre **otro** archivo. Devolver cero filas
   sin decirlo es exactamente la clase de verde que este repositorio persigue.

Y un tercer defecto, del propio censo: [`FUENTES.txt`](examples/portadores/FUENTES.txt)
declaraba sobre `debian-12.15-Release` que «la firma PGP final no se verifica».
Ese archivo tiene **0 bytes** de PGP. El punto ciego estaba inventado.

## 2. Tres topologías, y ninguna se adivina

```
sin_sobre         ->  el archivo ES el objeto
firmado_en_claro  ->  el objeto va dentro  (BEGIN PGP SIGNED MESSAGE)
firma_pegada      ->  el objeto está fuera  (y su nombre no viaja dentro)
```

Las tres son de Debian, no de un laboratorio. `TOPOLOGIAS` publica el conjunto
cerrado y P-94 lo fija contra los tres artefactos reales.

La tercera es la que más dice: `Release.gpg` ↔ `Release` se vinculan **por el
nombre del archivo**, igual que el portador `suelto` se vincula a su ruta por el
nombre. El vínculo no viaja dentro del artefacto, así que el lector **no puede**
verificarlo solo: por eso `desenvolver()` lanza `SobreSinCarga` con el número de
bytes de firma, en vez de devolver una carga vacía que se leería como un
manifiesto de cero filas.

## 3. Las dos leyes del anillo

**Ley 1 — el sobre no cambia el objeto, cambia el archivo.** Quitado el sobre,
el `InRelease` de Debian son 149 266 bytes cuyo `sha256` es
`abcf5882746e0f68…`, que es el `sha256` del `Release` **entero**. Ese valor lo
publica Debian: el lector no lo calcula, lo tiene que acertar. Es la diana de
P-93, y no admite que dos errores se compensen porque el digest es de 256 bits.

```bash
python3 -B -c "import sys; sys.path.insert(0,'src')
from protocol.portador import leer_sin_declarar
t=open('examples/portadores/debian-12.15-InRelease',encoding='utf-8').read()
print(leer_sin_declarar(t).digest()[:12])"   # c0dc59762595 — igual que el Release
```

**Ley 2 — declarar un punto ciego exige testigo.** `firma no verificada` sólo se
escribe si hay bytes de firma. Sin firma se publica el hecho, no la disculpa:

```
sobre | ninguno | 0 bytes de firma | no habia nada que verificar
```

P-95 exige la **doble implicación** sobre los diez artefactos del censo: se
nombra el punto ciego **si y sólo si** `bytes_firma > 0`. Una sola dirección no
basta — sin firma no se declara, y con firma no se calla. Hoy son 3 de 10 con
firma: `debian-12.15-InRelease`, `debian-12.15-Release.gpg` y `fedora-41-CHECKSUM`.

## 4. Lo que el sobre publica

```
sobre | firmado_en_claro | 1759 bytes de firma | carga abcf5882746e | sobre 77737fa4b34f | firma no verificada
```

y, cuando el sobre hubo que deshacerlo, una línea más con **cuántas** líneas se
tocaron —`desescapadas`, `espacio final quitado`, `fines de linea CR`— porque una
transformación que no se cuenta no se puede auditar. En los diez artefactos esas
tres cuentas valen `0`: la transformación está implementada y medida por testigo
sintético (P-96), y su **frecuencia** en lo publicado se declara `no_medida` en
vez de suponerla cero.

## 5. Lo que este objeto no hace — lista cerrada

1. **No verifica la firma.** No hay verificación de clave pública en este anillo
   ni se pretende: `firma no verificada` viaja con su número de bytes para que el
   tercero sepa cuánto no se comprobó.
2. **No elige entre varias firmas.** Publica el bloque que encuentra; un archivo
   con dos armaduras no está en el censo y no se inventa su semántica.
3. **No resuelve el nombre de la firma pegada.** `firma_pegada` es
   `SobreSinCarga`: el vínculo con su objeto es el nombre del archivo, y adivinarlo
   sería inventar el sujeto. El llamador lo aporta, como en `suelto`.
4. **No reescribe el sobre.** El `carga_digest` describe el objeto; no se publica
   una versión «normalizada» del archivo del tercero.
5. **No convierte el punto ciego en un cero.** Lo que no se midió se publica como
   `no_medida` con su causa, nunca como ausencia.

## 6. Falsadores

`python3 -B -m unittest tests.test_sobre` — 13 pruebas, `OK`.

| id | qué falsa |
|---|---|
| P-93 | quitado el sobre, la carga del `InRelease` es el `Release` entero: 149 266 B y su `sha256` |
| P-93b | las dos vías publican la misma página (772 filas, `c0dc59762595`) |
| P-94 | las tres topologías son hechos de Debian 12, no del laboratorio |
| P-94b | `Release.gpg` no trae filas y lo dice: `SobreSinCarga` con su número de bytes |
| P-95 | `firma no verificada` ⇔ `bytes_firma > 0`, sobre los diez artefactos |
| P-95b | sin sobre se publica un hecho, no una disculpa |
| P-96 | el escape `- ` de RFC 4880 §7.1 se deshace y se cuenta (ida y vuelta) |
| P-96b | la frecuencia del escape en lo real es 0 de 10 y se declara `no_medida` |
| P-97 | dos archivos, un objeto: `carga` del firmado = `sobre` del sin firmar |
| P-97b | **resultado negativo**: las dos formas llevan dos firmas distintas |
| P-98 | el verificador externo desenvuelve sin importar el generador y coincide |
| P-98b | el tercero obtiene el mismo `sha256` de carga que Debian publicó |
| P-98c | una firma pegada es `EntradaInvalida`, no un manifiesto vacío |

**P-97b, el resultado que no se esperaba.** Las dos firmas de Debian miden lo
mismo —1 759 B, bloque interno de 1 732 B— y **1 452 de esos 1 732 bytes
difieren**. No son la misma firma: la pegada firma el archivo crudo y la de
en-claro firma el texto ya canonizado por RFC 4880. Cualquier documento que
dijera «Debian firma el `Release`» a secas estaría mezclando dos actos.

## 7. Cómo volver a medirlo

```bash
cd /tmp && mkdir -p sobre && cd sobre
curl -sL -O http://deb.debian.org/debian/dists/bookworm/Release
curl -sL -O http://deb.debian.org/debian/dists/bookworm/InRelease
curl -sL -O http://deb.debian.org/debian/dists/bookworm/Release.gpg
sha256sum Release InRelease Release.gpg
cd /Users/marlene/protocol-core && python3 -B -m unittest tests.test_sobre
```

Si el `sha256` del `Release` deja de coincidir con la carga del `InRelease` en
la misma fecha de `bookworm`, hay dos posibilidades y el test las distingue
porque no adivina: o Debian republicó entre las dos descargas, o el lector está
midiendo otra cosa. Nunca «las dos».
