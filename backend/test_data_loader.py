"""
Standalone test script for the data loader.
Run from backend directory: python test_data_loader.py
"""

from pathlib import Path

from app.config import settings
from app.utils.data_loader import (
    get_scheme_statistics,
    load_schemes_from_json,
    prepare_scheme_text_for_embedding,
    validate_scheme,
)

print("=" * 70)
print("DATA LOADER TEST")
print("=" * 70)

# Resolve path relative to backend root
backend_root = Path(__file__).resolve().parent
schemes_path = settings.get_schemes_path(backend_root)

# Test 1: Load schemes
print("\n1. Loading schemes...")
schemes = load_schemes_from_json(str(schemes_path))
print(f"   [OK] Loaded {len(schemes)} schemes")

if not schemes:
    print("   [FAIL] ERROR: No schemes loaded!")
    exit(1)

# Test 2: Statistics
print("\n2. Generating statistics...")
stats = get_scheme_statistics(schemes)
print(f"   [OK] Total schemes: {stats['total']}")
print(f"   [OK] Average quality: {stats['avg_quality']}/100")
print(f"   [OK] Categories: {len(stats['categories'])}")

# Test 3: Sample scheme
print("\n3. Testing sample scheme...")
sample = schemes[0]
print(f"   [OK] Sample: {sample.get('scheme_name')}")
print(f"   [OK] Category: {sample.get('category')}")
print(f"   [OK] Quality: {sample.get('data_quality_score')}/100")

# Test 4: Embedding text
print("\n4. Testing embedding text generation...")
embed_text = prepare_scheme_text_for_embedding(sample)
print(f"   [OK] Generated text length: {len(embed_text)} chars")
print(f"   [OK] Preview: {embed_text[:100]}...")

# Test 5: Validation
print("\n5. Testing validation...")
valid_count = sum(1 for s in schemes if validate_scheme(s))
print(f"   [OK] Valid schemes: {valid_count}/{len(schemes)}")
print(f"   [OK] Validation rate: {round(valid_count / len(schemes) * 100, 1)}%")

# Test 6: Check data quality
print("\n6. Checking data quality...")
high_quality = sum(1 for s in schemes if s.get("data_quality_score", 0) >= 70)
medium_quality = sum(
    1 for s in schemes if 50 <= s.get("data_quality_score", 0) < 70
)
print(f"   [OK] High quality (>=70): {high_quality}")
print(f"   [OK] Medium quality (50-69): {medium_quality}")

print("\n" + "=" * 70)
print("All data loader tests passed!")
print("=" * 70)
