"""Everything after the outlines: kerning, features, naming, metadata, licence files, WOFF2."""
import copy
import unicodedata
from pathlib import Path

from fontTools.otlLib import builder as otl
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables import otTables as ot

from glyphs import SAME_LOWER, SAME_UPPER, uni

STYLE = "Regular"
VERSION = "1.100"
ADDITIONS_BY = "Propensive OÜ"


def release(greek=False):
    """The names and wording for a build.

    The Greek letters are work in progress and are left out of the font. A build that
    includes them is named apart, so it cannot be mistaken for the font itself."""
    scope = "Cyrillic and Greek additions" if greek else "Cyrillic additions"
    family = "Propensity Greek WIP" if greek else "Propensity"
    covers = "Cyrillic for Russian, Ukrainian and Belarusian"
    if greek:
        covers += ", and with unfinished Greek letters that are work in progress"
    return {
        "greek": greek,
        "family": family,
        "postscript": family.replace(" ", "") + "-" + STYLE,
        # one line, appended to the original notice
        "copyright": f"Copyright (c) 2026, {ADDITIONS_BY} ({scope})",
        "designer": f"Astigmatic (AOETI); {scope} by {ADDITIONS_BY}",
        "description": (f"{family} is based on Marcellus by Astigmatic (AOETI), extended with {covers}. "
                        "It is a modified version and is not Marcellus."),
        "scripts": ("DFLT", "cyrl", "grek", "latn") if greek else ("DFLT", "cyrl", "latn"),
    }


# For kerning, each new glyph borrows the behaviour of a Latin glyph with a similar edge:
# (left edge like, right edge like). None means no kerning on that side.
EDGES = {
    "Б": ("H", None), "Г": ("H", "T"), "Ґ": ("H", "T"), "Д": (None, None), "Ж": ("X", "K"),
    "З": (None, "B"), "И": ("H", "H"), "Й": ("H", "H"), "Л": (None, "H"), "П": ("H", "H"),
    "У": ("Y", "Y"), "Ў": ("Y", "Y"), "Ф": ("O", "O"), "Ц": ("H", None), "Ч": (None, "H"),
    "Ш": ("H", "H"), "Щ": ("H", None), "Ъ": ("T", None), "Ы": ("H", "H"), "Ь": ("H", None),
    "Э": (None, "O"), "Ю": ("H", "O"), "Я": (None, "H"), "Є": ("O", "C"),
    "б": ("o", "o"), "в": ("n", "o"), "г": ("n", "r"), "ґ": ("n", "r"), "д": (None, None),
    "ж": ("x", "k"), "з": (None, "o"), "и": ("n", "n"), "й": ("n", "n"), "к": ("n", "k"),
    "л": ("a", "n"), "м": ("n", "n"), "н": ("n", "n"), "п": ("n", "n"), "т": (None, "r"),
    "ф": ("o", "o"), "ц": ("n", None), "ч": (None, "n"), "ш": ("n", "n"), "щ": ("n", None),
    "ъ": (None, "o"), "ы": ("n", "n"), "ь": ("n", "o"), "э": (None, "o"), "ю": ("n", "o"),
    "я": (None, "n"), "є": ("o", "c"), "ў": ("y", "y"),
}
# the pointed alternates in ss01
ALT_EDGES = {"Л": ("A", "A"), "Д": (None, None), "л": ("a", None), "д": ("a", None)}


# ---- kerning ----------------------------------------------------------------------------

def _kern_lookup(font):
    gpos = font["GPOS"].table
    feature = next(fr.Feature for fr in gpos.FeatureList.FeatureRecord if fr.FeatureTag == "kern")
    return gpos, feature, gpos.LookupList.Lookup[feature.LookupListIndex[0]]


def latin_kern(font):
    """A function giving the original font's kerning for a pair of glyph names."""
    _, _, lookup = _kern_lookup(font)
    tables = []
    for st in lookup.SubTable:
        cov = {g: i for i, g in enumerate(st.Coverage.glyphs)}
        tables.append((st, cov))

    def kern(left, right):
        for st, cov in tables:
            if left not in cov:
                continue
            if st.Format == 1:
                for rec in st.PairSet[cov[left]].PairValueRecord:
                    if rec.SecondGlyph == right:
                        return rec.Value1.XAdvance or 0
                continue
            c1 = st.ClassDef1.classDefs.get(left, 0)
            c2 = st.ClassDef2.classDefs.get(right, 0)
            value = st.Class1Record[c1].Class2Record[c2].Value1
            return (value.XAdvance or 0) if value else 0
        return 0

    return kern


def add_kerning(font, specs):
    kern = latin_kern(font)
    cmap = font.getBestCmap()
    left_like, right_like = {}, {}
    for spec in specs:
        name, ch = spec["name"], spec["char"]
        if "edges" in spec:
            edges = spec["edges"]
        elif ch in SAME_UPPER or ch in SAME_LOWER:
            base = {**SAME_UPPER, **SAME_LOWER}[ch]
            edges = (base, base)
        elif name.endswith(".ss01"):
            edges = ALT_EDGES[ch]
        else:
            edges = EDGES.get(ch, (None, None))
        left_like[name], right_like[name] = edges

    # Latin partners: punctuation and symbols, which Cyrillic text shares
    partners = sorted({g for cp, g in cmap.items()
                       if cp < 0x370 or cp >= 0x2000
                       if unicodedata.category(chr(cp))[0] in "PS" and g not in set(s["name"] for s in specs)})
    new = [s["name"] for s in specs]
    firsts = [(n, right_like[n]) for n in new if right_like[n]] + [(p, p) for p in partners]
    seconds = [(n, left_like[n]) for n in new if left_like[n]] + [(p, p) for p in partners]
    new_set = set(new)
    script = {s["name"]: s.get("script") for s in specs}
    pairs = {}
    for g1, like1 in firsts:
        for g2, like2 in seconds:
            if g1 not in new_set and g2 not in new_set:
                continue
            if g1 in new_set and g2 in new_set and script[g1] != script[g2]:
                continue    # Cyrillic and Greek letters do not meet
            value = kern(like1, like2)
            if value:
                pairs[(g1, g2)] = (otl.buildValue({"XAdvance": value}), None)

    gpos, feature, _ = _kern_lookup(font)
    subtables = otl.buildPairPosGlyphs(pairs, font.getReverseGlyphMap())
    lookup = otl.buildLookup(subtables)
    gpos.LookupList.Lookup.append(lookup)
    gpos.LookupList.LookupCount = len(gpos.LookupList.Lookup)
    feature.LookupListIndex.append(gpos.LookupList.LookupCount - 1)
    feature.LookupCount = len(feature.LookupListIndex)
    return len(pairs)


# ---- features and scripts ---------------------------------------------------------------

def _sort_features(table):
    """Keep the feature list in tag order, remapping the indices scripts refer to."""
    records = table.FeatureList.FeatureRecord
    order = sorted(range(len(records)), key=lambda i: (records[i].FeatureTag, i))
    remap = {old: new for new, old in enumerate(order)}
    table.FeatureList.FeatureRecord = [records[i] for i in order]
    table.FeatureList.FeatureCount = len(records)
    for sr in table.ScriptList.ScriptRecord:
        systems = [sr.Script.DefaultLangSys] + [l.LangSys for l in sr.Script.LangSysRecord]
        for ls in systems:
            if ls is not None:
                ls.FeatureIndex = sorted(remap[i] for i in ls.FeatureIndex)
                ls.FeatureCount = len(ls.FeatureIndex)


def _register_scripts(table, tags):
    """Every feature is offered under each script's default language system."""
    everything = list(range(len(table.FeatureList.FeatureRecord)))
    existing = {sr.ScriptTag: sr for sr in table.ScriptList.ScriptRecord}
    for tag in tags:
        if tag in existing:
            ls = existing[tag].Script.DefaultLangSys
        else:
            sr = ot.ScriptRecord()
            sr.ScriptTag = tag
            sr.Script = ot.Script()
            sr.Script.LangSysRecord = []
            sr.Script.LangSysCount = 0
            ls = sr.Script.DefaultLangSys = ot.DefaultLangSys()
            ls.LookupOrder = None
            ls.ReqFeatureIndex = 0xFFFF
            existing[tag] = sr
        ls.FeatureIndex = everything
        ls.FeatureCount = len(everything)
    table.ScriptList.ScriptRecord = [existing[t] for t in sorted(existing)]
    table.ScriptList.ScriptCount = len(existing)


def add_features(font, specs, rel):
    gsub = font["GSUB"].table
    alternates = {s["name"][:-5]: s["name"] for s in specs if s["name"].endswith(".ss01")}

    lookup = otl.buildLookup([otl.buildSingleSubstSubtable(alternates)])
    gsub.LookupList.Lookup.append(lookup)
    gsub.LookupList.LookupCount = len(gsub.LookupList.Lookup)

    record = ot.FeatureRecord()
    record.FeatureTag = "ss01"
    record.Feature = ot.Feature()
    record.Feature.FeatureParams = None
    record.Feature.LookupListIndex = [gsub.LookupList.LookupCount - 1]
    record.Feature.LookupCount = 1
    gsub.FeatureList.FeatureRecord.append(record)

    # 'access all alternates' should reach them too
    aalt = next(fr.Feature for fr in gsub.FeatureList.FeatureRecord if fr.FeatureTag == "aalt")
    aalt_lookup = gsub.LookupList.Lookup[aalt.LookupListIndex[0]]
    if aalt_lookup.LookupType == 1:
        aalt_lookup.SubTable[0].mapping.update(alternates)

    _sort_features(gsub)
    _register_scripts(gsub, rel["scripts"])
    _register_scripts(font["GPOS"].table, rel["scripts"])
    return alternates


# ---- naming and metadata ----------------------------------------------------------------

def set_names(font, rel):
    name = font["name"]
    original = name.getDebugName(0)
    values = {
        0: original.replace("\r", " ") + ". " + rel["copyright"] + ".",
        1: rel["family"],
        2: STYLE,
        3: f"{VERSION};NONE;{rel['postscript']}",
        4: f"{rel['family']} {STYLE}",
        5: f"Version {VERSION}",
        6: rel["postscript"],
        9: rel["designer"],
        10: rel["description"],
        18: f"{rel['family']} {STYLE}",
    }
    # the manufacturer and vendor URL described the original font's publisher
    drop = {8, 11}
    name.names = [r for r in name.names if r.nameID not in drop]
    platforms = sorted({(r.platformID, r.platEncID, r.langID) for r in name.names})
    for pid, eid, lid in platforms:
        for nid, text in values.items():
            if nid == 18 and pid != 1:
                continue
            name.setName(text, nid, pid, eid, lid)
    name.names.sort()


def set_metadata(font, rel):
    major, minor = VERSION.split(".")
    font["head"].fontRevision = float(f"{major}.{minor}")
    os2 = font["OS/2"]
    os2.achVendID = "NONE"
    if rel["greek"]:
        os2.ulUnicodeRange1 |= 1 << 7      # Greek and Coptic
        os2.ulCodePageRange1 |= 1 << 3     # Windows Greek
    os2.ulUnicodeRange1 |= 1 << 9          # Cyrillic
    os2.ulUnicodeRange2 |= 1 << (35 - 32)  # Letterlike Symbols (numero)
    os2.ulUnicodeRange2 |= 1 << (33 - 32)  # Currency Symbols
    os2.ulCodePageRange1 |= 1 << 2         # Windows Cyrillic
    os2.recalcAvgCharWidth(font)
    codes = font.getBestCmap().keys()
    os2.usFirstCharIndex = min(codes)
    os2.usLastCharIndex = min(max(codes), 0xFFFF)


def finish(font, specs, greek=False):
    rel = release(greek)
    pairs = add_kerning(font, specs)
    add_features(font, specs, rel)
    set_names(font, rel)
    set_metadata(font, rel)
    print(f"glyphs added: {len(specs)}; kerning pairs added: {pairs}")


# ---- files alongside the font -----------------------------------------------------------

def write_extras(font, out, greek=False):
    if greek:
        return      # a work-in-progress build is only the font file
    rel = release()
    FAMILY = rel["family"]
    out = Path(out)
    web = TTFont(out)
    web.flavor = "woff2"
    web.save(out.with_suffix(".woff2"))

    vendor = Path(__file__).resolve().parent.parent / "vendor" / "marcellus" / "OFL.txt"
    lines = vendor.read_text(encoding="utf-8").splitlines()
    notice = lines[0]
    assert notice.startswith("Copyright"), notice
    text = "\n".join([notice, rel["copyright"]] + lines[1:]) + "\n"
    (out.parent / "OFL.txt").write_text(text, encoding="utf-8")

    (out.parent / "FONTLOG.txt").write_text(f"""FONTLOG for {FAMILY}

{FAMILY} is based on Marcellus by Brian J. Bonislawsky DBA Astigmatic (AOETI), and is a
modified version of it, released under the SIL Open Font License 1.1. "Marcellus" is a
Reserved Font Name, so this modified version carries a different name.

ChangeLog

1.100
- Based on Marcellus-Regular.ttf version 1.000 as distributed by Google Fonts. Every
  original glyph, its metrics and its Latin kerning are unchanged.
- Added Cyrillic for Russian, Ukrainian and Belarusian (U+0401, U+0404, U+0406, U+0407,
  U+040E, U+0410-U+044F, U+0451, U+0454, U+0456, U+0457, U+045E, U+0490, U+0491), the
  numero sign (U+2116), the hryvnia sign (U+20B4) and the ruble sign (U+20BD).
- The Cyrillic outlines are adapted from Marcellus's Latin glyphs; lowercase letters with
  small-capital shapes are adapted from Marcellus SC by the same designer.
- U+041B, U+0414, U+043B and U+0434 are flat-topped, with a curved left stroke adapted
  from J. Stylistic set ss01 replaces them with pointed forms.
- Added Cyrillic kerning derived from the Latin kerning of similarly shaped letters, and
  registered the layout features for the Cyrillic and default scripts.

Acknowledgements

Cyrillic additions: Propensive OÜ
Marcellus and Marcellus SC: Brian J. Bonislawsky DBA Astigmatic (AOETI), astigma@astigmatic.com
""", encoding="utf-8")
