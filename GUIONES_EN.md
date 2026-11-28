# GUIONES_EN — nine pieces, written before anything is filmed

<!-- HUELLA-GUIONES-EN-20261125 -->

**Status:** scripts closed · **frames rendered: 0** · figures measured 25-Nov-2026 on `protocol-core` and on the real Sello A ([`SHA256SUMS_SELLO_A`](../platino-labs/sellos-fecha-cierta-20261009/SHA256SUMS_SELLO_A)).

This is **not a translation** of [`GUIONES.md`](GUIONES.md). It is a second page in the same sense: the same six acts, the same figures, the same falsifiers — with the voice budget rewritten for an English-language audience and no receipt ever translated. If a line on screen reads `-> reubicada`, the act printed `-> reubicada`; the receipt is the object, the sentence about it is commentary.

It exists for one reason: the closing piece (G5) ends with `git clone` on camera, and that command has no language.

---

## 0 · The script contract — six rules

1. **No figure on screen without its command.** True for `206 routes` and for `RC 1`. The table in [§14](#14--figure-table) is the source; the script cites it, it does not remember it.
2. **The script is not transcribed, it is convoked.** The lines that go on screen are printed by `examples/ensayo_escalera.py`, not typed by an editor.
3. **The script is rehearsed before it is filmed.** `python3 -B examples/ensayo_escalera.py` ⇒ `ENSAYO | 7/7 | … | RC 0`. That RC is the falsifier: if the act changes, the rehearsal shouts before the camera does.
4. **Animation never runs ahead.** A line appears whole — as the act printed it — and then fades in. Never character by character: typing suggests a process the act did not have.
5. **Call the exit code by its name.** `RC 0` means *the act found no rupture*, not *correct*. On screen we never say "correct" or "approved"; we say the verdict (`intacta`, `reubicada`, `divergente`, `intercambiada`, `no_medida`) and the code.
6. **The voice has a budget: 12 words every 4 s, and the piece stands without voice.** What does not fit is not sped up: it becomes a second line on screen.

---

## 1 · The raw material (measured, not imagined)

Six measured subjects, all reproduced by one command. Full receipts, in this order, are in [`GUIONES.md` §1](GUIONES.md): the seven-step ladder, the real Sello A (14 declared rows / 87 819 swept paths), the foreign subject (jq 1.7.1 official `sha256sum.txt`), and the absence act over `.env`, `AGENTS.md` and a case-folded name.

Three figures carry the whole series, and each one is a **pair**, never a single number:

| what | figure | why the pair matters |
|---|---|---|
| copies | `1 declaradas \| 3 observadas` | one signed artifact, three routes with those bytes |
| sweep | `14 declaradas \| 87855 barridas \| 87819 hasheadas` | declared, swept and hashed are three different sets |
| absence | `ausente` · `presente` · `no_medida` | the same `grep -c … → 0` covers two different truths |

---

### 1.5 · The business subject — an agenda, not a tree

Ring 3 does not ask for a source tree: it asks for a **page**. `examples/manifiesto-negocio.py` builds an appointment calendar and a ledger with Spanish names, diacritics included, and declares the piece the algebra requires and no domain ships with: the projection `pi(k)` — diacritics folded, lowercased, separators collapsed to `-`.

```
ausencia | avila-cita-09-30-sillon1.tsv | ausente | entre las filas 0 y 1
pagina | 7 filas | canonica | 0 redactadas | digest f6d1b10923c9563ebe40dec7a3af09224adf1a1e2ebd10ff5753b326b463a912
testigo | "avila-cita-09-00-sillon1.tsv" < avila-cita-09-30-sillon1.tsv < "montes-cita-11-15-sillon3.tsv" | posicion 1
verificado | si | O(1) contra la pagina autenticada
coste | 7 declaradas | 7 autenticadas | sin merkle
-> ausente
```

Three things this agenda measures that an exporter's `grep` cannot:

- **The exporter's sort is not the object.** The same seven rows written in two file orders — one by the canonical key, one by the original name, where `Á` starts at `0xC3` and lands behind all of ASCII — yield **the same** `digest f6d1b109…`, the same witness and the same `-> ausente`. Only the flag changes: `| canonica |` versus `| desordenada |`. The act sorts, and publishes that it sorted.
- **`pi` is applied before the page exists.** A route with a byte outside `A-Za-z0-9._-` is not silently normalised: `ENTRADA INVALIDA | … | componente no admisible como slug`, RC 2. A diacritic dropped in silence is a row that disappears.
- **Two clients with the same `pi` are one client.** `Ávila-cita-09-00-sillon1` and `AVILA-CITA-09-00-SILLON1` project onto the same key and the act **refuses to seal**: `CONTRATO | colapsa-el-caso: … proyectan a la misma clave` · `-> no se emite: una clave que colapsa se resuelve, no se sella` · RC 1. Guessing which one is right would be inventing the owner's answer.

**What this measurement is not:** we wrote the manifest. It proves the algebra works outside a software tree; it does **not** prove that a manifest signed by a client behaves the same way. That remains open (see [`GUIONES.md` §16](GUIONES.md)).

---

### 1.6 · The chain — two receipts composed

Ring 4 does not measure one hop: it measures the **composition** of two, `R_AB ∘ R_BC`, and the object it produces has to serve an auditor who never saw B. Over the same agenda as §1.5, with B re-reading the book and C receiving B's package:

```
cadena | A -325c7ca8fb07-> B -325c7ca8fb07-> C
tramos | 2 | peor | reubicada
ausencia vigente | avila-cita-09-30-sillon1.tsv | "avila-cita-09-00-sillon1.tsv" < avila-cita-09-30-sillon1.tsv < "montes-cita-11-15-sillon3.tsv"
-> reubicada
```

And the same pair of hops with the frontier broken —B signed one page and C read another—:

```
cadena | A -325c7ca8fb07-> B -325c7ca8fb07-> C
tramos | 2 | peor | frontera_rota
frontera | rota | el tramo anterior dejo 325c7ca8fb07 y el siguiente leyo 196b31a91400
ausencia sin transito | avila-cita-09-30-sillon1.tsv | probada contra la pagina final y la cadena no sostiene
-> frontera_rota
```

The third object is the one that makes the chain auditable from outside. [`examples/verificar_recibo_externo.py`](examples/verificar_recibo_externo.py) receives **only** the manifest and the receipt's JSON —it does not import `protocol`, it never sees the generator— and recomputes everything:

```
tramo | A->B | intacta | 7 filas | 325c7ca8fb07
testigo | avila-cita-09-30-sillon1.tsv | ausente | avila-cita-09-00-sillon1.tsv < consulta < montes-cita-11-15-sillon3.tsv
tramo | B->C | reubicada | 7 filas | 325c7ca8fb07
veredicto | reubicada | recalculado sobre 2 tramos | sostiene si
manifiesto | 7 filas | 325c7ca8fb07 | archivo ya canonico
limite | el verificador comprueba que las paginas encadenadas son las mismas; no que B hiciera su trabajo
-> cierra
```

Four things this chain measures that two loose receipts cannot say:

- **The order is not invented twice.** The composed verdict is the **worst** of the hops, and "worst" uses the order [`UBICACION.md` §4](UBICACION.md) already published: the same one that decides the RC of a single act. With two orders, the same chain would yield two certificates depending on who read it.
- **The neutral is absorbed.** `R_AB ∘ Id_B = R_AB` with the same verdict, the same chain and the same witnesses: an identity hop that survived would grow the trace with hops that never happened. And a **sick** identity —`B -> B` in `no_medida`— is not absorbed: a neutral that certifies nothing is a hole shaped like a neutral.
- **The witness has three states, not two.** `ausencia vigente` (the page that proves it is the one arriving **and** the chain holds), `ausencia historica` (proven against another page: the witness aged) and `ausencia sin transito` (the witness did not age; what is missing is the path). The third blocks the shortcut: with a broken frontier, C can read a page whose digest matches A's, the witness fits by digest, and the chain still does not join the ends.
- **`FRONTERA_ROTA` ranks above `divergente`.** A `divergente` hop says something changed; a broken frontier says the two hops are not talking about the same object, and then there is no chain to compose.

**What this measurement is not:** it certifies **byte continuity across hops**, not that B applied the agreed rule. An integrity receipt read as a correctness receipt is the signed false green. And the chain does not get cheaper by being composed: verifying a hop still costs O(page).

### 1.7 · The carrier — the file the client brings

Everything above assumes the manifest can be read. Measured on 25-Nov-2026 over five carriers that are really published (jq 1.7.1, Node v22.11.0, gh 2.62.0, Fedora 41 and Debian 12.15's `Release`) plus one synthetic two-row file: the single-dialect reader read **two**, refused three, and **accused an intact file of tampering**. Debian's carrier, its 772 rows untouched:

```
portador | deb822 | 772 filas | canonico | digest c0dc59762595
sobre | ninguno | 0 bytes de firma | no habia nada que verificar
envoltura | seccion SHA256 | 13 bloques ignorados
```

Node's, which ships its rows in another order, publishes both facts at once —that it read it and that it reordered it—:

```
portador | coreutils | 41 filas | reordenado | digest 23aaeb143953
sobre | ninguno | 0 bytes de firma | no habia nada que verificar
envoltura | ninguna | 0 normalizaciones
```

Fedora's arrives inside a clearsigned message. Since ring 6 the envelope is **unwrapped**, and how much went unchecked is stated:

```
portador | bsd | 1 filas | canonico | digest 9bc34ed33916
sobre | firmado_en_claro | 832 bytes de firma | carga bc3ba445957b | sobre f482e55b35f5 | firma no verificada
envoltura | ninguna | 0 normalizaciones
```

**A correction on this very page.** Until ring 6 the first two outputs above ended in `firma no verificada`, and Debian's `Release` does not hold **a single byte** of PGP. The census note that justified it —"the final PGP signature is not verified"— described an artifact that was not the vendored one. An invented blind spot is as bad as a false green: it stops the auditor from telling "I could not verify it" from "there was nothing to verify". Both lines were re-measured and are published as measured (§1.8).

And the witness of the ring: the same two-row file, two readings, two digests. Debian's `Release` is `deb822` **because of its leading space**; remove it and the file becomes a `coreutils` file whose paths begin with the size:

```
portador | deb822 | 2 filas | canonico | digest 7674c4bedf05
portador | coreutils | 2 filas | canonico | recorte | digest f2ba089a097c
  (' 840868 contrib/Contents-amd64', 'd6c9c82f4e61…')
```

Over the whole file that second reading **does not exist**: 58 of its 772 rows fill the size field and break `coreutils` alignment. Over a 12-row slice, all twelve fit. The ambiguity is not in the format: it is in the **example** that gets published.

**What this measurement is not:** it does not verify the PGP signature (`firma no verificada`, and it says so), it does not accept `coreutils`' `\path` escape convention, it does not accept base64 SRI, it does not guess the filename of a `suelto` carrier, and it does not choose between two readings: it publishes them. It attests the **line**, not the author.

### 1.8 · The envelope — the file is not the object

Same author, same content, three artifacts downloaded from `deb.debian.org` on 25-Nov-2026 at `19:31:13Z`:

| file | bytes | topology | before ring 6 |
|---|---|---|---|
| `debian-12.15-Release` | 149 266 | `sin_sobre` | 772 rows, `c0dc59762595` |
| `debian-12.15-InRelease` | 151 075 | `firmado_en_claro` | **refused**: `linea 4: 'Origin: Debian'` |
| `debian-12.15-Release.gpg` | 1 760 | `firma_pegada` | **0 rows, silently** |

Once the envelope is removed, `InRelease` **is** `Release`: 149 266 bytes whose `sha256` is `abcf5882746e0f68…`, the one Debian publishes. The three topologies, read today:

```
sobre | firmado_en_claro | 1759 bytes de firma | carga abcf5882746e | sobre 77737fa4b34f | firma no verificada
sobre | ninguno | 0 bytes de firma | no habia nada que verificar
SobreSinCarga: firma pegada de 1759 bytes, sin carga: el manifiesto esta en otro archivo y su nombre no viaja dentro de este
```

And the two paths of the same object publish **the same page**, which is what the client buys:

```
portador | deb822 | 772 filas | canonico | digest c0dc59762595     (Release)
portador | deb822 | 772 filas | canonico | digest c0dc59762595     (InRelease)
```

The mistake that cost one run: rebuilding the payload while losing the final newline gives `149265` bytes and `c8394efad1f4` instead of `149266` and `abcf5882746e`. One separator byte between payload and signature block, and the digest of the object stops being the author's.

**What this measurement is not:** it does not verify the signature —there is no public key in this ring— and that is why `firma no verificada` travels **with its byte count**: 3 of the 10 census artifacts carry a signature and 7 publish `0 bytes de firma`. The frequency of RFC 4880's `- ` escape in published material is `0` of `10` and is declared `no_medida`; the transformation is measured by synthetic witness. Detail: [`SOBRE.md`](SOBRE.md).

---

### 1.9 · Conservation — the magnitude that survives

The envelope (§1.8) separates file from object, and neither of them asks whether what sits **inside** the page was computed correctly. The chain of §1.6 inherits that same blindness: two `intactas` hops yield an `intacto` receipt even if the middle node recalculated all three of its rows. Conservation is the first measure in the series that **does not look at bytes**: the client declares a magnitude over the page, and the chain checks that the same magnitude reads the same at both ends.

Two declared measures, the same three-node chain, two verdicts:

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

The same chain, the same pages, two opposite verdicts. It is not a contradiction; it is the only lesson the piece has. `filas=3` counts entries and does not see that `B` recalculated its three digests; `claves` authenticates the **set of routes** —deliberately discarding the digests— so it does not see the recalculation either, but it does see that `C` moved one appointment from chair 2 to chair 4. A finer measure implies the coarser one and not the reverse (P-100e), and **neither of them looks at a row's value**.

**What this measurement is not:** conservation does *not* certify that `B` computed correctly. A `conservada` chain says the magnitude the client chose survived transport; if `B` adds wrongly and its page keeps the count, the chain has nothing to accuse it with. That is why the `limite` line travels in both outputs, the green one included: a `conservada` without that line would read as an arithmetic certification this ring does not make. Algebra, refinement chain and the 29 falsifiers P-99…P-106: [`CONSERVACION.md`](CONSERVACION.md).

---

## 2 · Camera rules

- **Background** `#0B0E12` · **text** `#E8EDF2` · **amber** `#E0A83C` = verdict · **cyan** `#4CC3D9` = datum · **grey** `#8A949E` = gap.
- **Monospace, no ligatures**, for the receipt. The receipt is not re-flowed, not aligned "nicely" and not translated.
- **One movement per line**: opacity 0→1 in 120 ms, no bounce. The climax is not animated.
- **No tension music.** A 60 BPM pulse at most, and only under the closing lines.
- **Ephemeral subjects are struck through as `<subject>`**: never show a `/tmp` path the viewer cannot have.
- **Deterministic render** (a `letras-video` rule): same `cues.ts` ⇒ same MP4 bit for bit.

---

## 3 · G1 · "Fourteen copies" — 15 s · teaser

**Thesis:** a tree holds many more originals than it believes. The act does not pick the good one for you: it counts them.

| t | screen | voice |
|---|---|---|
| 0,0–2,5 | `14 archivos firmados.` | «Fourteen signed files.» |
| 2,5–6,0 | `206 rutas.` (cyan) | «Two hundred and six routes with those bytes.» |
| 6,0–10,5 | `10 conforme / 4 reubicado / 0 diverge / 0 opaco -> reubicada` | «Ten stayed. Four moved.» |
| 10,5–13,5 | `reubicado <acta> -> 14 caminos` + `RC 0` | «And it picks no destination for you.» |
| 13,5–15,0 | `protocol-core` | — |

**Figures:** `206` ⇒ §14 #4 · `14/4/10` ⇒ §14 #3.
**Falsifier:** the command in [`GUIONES.md` §1.2](GUIONES.md) must still print `10 conforme / 4 reubicado`. If the seal moves, the piece is re-measured, not re-filmed.

---

## 4 · G2 · "The ladder" — 45 s · main piece

**Thesis:** a verdict is not a traffic light. There are six distinguishable states, and two of them exist precisely because a naive verifier cannot see them.

| t | screen | voice |
|---|---|---|
| 0,0–3,0 | `Un recibo. Siete sujetos.` | «Same thing, seven times.» |
| 3,0–8,5 | block 1/7 complete | «The bytes are where declared.» |
| 8,5–14,5 | block 2/7 complete | «Same bytes, another route.» |
| 14,5–22,0 | block 3/7 complete + second line `cada digest sigue apareciendo una vez` | «Every digest still appears once. Still not `intacta`.» |
| 22,0–28,0 | block 4/7 complete | «One byte too many.» |
| 28,0–33,0 | block 5/7 complete | «No manifest, no adjudication. Code two.» |
| 33,0–39,5 | block 6/7 complete | «Undeclared copies: the datum appears.» |
| 39,5–43,0 | block 7/7 complete | «On disk, outside the universe: `no_medida`.» |
| 43,0–45,0 | `ENSAYO | 7/7 | RC 0` | «Seven of seven.» |

**Voice:** the argument of block 3 — that the multiset of hashes is identical to the declared one — **does not fit** in eight seconds and is not recited: it becomes a second line on screen. It is the one sentence in the series that is never spoken.

---

## 5 · G3 · "What it could not see" — 30 s

**Thesis:** the product is not "I detect ruptures", it is **I publish what I did not look at**. Everyone else sells green check marks.

| t | screen | voice |
|---|---|---|
| 0,0–4,0 | `2 conforme / 0 reubicado / 0 diverge / 0 opaco -> intacta` + `coste \| 2 declaradas \| 0 barridas \| 2 hasheadas` | «It says `intacta` and swept nothing.» |
| 4,0–10,0 | same subject with `--completo` ⇒ `coste \| 2 declaradas \| 4 barridas \| 4 hasheadas` + `redundancia \| bbbff613… \| 1 declaradas \| 2 observadas` | «Sweep asked: verdict unchanged, copy appears.» |
| 10,0–17,0 | `universo \| 3 rutas \| … \| 1 fuera del universo` + `opaco __pycache__/x.pyc` + `-> no_medida` | «A declared byte the act excludes: opaque.» |
| 17,0–23,0 | `RC 1` | «Not a bug. The program saying where it stopped looking.» |
| 23,0–30,0 | `opaco` · `no_medida` · `redundancia` (all cyan) | «An instrument that declares its blindness is auditable.» |

**Figures:** §14 #2, #5, #6, #7.
**Falsifier:** P-47 together with P-44/P-45 — without `--completo` the `redundancia` line **cannot** appear; with it, the verdict does not move.

---

## 6 · G4 · "Copies nobody signed" — 25 s

**Thesis:** the datum a client buys — how many copies of the signed bytes exist in their tree — and the honesty of saying how much of that is **not** measured.

| t | screen | voice |
|---|---|---|
| 0,0–6,0 | `$ curl -sL …/jq-1.7.1/sha256sum.txt` + `26 filas · 2129 B` (cyan) | «A manifest I did not write.» |
| 6,0–13,0 | `redundancia \| 5942c9b0… \| 1 declaradas \| 3 observadas \| jq-linux-amd64, vendor/…` | «One file signed by jq. Three routes.» |
| 13,0–19,0 | `1 conforme / 0 reubicado / 0 diverge / 0 opaco -> intacta` + `RC 0` | «Verdict unchanged. The copy is a datum.» |
| 19,0–25,0 | `14 digests \| 206 rutas` (amber) + second line `esto sí es mi árbol` | «In mine: two hundred and six routes.» |

**Figures:** §14 #4, #10.
**Falsifier:** [`GUIONES.md` §1.3](GUIONES.md) — the line `1 declaradas \| 3 observadas` over jq 1.7.1.
**Permanent lower third, grey, 6,0–19,0:** `bytes y manifiesto: jq 1.7.1 · las copias: mías`. The voice does not say it; the piece does not hide it.

---

## 7 · G6 · "What is not there" — 30 s

**Thesis:** half of an auditor's work is not proving what exists, it is proving what does **not**: that the bundle carries no private key, that the record does not include the deleted entry. A `grep` does not prove absence — it proves it searched. What proves absence is an **order witness**: two adjacent rows with the query between them.

| t | screen | voice |
|---|---|---|
| 0,0–5,0 | `$ grep -c '\.env' SHA256SUMS_SELLO_A` → `0` · same for `AGENTS.md` → `0` (grey) | «The same zero for both names.» |
| 5,0–13,0 | `testigo \| ⊥ < .env < "ACTA_DE_CIERRE…md" \| posicion 0` + `verificado \| si \| O(1)` + `-> ausente` `RC 0` | «This one is missing. Its neighbours prove it.» |
| 13,0–21,0 | `testigo \| "ACTA_GATE…md" < AGENTS.md < … \| posicion 3` + `arbol-ausencia \| presente` + `RC 1` | «This one exists, undeclared. Same zero.» |
| 21,0–27,0 | `caso \| colapsa-el-caso` + `caso-choque \| jq-linux-amd64 \| …` + `-> presente` `RC 1` | «Case-blind volume, uppercase name: still `presente`.» |
| 27,0–30,0 | `ausente` · `presente` · `no_medida` (all cyan) | «Absence proved. Presence declared. The rest said.» |

**Figures:** §14 #11, #12, #13.
**Falsifier:** `python3 -B -m unittest tests.test_ausencia` (27 tests) and the receipts in [`GUIONES.md` §1.4](GUIONES.md).

---

## 8 · G7 · "The appointment that never existed" — 30 s · domain piece

**Thesis:** the same order witness that proves a `.env` is not in a batch proves an appointment is not in a calendar — and it proves it **without showing the other appointments**. That is where the product leaves software: a clinic, a studio or a bank can attest the absence of a record without handing over the book.

| t | pantalla | voz |
|---|---|---|
| 0,0–5,0 | `pagina | 7 filas | canonica | digest f6d1b109…` (cyan) | "Seven signed appointments. None of them is the nine-thirty one." |
| 5,0–13,0 | `testigo | "avila-cita-09-00-sillon1.tsv" < avila-cita-09-30-sillon1.tsv < "montes-cita-11-15-sillon3.tsv" | posicion 1` + `verificado | si | O(1)` + `-> ausente` `RC 0` (amber verdict) | "Between nine and a quarter past eleven there is no room for anything." |
| 13,0–21,0 | `pagina | … | canonica | … digest f6d1b109…` above · `pagina | … | desordenada | … digest f6d1b109…` below (same digest, both cyan) | "Two exporters, two orders. One seal: the order was never the object." |
| 21,0–27,0 | `CONTRATO | colapsa-el-caso: 'Ávila-…' y 'AVILA-…' proyectan a la misma clave` + `-> no se emite` `RC 1` (amber) | "Ávila and AVILA are the same client. The act does not guess: it stops." |
| 27,0–30,0 | `ausente` · `presente` · `no_medida` (all three in cyan) | "Absence proven. Presence declared. The rest, unmeasured." |

**Animation:** the same as G3 and G6 — the series has one visual ending and does not invent new grammar.
**Figures:** §14 #14, #15.
**Falsifier:** `python3 -B -m unittest tests.test_negocio` (13 tests) and the receipts in [`GUIONES.md` §1.5](GUIONES.md).
**Permanent note, lower third in grey, while the 21,0–27,0 row is up:** `our own subject, not a client's · no client has signed this manifest`.

---

## 9 · G8 · "The chain that does not break" — 30 s · composition piece

**Thesis:** when the package passes through hands that are not the owner's, two loose receipts are not enough: it takes a **composed receipt** that names both what travelled and the point where the chain stopped talking about the same object. This is the piece for anyone whose data is already spread across an exporter, a worker and an auditor.

| t | screen | voice |
|---|---|---|
| 0,0–5,0 | `cadena \| A -325c7ca8fb07-> B -325c7ca8fb07-> C` (cyan) | "Two hops. One object." |
| 5,0–13,0 | `tramos \| 2 \| peor \| reubicada` + `ausencia vigente \| avila-cita-09-30-sillon1.tsv \| "…09-00…" < … < "montes…"` + `-> reubicada` (amber) | "The appointment is still absent three nodes later. The witness travels with the chain." |
| 13,0–21,0 | `frontera \| rota \| el tramo anterior dejo 325c7ca8fb07 y el siguiente leyo 196b31a91400` + `-> frontera_rota` (amber) | "The middle node swapped the book. The chain does not close, and without a chain there is no receipt." |
| 21,0–27,0 | `ausencia sin transito \| …` + `veredicto \| reubicada \| recalculado sobre 2 tramos \| sostiene si` + `limite \| … no que B hiciera su trabajo` (grey) | "Neither current nor stale: the witness is the same and the path is not." |
| 27,0–30,0 | `reubicada` · `frontera_rota` · `no_medida` (all three in cyan) | "What travelled. What broke." |

**Animation:** the one from G3, G6 and G7 —three words at the close, same movement, same opacity—; the new move is the joint: the `frontera` line enters **between** the two digests, not on top.
**Figures:** §14 #16, #17.
**Falsifier:** `python3 -B -m unittest tests.test_composicion` (22 tests) and the receipts in [`GUIONES.md` §1.6](GUIONES.md).
**Permanent note, lower third in grey, while the 13,0–21,0 row is up:** `byte continuity across hops · not that the middle node did its job`.

---

## 10 · G9 · "Your manifest, not mine" — 30 s · carrier piece

**Thesis:** the client does not hand us a clean tree: they hand us the file their tool wrote. The piece shows the same receipt being born over five different carriers and, above all, it shows the file the old reader **accused** of tampering while it was intact. This is the piece for anyone who already tried to verify somebody else's release and hit an "OK" that was not looking at what it claimed to look at.

| t | screen | voice |
|---|---|---|
| 0,0–5,0 | `portador \| coreutils \| 26 filas \| canonico \| digest f1f692fe9f92` (cyan) | "jq's manifest. Twenty-six rows." |
| 5,0–13,0 | `portador \| bsd \| 1 filas …` + `envoltura \| pgp \| firma no verificada` + `portador \| deb822 \| 772 filas \| canonico \| digest c0dc59762595` (cyan, three columns) | "Fedora signs it. Debian paginates it into seven hundred and seventy-two rows. Same receipt, three files." |
| 13,0–21,0 | `portador \| coreutils \| 41 filas \| reordenado \| digest 23aaeb143953` (amber) + `dddf2b497e71` under it in grey | "Node wrote it in another order. I read it, I said so, and I published both digests." |
| 21,0–27,0 | `portador \| deb822 \| 2 filas \| canonico \| digest 7674c4bedf05` + `portador \| coreutils \| 2 filas \| … recorte \| digest f2ba089a097c` + `881cba55a9d2` struck through in red | "The file was intact. The single-dialect reader called it tampered." |
| 27,0–30,0 | `coreutils` · `bsd` · `deb822` · `suelto` (all four in cyan) | "Four grammars. None chosen blindly." |

**Animation:** the first three columns enter with the usual movement; the new move is the **strike-through** of `881cba55a9d2` at 21,0–27,0 —one red line crossing the digest, 200 ms, no bounce—, because what is being withdrawn is an accusation, not a datum.
**Figures:** §14 #18, #19.
**Falsifier:** `python3 -B -m unittest tests.test_portador` (21 tests) and the eight artifacts in `examples/portadores/` with their `FUENTES.txt`.
**Permanent note, lower third in grey, while the 21,0–27,0 row is up:** `the signature is not verified · the line is attested, not the author`.

---

## 11 · G10 · "The file is not the object" — 30 s · envelope piece

**Thesis:** two files from the same author, with the same 149 266 bytes inside, give **two digests** —the file's and the object's— and that distinction is exactly what the client pays for. The piece shows Debian's `InRelease`, which the old reader refused while blaming its content, and the detached signature that used to read as a zero-row manifest.

| t | screen | voice |
|---|---|---|
| 0,0–5,0 | `sobre \| firmado_en_claro \| 1759 bytes de firma` + `carga abcf5882746e` and `sobre 77737fa4b34f` (cyan, two columns) | "The same file. Two digests." |
| 5,0–12,0 | `sobre \| ninguno \| 0 bytes de firma \| no habia nada que verificar` (grey) | "Debian publishes it unsigned too. I say which one I hold." |
| 12,0–20,0 | `sobre \| firma_pegada \| 1759 bytes de firma \| carga -` + `SobreSinCarga` (amber) | "A detached signature carries no object. Its link is the name." |
| 20,0–26,0 | `portador \| deb822 \| 772 filas \| canonico \| digest c0dc59762595` twice, identical columns | "Two files, one page: seven hundred and seventy-two rows." |
| 26,0–30,0 | `firma no verificada` (amber) + `0 bytes de firma` (grey) | "What I did not check, with its byte count." |

**Animation:** the two columns of 20,0–26,0 are drawn **at the same time and with the same motion**, and the two final figures stay character-aligned; the only highlight is the `-` of `carga -` at 12,0–20,0, which pulses once and then holds still, because it names an absence and not an error.
**Figures:** [`GUIONES.md` §14 #20, #21](GUIONES.md).
**Falsifier:** `python3 -B -m unittest tests.test_sobre` (13 tests) and the three Debian artifacts in `examples/portadores/`.
**Permanent notice, lower third in grey, from 26,0:** `the signature is not verified · how much was not verified is measured`.

---

## 12 · G11 · "The count survives, the calculation does not" — 30 s · conservation piece

**Thesis:** the chain of G8 says the bytes arrived; it does not say that what the middle node put inside was added up correctly. Conservation is the first measure in the series that **is not a byte**: the client declares a magnitude —how many rows, which keys— and the chain checks that it reads the same at both ends. The piece shows the same three nodes giving **two opposite verdicts** depending on the declared measure, and the limit line that accompanies both.

| t | screen | voice |
|---|---|---|
| 0,0–6,0 | `medida \| filas \| declarada por el cliente` + `filas=3 -> filas=3` (cyan) | "Three appointments in. Three appointments out." |
| 6,0–13,0 | `salto \| A->B \| filas \| filas=3 -> filas=3 \| conservada` and `salto \| B->C \| filas \| … \| conservada` | "The count survives even when every byte changes." |
| 13,0–20,0 | `manifiesto B: las tres filas, recalculadas` (grey) + `salto \| A->B \| claves \| … \| conservada` (amber) | "B recalculated all three rows. Neither measure saw it." |
| 20,0–26,0 | `salto \| B->C \| claves \| claves=17849efefd40 -> claves=37cc1abd699d \| no_conservada` + `degradado \| B->C \| no_conservada` | "C moved one appointment to another chair, and there it accuses." |
| 26,0–30,0 | `limite \| conserva el transporte, no el calculo: …` (amber, lower third) | "It conserves the transport. About the calculation it says nothing." |

**Animation:** the two runs of the act are drawn **one after the other over the same three nodes**, without any box moving: the only thing that changes between 6,0–13,0 and 20,0–26,0 is the word `filas` becoming `claves`. The `limite` line is not animated: it appears complete and stays, because it is the reading condition of everything above it.
**Figures:** [`GUIONES.md` §14 #22, #23](GUIONES.md).
**Falsifier:** `python3 -B -m unittest tests.test_conservacion` (26 tests) and the third-party act `python3 -B examples/verificar_conservacion.py --demo` (see [`GUIONES.md` §1.9](GUIONES.md)).
**Permanent notice, lower third in grey, from 26,0:** `conservation measures the transport · the calculation stays outside`.

---

## 13 · G5 · "Verify it without believing me" — 45 s · closing

**Thesis:** the whole product fits in one line: *I am not asking you to believe me, I am giving you the act.* The piece shows no conclusions — it shows the commands and their output, and leaves the keyboard to the viewer.

| t | screen | voice |
|---|---|---|
| 0,0–5,0 | `$ git clone …` + `Ran 302 tests` + `OK` | «A public clone. The whole suite.» |
| 5,0–13,0 | `$ python3 -B examples/verificar_sello.py --manifiesto … --check` ⇒ `REPRODUCE \| <digest>` | «Re-emitted and compared to itself.» |
| 13,0–21,0 | four grey `real` lines: `343,61 s` · `164,11 s` · `67,11 s` · `264,35 s` | «Four runs. Sixty-seven seconds, or three hundred.» |
| 21,0–29,0 | `coste \| 14 declaradas \| 87855 barridas \| 87819 hasheadas` (cyan) | «So the clock stays out. Counters go in.» |
| 29,0–38,0 | `ENSAYO \| 7/7 \| … \| RC 0` | «Everything you saw is convoked by one command.» |
| 38,0–45,0 | `git clone` + `python3 -B examples/ensayo_escalera.py` (monospace, still) | «If this stops being true, the rehearsal fails first.» |

**Animation:** the four `real` timings appear as columns of one table, not as a trend line: there is no trend, there is dispersion.
**Figures:** §14 #1, #3, #8, #9.
**Falsifier:** the commands themselves, on camera, from a cold clone (§15).

---

## 14 · Figure table

| # | figure | command that produces it | date |
|---|---|---|---|
| 1 | `ENSAYO 7/7 RC 0` | `python3 -B examples/ensayo_escalera.py` | 25-Nov-2026 |
| 2 | ladder `0 / 0 / 1 / 1 / 2` | idem, column `RC n · esperado m` | 25-Nov-2026 |
| 3 | `10 conforme / 4 reubicado … -> reubicada` · `coste \| 14 declaradas \| 87855 barridas \| 87819 hasheadas` | [`GUIONES.md` §1.2](GUIONES.md) | 25-Nov-2026 |
| 4 | `14 digests \| 206 rutas` | aggregate of [`GUIONES.md` §1.2](GUIONES.md) | 25-Nov-2026 |
| 5 | `coste \| 2 declaradas \| 0 barridas \| 2 hasheadas` | ensayo, step 1/7 | 25-Nov-2026 |
| 6 | `coste \| 2 declaradas \| 4 barridas \| 4 hasheadas` | ensayo, step 6/7 | 25-Nov-2026 |
| 7 | `1 fuera del universo` · `opaco __pycache__/x.pyc` | ensayo, step 7/7 | 25-Nov-2026 |
| 8 | `343,61 / 164,11 / 67,11 / 264,35 s` | `/usr/bin/time -p` over the act, four machine states | 24–25 Nov-2026 |
| 9 | `Ran 302 tests` · `OK` | `python3 -B -m unittest discover -s tests` | 27-Nov-2026 |
| 10 | `redundancia \| 5942c9b0… \| 1 declaradas \| 3 observadas` | [`GUIONES.md` §1.3](GUIONES.md) (jq 1.7.1, official manifest) | 25-Nov-2026 |
| 11 | `ausencia \| .env \| ausente` · `testigo \| ⊥ < .env < …` · `RC 0` | [`GUIONES.md` §1.4](GUIONES.md) | 25-Nov-2026 |
| 12 | `ausencia \| AGENTS.md \| ausente` · `arbol-ausencia \| presente` · `RC 1` | [`GUIONES.md` §1.4](GUIONES.md) | 25-Nov-2026 |
| 13 | `caso-choque \| jq-linux-amd64 \| …` · `caso \| colapsa-el-caso` · `RC 1` | [`GUIONES.md` §1.4](GUIONES.md) (jq 1.7.1) | 25-Nov-2026 |
| 14 | `pagina \| 7 filas \| canonica` and `… \| desordenada` · **same** `digest f6d1b109…` | [`GUIONES.md` §1.5](GUIONES.md) | 25-Nov-2026 |
| 15 | `ausencia \| avila-cita-09-30-sillon1.tsv \| ausente` · `testigo \| "…09-00…" < … < "montes…"` · `coste \| 7 declaradas \| 7 autenticadas` | [`GUIONES.md` §1.5](GUIONES.md) | 25-Nov-2026 |
| 16 | `cadena \| A -325c7ca8fb07-> B -325c7ca8fb07-> C` · `tramos \| 2 \| peor \| reubicada` · `ausencia vigente \| …` | [`GUIONES.md` §1.6](GUIONES.md) | 25-Nov-2026 |
| 17 | `frontera \| rota \| … 325c7ca8fb07 … 196b31a91400` · `ausencia sin transito \| …` · `veredicto \| reubicada \| recalculado sobre 2 tramos` | [`GUIONES.md` §1.6](GUIONES.md) | 25-Nov-2026 |
| 18 | `portador \| deb822 \| 772 filas \| canonico \| digest c0dc59762595` · `portador \| bsd \| 1 filas …` · `portador \| coreutils \| 41 filas \| reordenado \| digest 23aaeb143953` | [`GUIONES.md` §1.7](GUIONES.md) · `tests.test_portador` | 25-Nov-2026 |
| 19 | `deb822 2 filas 7674c4bedf05` and `coreutils 2 filas … recorte f2ba089a097c` over **the same file** · the accused `881cba55a9d2` | [`GUIONES.md` §1.7](GUIONES.md) | 25-Nov-2026 |
| 20 | `sobre \| firmado_en_claro \| 1759 bytes de firma \| carga abcf5882746e \| sobre 77737fa4b34f` · `sobre \| ninguno \| 0 bytes de firma` · `SobreSinCarga` over `firma_pegada` | [`GUIONES.md` §1.8](GUIONES.md) · `tests.test_sobre` | 25-Nov-2026 |
| 21 | the two paths of one object: `carga 149266 B abcf5882746e` through `Release` and through `InRelease` · the measured mistake: `149265 B c8394efad1f4` when the final newline is dropped | [`GUIONES.md` §1.8](GUIONES.md) · §7 of [`SOBRE.md`](SOBRE.md) | 25-Nov-2026 |
| 22 | `conservacion \| A -> B -> C` · `medida \| filas` · `salto \| A->B \| filas \| filas=3 -> filas=3 \| conservada` · `-> conservada` | [`GUIONES.md` §1.9](GUIONES.md) · `examples/verificar_conservacion.py --demo` | 27-Nov-2026 |
| 23 | the same chain with `medida \| claves`: `claves=17849efefd40 -> claves=37cc1abd699d` · `degradado \| B->C \| no_conservada` · `-> no_conservada` | [`GUIONES.md` §1.9](GUIONES.md) · `--demo --medida claves` | 27-Nov-2026 |

`87819` and `87855` count different sets (swept routes / hashed routes, which include declared routes outside the universe); they are not subtracted from each other. `206` is a sum of list lengths printed by the act, not a subtraction.

---

## 15 · Falsifiers of the series

| piece | what falsifies it | command |
|---|---|---|
| G1, G4 | the Sello A or the jq subject changes verdict or multiplicity | [`GUIONES.md` §1.2, §1.3](GUIONES.md) |
| G2, G5 | a step of the rehearsal stops matching | `python3 -B examples/ensayo_escalera.py` (RC ≠ 0) |
| G3 | `--completo` stops moving the counter, or moves the verdict | `python3 -B -m unittest tests.test_ubicacion.TestRedundancia` |
| G6 | the same `grep` distinguishes two truths again, or `21,0–27,0` stops printing `presente` | `python3 -B -m unittest tests.test_ausencia` |
| G7 | the absent appointment stops printing `ausente` RC 0, two orders stop sharing one digest, or a `pi` collision stops halting the act | `python3 -B -m unittest tests.test_negocio` |
| G8 | the chain stops naming the degraded hop, the neutral stops being absorbed, or a broken frontier inherits the absence again | `python3 -B -m unittest tests.test_composicion` |
| G9 | a real carrier stops being read, the intact file gets accused again, or a slice stops opening two readings | `python3 -B -m unittest tests.test_portador` |
| G10 | the envelope stops yielding `Release`'s `sha256`, a `firma_pegada` reads as a zero-row manifest again, or `firma no verificada` appears over a file with no signature | `python3 -B -m unittest tests.test_sobre` |
| G11 | the same chain stops giving two different verdicts depending on the measure, or a missing measure stops giving `sin_medida` | `python3 -B -m unittest tests.test_conservacion` · [`GUIONES.md` §1.9](GUIONES.md) |
| all | the suite falls | `python3 -B -m unittest discover -s tests` |

A script whose figure is no longer produced by its command **is not fixed**: it is withdrawn and re-measured.

Both pages are checked by `tests/test_guiones.py`: same section numbering, same figures cited, same voice budget, same test count. A page that drifts from the other one fails the suite.

---

## 16 · What must not be filmed yet

1. **The duplication rate of a client tree: `NO_MEDIDA`.** What is measured is the act over foreign bytes (jq 1.7.1) with a **self-built** copy topology. The `k = 14` copies of the Sello A are worktrees of the same owner.
2. **The cost on a client machine.** Four runs of the same act range from 67 to 344 s, all on this machine. None of them is "the time of the act".
3. **The precedence between `suplantada` and `intercambiada`** is fixed only in a fixture (P-28).
4. **Absence inside a client's universe.** The act proves absence over the page and checks it against a tree it walks with six declared exclusions.
5. **The business subject is ours.** The agenda in §1.5 is a fixture: it proves the algebra works outside a software tree, **not** that a manifest signed by a client behaves the same way.
6. **The full ladder against a third-party tree** covers `intacta`/`reubicada`/`suplantada`/`divergente`, not the seven steps.
7. **A client's chain.** Composition is measured between nodes of the same owner and over an agenda we wrote; no real three-party chain has gone through `componer`. And composing does not make verification cheaper: `n` hops still cost O(page) per hop someone has to re-hash.
8. **The middle node's arithmetic correctness: `NO_MEDIDA`.** Conservation says the declared magnitude survived transport; it does not say `B` computed correctly. If `B` adds wrongly **and** its page keeps the count it declared, the chain has nothing to accuse it with (P-103). What is measured is something else: that the chain falls silent when the measure is missing —`sin_medida`, worse than `conservada` and better than `no_conservada`— and that two measures of the same chain give different verdicts (P-102).

Filming any of these eight as if measured is the only mistake this file cannot repair afterwards.

---

## 17 · Bridge with `letras-video`

Each piece is a `cues.ts` file: `t` in, `t` out, the exact string, and the color. The render is deterministic, so the same cues produce the same MP4 — and the MP4 can be its own subject in G5. Full bridge in [`GUIONES.md` §17](GUIONES.md).
