# Testing Guide for AppsFlyerAgent
## מדריך בדיקות לפרוייקט

### 📋 מבנה הבדיקות

```
tests/
├── __init__.py                  # Package initialization
├── conftest.py                  # Pytest fixtures and configuration
├── test_json_utils.py           # בדיקות JSON (5 tests) ✅
├── test_standalone.py           # בדיקות כלליות (15 tests) ✅
├── test_intent_analyzer.py      # תבניות לזיהוי כוונות
├── test_query_executor.py       # תבניות לביצוע שאילתות
├── test_api.py                  # תבניות אינטגרציה ל-API
├── simple_demo.py               # דמו אינטראקטיבי להצגה
├── demo_tests.py                # דמו מתקדם
└── documentation/               # 📚 תיעוד והצגה
    ├── README.md                       # מדריך תיעוד
    ├── PROJECT_BOOK_TESTING_CHAPTER.md # פרק שלם לספר (30+ עמודים)
    ├── PRESENTATION_SLIDES.md          # 24 שקפים למצגת
    ├── CODE_SNIPPETS_FOR_BOOK.md       # קטעי קוד להעתקה
    ├── HOW_TO_PRESENT_TESTS.md         # מדריך הצגה
    └── TESTING_SUMMARY.md              # סיכום מפורט
```

**📚 לתיעוד מלא והצגה:** ראי [documentation/README.md](documentation/README.md)

---

## 🚀 התקנה והכנה

### 1. התקנת ספריות נדרשות
```bash
pip install pytest pytest-asyncio httpx pytest-cov
```

### 2. עדכון requirements.txt
הוסף לקובץ requirements.txt:
```
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
httpx==0.25.2
```

---

## 🧪 הרצת הבדיקות

### הרצת כל הבדיקות
```bash
# מתיקיית הפרוייקט הראשית
cd c:\Michal\Attempted_re_git\AppsFlyerAgent
python -m pytest tests/ -v
```

### הרצת בדיקה ספציפית
```bash
# בדיקות ל-Intent Analyzer
python -m pytest tests/test_intent_analyzer.py -v

# בדיקות ל-API
python -m pytest tests/test_api.py -v

# בדיקות ל-JSON Utils
python -m pytest tests/test_json_utils.py -v
```

### הרצה עם כיסוי קוד (Coverage)
```bash
python -m pytest tests/ --cov=backend --cov-report=html
```

לאחר מכן פתחי: `htmlcov/index.html` בדפדפן

### הרצת בדיקה בודדת
```bash
python -m pytest tests/test_api.py::TestHealthEndpoint::test_health_check -v
```

---

## 📊 דוגמאות לתוצאות צפויות

### ✅ הרצה מוצלחת
```
tests/test_api.py::TestHealthEndpoint::test_health_check PASSED           [ 10%]
tests/test_json_utils.py::TestJSONUtils::test_clean_json_valid PASSED     [ 20%]
tests/test_json_utils.py::TestJSONUtils::test_clean_json_with_markdown PASSED [ 30%]
========================== 10 passed in 2.43s ==========================
```

### ❌ בדיקה שנכשלה
```
tests/test_api.py::TestChatEndpoint::test_chat_success FAILED            [ 40%]
_________________________ test_chat_success ______________________________

    def test_chat_success(self, mock_run_agent, client):
        mock_run_agent.return_value = {...}
>       assert response.status_code == 200
E       assert 500 == 200

tests/test_api.py:45: AssertionError
```

---

## 🎯 סוגי בדיקות

### 1. Unit Tests (בדיקות יחידה)
בודקות פונקציונליות בודדות:
- `test_json_utils.py` - בדיקת פונקציות JSON
- `test_intent_analyzer.py` - בדיקת זיהוי כוונות
- `test_query_executor.py` - בדיקת ביצוע שאילתות

**דוגמה להרצה:**
```bash
python -m pytest tests/test_json_utils.py -v
```

**תוצאה צפויה:**
```
test_clean_json_valid PASSED
test_clean_json_with_markdown PASSED
test_clean_json_invalid PASSED
```

### 2. Integration Tests (בדיקות אינטגרציה)
בודקות את כל המערכת:
- `test_api.py` - בדיקת API endpoints

**דוגמה להרצה:**
```bash
python -m pytest tests/test_api.py -v
```

---

## 🛠️ דוגמאות שימוש

### דוגמה 1: בדיקת Health Endpoint
```python
def test_health_check(client):
    """בדיקה פשוטה שהשרת עובד"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"ok": True}
```

**הרצה:**
```bash
python -m pytest tests/test_api.py::TestHealthEndpoint::test_health_check -v
```

### דוגמה 2: בדיקת ניקוי JSON
```python
def test_clean_json_with_markdown():
    """בדיקה שמנקה JSON מתוך Markdown"""
    json_str = '''```json
    {"status": "ok"}
    ```'''
    result = clean_json(json_str)
    assert result["status"] == "ok"
```

**הרצה:**
```bash
python -m pytest tests/test_json_utils.py::TestJSONUtils::test_clean_json_with_markdown -v
```

### דוגמה 3: בדיקת CORS Headers
```python
def test_cors_headers_present(client):
    """בדיקה ש-CORS מוגדר נכון"""
    response = client.options("/chat")
    assert "access-control-allow-origin" in response.headers
```

---

## 📈 מדדי איכות

### Coverage Report (דוח כיסוי)
```bash
# יצירת דוח HTML
python -m pytest tests/ --cov=backend --cov-report=html

# צפייה בדוח
start htmlcov/index.html  # Windows
```

### דוח בטרמינל
```bash
python -m pytest tests/ --cov=backend --cov-report=term
```

**תוצאה לדוגמה:**
```
Name                                    Stmts   Miss  Cover
-----------------------------------------------------------
backend/main.py                           45      5    89%
backend/flow_manager_agent/agent.py       89     12    87%
backend/utils/json_utils.py               23      2    91%
-----------------------------------------------------------
TOTAL                                    157     19    88%
```

---

## 🔍 בדיקות מתקדמות

### Async Tests
```python
@pytest.mark.asyncio
async def test_async_agent():
    """בדיקה אסינכרונית"""
    result = await some_async_function()
    assert result is not None
```

### Parametrized Tests
```python
@pytest.mark.parametrize("input,expected", [
    ("היום", "today"),
    ("אתמול", "yesterday"),
    ("שלשום", "day_before")
])
def test_date_parsing(input, expected):
    """בדיקה עם מספר מקרי בוחן"""
    assert parse_date(input) == expected
```

---

## 🐛 Debugging

### הרצה עם פרטים מלאים
```bash
python -m pytest tests/ -vv -s
```

### הרצה עם breakpoint
```python
def test_something():
    result = function_to_test()
    breakpoint()  # עצור כאן
    assert result == expected
```

### הרצה של בדיקות שנכשלו בלבד
```bash
python -m pytest tests/ --lf  # Last Failed
```

---

## 📝 הוספת בדיקות חדשות

### תבנית לבדיקה חדשה
```python
import pytest

class TestNewFeature:
    """בדיקות לפיצ'ר חדש"""
    
    def test_basic_functionality(self):
        """תיאור הבדיקה"""
        # Arrange
        input_data = "test"
        
        # Act
        result = my_function(input_data)
        
        # Assert
        assert result == expected_output
```

---

## ⚡ טיפים

1. **הרץ בדיקות לפני commit:**
   ```bash
   python -m pytest tests/ --tb=short
   ```

2. **שמור על בדיקות מהירות:**
   - השתמש ב-mocks לשירותים חיצוניים
   - הימנע מקריאות DB אמיתיות ב-unit tests

3. **כתוב בדיקות קריאות:**
   - שמות תיאוריים
   - הערות בעברית אם צריך
   - מבנה Arrange-Act-Assert

4. **Coverage מינימלי:**
   - שאף ל-80%+ כיסוי קוד
   - התמקד בלוגיקה עסקית קריטית

---

## 🎓 משאבים נוספים

- [Pytest Documentation](https://docs.pytest.org/)
- [Testing FastAPI](https://fastapi.tiangolo.com/tutorial/testing/)
- [Python Mocking](https://docs.python.org/3/library/unittest.mock.html)

---

## 📞 בעיות נפוצות

### בעיה: "ModuleNotFoundError"
**פתרון:**
```bash
# ודא שאת בתיקייה הנכונה
cd c:\Michal\Attempted_re_git\AppsFlyerAgent
# הרץ עם python -m
python -m pytest tests/
```

### בעיה: "Async tests not running"
**פתרון:**
```bash
pip install pytest-asyncio
```

### בעיה: "Import errors"
**פתרון:** וודא ש-`__init__.py` קיים בכל תיקייה

---

**נוצר בתאריך:** 22/12/2025  
**גרסה:** 1.0
