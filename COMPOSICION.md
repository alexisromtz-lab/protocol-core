# Composición de recibos — `R_AB ∘ R_BC`

Un recibo prueba que lo que salió de A es lo que se leyó en B. Una cadena de
nodos —exportación → worker de conciliación → auditor— no se documenta con dos
recibos sueltos: se documenta con **uno compuesto**, y ese objeto tiene reglas
propias. Este documento las fija. El código vive en
[`src/protocol/composicion.py`](src/protocol/composicion.py); los falsadores, en
[`tests/test_composicion.py`](tests/test_composicion.py).

## 0. Qué certifica el recibo compuesto

> El nodo que entregó a C es **el mismo objeto** que salió de A, salvo lo que el
> recibo declara opaco.

Eso es todo. Un recibo compuesto **no** certifica que B hiciera bien su trabajo,
ni que la transformación fuera la acordada, ni que el resultado sea correcto:
certifica **continuidad de bytes a través de saltos**, tramo a tramo, con la
cuenta de lo que no se pudo ver. Un auditor que lea un `-> intacta` como «los
datos son buenos» está leyendo un recibo de integridad como si fuera un recibo
de corrección; son objetos distintos y este sólo es el primero.

## 1. El orden no se inventa: se importa

Componer es tomar el **peor** de los tramos, y «peor» exige un orden total. Ese
orden ya estaba publicado en [`UBICACION.md`](UBICACION.md) §4 para el veredicto
de un acto, y el recibo compuesto lo **importa** en vez de inventar el suyo:

| rango | veredicto | ¿la afirmación se sostiene? |
|---|---|---|
| 0 | `INTACTA` | sí |
| 1 | `REUBICADA` | sí |
| 2 | `NO_MEDIDA` | no se sabe |
| 3 | `INTERCAMBIADA` | no |
| 4 | `SUPLANTADA` | no |
| 5 | `DIVERGENTE` | no |
| 6 | `FRONTERA_ROTA` | no — y además invalida la cadena |

`SOSTIENEN = (INTACTA, REUBICADA)` es la misma pareja que da RC 0 en el acto
simple, y por la misma razón: son los dos únicos casos en que la afirmación
—«estos bytes en estas rutas»— se sostiene.

**Dos fuentes de verdad para un orden total divergen en la primera edición.** El
falsador P-79a no comprueba que el orden sea razonable: comprueba que sea **el
mismo** que el de `UBICACION.md`. Si alguien inserta un veredicto allí y no aquí
—o al revés—, P-79a falla, y no hay forma de que el compuesto y el simple
discrepen en silencio sobre qué es peor.

`FRONTERA_ROTA` no existe en un recibo simple porque un acto simple no tiene
empalmes. Va **por encima** de `DIVERGENTE`: `DIVERGENTE` dice que un tramo
cambió; `FRONTERA_ROTA` dice que los dos tramos no hablan del mismo objeto, y con
eso no hay cadena que componer. Un `divergente` dentro de una cadena rota es un
detalle de un tramo que ya no pertenece al camino.

## 2. El tramo

Un `Tramo` es un salto `origen -> destino` con el veredicto de ese salto y las
dos páginas que lo sostienen. Sus digests **se recalculan del contenido**, nunca
se aceptan de quien lo construye: un tramo que declara un digest que sus filas
no producen no es un tramo con un dato raro, es un tramo falso.

La excepción es `sha256_regla`, y va declarada como excepción: no es un digest
del contenido del tramo, sino el de un artefacto que vive **fuera** del testigo
—la especificación de la transformación—. Por eso es una *entrada* y se acepta
de quien declara, con una obligación que la vuelve falsable: el verificador
exige el artefacto y lo hashea él mismo (§6). Un `sha256_regla` que nadie
coteja sería otro número que se cree medida.

`es_identidad` es un tramo sin filas ni testigos cuyo origen y destino
coinciden: el neutro.

## 3. La frontera: tres estados, no dos

El empalme entre `R_AB` y `R_BC` es el nodo B. Comparar lo que A dejó con lo que
B leyó da tres resultados, y **los tres son distintos**:

| estado | condición | qué se publica |
|---|---|---|
| cerrada | ambos digests presentes e iguales | nada; la cadena sigue |
| `frontera_rota` | ambos presentes y distintos | los dos digests, con nombre de tramo |
| `frontera_vacua` | falta la página de un lado | `frontera \| sin medir` |

Fundir la tercera con la primera es un **falso verde**: no haber leído la página
de B no es que B coincida con A. Fundirla con la segunda es afirmar un cambio
que nadie midió. La página ausente es `no_medida`, y `no_medida` no se lee como
cero — la misma regla que en `UBICACION.md` §4 para el acto que no pudo mirar.

## 4. `componer` es un monoide, y el neutro no deja basura

`componer(izq, der)` devuelve el recibo compuesto:

- **veredicto** = el mayor rango de `{izq, der, frontera}`, con `FRONTERA_ROTA`
  si el empalme no cierra;
- **cadena** = la traza de digests de extremo a extremo
  (`A -d1-> B -d2-> C`), que es la huella de *qué objeto* viajó, no de *quién* lo
  tocó;
- **testigos** = los de ambos recibos, sin deduplicar por consulta: dos testigos
  de la misma clave en páginas distintas son dos hechos, no uno repetido.

**Identidad** (P-80): `R_AB ∘ Id_B = R_AB` y `Id_A ∘ R_AB = R_AB`, comparando
veredicto, cadena y testigos. El neutro **se absorbe**, no se acumula: un tramo
de identidad que sobreviviera en el compuesto haría crecer la cadena con saltos
que no existieron y la traza de digests dejaría de leerse.

Un tramo de identidad **enfermo** —`B -> B` con `no_medida`, es decir, ni
siquiera se pudo mirar el nodo contra sí mismo— no se absorbe (P-80c): el neutro
es el que certifica que no hubo cambio, y uno que no certifica nada no es
neutro, es un hueco con forma de neutro.

**Asociatividad** (P-81): `(R_AB ∘ R_BC) ∘ R_CD = R_AB ∘ (R_BC ∘ R_CD)` en
veredicto y en cadena. Es la propiedad que permite **no guardar los
intermedios**: quien tenga la cadena y los testigos puede recomponer el extremo
a extremo sin pedirle a nadie los recibos parciales. Sin asociatividad, el mismo
camino daría dos certificados según cómo se agrupara, y un certificado que
depende del orden de las operaciones no es un certificado: es un cálculo.

## 5. La ausencia en tránsito: tres estados

Una ausencia probada con testigo de vecinos (ver [`AUSENCIA.md`](AUSENCIA.md))
sobre la página de A es cierta **de A** para siempre. Que siga siendo cierta del
extremo de la cadena es otra pregunta, y tiene tres respuestas:

| línea | condición | qué afirma |
|---|---|---|
| `ausencia vigente` | la página final es la que prueba el testigo **y** la cadena sostiene | la ausencia viajó |
| `ausencia sin transito` | la página final es la que prueba el testigo, pero la cadena no sostiene | nada: falta el camino |
| `ausencia historica` | el testigo se probó contra otra página | fue cierta en su nodo |

La tercera fila es la que casi nadie publica y la que hace auditable el conjunto:
el testigo **no envejeció** —los bytes que lo probaron son los mismos— pero la
página contra la que se probó ya no es la que llega. Se conserva y se nombra.

La segunda es la que impide el atajo más tentador: con la frontera rota, C puede
perfectamente leer una página cuyo digest coincide con el de A —porque C releyó el
origen— y entonces el testigo encaja por digest y la cadena no une los extremos.
Dos hechos verdaderos por separado y una conclusión falsa («esta cita nunca
estuvo en el registro de A→C»). P-82f lo fija: mismo digest, `FRONTERA_ROTA`,
cero vigentes.

## 6. El verificador externo

[`examples/verificar_recibo_externo.py`](examples/verificar_recibo_externo.py)
recomputa un recibo —simple o compuesto— **sin importar `protocol`**: vuelve a
hashear el manifiesto, revalida el orden canónico, recalcula los vecinos, revisa
la cadena de fronteras y compara el veredicto publicado con el que sale de los
datos. Cero dependencias fuera de la biblioteca estándar.

Un verificador que importa el generador no verifica: **reproduce**. La
diferencia es la que separa «confío en ti» de «puedo comprobarlo», y es la única
razón por la que el recibo sirve frente a un tercero. P-84e lo comprueba
estructuralmente: el verificador no menciona `protocol` ni en un import ni en un
comentario.

Su límite va impreso en cada corrida, no en la letra pequeña:
`limite | el verificador comprueba que las paginas encadenadas son las mismas; no que B hiciera su trabajo`.

### La regla: de continuidad a autoría

Un recibo `/1` certifica que los bytes viajaron. No certifica **con qué regla**
los transformaron: una cadena de páginas inventadas, internamente consistente,
cierra `intacta` con RC 0 — y con razón, porque cada digest es función de bytes
que escribió el mismo que construyó la cadena. `intacta` significa entonces
«los bytes que digo son los bytes que digo», que es una tautología con firma.

`recibo-de-composicion/2` añade `sha256_regla` por tramo, y el tercero aporta el
artefacto:

```bash
python3 examples/verificar_recibo_externo.py recibo.json --regla ab.md --regla bc.md
```

Una regla por salto, en orden. El verificador **hashea el archivo que recibe** y
lo compara con lo declarado (`REGLA_NO_COINCIDE`). Regla declarada sin artefacto
⇒ `REGLA_NO_APORTADA`; exigencia pedida sobre un `/1` (`--exigir-regla`) ⇒
`REGLA_NO_DECLARADA`. Un `/2` exige la regla **por construcción**: el formato es
el contrato, no una bandera que alguien pueda olvidar pasar.

**No se añade `sha256_entrada`,** aunque el nombre lo pida. La entrada de B ya
está medida: `verificar()` rehashea las filas de B y `_cruce()` compara ese
digest recalculado con la salida de A (§3). Un `sha256_entrada` declarado sería
la copia débil de una cantidad ya medida —dos fuentes para una arista—, y la
misma disciplina que derivó `--saltos` de `--paginas` en el verificador de
conservación es la que se aplica aquí.

El límite nuevo se imprime junto al viejo: la regla **ata** el tramo a un
artefacto declarado fuera; no prueba que B aplicara esa regla.

### La firma: de la continuidad de bytes a la autoría del documento

El anillo 8 añade Ed25519 en biblioteca estándar, sin dependencias nuevas:

```bash
python3 examples/firmar_recibo.py --recibo recibo.json --semilla <archivo>   # emisor
python3 examples/verificar_recibo_externo.py recibo.json --regla ab.md --regla bc.md \
    --clave recibo.json.pub --firma recibo.json.firma                          # auditor
```

**Se firma al lado, nunca dentro.** Una firma incluida en el JSON que firma no
puede cubrirse a sí misma; excluirla exigiría una segunda regla —«todo menos
esta llave»— con su propio agujero. Separada, los bytes firmados son el recibo
entero.

**Los bytes firmados son `recibo-de-composicion/2\n` + canon.** El dominio lleva
la versión, así que un `/3` no puede reutilizar los bytes de un `/2`. El canon
—NFC, llaves ordenadas, sin espacios, sin `float`— es el que se firma, no una
proyección del recibo: por eso la firma cubre **también las llaves que ningún
verificador conoce**, que es exactamente el hueco que dejan los chequeos de
campo (P-110d).

**Sólo se firma `/2`.** Un `/1` no tiene regla externa que atar, así que
firmarlo sería autenticar una cadena que el propio emisor pudo fabricar: se
rechaza con RC ≠ 0 antes de producir firma (`FIRMA_NO_FIRMABLE`).

El cotejo se **reescribe** dentro del verificador externo en vez de importarlo:
P-84e prohíbe la mención de `protocol` en ese archivo. Dos copias divergen
solas, así que P-110a las ata a los cinco vectores oficiales de RFC 8032 §7.1
guardados en [`tests/fixtures/rfc8032.json`](tests/fixtures/rfc8032.json).

La firma **no** entra en el canon ni en ningún digest del recibo: no cambia el
veredicto de composición, sólo añade una línea que dice quién emitió esos
bytes. Un recibo firmado y uno sin firmar componen igual.

### El acto del emisor: dos páginas por tramo

La cadena quedaba abierta del lado del cliente: `componer()` no tenía CLI y el
único recibo que se podía emitir era el de juguete de `--demo`. Lo cierra
[`examples/emitir_recibo.py`](examples/emitir_recibo.py), que pliega los tramos
declarados y escribe el JSON que el verificador externo ya sabe leer:

```bash
python3 -B examples/emitir_recibo.py \
    --tramo A=B --paginas agenda-A.txt,agenda-B.txt \
    --tramo B=C --paginas agenda-B.txt,agenda-C.txt \
    --regla regla-AB.md --regla regla-BC.md \
    --salida recibo.json
```

**Dos páginas por tramo, no una por nodo.** Con una sola página por nodo la
frontera cierra por construcción: `B` no puede cambiar entre `A -> B` y `B -> C`
porque sólo hay un `B`. Un acto así siempre diría `cierra` y no mediría nada.
Con dos, la frontera que no cierra es expresable —el emisor sale con RC 1, el
recibo lo declara en `frontera` y el tercero lo rechaza.

El emisor **no** se auto-verifica: usa `componer`, que es el que mide las
fronteras, y su `a_dict()` es el del núcleo, sin campos inventados. Si emitiera
una forma que su propio auditor no entiende, el defecto no sería del cliente.
Sin `--regla` el recibo es `/1`, y lo dice antes de que el cliente descubra que
[`examples/firmar_recibo.py`](examples/firmar_recibo.py) se niega a firmarlo.

## 7. Lo que este objeto no hace — lista cerrada

1. **No certifica la transformación.** Que B leyera lo que A dejó no dice nada
   sobre si B aplicó la regla acordada. Un recibo de continuidad leído como
   recibo de corrección es un falso verde con firma. El anillo 7
   ([`CONSERVACION.md`](CONSERVACION.md)) **acota** este hueco con una magnitud
   que el cliente declara y se recalcula de las páginas; no lo cierra: una
   medida puede sobrevivir a un valor mal calculado y la línea `limite` lo
   publica en cada corrida (P-103). `sha256_regla` (§6) añade la pieza que
   faltaba para que la firma del anillo 8 cubra algo más que bytes arbitrarios:
   ata cada tramo a un artefacto declarado fuera del testigo. Sigue sin probar
   que B aplicara esa regla.2. **No abarata la cadena larga.** Componer es barato; **verificar** un salto es
   O(página). La cadena de `n` nodos no se vuelve O(1) por componerla: el coste
   sigue en los extremos que alguien tenga que rehashear, y quien afirme lo
   contrario está midiendo su caché, no el acto.
3. **No elige entre dos páginas del mismo nodo.** Si B tiene dos páginas
   vigentes —dos escritores—, la frontera puede cerrar con la equivocada. El
   recibo lo delata sólo si el digest final no coincide con el esperado; la
   elección de cuál es la buena no es un problema de álgebra.
4. **No sustituye al sello.** Un recibo compuesto sin sello que lo ancle al
   manifiesto publicado es una afirmación sobre afirmaciones.
5. **No prueba que el emisor dijera la verdad.** La firma (§6) autentica
   **quién emitió estos bytes** y que nadie los cambió después —incluidas las
   llaves que ningún verificador conoce—; no autentica el trabajo que esos
   bytes describen, ni que el nodo intermedio aplicara la regla que declaró. Y
   no resuelve la custodia de la semilla: quien la tenga firma como el emisor,
   y ningún algoritmo arregla eso.

## 8. Falsadores

| regla | falsador |
|---|---|
| el orden es el de `UBICACION.md` §4 | P-79a |
| `FRONTERA_ROTA` ordena por encima de `DIVERGENTE` | P-79b |
| un tramo opaco no produce `intacta` | P-79c |
| el peor tramo manda y se nombra | P-79d, P-79e |
| páginas ausentes ⇒ `no_medida`, no `intacta` | P-79f |
| identidad absorbida a ambos lados | P-80a |
| identidad sobre otra página no es neutra | P-80b |
| identidad enferma no se absorbe | P-80c |
| asociatividad de veredicto y cadena | P-81 |
| vigente / histórica | P-82a, P-82b |
| testigo de página ajena y digest mentido | P-82c, P-82d |
| ida y vuelta por JSON | P-82e |
| cadena rota ⇒ cero vigentes con el mismo digest | P-82f |
| el verificador externo cierra y detecta manipulación | P-84a…P-84d |
| el verificador no importa el generador | P-84e |
| verificador y generador degradan igual | P-84f |
| la forja sin regla cierra, y cae cuando se le exige | P-84g |
| la regla declarada se coteja contra el artefacto aportado | P-84h |
| un `/1` no se reconstruye como `/2` | P-84i |
| `sha256_regla` sobrevive la ida y vuelta por JSON | P-84j |
| las dos implementaciones de Ed25519 cotejan los vectores RFC 8032 §7.1 | P-110a |
| dominio y canon del emisor y del auditor son el mismo | P-110b |
| un recibo firmado cierra bajo `env -i` fuera del árbol | P-110c |
| el canon firmado cubre la llave que ningún chequeo de campo mira | P-110d |
| un byte en la firma o en la regla aportada no cierra | P-110d |
| un `/1` no se firma ni se coteja como firmado | P-110e |
| el emisor pliega y el tercero cierra bajo `env -i`, sin árbol | P-112a |
| una frontera que no cierra se emite, se declara y no pasa | P-112b |
| un byte en la regla aportada rompe el atajo | P-112c |
| un nibble en la firma refuta | P-112d |
| sin regla el recibo es `/1` y el firmador lo rechaza | P-112e |
