# 🧪 Quick Testing Guide
## מדריך מהיר לבדיקות

---

## 🚀 הרצה מהירה

### דמו אינטראקטיבי (מומלץ להצגה!)
```bash
python tests\simple_demo.py
```

### בדיקות Pytest מלאות
```bash
python -m pytest tests\test_json_utils.py tests\test_standalone.py -v
```

### סקריפט אוטומטי
```bash
.\quick_test.ps1
```

---

## 📊 מה יש כאן

```
✅ 20 בדיקות אוטומטיות
⚡ 0.07 שניות זמן ריצה
📊 100% שיעור הצלחה
🎯 4 תחומים מכוסים
```

---

## 📁 מבנה התיקיות

### `tests/` - הבדיקות עצמן
- **test_json_utils.py** - 5 בדיקות עיבוד JSON ✅
- **test_standalone.py** - 15 בדיקות נוספות ✅
- **simple_demo.py** - דמו אינטראקטיבי 🎬
- **README.md** - מדריך הבדיקות המלא

### `tests/documentation/` - תיעוד והצגה לספר
- **PROJECT_BOOK_TESTING_CHAPTER.md** - פרק שלם (30+ עמודים) 📖
- **PRESENTATION_SLIDES.md** - 24 שקפים למצגת 📊
- **CODE_SNIPPETS_FOR_BOOK.md** - קטעי קוד מוכנים 💻
- **HOW_TO_PRESENT_TESTS.md** - מדריך הצגה 📝
- **TESTING_SUMMARY.md** - סיכום מפורט 📋

---

## 📚 תיעוד מלא

### להרצת בדיקות:
👉 [tests/README.md](tests/README.md)

### להצגה בספר פרוייקט:
👉 [tests/documentation/README.md](tests/documentation/README.md)

---

## 💡 דוגמאות מהירות

### בדיקת JSON:
```python
def test_clean_json_valid():
    json_str = '{"status": "ok"}'
    result = clean_json(json_str)
    assert result["status"] == "ok"
```

### בדיקת תאריך:
```python
def test_parse_today_hebrew():
    result = parse_date_hebrew("היום")
    assert result == datetime.now().date()
```

---

## 🎯 למה להתחיל?

**רוצה להריץ בדיקות?**  
→ [tests/README.md](tests/README.md)

**רוצה להציג בספר?**  
→ [tests/documentation/README.md](tests/documentation/README.md)

**רוצה דמו מהיר?**  
→ `python tests\simple_demo.py`

---

**הכל מוכן ומאורגן! 🎉**
