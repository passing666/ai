from google import genai
from google.genai import types
import os

api_key = os.environ.get("GEMINI_API_KEY", "AIzaSyC4_IZNZ3KDyCnKGyQwnEppPRlCJUMfjA0")
client = genai.Client(api_key=api_key)

def translate_to_english(text: str) -> str:
    if not text.strip():
        return ""

    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=text,
            config=types.GenerateContentConfig(
                system_instruction=(
                    "You are a professional academic translator. "
                    "Translate the input Chinese to formal and academic English. "
                    "CRITICAL: Always expand abbreviations to their full academic names "
                    "(e.g., 'AI' becomes 'Artificial Intelligence'). "
                    "Return ONLY the translated text."
                ),
                temperature=0.1,
                max_output_tokens=100,
            )
        )
        
        if response.text:
            return response.text.strip()
        return text
        
    except Exception as e:
        print(f"Gemini Translation Error: {e}")
        return text
