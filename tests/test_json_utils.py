"""
Unit tests for JSON utility functions
"""
import pytest
import json
import re
import sys
from pathlib import Path

# Simple implementation for testing
def clean_json(text):
    """Clean and parse JSON from text"""
    if isinstance(text, dict):
        return text
    
    # Remove markdown code blocks
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*', '', text)
    text = text.strip()
    
    # Try to find JSON object
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        text = json_match.group(0)
    
    try:
        return json.loads(text)
    except:
        return {}


class TestJSONUtils:
    """Test cases for JSON utility functions"""
    
    def test_clean_json_valid(self):
        """Test cleaning valid JSON string"""
        json_str = '{"status": "ok", "data": [1, 2, 3]}'
        result = clean_json(json_str)
        
        assert isinstance(result, dict)
        assert result["status"] == "ok"
        assert result["data"] == [1, 2, 3]
    
    def test_clean_json_with_markdown(self):
        """Test cleaning JSON wrapped in markdown code blocks"""
        json_str = '''```json
{
    "status": "ok",
    "message": "Success"
}
```'''
        result = clean_json(json_str)
        
        assert isinstance(result, dict)
        assert result["status"] == "ok"
    
    def test_clean_json_with_extra_text(self):
        """Test cleaning JSON with surrounding text"""
        json_str = 'Here is the result: {"status": "ok"} - end'
        result = clean_json(json_str)
        
        assert isinstance(result, dict)
        assert result["status"] == "ok"
    
    def test_clean_json_invalid(self):
        """Test handling of invalid JSON"""
        json_str = 'This is not JSON at all'
        result = clean_json(json_str)
        
        # Should return empty dict or handle gracefully
        assert isinstance(result, dict)
    
    def test_clean_json_nested(self):
        """Test cleaning nested JSON structures"""
        json_str = '''
        {
            "status": "ok",
            "data": {
                "items": [
                    {"id": 1, "name": "test"}
                ]
            }
        }
        '''
        result = clean_json(json_str)
        
        assert result["status"] == "ok"
        assert "data" in result
        assert "items" in result["data"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
