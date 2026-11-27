# La conservación — la magnitud que sobrevive, y lo que no certifica

Anillo 7 de `protocol-core`. Acota el punto ciego más caro que quedaba en la
composición: una cadena de bytes intacta puede transportar un dato **mal
calculado** y publicar `intacta`. `COMPOSICION.md` §7 lo declaraba; aquí se
convierte en una magnitud que el cliente elige y que se puede medir.

Medido el 2026-11-27 sobre una agenda de citas de tres filas. Cero
dependencias; el módulo es [`src/protocol/conservacion.py`](src/protocol/conservacion.py),
los falsadores son [`tests/test_conservacion.py`](tests/test_conservacion.py) y
el verificador de tercero es
[`examples/verificar_conservacion.py`](examples/verificar_conservacion.py).

## 0. Qué certifica una cadena de conservación

Un recibo del anillo 4 prueba **continuidad de bytes**: que lo que `B` publicó
es lo que `C` leyó. No prueba nada sobre lo que hay **dentro** de esos bytes.

La conservación añade una pregunta que se hace *después*, y que el recibo no
puede contestar solo porque no sabe qué le importa al cliente:

| pregunta | quién la elige | qué la responde |
|---|---|---|
| ¿los bytes son los mismos? | el protocolo | el recibo, anillo 4 |
| ¿sobrevivió la magnitud que a mí me importa? | **el cliente** | la cadena de conservación, anillo 7 |

Medir no es certificar el cálculo: es **acotar** el hueco de §7, no cerrarlo. La
línea `limite` viaja en cada corrida para que nadie lea más de lo que dice.

## 1. La medición que abrió el anillo — 2026-11-27

El verificador externo del anillo 6 cierra su corrida con esta frase:

```
limite | el verificador comprueba que las paginas encadenadas son las mismas; no que B hiciera su trabajo
```

Sobre un libro de citas cuya segunda fila cambia de valor en `B` —`450` pasa a
`999`— el mismo recibo da dos respuestas, y las dos son correctas:

```
conservacion | A -> B -> C
medida | filas | declarada por el cliente
salto | A->B | filas | filas=3 -> filas=3 | conservada
salto | B->C | filas | filas=3 -> filas=3 | conservada
limite | conserva el transporte, no el calculo: la magnitud elegida puede sobrevivir a un valor mal calculado
-> conservada
conservacion | A -> B -> C
medida | claves | declarada por el cliente
salto | A->B | claves | claves=17849efefd40 -> claves=17849efefd40 | conservada
salto | B->C | claves | claves=17849efefd40 -> claves=37cc1abd699d | no_conservada
degradado | B->C | no_conservada
limite | conserva el transporte, no el calculo: la magnitud elegida puede sobrevivir a un valor mal calculado
-> no_conservada
```

`filas` cuenta entradas y no ve el cambio; `claves` autentica el **conjunto de
rutas** y lo ve. La misma cadena, dos veredictos, ninguno falso: la segunda
medida es más fina, y solo las medidas más finas pueden acusar donde la gruesa
callaba (P-100f).

## 2. Tres decisiones de álgebra

1. **La medida la declara el cliente, no el protocolo.** `MEDIDAS` es una lista
   cerrada y corta (`filas`, `claves`) por la misma razón por la que el dialecto
   del portador es cerrado: una medida improvisada por el llamador no sería
   comparable entre saltos. Declarar más exige un acto, no un parámetro.
2. **El valor no se acepta: se recalcula.** `valor_origen` y `valor_destino` son
   propiedades, no campos (P-99e). Un recibo que pudiera escribir su propia
   magnitud sería un recibo que miente sobre sí mismo, y el anillo entero
   descansaría en la buena fe de la parte que se audita.
3. **Hay tres estados, no dos.** `conservada < sin_medida < no_conservada`
   (P-99a). `sin_medida` es el estado que un álgebra de dos valores pierde: falta
   una página, y eso no es que la comparación saliera bien. El orden se declara
   en `conservacion.RANGO` y no se importa de `UBICACION.md` §4, que ordena
   objetos y no magnitudes.

## 3. Las dos leyes, y su asimetría

La conservación es **completa para conservar**: si `f(A)=f(B)` y `f(B)=f(C)`,
entonces `f(A)=f(C)` por transitividad de la igualdad (P-100a). Y **no es
completa para acusar**: `no_conservada` no dice que `f(A) != f(C)`. Un salto
puede perder una clave y el siguiente volver a añadirla (P-104): los dos saltos
degradan la cadena, y los extremos coinciden. Degradar no es acusar.

El neutro es la identidad `B -> B` con la misma página: se absorbe a izquierda y
a derecha sin arrastrarse (P-100c), y la composición es asociativa sobre el
veredicto y sobre la traza de saltos (P-100b), de modo que una cadena de cuatro
nodos admite cualquier agrupación sin cambiar lo que publica.

## 4. La cadena de refinamiento

`página ⊒ claves ⊒ filas`: la misma página da las mismas claves, y las mismas
claves dan la misma cuenta. Ninguna implicación vuelve (P-100f). De ahí la regla
de lectura:

- `conservada` bajo `claves` ⇒ `conservada` bajo `filas`.
- `no_conservada` bajo `filas` ⇒ `no_conservada` bajo cualquier medida más fina.
- Lo contrario no se sigue, y el módulo no lo publica.

`claves` es `sha256` de las rutas ordenadas, **sin los digests**. Incluirlos
convertiría la medida en una medida de bytes, que es el anillo 4 otra vez: la
magnitud tiene que poder sobrevivir a que los bytes cambien, o no añade nada.

## 5. El empalme: el defecto que no vive en ningún salto

Cada salto puede conservar por separado y la cadena no conservar, porque el nodo
`B` publicó **dos magnitudes distintas** —una al cerrar `A->B` y otra al abrir
`B->C`—. Eso no es un defecto de un salto: es del empalme, y se publica aparte
(P-102a):

```
empalme | B | a != b
```

Es el mismo patrón que en el resto del corpus: cuatro de cada cinco defectos
viven en el borde entre dos objetos, no en el álgebra de ninguno de los dos.

## 6. Lo que este objeto no hace — lista cerrada

1. **No juzga si `B` calculó bien.** Conservar no es calcular bien (P-103): las
   dos medidas sobreviven a un valor mal calculado y la línea `limite` lo dice.
   Cerrar eso exige un testigo de conservación que `B` esté obligado a emitir, y
   eso es otro anillo.
2. **No elige la medida por el cliente.** Si elige `filas` para un problema de
   claves, obtiene un verde verdadero y una respuesta inútil. La `limite` es la
   única defensa y es del lector.
3. **No mide el coste.** Medir cadenas largas cuesta; no se publica ni se
   optimiza aquí.
4. **No compone medidas distintas.** Una cadena con dos medidas no es una cadena:
   es `ContratoViolado` (P-105c). Mezclarlas produciría un veredicto que nadie
   sabría leer.
5. **No convierte el hueco en un cero.** Si falta una página, el estado es
   `sin_medida` con su causa, nunca `conservada`.

## 7. Falsadores

`python3 -B -m unittest tests.test_conservacion` — 26 pruebas, `OK`.

| id | qué falsa |
|---|---|
| P-99a | el orden publicado (`RANGO`) y el usado son el mismo |
| P-99b | una medida sin nombre o desconocida se rechaza: `ContratoViolado` |
| P-99c | dos medidas, dos respuestas, sobre el mismo par de páginas |
| P-99d | la medida cambia la respuesta y no el par de páginas |
| P-99e | el valor es propiedad recalculada, no campo |
| P-99f | suministrar el valor es un error de tipo |
| P-99g | el valor recalculado es el de la página, no el del recibo |
| P-100a | transitividad: dos saltos conservados dan una cadena conservada |
| P-100b | asociatividad sobre el veredicto y sobre la traza |
| P-100c | el neutro se absorbe a los dos lados y no se arrastra |
| P-100d | un neutro sobre otra página no es neutro |
| P-100e | la página implica las claves y la cuenta |
| P-100f | las claves implican la cuenta y no al revés |
| P-100g | las claves no implican la página |
| P-101a | un salto que no conserva degrada la cadena y **nombra** el tramo |
| P-101b | la misma cadena conserva bajo la otra medida |
| P-102a | un nodo que publica dos magnitudes rompe el empalme |
| P-103a | un valor mal calculado sobrevive a las dos medidas |
| P-103b | la línea `limite` se emite también cuando conserva |
| P-104a | una clave que se pierde y se recupera: `f(A)=f(C)` y la cadena no conserva |
| P-105a | falta una página y el veredicto no es `conservada` |
| P-105b | el empalme sin página no se lee como conservado |
| P-105c | no se mezclan medidas ni se componen cadenas que no se tocan |
| P-106a | el verificador externo reproduce las líneas del módulo, medida a medida |
| P-106b | el verificador externo no importa el generador |
| P-106c | `--medida importes` sale con RC 2: entrada inválida, no verde |
| P-106d | tres páginas en archivos fuera del árbol, bajo `env -i`, dan las mismas líneas que el módulo |
| P-106e | el acto recorre tres saltos y condena la fuga intermedia nombrando el tramo (RC 1) |
| P-106f | `medir_cadena` recibe la cadena: no lee ninguna constante del módulo |

**P-106a es el falsador de la autoría.** El verificador de tercero reimplementa
la medida, el orden y el veredicto en un archivo que no hace `import protocol`, y
su salida tiene que coincidir **línea a línea** con la del módulo. Si discrepan,
uno de los dos está midiendo otra cosa y no se sabe cuál.

## 8. Cómo volver a medirlo

```bash
cd /Users/marlene/protocol-core
python3 -B examples/verificar_conservacion.py --demo            # las dos medidas
python3 -B examples/verificar_conservacion.py --medida claves   # una sola
python3 -B -m unittest tests.test_conservacion
```

**Como tercero, sin el arbol.** La cadena entra por archivos, una ruta por linea;
los saltos salen del orden de la lista, y `--saltos` solo los confirma:

```bash
python3 -B examples/verificar_conservacion.py \
    --paginas a.txt,b.txt,c.txt,d.txt --medida filas
```

Sale `0` si la cadena conserva, `1` si no conserva —nombrando el tramo— y `2` si
la entrada no sirve. En `--demo` el codigo es siempre `0`: ahi no hay cadena
ajena que condenar, hay un dialecto que se muestra.

Si `claves` deja de discrepar donde discrepaba, hay dos posibilidades y el test
las distingue porque no adivina: o la agenda cambió —la segunda fila dejó de
cambiar de valor— o `claves` dejó de autenticar el conjunto de rutas. Nunca
«las dos».
