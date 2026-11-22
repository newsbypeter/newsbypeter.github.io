"""Gemini steps: English analysis first, then Burmese translation (one call per step)."""
import json
import os
import time

from google import genai
from google.genai import types

MODEL = "gemini-3.5-flash"  # change here if your key cannot use this model
ANALYSIS_FIELDS = ("why_it_matters", "perspectives", "reasoning")
TEXT_FIELDS = ("title", "details") + ANALYSIS_FIELDS
RETRIES = 3

ANALYSIS_PROMPT = """You are an analyst writing for International Relations and Law students.
For EACH story below, using ONLY its own facts, return one JSON object. Its keys are the story
ids. Each value is an object with exactly these keys:
- why_it_matters: 2 sentences on the significance.
- perspectives: 2-3 sentences on how different parties may view it.
- reasoning: 2-3 sentences on logical reasons and possible outcomes, phrased as possibilities.
- roles: a list using "ir" (International Relations students), "law" (Law students) or both. Include "law" whenever courts, legislation, treaties, rights or legal arguments are involved. If unsure, include both.
Do not invent facts, names, numbers or quotes. If the facts are thin, say what is unclear.

Stories:
{stories}
"""

TRANSLATE_PROMPT = """Translate the values of this JSON from English to Burmese (Myanmar, Unicode, not Zawgyi).
Keep every key exactly as it is. Keep names, numbers and organisation names accurate.
Use a clear, neutral news style. Return only JSON.

{payload}
"""


def ask_json(prompt):
    """Make one Gemini call and return a dict, or None if it fails."""
    if not os.environ.get("GEMINI_API_KEY"):
        print("GEMINI_API_KEY not set. Skipping this Gemini step.")
        return None
    client = genai.Client()
    for attempt in range(1, RETRIES + 1):
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(response_mime_type="application/json"),
            )
            data = json.loads(response.text)
            if isinstance(data, dict):
                return data
            raise ValueError("response was not a JSON object")
        except Exception as err:
            print(f"Gemini call failed (attempt {attempt}/{RETRIES}): {str(err)[:200]}")
            if "RESOURCE_EXHAUSTED" in str(err) or attempt == RETRIES:
                break  # a quota error will not fix itself by retrying
            time.sleep(15 * attempt)
    return None


def analyze_all(items):
    stories = [
        {
            "id": i["id"],
            "headline": i["title"]["en"],
            "summary": i["details"]["en"],
            "reported_by": i["coverage"],
        }
        for i in items
    ]
    data = ask_json(ANALYSIS_PROMPT.format(stories=json.dumps(stories, ensure_ascii=False)))
    if not data:
        return
    for item in items:
        entry = data.get(item["id"])
        if not isinstance(entry, dict):
            print(f"{item['id']}: no analysis returned")
            continue
        missing = [f for f in ANALYSIS_FIELDS if not entry.get(f)]
        if missing:
            print(f"{item['id']}: missing {missing}; model returned {list(entry)}")
        for field in ANALYSIS_FIELDS:
            item[field]["en"] = str(entry.get(field, "")).strip()
        roles = [r for r in entry.get("roles") or [] if r in ("ir", "law")]
        if roles:
            item["roles"] = roles


def translate_all(items):
    payload = {
        i["id"]: {f: i[f]["en"] for f in TEXT_FIELDS if i[f]["en"]}
        for i in items
    }
    data = ask_json(TRANSLATE_PROMPT.format(payload=json.dumps(payload, ensure_ascii=False)))
    if not data:
        return
    for item in items:
        entry = data.get(item["id"])
        if not isinstance(entry, dict):
            print(f"{item['id']}: no translation returned")
            continue
        for field in TEXT_FIELDS:
            if entry.get(field):
                item[field]["my"] = str(entry[field]).strip()
