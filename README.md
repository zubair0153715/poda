# Poda — پودا

**Free AI plant identifier.** Photo dein, poda pehchanein — unlimited,
no account, no card, no trial, no credits, no ads. Urdu-first.

An original clean-room build from the daily-app-gap-build series. It
fills the gaps in **PictureThis** (plant identifier: Pro $3.99/week,
$7.99/month, $39.99/year; free tier is credit-rationed; 84M installs,
4.55 stars on Google Play). Poda is **not affiliated** with
PictureThis or Glority Global Group Ltd.

## Why Poda exists

| | PictureThis | Poda |
|---|---|---|
| Price | Free download; Pro $3.99/wk, $7.99/mo, $39.99/yr; Family $49.99 | **Free, forever — unlimited** |
| Free tier | Limited credits; earn more by logging in, watching ads, sharing on Facebook | **No credits, no ads, no account** |
| Trial billing | 7-day trial needs payment info; 1-star reviews report full-year charges after cancelling on the last trial day (Trustpilot 2.0/5) | **No payment exists — nothing to charge, nothing to cancel** |
| Misidentification | Oct 2026 review: a highly toxic plant called edible; a plastic plant got a treatment plan; no confidence shown | **Confidence shown on every ID**; under 60% flagged uncertain; **non-plants refused**; **never says a plant is safe to eat** |
| Urdu / Pakistan | No Urdu names, no local climate care | **Urdu-first: Urdu + Roman-Urdu + English names**; Pakistan-season watering (summer Apr–Sep, winter Oct–Mar) |
| Accuracy claim | "98%" — vendor claim, no independent benchmark; one 2026 comparison found 76% fully correct | **No claim made — honest limits on the page** |
| Privacy | Collects and may share personal, financial and location data with third parties | **Nothing stored server-side**; photo sent only to Gemini for the one ID, then discarded |

Gap report: `../market-gaps/daily/2026-11-12-poda.md` (in the builder's workspace).

## Features

- **Photo identification (Gemini vision)** — upload or camera photo; returns common name (EN), Urdu name, Roman-Urdu name, scientific name, confidence, description, care guide, toxicity for children/pets, and a Pakistan-season note.
- **Disease diagnosis mode** — photo of a sick plant: likely problem, severity, causes, treatment steps, and when home care is not enough.
- **Safety first** — every result carries a do-not-eat warning; the AI is instructed never to call a plant safe to eat, and the engine **refuses** any answer that does. Low-confidence results are flagged, not hidden.
- **Verified care table (no key needed)** — 10 plants every Pakistani home has (neem, money plant, snake plant, aloe vera, motia, rose, marigold, tulsi, hibiscus, desert rose) with watering intervals taken from published care guides, each with its source.
- **Watering calculator** — next-watering date from last watering + season interval, with overdue / due-today status.
- **My Plants (browser only)** — save identified plants, log watering, see the next watering date. Lives in localStorage; the server stores nothing.

## Honest limits

- Identification is Gemini vision's best guess, not a lab test. Neem and chinaberry (bakain) look alike even to experts — Wikipedia notes the confusion — so Poda shows confidence and asks the user to verify before any medicinal or eating use.
- AI identification and diagnosis need `GEMINI_API_KEY` in the environment (owner's free quota). Without it, the common-plants table, watering calculator and My Plants still work fully.
- Photos are sent to Google's Gemini servers for the one identification; Poda itself stores nothing. Diagnosis from a photo cannot confirm every plant-health problem.
- Poda is not a botanist and not a doctor: never eat, smoke or medicate with a plant on the basis of an app identification.

## Run

```bash
# as a FastAPI route (lives at /poda in the clinic-demo app)
pip install fastapi uvicorn python-multipart
uvicorn app.main:app --reload   # from the clinic-demo repo
```

## Tests

```bash
~/workspace/.venv-fc/bin/python tests/verify.py      # deterministic checks, no network, no key
~/workspace/.venv-fc/bin/python tests/live_check.py  # real Gemini vision on two public neem photos
```
