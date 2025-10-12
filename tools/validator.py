# tools/validate_front_matter.py
import os, re, sys, yaml

# ---- CONFIG ----
CONTENT_DIR = "german-revision-helper/content"
REQUIRED_KEYS = ["title", "level", "topics", "usage", "themes", "context"]  # for regular content pages
ALLOWED_LEVELS = {"A1", "A2", "B1", "B2", "C1", "C2"}
# ----------------

errors = []
checked = 0

for root, dirs, files in os.walk(CONTENT_DIR):
    for f in files:
        if not f.endswith(".md"):
            continue
        path = os.path.join(root, f)
        checked += 1
        text = open(path, encoding="utf-8").read()

        m = re.search(r"^---\s*(.*?)\s*---\s*", text, re.S | re.M)
        if not m:
            print(f"[FAIL] {path}: missing front matter block (--- ... ---)")
            errors.append(path)
            continue

        try:
            fm = yaml.safe_load(m.group(1)) or {}
        except Exception as e:
            print(f"[FAIL] {path}: YAML parse error: {e}")
            errors.append(path)
            continue

        if f == "_index.md":
            # Light validation for section index pages
            if "title" not in fm or not isinstance(fm.get("title"), str) or not fm.get("title").strip():
                print(f"[FAIL] {path}: _index.md must have a non-empty title")
                errors.append(path)
                continue
            # Optional: if description exists, ensure it's a string
            if "description" in fm and not isinstance(fm.get("description"), str):
                print(f"[FAIL] {path}: description must be a string if present")
                errors.append(path)
                continue
            print(f"[OK]   {path} (section index)")
            continue

        # Full validation for regular content pages
        missing = [k for k in REQUIRED_KEYS if k not in fm]
        if missing:
            print(f"[FAIL] {path}: missing keys {missing}")
            errors.append(path)
            continue

        level = fm.get("level")
        if level not in ALLOWED_LEVELS:
            print(f"[FAIL] {path}: invalid level '{level}' (allowed: {sorted(ALLOWED_LEVELS)})")
            errors.append(path)
            continue

        list_fields = ["topics", "usage", "themes", "context"]
        bad = False
        for key in list_fields:
            val = fm.get(key)
            if not isinstance(val, list):
                print(f"[FAIL] {path}: '{key}' must be a list")
                bad = True
                break
            for item in val:
                if not isinstance(item, str):
                    print(f"[FAIL] {path}: {key} contains non-string item: {item!r}")
                    bad = True
                    break
        if bad:
            errors.append(path)
            continue

        # Title must be a non-empty string
        if not isinstance(fm.get("title"), str) or not fm.get("title").strip():
            print(f"[FAIL] {path}: title must be a non-empty string")
            errors.append(path)
            continue

        print(f"[OK]   {path}")

if errors:
    print(f"\n{len(errors)} file(s) failed validation out of {checked} checked.")
    sys.exit(1)
else:
    print(f"\nAll {checked} markdown files validated successfully (including section indexes).")
    sys.exit(0)
