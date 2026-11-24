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

## 2. La forma canónica

El digest se calcula **sólo** sobre la forma canónica. Una implementación que no
produzca bytes idénticos a estos no verifica:

1. **Texto**: toda cadena, en cualquier profundidad, se normaliza a NFC (Unicode
   Normalization Form C). APFS entrega NFD donde Linux entrega NFC; sin esto el
   mismo acto daría dos digests y el digest mediría la máquina. La normalización
   es del valor **antes** de serializar, no del serializado.
2. **Claves**: ordenadas por bytes UTF-8, ascendente (`sort_keys`).
3. **Separadores**: `,` y `:` sin espacios.
4. **No-ASCII**: se emite tal cual, en UTF-8 (`ensure_ascii=false`), nunca como
   `\uXXXX`. La forma escapada y la literal son el mismo texto y no deben poder
   producir dos digests.
5. **Números**: se **rechazan** los flotantes. Su representación decimal no es
   portable y cualquier redondeo introduce una decisión no declarada. Un entero
   es un entero en toda plataforma; un flotante es una promesa.
6. **Nulos**: `null` es un valor y se admite (`h_prev` en el génesis no es "sin
   campo", es "sin eslabón anterior").

Ningún campo puede contener una ruta absoluta, un componente `..` ni NUL, y
ningún hash puede estar truncado: **una identidad truncada no es una identidad**.

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

## 6. Proyección a in-toto Statement v1

El predicado no compite con el estándar; se monta encima. La proyección es
literal y no pierde nada:

```json
{
  "_type": "https://in-toto.io/Statement/v1",
  "subject": [ { "name": "<salida.ruta>", "digest": { "sha256": "<salida.sha256>" } } ],
  "predicateType": "https://github.com/alexisromtz-lab/protocol-core/blob/main/PREDICADO.md#v1",
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

Un verificador que acepte cualquiera de (2) con un `warning` y siga no ha
verificado: ha saludado.
