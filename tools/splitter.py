# tools/minimal_split_no_funcs.py
import os, re, unicodedata

# ---- EDIT THESE TWO LINES ----
IN_PATH  = "source/2025-10-12.md"                 # your daily source file
OUT_ROOT = "german-revision-helper/content"       # your Hugo content/ root
# --------------------------------

text = open(IN_PATH, "r", encoding="utf-8").read()

# date from front matter or filename
date = None
_m = re.search(r"^---\s*(.*?)^---", text, flags=re.S|re.M)
if _m:
    _fm = _m.group(1)
    _md = re.search(r'(?im)^\s*Date:\s*"?(?P<d>\d{4}-\d{2}-\d{2})"?', _fm)
    if _md: date = _md.group("d")
if not date:
    _md = re.search(r'(\d{4}-\d{2}-\d{2})', IN_PATH)
    date = _md.group(1) if _md else "1970-01-01"

# find top-level sections (# ...)
_sections = []
for _m in re.finditer(r"(?m)^#\s+(.+)$", text):
    _sections.append((_m.start(), _m.group(1).strip()))
_sections.append((len(text), "__END__"))

for _i in range(len(_sections)-1):
    sec_start, sec_name = _sections[_i]
    sec_end, _ = _sections[_i+1]
    sec_body = text[sec_start:sec_end]

    sec_key = sec_name.strip().lower()
    if sec_key not in {"grammar","vocabulary","verbs","daily paragraph","phrases"}:
        continue

    # find items within section (## ...)
    _items = []
    for _m in re.finditer(r"(?m)^##\s+(.+)$", sec_body):
        _items.append((_m.start(), _m.group(1).strip()))
    _items.append((len(sec_body), "__END__"))

    for _j in range(len(_items)-1):
        item_start, item_title_raw = _items[_j]
        item_end, _ = _items[_j+1]
        block = sec_body[item_start:item_end]

        # strip md emphasis from title (for display)
        item_title = re.sub(r"[*_`]+", "", item_title_raw).strip()

        # parse sectionmeta fence
        meta_level = ""
        meta_topics = []
        meta_usage  = []
        meta_themes = []
        meta_context= []

        _fm = re.search(r"```sectionmeta\s*(.*?)\s*```", block, flags=re.S)
        if _fm:
            meta_raw = _fm.group(1)

            _ml = re.search(r'(?im)^\s*level\s*:\s*("?)([A-C][1-2])\1', meta_raw)
            if _ml: meta_level = _ml.group(2).upper()

            for _key in ("topics","usage","themes","context"):
                _mm = re.search(rf'(?im)^\s*{_key}\s*:\s*(\[.*?\]|.+)$', meta_raw)
                if _mm:
                    _val = _mm.group(1).strip()
                    if _val.startswith("[") and _val.endswith("]"): _val = _val[1:-1]
                    _parts = [p.strip() for p in _val.split(",") if p.strip()]
                    _norm = []
                    for p in _parts:
                        p = re.sub(r"[\s/]+","-", p.lower())
                        _norm.append(p)
                    if _key=="topics": meta_topics = _norm
                    if _key=="usage":  meta_usage  = _norm
                    if _key=="themes": meta_themes = _norm
                    if _key=="context":meta_context= _norm

        # body after fence (or after H2 line if no fence)
        if _fm:
            body = block[_fm.end():].lstrip()
        else:
            body = re.sub(r"(?m)^##\s+.+\n", "", block, count=1).lstrip()

        # slugify (inline steps, no function)
        _title_for_slug = item_title
        _tmp = re.sub(r"[*_`~#>]", "", _title_for_slug)
        _tmp = unicodedata.normalize("NFKD", _tmp).encode("ascii","ignore").decode("ascii")
        _tmp = re.sub(r"[^\w\s-]", "", _tmp).strip().lower()
        _tmp = re.sub(r"[\s/]+", "-", _tmp)
        _slug = re.sub(r"-{2,}", "-", _tmp)

        # decide output path + final title
        if sec_key == "grammar":
            out_dir = os.path.join(OUT_ROOT, "grammar", _slug)
            title_out = item_title
        elif sec_key == "verbs":
            out_dir = os.path.join(OUT_ROOT, "verbs", _slug)
            title_out = item_title
        elif sec_key == "vocabulary":
            out_dir = os.path.join(OUT_ROOT, "vocabulary", "lists", date)
            title_out = f"Vocabulary: {date}"
        elif sec_key == "phrases":
            out_dir = os.path.join(OUT_ROOT, "phrases", "lists", date)
            title_out = f"Phrases: {date}"
        elif sec_key == "daily paragraph":
            out_dir = os.path.join(OUT_ROOT, "writing", "daily", date)
            title_out = f"Daily Paragraph: {date}"
        else:
            continue

        # derived tags (inline)
        tags = []
        if sec_key: tags.append("section-" + re.sub(r"[\s/]+","-", sec_key))
        if meta_level: tags.append("level-" + meta_level.lower())
        for _v in meta_topics:  tags.append("topic-"   + _v)
        for _v in meta_usage:   tags.append("usage-"   + _v)
        for _v in meta_themes:  tags.append("theme-"   + _v)
        for _v in meta_context: tags.append("context-" + _v)

        # write leaf bundle index.md
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, "index.md")

        front = []
        front.append("---")
        front.append(f'title: "{title_out}"')
        front.append(f'date: "{date}"')
        front.append(f'level: "{meta_level}"')
        front.append("topics: [" + ", ".join(f'"{x}"' for x in meta_topics) + "]")
        front.append("usage: [" + ", ".join(f'"{x}"' for x in meta_usage) + "]")
        front.append("themes: [" + ", ".join(f'"{x}"' for x in meta_themes) + "]")
        front.append("context: [" + ", ".join(f'"{x}"' for x in meta_context) + "]")
        front.append("draft: false")
        front.append("tags: [" + ", ".join(f'"{t}"' for t in tags) + "]")
        front.append("---\n")

        with open(out_path, "w", encoding="utf-8") as f:
            f.write("\n".join(front))
            f.write(body.strip() + "\n")

        print("WROTE:", out_path)
