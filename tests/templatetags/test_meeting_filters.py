"""
Unit tests for Template Tags
Tests for custom template filters in meeting_filters.py
"""
import pytest
from datetime import datetime

from meetings.templatetags.meeting_filters import get_item, format_date_header


class TestGetItemFilter:
    """Test get_item template filter"""
    
    def test_none_dictionary(self):
        """Test that None dictionary returns None"""
        result = get_item(None, 'key')
        assert result is None
    
    def test_key_exists(self):
        """Test getting existing key from dictionary"""
        dictionary = {'name': 'John', 'age': 30}
        result = get_item(dictionary, 'name')
        assert result == 'John'
    
    def test_key_does_not_exist(self):
        """Test getting non-existent key returns None"""
        dictionary = {'name': 'John'}
        result = get_item(dictionary, 'age')
        assert result is None
    
    def test_empty_dictionary(self):
        """Test with empty dictionary"""
        dictionary = {}
        result = get_item(dictionary, 'key')
        assert result is None
    
    def test_different_value_types(self):
        """Test getting different types of values"""
        dictionary = {
            'string': 'hello',
            'number': 42,
            'list': [1, 2, 3],
            'dict': {'nested': 'value'},
            'bool': True,
            'none': None
        }
        
        assert get_item(dictionary, 'string') == 'hello'
        assert get_item(dictionary, 'number') == 42
        assert get_item(dictionary, 'list') == [1, 2, 3]
        assert get_item(dictionary, 'dict') == {'nested': 'value'}
        assert get_item(dictionary, 'bool') is True
        assert get_item(dictionary, 'none') is None
    
    def test_numeric_key(self):
        """Test with numeric key"""
        dictionary = {1: 'one', 2: 'two'}
        result = get_item(dictionary, 1)
        assert result == 'one'


class TestFormatDateHeaderFilter:
    """Test format_date_header template filter"""
    
    def test_monday_formatting(self):
        """Test formatting Monday date"""
        # 2025-01-13 is a Monday
        result = format_date_header('2025-01-13')
        assert 'T2' in result  # Monday in Vietnamese
        assert '13' in result
        assert '1' in result  # Month
    
    def test_tuesday_formatting(self):
        """Test formatting Tuesday date"""
        # 2025-01-14 is a Tuesday
        result = format_date_header('2025-01-14')
        assert 'T3' in result
        assert '14' in result
    
    def test_wednesday_formatting(self):
        """Test formatting Wednesday date"""
        # 2025-01-15 is a Wednesday
        result = format_date_header('2025-01-15')
        assert 'T4' in result
        assert '15' in result
    
    def test_thursday_formatting(self):
        """Test formatting Thursday date"""
        # 2025-01-16 is a Thursday
        result = format_date_header('2025-01-16')
        assert 'T5' in result
        assert '16' in result
    
    def test_friday_formatting(self):
        """Test formatting Friday date"""
        # 2025-01-17 is a Friday
        result = format_date_header('2025-01-17')
        assert 'T6' in result
        assert '17' in result
    
    def test_saturday_formatting(self):
        """Test formatting Saturday date"""
        # 2025-01-18 is a Saturday
        result = format_date_header('2025-01-18')
        assert 'T7' in result
        assert '18' in result
    
    def test_sunday_formatting(self):
        """Test formatting Sunday date"""
        # 2025-01-19 is a Sunday
        result = format_date_header('2025-01-19')
        assert 'CN' in result  # Sunday in Vietnamese
        assert '19' in result
    
    def test_different_months(self):
        """Test formatting dates from different months"""
        result_jan = format_date_header('2025-01-15')
        result_dec = format_date_header('2025-12-25')
        
        assert '1' in result_jan or '/1' in result_jan
        assert '12' in result_dec or '/12' in result_dec
    
    def test_invalid_date_format_returns_original(self):
        """Test that invalid date format returns original string"""
        invalid_date = 'not-a-date'
        result = format_date_header(invalid_date)
        assert result == invalid_date
    
    def test_wrong_format_returns_original(self):
        """Test that wrong date format returns original string"""
        wrong_format = '01/15/2025'  # MM/DD/YYYY instead of YYYY-MM-DD
        result = format_date_header(wrong_format)
        assert result == wrong_format
    
    def test_empty_string_returns_original(self):
        """Test that empty string returns itself"""
        result = format_date_header('')
        assert result == ''
    
    def test_exception_handling(self):
        """Test that exceptions are handled gracefully"""
        # Various invalid inputs
        test_cases = [
            ('2025-13-01', '2025-13-01'),  # Invalid month
            ('2025-01-32', '2025-01-32'),  # Invalid day
            ('2025-1-1', 'T4 1/1'),        # Wrong format but parses - returns formatted
            (None, None),                   # None value
        ]
        
        for test_input, expected in test_cases:
            result = format_date_header(test_input)
            # Should return expected output without crashing
            assert result == expected
    
    def test_format_output_structure(self):
        """Test that output has expected structure"""
        result = format_date_header('2025-01-15')
        # Should be in format: "T4 15/1"
        parts = result.split()
        assert len(parts) == 2  # Day name and date
        assert 'T' in parts[0] or 'CN' == parts[0]  # Vietnamese day name
        assert '/' in parts[1]  # Date separator
