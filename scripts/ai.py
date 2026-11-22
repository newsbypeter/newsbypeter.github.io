"""Gemini steps: English analysis first, then Burmese translation."""
import json
import os
import time

from google import genai
from google.genai import types

MODEL = "gemini-3.5-flash"  # change here if your key cannot use this model
ANALYSIS_FIELDS = ("why_it_matters", "perspectives", "reasoning")
TEXT_FIELDS = ("title", "details") + ANALYSIS_FIELDS
RETRIES = 3        # attempts per story
MAX_FAILURES = 2   # stop a step after this many stories in a row fail

ANALYSIS_PROMPT = """You are an analyst writing for International Relations and Law students.
Using ONLY the facts below, return JSON with exactly these keys:
- why_it_matters: 2 sentences on the significance.
- perspectives: 2-3 sentences on how different parties may view it.
- reasoning: 2-3 sentences on logical reasons and possible outcomes, phrased as possibilities.
- roles: a list using "ir" (International Relations students), "law" (Law students) or both. Include "law" whenever courts, legislation, treaties, rights or legal arguments are involved. If unsure, include both.
Do not invent facts, names, numbers or quotes. If the facts are thin, say what is unclear.

Headline: {title}
Summary: {summary}
Reported by: {sources}
"""

TRANSLATE_PROMPT = """Translate the values of this JSON from English to Burmese (Myanmar, Unicode, not Zawgyi).
Keep the same keys. Keep names, numbers and organisation names accurate. Use a clear, neutral news style.
Return only JSON.

{payload}
"""


def ask_json(client, prompt):
    """Call Gemini and return a dict, or None if every attempt fails."""
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
            print(f"Gemini call failed (attempt {attempt}/{RETRIES}): {err}")
            if attempt < RETRIES:
                time.sleep(15 * attempt)
    return None


def run_step(name, items, make_prompt, apply):
    """Send one prompt per story and apply each reply. Stops early if Gemini keeps failing."""
    if not os.environ.get("GEMINI_API_KEY"):
        print(f"GEMINI_API_KEY not set. Skipping {name}.")
        return
    client = genai.Client()
    failures = 0
    for item in items:
        prompt = make_prompt(item)
        if prompt is None:
            continue
        data = ask_json(client, prompt)
        if data is None:
            failures += 1
            if failures >= MAX_FAILURES:
                print(f"Stopping {name}: Gemini keeps failing.")
                return
            continue
        failures = 0
        apply(item, data)


def analysis_prompt(item):
    return ANALYSIS_PROMPT.format(
        title=item["title"]["en"],
        summary=item["details"]["en"],
        sources=", ".join(item["coverage"]),
    )


def apply_analysis(item, data):
    missing = [f for f in ANALYSIS_FIELDS if not data.get(f)]
    if missing:
        print(f"{item['id']}: missing {missing}; model returned {list(data)}")
    for field in ANALYSIS_FIELDS:
        item[field]["en"] = str(data.get(field, "")).strip()
    roles = [r for r in data.get("roles") or [] if r in ("ir", "law")]
    if roles:
        item["roles"] = roles


def translation_prompt(item):
    payload = {f: item[f]["en"] for f in TEXT_FIELDS if item[f]["en"]}
    if not payload:
        return None
    return TRANSLATE_PROMPT.format(payload=json.dumps(payload, ensure_ascii=False))


def apply_translation(item, data):
    for field in TEXT_FIELDS:
        if data.get(field):
            item[field]["my"] = str(data[field]).strip()


def analyze_all(items):
    run_step("analysis", items, analysis_prompt, apply_analysis)


def translate_all(items):
    run_step("translation", items, translation_prompt, apply_translation)
