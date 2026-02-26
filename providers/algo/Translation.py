import requests
import urllib.parse


def translate_to_english(text: str) -> str:
    try:
        encoded_text = urllib.parse.quote(text)
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=zh-CN&tl=en&dt=t&q={encoded_text}"
        response = requests.get(url, timeout=5.0)
        if response.status_code == 200:
            return response.json()[0][0][0]
    except Exception as e:
        print(f"Translation failed: {e}")
    return text
