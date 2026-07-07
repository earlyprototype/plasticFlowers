# Test Fixtures

JSON fixture files for testing plasticFlower.

## Quick Reference

| File | Purpose | Chunks | Duration |
|------|---------|--------|----------|
| `ml_lecture.json` | Full integration testing | 8 | ~4 min |
| `transformers_quick.json` | Smoke tests | 3 | ~16 sec |
| `stt_errors.json` | Proofreading testing | 4 | ~32 sec |
| `duplicate_detection.json` | Merge/dedup testing | 5 | ~40 sec |
| `research_testing.json` | Research agent testing | 4 | ~32 sec |

## Usage

### Python

```python
import json
from pathlib import Path

FIXTURES = Path(__file__).parent / "_docs/_dev/fixtures"

def load_fixture(name: str) -> list:
    return json.loads((FIXTURES / f"{name}.json").read_text())

chunks = load_fixture("ml_lecture")
```

### JavaScript

```javascript
import mlLecture from './_docs/_dev/fixtures/ml_lecture.json';
```

### curl

```bash
# Submit a single chunk
curl -X POST http://localhost:8010/api/sessions/{sid}/chunks \
  -H "Content-Type: application/json" \
  -d @_docs/_dev/fixtures/transformers_quick.json
```

## Detailed Documentation

See [`../TEST_FIXTURES.md`](../TEST_FIXTURES.md) for:
- Expected nodes/relationships per fixture
- Mock LLM responses
- Expected corrections and merges

