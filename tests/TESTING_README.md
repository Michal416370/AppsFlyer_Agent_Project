# Quick Testing Guide
## Quick Testing Guide

---

## Quick Run

### Interactive Demo (Recommended for presentation!)
```bash
python tests\simple_demo.py
```

### Full Pytest Tests
```bash
python -m pytest tests\test_json_utils.py tests\test_standalone.py -v
```

### Automatic Script
```bash
.\quick_test.ps1
```

---

## What's Here

```
PASS 20 automated tests
FAST 0.07 seconds runtime
STATS 100% success rate
TARGET 4 areas covered
```

---

## Folder Structure

### `tests/` - The tests themselves
- **test_json_utils.py** - 5 JSON processing tests
- **test_standalone.py** - 15 more tests
- **simple_demo.py** - Interactive demo
- **README.md** - Full testing guide

### `tests/documentation/` - Documentation and presentation for book
- **PROJECT_BOOK_TESTING_CHAPTER.md** - Full chapter (30+ pages)
- **PRESENTATION_SLIDES.md** - 24 slides for presentation
- **CODE_SNIPPETS_FOR_BOOK.md** - Ready code snippets
- **HOW_TO_PRESENT_TESTS.md** - Presentation guide
- **TESTING_SUMMARY.md** - Detailed summary

---

## Full Documentation

### To run tests:
👉 [tests/README.md](tests/README.md)

### To present in project book:
👉 [tests/documentation/README.md](tests/documentation/README.md)

---

## Quick Examples

### JSON Test:
```python
def test_clean_json_valid():
    json_str = '{"status": "ok"}'
    result = clean_json(json_str)
    assert result["status"] == "ok"
```

### Date Test:
```python
def test_parse_today():
    result = parse_date("today")
    assert result == datetime.now().date()
```

---

## Where to Start?

**Want to run tests?**  
→ [tests/README.md](tests/README.md)

**Want to present in book?**  
→ [tests/documentation/README.md](tests/documentation/README.md)

**Want a quick demo?**  
→ `python tests\simple_demo.py`

---

**Everything is ready and organized!**
