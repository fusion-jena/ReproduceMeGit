# -*- coding: utf-8 -*-
"""Public forms."""
from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField
from wtforms.validators import DataRequired

class ReproduceForm(FlaskForm):
    """Reproduce Form."""

    github_url = StringField("GithubUrl", validators=[DataRequired()])
