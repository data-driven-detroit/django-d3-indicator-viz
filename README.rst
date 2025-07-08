============
django-d3-indicator-viz
============

django-d3-indicator-viz is a Django app for scaffolding models for categorized and filterable indicator data, and 
visualizing that data in a variety of formats using the Apache ECharts library.

Detailed documentation is in the "docs" directory.

Quick start
-----------

1. Add "django_d3_indicator_viz" to your INSTALLED_APPS setting like this::

    INSTALLED_APPS = [
        ...,
        "django_d3_indicator_viz",
    ]

2. Include the django_d3_indicator_viz URLconf in your project urls.py like this::

    path("data-visuals/", include("django_d3_indicator_viz.urls")),

3. Run ``python manage.py migrate`` to create the models.

4. Start the development server and visit the admin to create categories, indicators, filters, and data visualizations.

5. Visit the ``/data-visuals/demo`` URL to view demo data visualizations.