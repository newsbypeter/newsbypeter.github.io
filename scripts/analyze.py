"""Add AI analysis to each story using the Gemini API."""
import json
import os

from google import genai
from google.genai import types

MODEL = "gemini-3.5-flash"  # change here if your key cannot use this model
FIELDS = ("why_it_matters", "perspectives", "reasoning")

PROMPT = """You are an analyst writing for International Relations and Law students.
Using ONLY the facts below, return JSON with exactly these keys:
- why_it_matters: 2 sentences on the significance.
- perspectives: 2-3 sentences on how different parties may view it.
- reasoning: 2-3 sentences on logical reasons and possible outcomes, phrased as possibilities.
Do not invent facts, names, numbers or quotes. If the facts are thin, say what is unclear.

Headline: {title}
Summary: {summary}
Reported by: {sources}
"""


def analyze_all(items):
    """Fill the analysis fields in place. Skips quietly if anything fails."""
    if not os.environ.get("GEMINI_API_KEY"):
        print("GEMINI_API_KEY not set. Skipping analysis.")
        return
    client = genai.Client()
    for item in items:
        prompt = PROMPT.format(
            title=item["title"]["en"],
            summary=item["details"]["en"],
            sources=", ".join(item["coverage"]),
        )
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(response_mime_type="application/json"),
            )
            data = json.loads(response.text)
        except Exception as err:
            print(f"Analysis skipped for {item['id']}: {err}")
            continue
        for field in FIELDS:
            item[field]["en"] = str(data.get(field, "")).strip()
