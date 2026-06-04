import sys
from pathlib import Path
from dotenv import load_dotenv

backend_root = Path("backend").resolve()
sys.path.insert(0, str(backend_root))

from app.config import get_settings

load_dotenv()
settings = get_settings()

print(f"Builder Model: {settings.gemini_model_builder}")
print(f"Gardener Model: {settings.gemini_model_gardener}")



