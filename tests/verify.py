# -*- coding: utf-8 -*-
"""Poda verification — seasons, watering math, care table, image
validation, AI-output validators, routes.

Run: ~/workspace/.venv-fc/bin/python tests/verify.py
Exit code 0 = all pass. No network, no key needed (AI tests only
check the no-key error path and the shape validators, never a live
call). Fully deterministic.
"""

import base64
import os
import sys
from datetime import date

# Force the no-key path so AI-status tests are deterministic.
for _k in ("GEMINI_API_KEY", "GEMINI_APIkey"):
    os.environ.pop(_k, None)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from poda import engine, gemini  # noqa: E402

PASS = 0
FAIL = []


def check(name, cond, extra=""):
    global PASS
    if cond:
        PASS += 1
    else:
        FAIL.append(f"{name} {extra}")


# --- seasons ---------------------------------------------------------------
for m in (4, 5, 6, 7, 8, 9):
    s, e = engine.season_for_month(m)
    check(f"summer month {m}", e is None and s == "summer", repr((s, e)))
for m in (1, 2, 3, 10, 11, 12):
    s, e = engine.season_for_month(m)
    check(f"winter month {m}", e is None and s == "winter", repr((s, e)))
s, e = engine.season_for_month(0)
check("month 0 invalid", s is None and e is not None)
s, e = engine.season_for_month(13)
check("month 13 invalid", s is None and e is not None)
s, e = engine.season_for_month("5")
check("month str invalid", s is None and e is not None)

# --- care table sanity ------------------------------------------------------
plants = engine.common_plants()
check("table has 10 plants", len(plants) == 10, str(len(plants)))
ids = [p["id"] for p in plants]
check("plant ids unique", len(set(ids)) == 10)
for p in plants:
    check(f"{p['id']} fields",
          all(p.get(k) for k in ("name_en", "name_roman", "name_ur",
                                 "scientific", "sunlight_en", "soil_en",
                                 "toxic_pets", "toxic_humans", "tip_en",
                                 "source")))
    check(f"{p['id']} summer<=winter interval",
          1 <= p["water_summer"] <= p["water_winter"] <= 31,
          f"{p['water_summer']}/{p['water_winter']}")
    check(f"{p['id']} temp range sane",
          -5 <= p["temp_min_c"] < p["temp_max_c"] <= 50,
          f"{p['temp_min_c']}/{p['temp_max_c']}")
# Published ranges (gap report 2026-11-12-poda.md): money plant
# 7–10 summer / 14 winter; snake 14–21 / 30; aloe 14–21 / ~30;
# neem 7–10 / 14–21; motia 4–5 / 7; desert rose 2–3x week / weekly.
by_id = {p["id"]: p for p in plants}
check("money plant in published range",
      7 <= by_id["money-plant"]["water_summer"] <= 10
      and by_id["money-plant"]["water_winter"] == 14)
check("snake plant in published range",
      14 <= by_id["snake-plant"]["water_summer"] <= 21
      and by_id["snake-plant"]["water_winter"] == 30)
check("aloe in published range",
      14 <= by_id["aloe-vera"]["water_summer"] <= 21
      and by_id["aloe-vera"]["water_winter"] == 30)
check("neem in published range",
      7 <= by_id["neem"]["water_summer"] <= 10
      and 14 <= by_id["neem"]["water_winter"] <= 21)
check("motia in published range",
      4 <= by_id["motia"]["water_summer"] <= 5
      and by_id["motia"]["water_winter"] == 7)
check("desert rose in published range",
      by_id["desert-rose"]["water_summer"] == 3
      and by_id["desert-rose"]["water_winter"] == 7)
check("neem temp floor 5C (Wikipedia: no frost)",
      by_id["neem"]["temp_min_c"] == 5)
check("desert rose temp floor 21C (Karachi nursery)",
      by_id["desert-rose"]["temp_min_c"] == 21)

# --- match_common_plant ------------------------------------------------------
m = engine.match_common_plant("Azadirachta indica")
check("match neem exact", m is not None and m["id"] == "neem")
m = engine.match_common_plant("azadirachta indica")
check("match neem case-insensitive", m is not None and m["id"] == "neem")
m = engine.match_common_plant("Rosa damascena")
check("match rose by genus", m is not None and m["id"] == "rose")
m = engine.match_common_plant("Ficus benjamina")
check("no match unknown plant", m is None)
m = engine.match_common_plant("")
check("no match empty", m is None)

# --- watering math -----------------------------------------------------------
d, e = engine.next_watering(date(2026, 11, 10), 8)
check("next watering +8d", e is None and d == date(2026, 11, 18), repr(d))
d, e = engine.next_watering(date(2026, 11, 28), 5)
check("next watering month rollover", e is None and d == date(2026, 12, 3), repr(d))
d, e = engine.next_watering(date(2026, 12, 30), 5)
check("next watering year rollover", e is None and d == date(2027, 1, 4), repr(d))
d, e = engine.next_watering(date(2028, 2, 28), 3)
check("next watering leap year", e is None and d == date(2028, 3, 2), repr(d))
d, e = engine.next_watering(date(2026, 11, 10), 0)
check("interval 0 rejected", d is None and e is not None)
d, e = engine.next_watering("2026-11-10", 5)
check("non-date rejected", d is None and e is not None)

st, e = engine.watering_status(date(2026, 11, 10), 8, today=date(2026, 11, 18))
check("due today", e is None and st["status"] == "due_today"
      and st["days_until"] == 0, repr(st))
st, e = engine.watering_status(date(2026, 11, 10), 8, today=date(2026, 11, 20))
check("overdue 2d", e is None and st["status"] == "overdue"
      and st["overdue_days"] == 2, repr(st))
st, e = engine.watering_status(date(2026, 11, 10), 8, today=date(2026, 11, 12))
check("in 6 days", e is None and st["status"] == "in_days"
      and st["days_until"] == 6, repr(st))
st, e = engine.watering_status(date(2026, 11, 10), 8, today=date(2026, 11, 11))
check("next_date iso", e is None and st["next_date"] == "2026-11-18", repr(st))

iv, e = engine.water_interval("neem", 6)
check("neem summer interval", e is None and iv == 10, repr(iv))
iv, e = engine.water_interval("neem", 11)
check("neem winter interval", e is None and iv == 18, repr(iv))
iv, e = engine.water_interval("nope", 6)
check("unknown plant interval rejected", iv is None and e is not None)
iv, e = engine.water_interval("neem", 13)
check("bad month interval rejected", iv is None and e is not None)

d, e = engine.parse_date("2026-11-12")
check("parse date ok", e is None and d == date(2026, 11, 12))
d, e = engine.parse_date("2026-02-30")
check("parse impossible date rejected", d is None and e is not None)
d, e = engine.parse_date("12/11/2026")
check("parse wrong format rejected", d is None and e is not None)

# --- image validation --------------------------------------------------------
good_b64 = base64.b64encode(b"\xff\xd8\xff\xe0fakejpeg").decode()
c, e = engine.validate_image("image/jpeg", 12, good_b64)
check("jpeg ok", e is None and c["size_bytes"] == 12, repr((c, e)))
c, e = engine.validate_image("image/png", 12, good_b64)
check("png ok", e is None)
c, e = engine.validate_image("image/webp", 12, good_b64)
check("webp ok", e is None)
c, e = engine.validate_image("image/gif", 12, good_b64)
check("gif rejected", c is None and e is not None)
c, e = engine.validate_image("image/jpeg", 0, good_b64)
check("empty image rejected", c is None and e is not None)
c, e = engine.validate_image("image/jpeg", 6 * 1024 * 1024, good_b64)
check("oversize image rejected", c is None and e is not None)
c, e = engine.validate_image("image/jpeg", 12, "not-base64!!!")
check("bad base64 rejected", c is None and e is not None)
c, e = engine.validate_image("", 12, good_b64)
check("missing type rejected", c is None and e is not None)

# --- AI identification validator ---------------------------------------------
GOOD_ID = {
    "common_name_en": "Neem", "name_ur": "نیم",
    "name_roman": "Neem", "scientific_name": "Azadirachta indica",
    "confidence": 92, "is_plant": True,
    "description": "A fast-growing tree native to the Indian "
                   "subcontinent, famous for shade and neem oil.",
    "care": {"water": "Every 7-10 days in a pot in summer",
             "sunlight": "Full sun, 6-8 hours",
             "soil": "Deep, sandy, well-draining",
             "temperature": "21-32 C, no frost"},
    "toxicity_humans": "Neem oil is toxic if swallowed.",
    "toxicity_pets": "Toxic to pets if swallowed.",
    "safe_to_eat": False,
    "edible_warning": "Do not eat, smoke or use this plant as medicine "
                      "based on an app identification.",
    "season_note_pk": "Loves Pakistani heat; needs no winter protection "
                      "in the plains.",
}


def _good_id(**over):
    d = dict(GOOD_ID)
    d["care"] = dict(GOOD_ID["care"])
    d.update(over)
    return d


clean, e = engine.validate_ai_identification(_good_id())
check("good identification passes", e is None and clean["confidence"] == 92
      and clean["safe_to_eat"] is False and not clean["uncertain"], repr(e))
clean, e = engine.validate_ai_identification(_good_id(confidence=45))
check("low confidence flagged uncertain", e is None and clean["uncertain"] is True)
clean, e = engine.validate_ai_identification(_good_id(confidence=60))
check("confidence 60 not uncertain", e is None and clean["uncertain"] is False)
clean, e = engine.validate_ai_identification(_good_id(confidence=101))
check("confidence 101 rejected", clean is None and e is not None)
clean, e = engine.validate_ai_identification(_good_id(confidence=-1))
check("confidence -1 rejected", clean is None and e is not None)
clean, e = engine.validate_ai_identification(_good_id(is_plant=False))
check("non-plant refused", clean is None and e is not None
      and "zinda poda" in (e or ""))
clean, e = engine.validate_ai_identification(_good_id(safe_to_eat=True))
check("safe-to-eat claim REFUSED", clean is None and e is not None
      and "khaane" in (e or ""))
clean, e = engine.validate_ai_identification(_good_id(safe_to_eat=None))
check("safe-to-eat missing refused", clean is None and e is not None)
d = _good_id()
del d["scientific_name"]
clean, e = engine.validate_ai_identification(d)
check("missing scientific name rejected", clean is None and e is not None)
d = _good_id()
d["care"] = {"water": "x"}
clean, e = engine.validate_ai_identification(d)
check("incomplete care rejected", clean is None and e is not None)
d = _good_id()
d["description"] = "short"
clean, e = engine.validate_ai_identification(d)
check("too-short description rejected", clean is None and e is not None)
clean, e = engine.validate_ai_identification("not a dict")
check("non-dict rejected", clean is None and e is not None)
d = _good_id()
del d["season_note_pk"]
clean, e = engine.validate_ai_identification(d)
check("season note optional", e is None and clean["season_note_pk"] == "")

# --- AI diagnosis validator --------------------------------------------------
GOOD_DG = {
    "problem_en": "Looks healthy", "problem_ur": "Sehatmand lagta hai",
    "severity": "mild", "confidence": 80,
    "likely_causes": ["No visible disease"],
    "treatment_steps": ["Keep watering as usual", "Check new growth weekly"],
    "when_to_seek_help": "If yellow leaves spread, ask a nursery.",
}


def _good_dg(**over):
    d = dict(GOOD_DG)
    d["likely_causes"] = list(GOOD_DG["likely_causes"])
    d["treatment_steps"] = list(GOOD_DG["treatment_steps"])
    d.update(over)
    return d


clean, e = engine.validate_ai_diagnosis(_good_dg())
check("good diagnosis passes", e is None and clean["severity"] == "mild")
clean, e = engine.validate_ai_diagnosis(_good_dg(severity="bad"))
check("bad severity rejected", clean is None and e is not None)
clean, e = engine.validate_ai_diagnosis(_good_dg(likely_causes=[]))
check("empty causes rejected", clean is None and e is not None)
clean, e = engine.validate_ai_diagnosis(_good_dg(treatment_steps=["a"] * 7))
check("too many steps rejected", clean is None and e is not None)
clean, e = engine.validate_ai_diagnosis(_good_dg(confidence=55))
check("diagnosis low confidence flagged", e is None and clean["uncertain"] is True)
clean, e = engine.validate_ai_diagnosis("nope")
check("diagnosis non-dict rejected", clean is None and e is not None)

# --- Gemini no-key path --------------------------------------------------------
check("key not available (forced)", gemini.key_available() is False)
res, e = gemini.identify_from_file(b"\xff\xd8\xff\xe0x", "image/jpeg", "en")
check("identify no-key error", res is None and e is not None
      and "GEMINI_API_KEY" in e, repr(e))
res, e = gemini.diagnose_from_file(b"\xff\xd8\xff\xe0x", "image/jpeg", "en")
check("diagnose no-key error", res is None and e is not None)
res, e = gemini.identify("", "image/jpeg", "en")
check("identify empty image rejected", res is None and e is not None)
res, e = gemini.identify_from_file(b"x", "image/gif", "en")
check("identify gif rejected", res is None and e is not None)
res, e = gemini.identify_from_file(b"x", "image/jpeg", "xx")
check("identify bad language rejected", res is None and e is not None)
check("word count", engine.word_count("aaj paani diya") == 3)

# --- routes (TestClient) -------------------------------------------------------
try:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from poda.routes import router

    app = FastAPI()
    app.include_router(router)
    c = TestClient(app)

    r = c.get("/poda")
    check("route /poda 200", r.status_code == 200 and "Poda" in r.text,
          str(r.status_code))
    check("route /poda has safety warning", "kabhi nahi kehta" in r.text)
    r = c.get("/poda/api/ai-status")
    check("route ai-status", r.status_code == 200
          and r.json()["ai_available"] is False, r.text[:120])
    r = c.get("/poda/api/common-plants")
    check("route common-plants 10", r.status_code == 200
          and len(r.json()["plants"]) == 10, r.text[:120])
    r = c.post("/poda/api/water-schedule",
               data={"plant_id": "neem", "last_watered": "2026-11-10",
                     "month": 11})
    j = r.json()
    check("route water-schedule neem winter", r.status_code == 200
          and j.get("ok") and j.get("interval_days") == 18
          and j.get("next_date") == "2026-11-28", r.text[:200])
    r = c.post("/poda/api/water-schedule",
               data={"plant_id": "neem", "last_watered": "2026-11-10",
                     "month": 6})
    j = r.json()
    check("route water-schedule neem summer", j.get("ok")
          and j.get("interval_days") == 10
          and j.get("next_date") == "2026-11-20", r.text[:200])
    r = c.post("/poda/api/water-schedule",
               data={"plant_id": "nope", "last_watered": "2026-11-10",
                     "month": 11})
    check("route water-schedule bad plant", r.json().get("ok") is False)
    r = c.post("/poda/api/water-schedule",
               data={"plant_id": "neem", "last_watered": "bad",
                     "month": 11})
    check("route water-schedule bad date", r.json().get("ok") is False)
    r = c.post("/poda/api/identify")
    check("route identify no photo", r.json().get("ok") is False)
    r = c.post("/poda/api/diagnose")
    check("route diagnose no photo", r.json().get("ok") is False)
    r = c.post("/poda/api/identify",
               files={"photo": ("leaf.jpg", b"\xff\xd8\xff\xe0x",
                                "image/jpeg")},
               data={"language": "en"})
    check("route identify no-key error path", r.json().get("ok") is False
          and "GEMINI_API_KEY" in (r.json().get("error") or ""),
          r.text[:200])
except Exception as exc:  # noqa: BLE001 - report as failures
    check("routes import/run", False, repr(exc))

print(f"\n{PASS} passed, {len(FAIL)} failed")
for f in FAIL:
    print("FAIL:", f)
sys.exit(1 if FAIL else 0)
