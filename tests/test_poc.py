# tests/test_poc.py

def test_always_passes():
    """A trivial test that always passes."""
    assert True

def test_addition():
    """Test a simple addition."""
    result = 2 + 3
    assert result == 5

def test_string_upper():
    """Test string uppercase."""
    s = "hello"
    assert s.upper() == "HELLO"
