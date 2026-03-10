"""
Tests for django-d3-indicator-viz views.

Focus on testing the API endpoints and view responses.
"""
import pytest
import json
from django.test import Client
from django.urls import reverse
from tests.factories import (
    SectionFactory,
    CategoryFactory,
    IndicatorFactory,
    IndicatorDataVisualFactory,
    IndicatorDataVisualSourceFactory,
    IndicatorSourceFactory,
    IndicatorValueFactory,
    LocationFactory,
    ColorScaleFactory,
    IndicatorFilterOptionFactory,
    LocationTypeFactory,
    create_complete_section,
)


@pytest.fixture
def client():
    """Return Django test client."""
    return Client()


@pytest.mark.django_db
class TestSectionDataView:
    """Tests for section_data API endpoint."""

    def test_section_data_returns_json(self, client):
        """Test that section_data endpoint returns JSON response."""
        # Create test data
        section = create_complete_section(num_categories=1, num_indicators_per_category=1)
        location = LocationFactory()

        # Add some indicator values
        indicator = section.category_set.first().indicator_set.first()
        source = IndicatorSourceFactory()
        IndicatorValueFactory(indicator=indicator, location=location, source=source)

        # Make request
        url = reverse('section_data', kwargs={
            'location_id': location.id,
            'section_id': section.id
        })
        response = client.get(url)

        # Check response
        assert response.status_code == 200
        assert response['Content-Type'] == 'application/json'

        # Parse JSON
        data = json.loads(response.content)

        # Check structure
        assert 'section' in data
        assert 'categories' in data
        assert 'dataVisuals' in data
        assert 'indicatorValues' in data

    def test_section_data_includes_comparison_locations(self, client):
        """Test that section_data includes parent/sibling data when needed."""
        # Create section with parents comparison
        section = SectionFactory()
        category = CategoryFactory(section=section)
        indicator = IndicatorFactory(category=category)
        source = IndicatorSourceFactory()

        visual = IndicatorDataVisualFactory(
            indicator=indicator,
            location_comparison_type='parents'
        )
        IndicatorDataVisualSourceFactory(data_visual=visual, source=source, priority=0)

        # Create location hierarchy
        location_type = LocationTypeFactory()
        parent_location_type = LocationTypeFactory()
        parent_location_type.parent_location_types.add(location_type)

        location = LocationFactory(location_type=location_type)
        parent = LocationFactory(location_type=parent_location_type)

        # Create indicator values
        IndicatorValueFactory(indicator=indicator, location=location, source=source)
        IndicatorValueFactory(indicator=indicator, location=parent, source=source)

        # Make request
        url = reverse('section_data', kwargs={
            'location_id': location.id,
            'section_id': section.id
        })
        response = client.get(url)

        assert response.status_code == 200

        data = json.loads(response.content)

        # Should have indicator values (exact count depends on parent detection logic)
        assert 'indicatorValues' in data
        assert len(data['indicatorValues']) > 0

    def test_section_data_returns_404_for_invalid_section(self, client):
        """Test that section_data returns 404 for non-existent section."""
        location = LocationFactory()

        url = reverse('section_data', kwargs={
            'location_id': location.id,
            'section_id': 99999  # Non-existent
        })
        response = client.get(url)

        assert response.status_code == 404

    def test_section_data_returns_404_for_invalid_location(self, client):
        """Test that section_data returns 404 for non-existent location."""
        section = SectionFactory()

        url = reverse('section_data', kwargs={
            'location_id': 'INVALID_LOC',
            'section_id': section.id
        })
        response = client.get(url)

        assert response.status_code == 404


@pytest.mark.django_db
class TestProfileView:
    """Tests for profile view."""

    def test_profile_view_returns_html(self, client):
        """Test that profile view returns HTML response."""
        location = LocationFactory()

        # Create some sections
        SectionFactory()
        SectionFactory()

        url = reverse('profile', kwargs={'location_id': location.id})
        response = client.get(url)

        assert response.status_code == 200
        assert 'text/html' in response['Content-Type']

    def test_profile_view_includes_profile_data(self, client):
        """Test that profile view includes profile-data script tag."""
        location = LocationFactory()
        SectionFactory()

        url = reverse('profile', kwargs={'location_id': location.id})
        response = client.get(url)

        # Check for profile-data script tag
        content = response.content.decode('utf-8')
        assert 'id="profile-data"' in content
        assert 'application/json' in content

    def test_profile_view_includes_sections(self, client):
        """Test that profile view includes section placeholders."""
        location = LocationFactory()
        section1 = SectionFactory(name="Demographics")
        section2 = SectionFactory(name="Economics")

        url = reverse('profile', kwargs={'location_id': location.id})
        response = client.get(url)

        content = response.content.decode('utf-8')

        # Check for section placeholders
        assert 'Demographics' in content
        assert 'Economics' in content
        assert 'section-placeholder' in content

    def test_profile_view_404_for_invalid_location(self, client):
        """Test that profile view returns 404 for non-existent location."""
        url = reverse('profile', kwargs={'location_id': 'INVALID'})
        response = client.get(url)

        assert response.status_code == 404
