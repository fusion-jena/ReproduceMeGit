"""
Sheeba Samuel
Heinz-Nixdorf Chair for Distributed Information Systems
Friedrich Schiller University Jena, Germany
Email: sheeba.samuel@uni-jena.de
Website: https://github.com/Sheeba-Samuel
"""
from flask import Response
from reproducemegit.analysis import repository_analysis

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)

blueprint = Blueprint("analysis", __name__, static_folder="../static")