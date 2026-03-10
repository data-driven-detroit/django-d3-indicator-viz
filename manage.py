#!/usr/bin/env python
"""
Django management script for django-d3-indicator-viz development.

This is only used for development (running migrations, shell, etc.)
and is not needed by users who install the package.
"""
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
