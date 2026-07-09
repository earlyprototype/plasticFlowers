
import asyncio
import time
import sys

print("[START] Lock Debug")
try:
    start = time.time()
    l = asyncio.Lock()
    print(f"[SUCCESS] Lock created in {time.time() - start:.4f}s")
except Exception as e:
    print(f"[FAIL] {e}")
print("[END]")
