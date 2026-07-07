"""List available Gemini models using the new Google GenAI SDK."""
import sys
import os
import asyncio

# Ensure backend is in path to import app.config
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
# Also add the parent directory of backend so 'app' module can be found if running from backend root
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from dotenv import load_dotenv
load_dotenv(os.path.join(parent_dir, ".env"))

try:
    from google import genai
except ImportError:
    print("ERROR: 'google-genai' package not found. Please install it (pip install google-genai).")
    sys.exit(1)

def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not found in environment.")
        return

    client = genai.Client(api_key=api_key)

    print("\n" + "="*80)
    print("AVAILABLE GEMINI MODELS (google.genai SDK)")
    print("="*80 + "\n")

    try:
        # Pager object, iterate to get models
        pager = client.models.list()
        
        count = 0
        for m in pager:
            # Filter for Gemini models usually
            if "gemini" in m.name.lower():
                count += 1
                print(f"Model: {m.name}")
                print(f"  Display Name: {m.display_name}")
                if hasattr(m, 'input_token_limit'):
                    print(f"  Input Token Limit: {m.input_token_limit:,}")
                if hasattr(m, 'output_token_limit'):
                    print(f"  Output Token Limit: {m.output_token_limit:,}")
                print("-" * 40)
        
        if count == 0:
            print("No 'gemini' models found.")

        print(f"\nTotal 'gemini' models listed: {count}")

    except Exception as e:
        print(f"API Error: {e}")

if __name__ == "__main__":
    main()

