# -*- coding: utf-8 -*-
"""
Sheeba Samuel
Heinz-Nixdorf Chair for Distributed Information Systems
Friedrich Schiller University Jena, Germany
Email: sheeba.samuel@uni-jena.de
Website: https://github.com/Sheeba-Samuel
"""

from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField
from wtforms.validators import DataRequired

class ReproduceForm(FlaskForm):
    """Reproduce Form."""

    github_url = StringField("GitHubURL", validators=[DataRequired()])
