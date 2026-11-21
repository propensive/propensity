"""Render the proof sheets and the HTML specimen.

usage: proof.py BUILT.ttf OUT_DIR

A font that contains the Greek letters gets the Greek sheets as well.
"""
import base64
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fontTools.ttLib import TTFont  # noqa: E402

from render import render  # noqa: E402

UPPER = "АБВГҐДЕЁЄЖЗИІЇЙКЛМНОПРСТУЎФХЦЧШЩЪЫЬЭЮЯ"
LOWER = "абвгґдеёєжзиіїйклмнопрстуўфхцчшщъыьэюя"
RU = "Съешь же ещё этих мягких французских булок, да выпей чаю."
RU2 = "Широкая электрификация южных губерний даст мощный толчок подъёму сельского хозяйства."
UK = "Жебракують філософи при ґанку церкви в Гадячі, ще й шатро їхнє п’яне знаємо."
BE = "У рудога вераб’я ў сховішчы пад фатэлем ляжаць нейкія гаючыя зёлкі."
EN = "The quick brown fox jumps over the lazy dog. Hamburgefonstiv"
LD = "Людмила Дмитриевна ДЛЯ ДЕЛА далеко"
G_UPPER = "ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ"
G_LOWER = "αβγδεζηθικλμνξοπρσςτυφχψω"
G_ACCENTED = "άέήίόύώϊϋΐΰ ΆΈΉΊΌΎΏΪΫ ·;"
EL = "Ξεσκεπάζω την ψυχοφθόρα βδελυγμία."
EL2 = "Ζαφείρι δέξου πάγκαλο, βαθών ψυχής το σήμα."
EL3 = "Η γλώσσα μου έδωσαν ελληνική· το σπίτι φτωχικό στις αμμουδιές του Ομήρου. Τι ώρα είναι;"


def chunks(text, n):
    return [text[i:i + n] for i in range(0, len(text), n)]


def cyrillic_sheets(font, out):
    render(font, out / "1-alphabet-upper.png", 150, chunks(UPPER, 13), guides=True)
    render(font, out / "2-alphabet-lower.png", 150, chunks(LOWER, 13), guides=True)
    render(font, out / "3-lookalikes.png", 110, [
        "HНПИ EГБ OФЮ KЖ RЯ CЭЄ AЛД BВЬЗ XУ JЛ",
        "nнпи oбфю cэє kкж vлд eе aа pр xх yу",
        "№ 25 ₽ 100 ₴ 40 € 12 $ 9 £ 3",
    ])
    spacing_u = ["НН" + c + "НОО" + c + "ОО" for c in "БГДЖЗИЛПУФЦЧШЩЪЫЬЭЮЯ"]
    spacing_l = ["нн" + c + "ноо" + c + "оо" for c in "бвгджзиклмптфцчшщъыьэюя"]
    render(font, out / "4-spacing-upper.png", 60, ["  ".join(spacing_u[i:i + 4]) for i in range(0, len(spacing_u), 4)])
    render(font, out / "5-spacing-lower.png", 60, ["  ".join(spacing_l[i:i + 4]) for i in range(0, len(spacing_l), 4)])
    render(font, out / "6-text-display.png", 64, [RU, UK, BE, EN, RU.upper(), UK.upper()[:52], "ГАЛЕРЕЯ ТАТАРСТАН УДАЧА ГОД АТЛАС ТУЛА РУКА"])
    render(font, out / "7-text-small.png", 30, [RU, RU2, UK, BE, EN, RU.upper(), BE.upper()])
    render(font, out / "8-default.png", 72, [LD])
    render(font, out / "8-ss01.png", 72, [LD], features=["ss01"])


def greek_sheets(font, out):
    render(font, out / "greek-1-upper.png", 150, chunks(G_UPPER, 12), guides=True)
    render(font, out / "greek-2-lower.png", 150, chunks(G_LOWER, 13) + [G_ACCENTED], guides=True)
    render(font, out / "greek-3-lookalikes.png", 110, [
        "AΑΛΔ EΕΞΣ HΗΠ OΟΘΩ PΡ TΤΓ YΥΨ XΧ ФΦ",
        "aα oοσρθ cςε nηπ vνγ uυψω kκ xχ pρφ ßβ zζξ",
        "мμ иηι тτ кκ пπ лλ фφ зε",
    ])
    sp_u = ["ΗΗ" + c + "ΗΟΟ" + c + "ΟΟ" for c in "ΓΔΘΛΞΠΣΦΨΩ"]
    sp_l = ["ηη" + c + "ηοο" + c + "οο" for c in "αβγδεζθικλμνξπρσςτυφχψω"]
    render(font, out / "greek-4-spacing.png", 60, ["  ".join(sp_u[i:i + 4]) for i in range(0, len(sp_u), 4)]
           + ["  ".join(sp_l[i:i + 4]) for i in range(0, len(sp_l), 4)])
    render(font, out / "greek-5-text-display.png", 64, [EL, EL2, EL3, EL.upper(), EL2.upper(), "ΆΈΉΊΌΎΏ Άρης Έλλη Ήρα Ίων Όλγα Ύδρα Ώρα"])
    render(font, out / "greek-6-text-small.png", 30, [EL, EL2, EL3, EL.upper(), EN, RU])


def specimen(font, out, family, has_greek):
    # The specimen carries the font inside itself, so it shows the same thing wherever it
    # is opened from and however the browser treats local files.
    web = Path(font).with_suffix(".woff2")
    source, kind = (web, "woff2") if web.exists() else (Path(font), "truetype")
    mime = "font/woff2" if kind == "woff2" else "font/ttf"
    data = base64.b64encode(source.read_bytes()).decode("ascii")
    spaced = lambda text: " ".join(text)  # noqa: E731
    face = f"{family} Specimen"
    greek = f"""<h2>Greek uppercase (work in progress)</h2><div class="big">{spaced(G_UPPER)}</div>
<h2>Greek lowercase (work in progress)</h2><div class="big">{spaced(G_LOWER)}</div>
<h2>Greek accented letters and punctuation (work in progress)</h2><div class="big">{spaced(G_ACCENTED.replace(" ", ""))}</div>
<h2>Greek (work in progress)</h2><div class="mid">{EL}</div><div class="mid">{EL2}</div><p class="txt">{EL3}</p>
""" if has_greek else ""
    probe = "АГҐЯ" + ("Ωζ" if has_greek else "")
    (out / "specimen.html").write_text(f"""<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><title>{family} specimen</title>
<style>
@font-face {{ font-family: "{face}"; src: url("data:{mime};base64,{data}") format("{kind}"); }}
body {{ font-family: "{face}", serif; margin: 3rem auto; max-width: 62rem; padding: 0 2rem; color: #1a1a1a; background: #fff; }}
h1 {{ font-weight: normal; font-size: 4.5rem; margin: 0 0 1rem; }}
h2, #status, #basis {{ font: 0.8rem/1.4 system-ui, sans-serif; letter-spacing: .08em; text-transform: uppercase; color: #777; margin: 3rem 0 .6rem; }}
#status, #basis {{ margin: 0 0 .4rem; letter-spacing: .02em; text-transform: none; }}
.big {{ font-size: 3rem; line-height: 1.3; }}
.mid {{ font-size: 1.6rem; line-height: 1.45; }}
.txt {{ font-size: 1.05rem; line-height: 1.6; max-width: 40rem; }}
.alt {{ font-feature-settings: "ss01"; }}
</style></head><body>
<h1>{family}</h1>
<p id="basis">Based on Marcellus by Astigmatic (AOETI), with Cyrillic added. Licensed under the SIL Open Font License 1.1.</p>
<p id="status">Checking whether the web font loaded…</p>
<h2>Uppercase</h2><div class="big">{spaced(UPPER)}</div>
<h2>Lowercase</h2><div class="big">{spaced(LOWER)}</div>
<h2>Symbols</h2><div class="big">№ 25 · 100 ₽ · 40 ₴ · 12 €</div>
<h2>Russian</h2><div class="mid">{RU}</div><p class="txt">{RU2} {RU}</p>
<h2>Ukrainian</h2><div class="mid">{UK}</div>
<h2>Belarusian</h2><div class="mid">{BE}</div>
{greek}<h2>Latin (unchanged from Marcellus)</h2><div class="mid">{EN}</div>
<h2>Default Л and Д (flat-topped, curved left stroke)</h2><div class="big">{LD}</div>
<h2>Stylistic set ss01 (pointed)</h2><div class="big alt">{LD}</div>
<script>
document.fonts.ready.then(function () {{
  var ok = document.fonts.check('48px "{face}"', '{probe}');
  var el = document.getElementById('status');
  el.textContent = ok
    ? 'Web font loaded: everything below is set in it.'
    : 'The web font did NOT load in this browser: the text below is in a fallback font.';
  el.style.color = ok ? '#2a7a2a' : '#b00020';
}});
</script>
</body></html>
""", encoding="utf-8")


def main():
    font, out = sys.argv[1], Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    tt = TTFont(font)
    family = tt["name"].getDebugName(1)
    has_greek = ord("α") in tt.getBestCmap()
    if has_greek:
        greek_sheets(font, out)      # a work-in-progress build: only the Greek is of interest
    else:
        cyrillic_sheets(font, out)
    specimen(font, out, family, has_greek)


if __name__ == "__main__":
    main()
