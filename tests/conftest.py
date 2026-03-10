"""
Pytest configuration and shared fixtures for django-d3-indicator-viz tests.
"""
import pytest


@pytest.fixture
def create_test_location():
    """
    Factory fixture for creating test locations.

    Usage:
        def test_something(create_test_location):
            location = create_test_location(name="Detroit")
    """
    from tests.factories import LocationFactory

    def _create(**kwargs):
        return LocationFactory(**kwargs)

    return _create


@pytest.fixture
def create_test_section():
    """
    Factory fixture for creating test sections.

    Usage:
        def test_something(create_test_section):
            section = create_test_section(name="Demographics")
    """
    from tests.factories import SectionFactory

    def _create(**kwargs):
        return SectionFactory(**kwargs)

    return _create


@pytest.fixture
def create_complete_test_section():
    """
    Factory fixture for creating a complete section with categories and indicators.

    Usage:
        def test_something(create_complete_test_section):
            section = create_complete_test_section(num_categories=2)
    """
    from tests.factories import create_complete_section

    def _create(**kwargs):
        return create_complete_section(**kwargs)

    return _create


@pytest.fixture
def location_hierarchy():
    """
    Fixture that creates a location hierarchy (state, county, city).

    Returns:
        dict with 'state', 'county', 'city' keys
    """
    from tests.factories import create_location_hierarchy
    return create_location_hierarchy()


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """
    Give all tests access to the database by default.

    This avoids having to add @pytest.mark.django_db to every test.
    Remove 'autouse=True' if you prefer explicit database access.
    """
    pass
