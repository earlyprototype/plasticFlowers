
print("PYTHON_WORKS")
try:
    import google.genai
    print("IMPORT_WORKS")
except ImportError:
    print("IMPORT_FAILED")
except Exception as e:
    print(f"IMPORT_ERROR: {e}")
