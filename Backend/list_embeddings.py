from __future__ import annotations

from importlib import import_module

from pcg.config.settings import settings


client = import_module("google.genai").Client(api_key=settings.secret_value(settings.gemini_api_key))
print("Listing Gemini embedding models...")
for model in client.models.list():
    if "embedding" in model.name:
        print(f"Name: {model.name}")
