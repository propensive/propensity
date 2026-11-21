"""The glyph list: which recipe or reference makes each new glyph."""
import greek
import recipes as r
from geom import Shape
from recipes import CAP_HEIGHT, SC_HEIGHT, X_HEIGHT, Master

UPPER = "АБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"

# Cyrillic capital -> Latin glyph with the same shape
SAME_UPPER = {"А": "A", "В": "B", "Е": "E", "К": "K", "М": "M", "Н": "H", "О": "O", "Р": "P",
              "С": "C", "Т": "T", "Х": "X", "І": "I", "Ё": "Edieresis", "Ї": "Idieresis"}
SAME_LOWER = {"а": "a", "е": "e", "о": "o", "р": "p", "с": "c", "у": "y", "х": "x", "і": "i",
              "ё": "edieresis", "ї": "idieresis"}

# built by one recipe on both masters
BOTH = {
    "Г": r.ge, "Ґ": r.ghe_upturn, "П": r.pe, "Ц": r.tse, "Ш": r.sha, "Щ": r.shcha,
    "И": r.i_cy, "Ж": r.zhe, "Э": r.e_rev, "Є": r.ye, "Ю": r.yu,
    "Я": r.ya, "Ь": r.soft, "Ъ": r.hard, "Ы": r.yery, "Ч": r.che,
}
# lowercase letters that are simply the small cap of a Latin letter
SMALL_COPY = {"в": "B", "к": "K", "м": "M", "н": "H", "т": "T"}


def uni(ch):
    return "uni%04X" % ord(ch)


def build_specs(font, sc_font, with_greek=False):
    cap = Master(font, lower=False, yscale=1.0, height=CAP_HEIGHT)
    small = Master(sc_font, lower=True, yscale=X_HEIGHT / SC_HEIGHT, height=X_HEIGHT)
    gs = font.getGlyphSet()
    hmtx = font["hmtx"]
    specs = []

    def shape(ch, result, name=None, code=True):
        s, adv = result
        specs.append({"name": name or uni(ch), "kind": "shape", "shape": s, "adv": adv,
                      "code": ord(ch) if code else None, "char": ch})

    def comp(ch, parts, adv):
        specs.append({"name": uni(ch), "kind": "comp", "parts": parts, "adv": adv,
                      "code": ord(ch), "char": ch})

    for ch, base in {**SAME_UPPER, **SAME_LOWER}.items():
        comp(ch, [(base, 0, 0)], hmtx[base][0])

    for ch, recipe in BOTH.items():
        shape(ch, recipe(cap))
        shape(ch.lower(), recipe(small))

    for ch, letter in SMALL_COPY.items():
        shape(ch, r.copy(letter)(small))

    three = Shape.glyph(gs, "three")
    shape("З", r.ze(cap, three))
    shape("з", r.ze(small, three, weight=11))
    shape("Б", r.be(cap))
    shape("У", r.u_cap(cap))
    shape("Ф", r.ef_cap(cap))

    lat = lambda n: Shape.glyph(gs, n)  # noqa: E731
    o_adv = hmtx["o"][0]
    shape("б", (r.be_lower(lat("o"), lat("f")), o_adv))
    shape("ф", r.ef_lower(lat("o"), lat("l")))

    # Л Д: flat-topped with a curved left stroke by default; the pointed forms are in ss01
    # the left stroke is J for the capitals and, for the lowercase, Marcellus SC's small
    # capital J, which has the same tail at the lowercase stem weight; neither is rescaled
    J, small_j = lat("J"), Shape.glyph(sc_font.getGlyphSet(), "j")
    for ch, flat, pointed in (("Л", r.el_flat, r.el), ("Д", r.de_flat, r.de)):
        shape(ch, flat(cap, J))
        shape(ch.lower(), flat(small, small_j))
        shape(ch, pointed(cap), name=uni(ch) + ".ss01", code=False)
        shape(ch.lower(), pointed(small), name=uni(ch.lower()) + ".ss01", code=False)

    shape("№", r.numero(lat("N"), hmtx["N"][0], lat("ordmasculine"), hmtx["ordmasculine"][0]))
    shape("₽", r.ruble(lat("P"), hmtx["P"][0], CAP_HEIGHT))
    shape("₴", r.hryvnia(lat("S"), hmtx["S"][0], CAP_HEIGHT))

    # breve accents: Й й Ў ў
    bx = 512
    by = CAP_HEIGHT - X_HEIGHT

    def centre(name):
        s = next(sp for sp in specs if sp["name"] == name)
        b = s["shape"].bounds
        return (b[0] + b[2]) / 2, s["adv"]

    cx, adv = centre(uni("И"))
    comp("Й", [(uni("И"), 0, 0), ("breve", cx - bx, by)], adv)
    cx, adv = centre(uni("и"))
    comp("й", [(uni("и"), 0, 0), ("breve", cx - bx, 0)], adv)
    cx, adv = centre(uni("У"))
    comp("Ў", [(uni("У"), 0, 0), ("breve", cx - bx + 40, by)], adv)
    comp("ў", [("y", 0, 0), ("breve", 540 - bx, 0)], hmtx["y"][0])
    for spec in specs:
        spec["script"] = "cyrl"
    # the Greek letters are work in progress and are built only on request
    return specs + greek.build(font, cap, small, specs) if with_greek else specs
