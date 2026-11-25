# GUIONES_EN — seven pieces, written before anything is filmed

<!-- HUELLA-GUIONES-EN-20261125 -->

**Status:** scripts closed · **frames rendered: 0** · figures measured 25-Nov-2026 on `protocol-core` and on the real Sello A ([`SHA256SUMS_SELLO_A`](../platino-labs/sellos-fecha-cierta-20261009/SHA256SUMS_SELLO_A)).

This is **not a translation** of [`GUIONES.md`](GUIONES.md). It is a second page in the same sense: the same six acts, the same figures, the same falsifiers — with the voice budget rewritten for an English-language audience and no receipt ever translated. If a line on screen reads `-> reubicada`, the act printed `-> reubicada`; the receipt is the object, the sentence about it is commentary.

It exists for one reason: the closing piece (G5) ends with `git clone` on camera, and that command has no language.

---

## 0 · The script contract — six rules

1. **No figure on screen without its command.** True for `206 routes` and for `RC 1`. The table in [§10](#10--figure-table) is the source; the script cites it, it does not remember it.
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

**What this measurement is not:** we wrote the manifest. It proves the algebra works outside a software tree; it does **not** prove that a manifest signed by a client behaves the same way. That remains open (see [`GUIONES.md` §12](GUIONES.md)).

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

**Figures:** `206` ⇒ §10 #4 · `14/4/10` ⇒ §10 #3.
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

**Figures:** §10 #2, #5, #6, #7.
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

**Figures:** §10 #4, #10.
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

**Figures:** §10 #11, #12, #13.
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
**Figures:** §10 #14, #15.
**Falsifier:** `python3 -B -m unittest tests.test_negocio` (9 tests) and the receipts in [`GUIONES.md` §1.5](GUIONES.md).
**Permanent note, lower third in grey, while the 21,0–27,0 row is up:** `our own subject, not a client's · no client has signed this manifest`.

---

## 9 · G5 · "Verify it without believing me" — 45 s · closing

**Thesis:** the whole product fits in one line: *I am not asking you to believe me, I am giving you the act.* The piece shows no conclusions — it shows the commands and their output, and leaves the keyboard to the viewer.

| t | screen | voice |
|---|---|---|
| 0,0–5,0 | `$ git clone …` + `Ran 176 tests` + `OK` | «A public clone. The whole suite.» |
| 5,0–13,0 | `$ python3 -B examples/verificar_sello.py --manifiesto … --check` ⇒ `REPRODUCE \| <digest>` | «Re-emitted and compared to itself.» |
| 13,0–21,0 | four grey `real` lines: `343,61 s` · `164,11 s` · `67,11 s` · `264,35 s` | «Four runs. Sixty-seven seconds, or three hundred.» |
| 21,0–29,0 | `coste \| 14 declaradas \| 87855 barridas \| 87819 hasheadas` (cyan) | «So the clock stays out. Counters go in.» |
| 29,0–38,0 | `ENSAYO \| 7/7 \| … \| RC 0` | «Everything you saw is convoked by one command.» |
| 38,0–45,0 | `git clone` + `python3 -B examples/ensayo_escalera.py` (monospace, still) | «If this stops being true, the rehearsal fails first.» |

**Animation:** the four `real` timings appear as columns of one table, not as a trend line: there is no trend, there is dispersion.
**Figures:** §10 #1, #3, #8, #9.
**Falsifier:** the commands themselves, on camera, from a cold clone (§11).

---

## 10 · Figure table

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
| 9 | `Ran 176 tests` · `OK` | `python3 -B -m unittest discover -s tests` | 25-Nov-2026 |
| 10 | `redundancia \| 5942c9b0… \| 1 declaradas \| 3 observadas` | [`GUIONES.md` §1.3](GUIONES.md) (jq 1.7.1, official manifest) | 25-Nov-2026 |
| 11 | `ausencia \| .env \| ausente` · `testigo \| ⊥ < .env < …` · `RC 0` | [`GUIONES.md` §1.4](GUIONES.md) | 25-Nov-2026 |
| 12 | `ausencia \| AGENTS.md \| ausente` · `arbol-ausencia \| presente` · `RC 1` | [`GUIONES.md` §1.4](GUIONES.md) | 25-Nov-2026 |
| 13 | `caso-choque \| jq-linux-amd64 \| …` · `caso \| colapsa-el-caso` · `RC 1` | [`GUIONES.md` §1.4](GUIONES.md) (jq 1.7.1) | 25-Nov-2026 |
| 14 | `pagina \| 7 filas \| canonica` and `… \| desordenada` · **same** `digest f6d1b109…` | [`GUIONES.md` §1.5](GUIONES.md) | 25-Nov-2026 |
| 15 | `ausencia \| avila-cita-09-30-sillon1.tsv \| ausente` · `testigo \| "…09-00…" < … < "montes…"` · `coste \| 7 declaradas \| 7 autenticadas` | [`GUIONES.md` §1.5](GUIONES.md) | 25-Nov-2026 |

`87819` and `87855` count different sets (swept routes / hashed routes, which include declared routes outside the universe); they are not subtracted from each other. `206` is a sum of list lengths printed by the act, not a subtraction.

---

## 11 · Falsifiers of the series

| piece | what falsifies it | command |
|---|---|---|
| G1, G4 | the Sello A or the jq subject changes verdict or multiplicity | [`GUIONES.md` §1.2, §1.3](GUIONES.md) |
| G2, G5 | a step of the rehearsal stops matching | `python3 -B examples/ensayo_escalera.py` (RC ≠ 0) |
| G3 | `--completo` stops moving the counter, or moves the verdict | `python3 -B -m unittest tests.test_ubicacion.TestRedundancia` |
| G6 | the same `grep` distinguishes two truths again, or `21,0–27,0` stops printing `presente` | `python3 -B -m unittest tests.test_ausencia` |
| G7 | the absent appointment stops printing `ausente` RC 0, two orders stop sharing one digest, or a `pi` collision stops halting the act | `python3 -B -m unittest tests.test_negocio` |
| all | the suite falls | `python3 -B -m unittest discover -s tests` |

A script whose figure is no longer produced by its command **is not fixed**: it is withdrawn and re-measured.

Both pages are checked by `tests/test_guiones.py`: same section numbering, same figures cited, same voice budget, same test count. A page that drifts from the other one fails the suite.

---

## 12 · What must not be filmed yet

1. **The duplication rate of a client tree: `NO_MEDIDA`.** What is measured is the act over foreign bytes (jq 1.7.1) with a **self-built** copy topology. The `k = 14` copies of the Sello A are worktrees of the same owner.
2. **The cost on a client machine.** Four runs of the same act range from 67 to 344 s, all on this machine. None of them is "the time of the act".
3. **The precedence between `suplantada` and `intercambiada`** is fixed only in a fixture (P-28).
4. **Absence inside a client's universe.** The act proves absence over the page and checks it against a tree it walks with six declared exclusions.
5. **The full ladder against a third-party tree** covers `intacta`/`reubicada`/`suplantada`/`divergente`, not the seven steps.

Filming any of these six as if measured is the only mistake this file cannot repair afterwards.

---

## 13 · Bridge with `letras-video`

Each piece is a `cues.ts` file: `t` in, `t` out, the exact string, and the color. The render is deterministic, so the same cues produce the same MP4 — and the MP4 can be its own subject in G5. Full bridge in [`GUIONES.md` §13](GUIONES.md).
