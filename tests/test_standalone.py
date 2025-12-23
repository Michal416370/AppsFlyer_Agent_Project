"""
Standalone tests - tests that don't require full system
בדיקות עצמאיות שלא דורשות את המערכת המלאה
"""
import pytest
from datetime import datetime, timedelta


class TestDateParsing:
    """Test date parsing logic"""
    
    def parse_date_hebrew(self, text):
        """Parse Hebrew and English date expressions"""
        today = datetime.now().date()
        
        date_map = {
            "היום": today,
            "today": today,
            "אתמול": today - timedelta(days=1),
            "yesterday": today - timedelta(days=1),
            "שלשום": today - timedelta(days=2)
        }
        
        return date_map.get(text.lower(), None)
    
    def test_parse_today_hebrew(self):
        """Test parsing 'היום'"""
        result = self.parse_date_hebrew("היום")
        expected = datetime.now().date()
        assert result == expected
    
    def test_parse_today_english(self):
        """Test parsing 'today'"""
        result = self.parse_date_hebrew("today")
        expected = datetime.now().date()
        assert result == expected
    
    def test_parse_yesterday_hebrew(self):
        """Test parsing 'אתמול'"""
        result = self.parse_date_hebrew("אתמול")
        expected = datetime.now().date() - timedelta(days=1)
        assert result == expected
    
    def test_parse_yesterday_english(self):
        """Test parsing 'yesterday'"""
        result = self.parse_date_hebrew("yesterday")
        expected = datetime.now().date() - timedelta(days=1)
        assert result == expected
    
    def test_parse_day_before_hebrew(self):
        """Test parsing 'שלשום'"""
        result = self.parse_date_hebrew("שלשום")
        expected = datetime.now().date() - timedelta(days=2)
        assert result == expected
    
    def test_parse_invalid_date(self):
        """Test parsing invalid date string"""
        result = self.parse_date_hebrew("invalid")
        assert result is None


class TestIntentClassification:
    """Test intent classification logic"""
    
    def classify_intent(self, query):
        """Classify user intent"""
        query_lower = query.lower()
        
        data_keywords = ["show", "give", "top", "list", "הצג", "תן", "מה"]
        anomaly_keywords = ["anomaly", "spike", "drop", "אנומליה", "קפיצה", "ירידה"]
        
        if any(keyword in query_lower for keyword in data_keywords):
            return "data_query"
        elif any(keyword in query_lower for keyword in anomaly_keywords):
            return "anomaly_detection"
        else:
            return "not_relevant"
    
    def test_data_query_english(self):
        """Test data query in English"""
        result = self.classify_intent("Show me top 10 media sources")
        assert result == "data_query"
    
    def test_data_query_hebrew(self):
        """Test data query in Hebrew"""
        result = self.classify_intent("הצג לי את 10 מקורות המדיה")
        assert result == "data_query"
    
    def test_anomaly_detection(self):
        """Test anomaly detection query"""
        result = self.classify_intent("Find spike in clicks")
        assert result == "anomaly_detection"
    
    def test_not_relevant(self):
        """Test non-relevant query"""
        result = self.classify_intent("What's the weather?")
        assert result == "not_relevant"


class TestAPIResponseValidation:
    """Test API response validation"""
    
    def validate_response(self, response):
        """Validate API response structure"""
        if not isinstance(response, dict):
            return False, "Not a dictionary"
        
        if "status" not in response:
            return False, "Missing status"
        
        valid_statuses = ["ok", "error", "clarification_needed", "not_relevant"]
        if response["status"] not in valid_statuses:
            return False, f"Invalid status: {response['status']}"
        
        return True, "Valid"
    
    def test_valid_ok_response(self):
        """Test valid OK response"""
        response = {"status": "ok", "data": [1, 2, 3]}
        is_valid, msg = self.validate_response(response)
        assert is_valid is True
    
    def test_valid_error_response(self):
        """Test valid error response"""
        response = {"status": "error", "message": "Error occurred"}
        is_valid, msg = self.validate_response(response)
        assert is_valid is True
    
    def test_missing_status(self):
        """Test response without status"""
        response = {"data": [1, 2, 3]}
        is_valid, msg = self.validate_response(response)
        assert is_valid is False
        assert "status" in msg.lower()
    
    def test_invalid_status(self):
        """Test response with invalid status"""
        response = {"status": "unknown"}
        is_valid, msg = self.validate_response(response)
        assert is_valid is False
    
    def test_not_dict(self):
        """Test non-dictionary response"""
        response = "not a dict"
        is_valid, msg = self.validate_response(response)
        assert is_valid is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
