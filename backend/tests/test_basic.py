"""Basic tests to ensure the application can start"""

def test_import():
    """Test that main imports work"""
    try:
        from hoistscraper import main
        assert True
    except ImportError:
        assert False, "Failed to import main module"

def test_basic():
    """Basic test to ensure pytest works"""
    assert 1 + 1 == 2