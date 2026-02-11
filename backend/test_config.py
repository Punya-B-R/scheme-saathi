"""
Test script to verify configuration loads correctly.
Run from backend directory: python test_config.py
"""

from app.config import settings

print("=" * 60)
print("CONFIGURATION TEST")
print("=" * 60)

print(f"\n[OK] App Name: {settings.APP_NAME}")
print(f"[OK] Version: {settings.APP_VERSION}")
print(f"[OK] Debug Mode: {settings.DEBUG}")

print(f"\n[OK] Gemini Model: {settings.GEMINI_MODEL}")
print(f"[OK] API Key Set: {'Yes' if settings.GEMINI_API_KEY != 'placeholder' else 'No (placeholder)'}")

print(f"\n[OK] Schemes Data Path: {settings.SCHEMES_DATA_PATH}")
print(f"[OK] ChromaDB Path: {settings.CHROMA_DB_PATH}")

print(f"\n[OK] Top K Schemes: {settings.TOP_K_SCHEMES}")
print(f"[OK] Similarity Threshold: {settings.SIMILARITY_THRESHOLD}")

print(f"\n[OK] CORS Origins: {settings.allowed_origins_list}")

print("\n" + "=" * 60)
print("Configuration loaded successfully!")
print("=" * 60)
