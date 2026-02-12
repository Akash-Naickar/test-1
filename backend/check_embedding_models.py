
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
try:
    genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
    print("Listing embedding models:")
    for m in genai.list_models():
        if 'embedContent' in m.supported_generation_methods:
            print(m.name)
except Exception as e:
    print(f"Error: {e}")
