# Propensity

Propensity is a flared roman typeface with Latin and Cyrillic, and the official typeface of
[Propensive](https://propensive.com/).

It is based on [Marcellus](https://fonts.google.com/specimen/Marcellus) by Brian J. Bonislawsky
(Astigmatic). Every Latin glyph, its metrics and its kerning are Marcellus's, unchanged.
Propensity adds Cyrillic for Russian, Ukrainian and Belarusian, with outlines adapted from
Marcellus's own letters and from Marcellus SC. Because "Marcellus" is a Reserved Font Name,
this modified version carries a different name.

## The font

- `build/Propensity-Regular.ttf` and `build/Propensity-Regular.woff2`
- `proofs/specimen.html` shows it in a browser; the proof sheets are beside it
- Stylistic set `ss01` gives pointed forms of Л, Д, л and д in place of the flat-topped defaults

Greek letters are in progress and are not part of the font yet; see `wip/GREEK.md`.

## Licence

Propensity is released under the [SIL Open Font License 1.1](license.md), the same licence
as Marcellus. Marcellus is copyright Brian J. Bonislawsky DBA Astigmatic (AOETI); the Cyrillic
additions are copyright Propensive OÜ.

## Building

The font is generated from the Marcellus files in `vendor/` by the scripts in `tools/`.

    python3 -m venv .venv
    .venv/bin/pip install -r requirements.txt
    ./make.sh          # builds the font, renders the proofs, runs the checks
    ./make.sh greek    # builds the Greek work in progress into wip/
