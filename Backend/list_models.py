import os
from google import genai
from pcg.config.settings import settings

def main():
    api_key = settings.secret_value(settings.gemini_api_key)
    client = genai.Client(api_key=api_key)
    print("Available Models:")
    for m in client.models.list():
        print(f"  {m.name}")

if __name__ == "__main__":
    main()
