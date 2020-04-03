# -*- coding: utf-8 -*-
"""
Sheeba Samuel
Heinz-Nixdorf Chair for Distributed Information Systems
Friedrich Schiller University Jena, Germany
Email: sheeba.samuel@uni-jena.de
Website: https://github.com/Sheeba-Samuel
"""

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)

from reproducemegit.utils import flash_errors
from reproducemegit.analysis import repository_analysis
from reproducemegit.jupyter_reproducibility import config
from reproducemegit.rmegit.forms import ReproduceForm
from reproducemegit.rmegit.repository_crawler import github_crawler, get_notebook

from matplotlib.backends.backend_agg import FigureCanvasAgg
import io
from flask import Response
import subprocess
blueprint = Blueprint("rmegit", __name__, static_folder="../static")

@blueprint.route("/", methods=["GET", "POST"])
def home():
    """Home page."""
    return render_template("rmegit/home.html")

@blueprint.route("/about/")
def about():
    """About page."""
    return render_template("rmegit/about.html")


@blueprint.route("/rme", methods=["GET", "POST"])
def reproduce():
    """Reproduce Page"""
    if request.method == "POST":
        repository_id = github_crawler(request.form.get('github_url'))
        redirect_url = url_for("rmegit.reproduceresults", **locals())
        return redirect(redirect_url)
    else:
        form = ReproduceForm(request.form)
        return render_template("rmegit/rme_gitnb.html", form=form)

@blueprint.route("/rme/<repository_id>", methods=["GET", "POST"])
def reproduceresults(repository_id):
    """Reproduce Results Page"""
    repository_info = repository_analysis.get_repository_info(repository_id)
    if not repository_info:
        return render_template('404.html')
    notebooks = repository_analysis.get_repository_nb_info(repository_id)
    notebook_modules = repository_analysis.get_notebook_modules_info(repository_id)
    notebook_execution = repository_analysis.get_notebook_execution_info(repository_id)
    return render_template("rmegit/rme_result.html",
        **locals()
    )

@blueprint.route("/reproducednb/<repository_id>")
def reproducednb(repository_id):
    reproducednb = repository_analysis.get_reproduced_nb(repository_id)
    if reproducednb:
        return reproducednb
    else:
        return ('', 204)

@blueprint.route("/nblanguage/<repository_id>")
def get_nblanguage_plot(repository_id):
    """ renders the plot
    """
    fig = repository_analysis.get_nblanguage(repository_id)
    if fig:
        output = io.BytesIO()
        FigureCanvasAgg(fig).print_png(output)
        return Response(output.getvalue(), mimetype="image/png")
    else:
        return ('', 204)

@blueprint.route("/nblanguageversion/<repository_id>")
def get_nblanguage_version_plot(repository_id):
    """ renders the plot
    """
    fig = repository_analysis.get_nblanguage_version(repository_id)
    if fig:
        output = io.BytesIO()
        FigureCanvasAgg(fig).print_png(output)
        return Response(output.getvalue(), mimetype="image/png")
    else:
        return ('', 204)

@blueprint.route("/celltype/<repository_id>")
def get_cell_type_plot(repository_id):
    """ renders the plot
    """
    fig = repository_analysis.get_cell_type(repository_id)
    if fig:
        output = io.BytesIO()
        FigureCanvasAgg(fig).print_png(output)
        return Response(output.getvalue(), mimetype="image/png")
    else:
        return ('', 204)


@blueprint.route("/rme/nb2rdf/<repository_id>/<notebook_id>", methods=["GET", "POST"])
def rme_nb2rdf(repository_id, notebook_id):
    """Reproduce Results Page"""
    nb2rdf, filename = get_notebook(repository_id, notebook_id)
    if nb2rdf:
        return Response(nb2rdf, mimetype="text/turtle", headers={"Content-disposition": "attachment; filename=" + filename + ".ttl"})
    else:
        return ('', 204)

@blueprint.route("/rme/binderurl/<repository_id>/<notebook_id>")
def rme_binderurl(repository_id, notebook_id):
    """Reproduce Results Page"""
    repository_name, repository_path, notebook_name = repository_analysis.get_repository_notebook(repository_id, notebook_id)
    if repository_name and notebook_name:
        binder_url ="https://mybinder.org/v2/gh/" + str(repository_name) + "/master/?filepath=" + str(notebook_name)
        return redirect(binder_url)

@blueprint.route("/rme/jupyterserverurl/<repository_id>/<notebook_id>")
def rme_jupyterserverurl(repository_id, notebook_id):
    """Reproduce Results Page"""
    repository_name, repository_path, notebook_name = repository_analysis.get_repository_notebook(repository_id, notebook_id)
    if repository_name and repository_path and notebook_name:
        notebook_url = str(repository_path) + "/" + str(notebook_name)
        pstatus = subprocess.call(
                '. {}/etc/profile.d/conda.sh '
                '&& conda activate {} '
                '&& jupyter notebook {}'
                .format(
                    config.ANACONDA_PATH, "work", notebook_url
                ), shell=True,
            )
        return 0