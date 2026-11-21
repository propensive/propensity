# Greek letters: work in progress

The Greek letters are not part of Propensity yet. They need more work, so the font is built
without them. Everything made so far is kept here and in `tools/greek.py`.

## Building them

    ./make.sh greek

This builds `wip/Propensity-Greek-WIP.ttf` (Propensity plus the Greek letters, named apart so
it cannot be mistaken for the font), renders proofs into `wip/proofs/`, and runs the checks.
It does not touch `build/`.

To put Greek into the font itself once it is ready, `tools/glyphs.py` decides whether the
Greek glyph list is included (`with_greek`), and `release()` in `tools/finish.py` holds the
naming, script registration and wording for each kind of build.

## What exists

- All 24 capitals. 14 reference the Latin capital of the same shape; Γ Λ Π Φ reuse Cyrillic
  glyphs; Δ Θ Ξ Σ Ψ Ω are constructed.
- 24 lowercase letters (μ is Marcellus's own glyph).
- Tonos and dialytika, the accented vowels of modern Greek, the raised dot and the Greek
  question mark.
- Kerning derived from Latin letters with similar edges, and the `grek` script registration.

## Settled so far

- ζ, ξ, ς, β were reviewed letter by letter. ξ has no top bar; its upper bowl is the top half
  of c at a smaller size. The stroke enters the tail of ζ and ξ 14 degrees below level
  (`TAIL_ENTRY`).
- Stems descend to -348, the depth of Marcellus's μ, not to -512 like Latin p.

## Known weaknesses

- δ is ð without its crossbar: the top ends in a point at the upper left with no turn back.
- α is the single-storey "script a" form, not the looped alpha.
- ω is m turned upside down with the middle stem shortened; its outer strokes are straight.
- Ξ's middle bar is thinner at the centre than at its ends.
- Ω's feet are heavy.
- ν, κ, π, τ are plain copies of v and the Cyrillic к, п, т.
- None of it has been reviewed by a reader of Greek.
