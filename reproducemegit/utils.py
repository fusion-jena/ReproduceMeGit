# -*- coding: utf-8 -*-
"""
Sheeba Samuel
Heinz-Nixdorf Chair for Distributed Information Systems
Friedrich Schiller University Jena, Germany
Email: sheeba.samuel@uni-jena.de
Website: https://github.com/Sheeba-Samuel
"""

"""Helper utilities and decorators."""
from flask import flash


def flash_errors(form, category="warning"):
    """Flash all errors for a form."""
    for field, errors in form.errors.items():
        for error in errors:
            flash(f"{getattr(form, field).label.text} - {error}", category)
