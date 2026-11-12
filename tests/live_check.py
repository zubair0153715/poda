# -*- coding: utf-8 -*-
"""Live Gemini vision check for Poda — uses the registered surrogate
credential (key never handled, never printed).

Downloads two PUBLIC Wikimedia Commons photos of neem
(Azadirachta indica) — leaves close-up and a whole tree — and
calls the real poda.gemini.identify / diagnose on them. Asserts the
scientific name returned contains Azadirachta indica.

Run: ~/workspace/.venv-fc/bin/python tests/live_check.py
"""

import os
import sys
import urllib.request

sys.path.insert(0, "/opt/muse/skills/custom-connector-setup/bin")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dynamic_credentials import dynamic_credential_entry  # noqa: E402

entry = dynamic_credential_entry("custom.google-gemini")
os.environ["GEMINI_API_KEY"] = entry["surrogate"]

from poda import gemini  # noqa: E402

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")
os.makedirs(FIXTURES, exist_ok=True)

# Public Wikimedia Commons photos (CC-licensed), via the file URLs
# shown on en.wikipedia.org/wiki/Azadirachta_indica.
IMAGES = {
    "neem-leaves.jpg": (
        "https://upload.wikimedia.org/wikipedia/commons/8/8e/"
        "Neem_tree_leaves.JPG"),
    "neem-tree.jpg": (
        "https://upload.wikimedia.org/wikipedia/commons/7/7b/"
        "Neem_Tree_in_Rajasthan%2C_India.jpg"),
}


def fetch(name, url):
    path = os.path.join(FIXTURES, name)
    if not os.path.exists(path) or os.path.getsize(path) < 5000:
        print(f"downloading {name} ...")
        req = urllib.request.Request(url, headers={"User-Agent": "Poda-test/1.0"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = resp.read()
        with open(path, "wb") as fh:
            fh.write(data)
    with open(path, "rb") as fh:
        return fh.read()


def shrink_jpeg(data, max_side=1200):
    """Downscale to a phone-like photo (the 5 MB route cap applies).
    Returns JPEG bytes."""
    import io
    from PIL import Image
    img = Image.open(io.BytesIO(data))
    img.thumbnail((max_side, max_side))
    buf = io.BytesIO()
    img.convert("RGB").save(buf, "JPEG", quality=85)
    return buf.getvalue()


print("key_available:", gemini.key_available())

leaves = shrink_jpeg(fetch("neem-leaves.jpg", IMAGES["neem-leaves.jpg"]))
print(f"neem leaves photo: {len(leaves)} bytes (downscaled)")
res, err = gemini.identify_from_file(leaves, "image/jpeg", "en")
if err:
    print("IDENTIFY LEAVES ERROR:", err)
    sys.exit(1)
print(f"IDENTIFY LEAVES OK: {res['common_name_en']} / {res['name_ur']} / "
      f"{res['scientific_name']} / confidence {res['confidence']}%")
print("description:", res["description"][:160])
assert "azadirachta indica" in res["scientific_name"].lower(), (
    f"expected Azadirachta indica, got {res['scientific_name']!r}")
assert res["safe_to_eat"] is False
assert res["edible_warning"]
print("verified_table:", res.get("verified_table") or "none")

res2, err = gemini.diagnose_from_file(leaves, "image/jpeg", "en")
if err:
    print("DIAGNOSE LEAVES ERROR:", err)
    sys.exit(1)
print(f"DIAGNOSE LEAVES OK: {res2['problem_en']} / severity "
      f"{res2['severity']} / confidence {res2['confidence']}%")
assert res2["likely_causes"] and res2["treatment_steps"]
assert res2["when_to_seek_help"]

tree = shrink_jpeg(fetch("neem-tree.jpg", IMAGES["neem-tree.jpg"]))
print(f"neem tree photo: {len(tree)} bytes (downscaled)")
res3, err = gemini.identify_from_file(tree, "image/jpeg", "roman")
if err:
    print("IDENTIFY TREE ERROR:", err)
    sys.exit(1)
print(f"IDENTIFY TREE OK: {res3['common_name_en']} / {res3['name_roman']} / "
      f"{res3['scientific_name']} / confidence {res3['confidence']}%")
assert "azadirachta" in res3["scientific_name"].lower(), (
    f"expected Azadirachta, got {res3['scientific_name']!r}")

print("LIVE CHECK PASSED")
