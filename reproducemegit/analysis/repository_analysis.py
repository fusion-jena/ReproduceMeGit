"""
Sheeba Samuel
Heinz-Nixdorf Chair for Distributed Information Systems
Friedrich Schiller University Jena, Germany
Email: sheeba.samuel@uni-jena.de
Website: https://github.com/Sheeba-Samuel
"""

from reproducemegit import settings
import pandas as pd
from reproducemegit.jupyter_reproducibility.db import connect, Repository, Notebook, Query, NotebookModule, Execution
from reproducemegit.jupyter_reproducibility.utils import human_readable_duration
from reproducemegit.rmegit import nb2rdf
from reproducemegit.analysis.analysis_helpers import display_counts, describe_processed
from reproducemegit.analysis.analysis_helpers import distribution_with_boxplot, savefig, boxplot_distribution
from reproducemegit.analysis.analysis_helpers import var, relative_var, calculate_auto, close_fig

from dask.dataframe.core import Series as DaskSeries

import matplotlib
from matplotlib import pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
from math import floor

from collections import Counter, defaultdict

from flask import send_file

from flask import current_app
import json

def get_repository_info(repository_id):
    with connect() as session:
        repository_obj = session.query(Repository).filter(
            Repository.id == repository_id
        ).first()

        repositories = {}
        if repository_obj is None:
            return repositories

        notebooks_info = []
        repositories["Link"] = "https://" + repository_obj.domain + "/" + repository_obj.repository
        repositories["No. of Notebooks"] = repository_obj.notebooks_count
        repositories["Setup Count"] = repository_obj.setups_count
        repositories["Requirement Count"] = repository_obj.requirements_count
        if repository_obj.setups_count > 0:
            repositories["Setup"] = repository_obj.setups
        elif repository_obj.requirements_count > 0:
            repositories["Requirement"] = repositories["Link"] + '/tree/master/' + repository_obj.requirements
        repositories["Valid Python Notebooks"] = valid_python_notebooks(repository_id)
        repositories["Invalid Python Notebooks"] = invalid_python_notebooks(repository_id)
        repositories["Count of notebooks without execution count"] = get_nb_without_execution_count(repository_id)
        repositories["Count of notebooks with execution count"] = get_nb_with_execution_count(repository_id)
        return repositories

def get_reproduced_nb(repository_id):
    with connect() as session:
        execution_query = (
            "SELECT id, notebook_id, mode, reason, msg, diff, cell, count, diff_count, timeout, duration, processed, skip "
            "FROM executions "
            "WHERE repository_id = {}"
        ).format(repository_id)
        executions = pd.read_sql(execution_query, session.connection())

        total_notebooks = get_total_notebooks(repository_id)
        if total_notebooks == 0:
            return

        validity_notebooks = get_valid_invalid_nb(repository_id)

        failed_installations = get_failed_installations(executions)

        non_declared_dependencies = get_non_declared_dependencies(executions)

        repro_exceptions = get_repro_exceptions(executions)

        installed_dp = executions[(executions["processed"] > 0) & (executions["mode"] == 3)]
        non_declared_dp = executions[(executions["processed"] > 0) & (executions["mode"] == 5)]
        combined = pd.concat([installed_dp, non_declared_dp])
        total_combined = len(combined)
        repro_excluded_nbformat = len(combined[combined["reason"] == "<Read notebook error>"])
        combined = combined[combined["reason"] != "<Read notebook error>"]
        with_exceptions = combined[combined["processed"] & 4 == 4]


        exception_error = get_exception_error(combined, executions)

        repro_timeout = get_repro_timeout(combined, total_notebooks)


        nb_finished_unfinished_executions = get_nb_finished_unfinished_executions(executions)

        nb_results_difference = get_nb_results_difference(executions)

        nb_execution_count = get_nb_execution_count(repository_id)

        nb_output_cell_count = get_nb_output_cell_count(repository_id)


        return json.dumps({
            'failed_installations': failed_installations,
            'non_declared_dependencies': non_declared_dependencies,
            'repro_exceptions': repro_exceptions,
            'exception_error': exception_error,
            'nb_finished_unfinished_executions': nb_finished_unfinished_executions,
            'nb_results_difference': nb_results_difference,
            'validity_notebooks': validity_notebooks,
            'nb_execution_count': nb_execution_count,
            'nb_output_cell_count': nb_output_cell_count
        })


def get_repository_notebook(repository_id, notebook_id):
    with connect() as session:
        filters = [
                Repository.id == repository_id
            ]
        repository = session.query(Repository).filter(*filters).first()
        if repository is not None:
            notebook_filters = [
                    Notebook.id == notebook_id,
                    Notebook.repository_id == repository_id

                ]
            notebook_query = session.query(Notebook).filter(*notebook_filters).first()
            notebook_name = notebook_query.name
            repository_path = repository.path
            repository_name = repository.repository
            return repository_name, repository_path, notebook_name

def get_total_notebooks(repository_id):
    with connect() as session:
        nb_query = (
                "SELECT count(id) "
                "FROM notebooks "
                "WHERE NOT (kernel = 'no-kernel' AND nbformat = '0') "
                "AND total_cells != 0 "
                "AND repository_id = {} "
            ).format(repository_id)
        result = session.execute(nb_query)
        total_notebooks = result.scalar()
        return total_notebooks

def get_valid_invalid_nb(repository_id):
    validity_notebooks = {}
    valid_notebooks_total = valid_python_notebooks(repository_id)
    invalid_notebooks_total = invalid_python_notebooks(repository_id)
    validity_notebooks_data = [valid_notebooks_total, invalid_notebooks_total]
    validity_notebooks_labels = ['Valid Python Notebooks', 'Invalid Python Notebooks']
    validity_notebooks = {
        'data': validity_notebooks_data,
        'labels': validity_notebooks_labels,
        'title': 'Valid vs Invalid Python Notebooks',
    }
    return validity_notebooks


def get_failed_installations(executions):
    failed_installations = {}
    failed_installations_total = len(executions[executions["processed"] == 0])
    attempted_installations_total = len(executions[executions["mode"] == 3])
    successfull_installations_total = attempted_installations_total - failed_installations_total
    failed_installations_data = [failed_installations_total, successfull_installations_total]
    failed_installations_labels = ['Total Failed Installations', 'Total Successful Installations']
    failed_installations = {
        'data': failed_installations_data,
        'labels': failed_installations_labels,
        'title': 'Failed vs Successful Installations',
    }
    return failed_installations

def get_non_declared_dependencies(executions):
    non_declared_dependencies = {}
    non_declared_dependencies_total = len(executions[(executions["processed"] > 0) & (executions["mode"] == 5)])
    installed_dependencies_total = len(executions[(executions["processed"] > 0) & (executions["mode"] == 3)])
    declared_dependencies = installed_dependencies_total - non_declared_dependencies_total
    non_declared_dependencies_data = [non_declared_dependencies_total, declared_dependencies]
    non_declared_dependencies_labels = ['Total Non Declared Dependencies', 'Total Declared Dependencies']
    non_declared_dependencies = {
        'data': non_declared_dependencies_data,
        'labels': non_declared_dependencies_labels,
        'title': 'Declared vs Non Declared Dependencies',
    }
    return non_declared_dependencies

def get_repro_exceptions(executions):
    installed_dp = executions[(executions["processed"] > 0) & (executions["mode"] == 3)]
    non_declared_dp = executions[(executions["processed"] > 0) & (executions["mode"] == 5)]
    combined = pd.concat([installed_dp, non_declared_dp])
    total_combined = len(combined)
    repro_excluded_nbformat = len(combined[combined["reason"] == "<Read notebook error>"])
    combined = combined[combined["reason"] != "<Read notebook error>"]
    with_exceptions = combined[combined["processed"] & 4 == 4]

    repro_exceptions = {}
    repro_exceptions_total = len(with_exceptions)
    without_exceptions = len(executions) - repro_exceptions_total
    repro_exceptions_data = [repro_exceptions_total, without_exceptions]
    repro_exceptions_labels = ['Total Notebooks with Exceptions', 'Total Notebooks without Exceptions']
    repro_exceptions = {
        'data': repro_exceptions_data,
        'labels': repro_exceptions_labels,
        'title': 'Notebooks with and without exceptions'
    }
    return repro_exceptions

def get_exception_error(combined, executions):
    exception_error = {}
    exception_error_labels = ['ImportError',
                                'ModuleNotFoundError',
                                'NameError',
                                'FileNotFoundError',
                                'IOError',
                                'OSError',
                                'OperationalError',
                                'TypeError',
                                'ValueError',
                                'HTTPError',
                                'SyntaxError',
                                'AttributeError',
                                'StdinNotImplementedError',
                                'Success'
                                ]
    if not combined.empty:
        combined.loc[~combined["reason"].isna() & combined["reason"].str.contains("ModuleNotFoundError"), "new_reason"] = "ModuleNotFoundError"
        combined.loc[~combined["reason"].isna() & combined["reason"].str.contains("NameError"), "new_reason"] = "NameError"
        combined.loc[~combined["reason"].isna() & combined["reason"].str.contains("AttributeError"), "new_reason"] = "AttributeError"
        combined.loc[~combined["reason"].isna() & combined["reason"].str.contains("SyntaxError"), "new_reason"] = "SyntaxError"
        combined.loc[~combined["reason"].isna() & combined["reason"].str.contains("StdinNotImplementedError"), "new_reason"] = "StdinNotImplementedError"
        combined.loc[~combined["reason"].isna() & combined["reason"].str.contains("IOError"), "new_reason"] = "IOError"
        combined.loc[~combined["reason"].isna() & combined["reason"].str.contains("OSError"), "new_reason"] = "OSError"
        combined.loc[~combined["reason"].isna() & combined["reason"].str.contains("OperationalError"), "new_reason"] = "OperationalError"
        combined.loc[~combined["reason"].isna() & combined["reason"].str.contains("TypeError"), "new_reason"] = "TypeError"
        combined.loc[~combined["reason"].isna() & combined["reason"].str.contains("ValueError"), "new_reason"] = "ValueError"
        combined.loc[~combined["reason"].isna() & combined["reason"].str.contains("HTTPError"), "new_reason"] = "HTTPError"
        combined.loc[~combined["reason"].isna() & combined["reason"].str.contains("ImportError"), "new_reason"] = "ImportError"
        combined.loc[~combined["reason"].isna() & combined["reason"].str.contains("FileNotFoundError"), "new_reason"] = "FileNotFoundError"

        import_error = len(combined[(combined["new_reason"] == "ImportError")])
        modulenotfound_error = len(combined[(combined["new_reason"] == "ModuleNotFoundError")])
        name_error = len(combined[(combined["new_reason"] == "NameError")])
        filenotfound_error = len(combined[(combined["new_reason"] == "FileNotFoundError")])
        io_error = len(combined[(combined["new_reason"] == "IOError")])
        os_error = len(combined[(combined["new_reason"] == "OSError")])
        operational_error = len(combined[(combined["new_reason"] == "OperationalError")])
        type_error = len(combined[(combined["new_reason"] == "TypeError")])
        value_error = len(combined[(combined["new_reason"] == "ValueError")])
        http_error = len(combined[(combined["new_reason"] == "HTTPError")])
        syntax_error = len(combined[(combined["new_reason"] == "SyntaxError")])
        attribute_error = len(combined[(combined["new_reason"] == "AttributeError")])
        stdinnotimplemented_error = len(combined[(combined["new_reason"] == "StdinNotImplementedError")])
        success_nb = len(get_finished_executions(executions))
        exception_error_data = [
            import_error, filenotfound_error, modulenotfound_error, name_error,
            io_error, os_error, operational_error, type_error, value_error,
            http_error, syntax_error, attribute_error, stdinnotimplemented_error, success_nb
        ]

        exception_error = {
            'data': exception_error_data,
            'labels': exception_error_labels,
            'title': 'Exceptions during Notebook Execution',
        }
    else:
        exception_error = {
            'data': [],
            'labels': exception_error_labels,
            'title': 'Exceptions during Notebook Execution',
        }

    return exception_error

def get_repro_timeout(combined, total_notebooks):
    repro_timeout = {}
    repro_timeout_total = len(combined[combined["processed"] & 8 == 8])
    repro_timeout_data = [repro_timeout_total, total_notebooks]
    repro_timeout_labels = ['TimeOut', 'Total Notebooks']
    repro_timeout = {
        'data': repro_timeout_data,
        'labels': repro_timeout_labels
    }
    return repro_timeout

def get_attempted_executions_total(executions):
    attempted_executions_total = len(executions)
    return attempted_executions_total


def get_nb_finished_unfinished_executions(executions):
    attempted_executions_total = get_attempted_executions_total(executions)
    finished_executions = get_finished_executions(executions)
    finished_executions_total = len(finished_executions)
    unfinished_executions_total = attempted_executions_total - finished_executions_total
    nb_finished_unfinished_executions_data = [finished_executions_total, unfinished_executions_total]
    nb_finished_unfinished_executions_labels = ['Finished Executions', 'Unfinished Executions']
    nb_finished_unfinished_executions = {
        'data': nb_finished_unfinished_executions_data,
        'labels': nb_finished_unfinished_executions_labels,
        'title': 'Finished vs Unfinished Executions'
    }
    return nb_finished_unfinished_executions

def get_finished_executions(executions):
    finished_executions = executions[
                np.bitwise_and(executions['processed'], 32 + 8 + 4) == 32
                ]
    return finished_executions

def get_same_results_total(executions):
    finished_executions = get_finished_executions(executions)
    same_value = finished_executions[
        np.bitwise_and(finished_executions['processed'], 16) == 16
    ]
    same_value_total = len(same_value)
    return same_value_total

def get_different_results_total(executions):
    finished_executions = get_finished_executions(executions)
    different_results = finished_executions[
                np.bitwise_and(finished_executions['processed'], 16) == 0
    ]
    different_results_total = len(different_results)
    return different_results_total


def get_nb_results_difference(executions):
    same_value_total = get_same_results_total(executions)
    different_results_total = get_different_results_total(executions)

    nb_results_difference = {}
    nb_results_difference_data = [different_results_total, same_value_total]
    nb_results_difference_labels = ['Different Results', 'Same Value']
    nb_results_difference = {
        'data': nb_results_difference_data,
        'labels': nb_results_difference_labels,
        'title': 'Different vs Same Notebook Results',
    }
    return nb_results_difference

def get_nb_execution_count(repository_id):
    nb_without_execution_count = get_nb_without_execution_count(repository_id)
    nb_with_execution_count = get_nb_with_execution_count(repository_id)
    nb_execution_count_data = [nb_with_execution_count, nb_without_execution_count]
    nb_execution_count_labels = ['With Execution Count', 'Without Execution Count']
    nb_execution_count = {
        'data': nb_execution_count_data,
        'labels': nb_execution_count_labels,
        'title': 'Notebooks with and without Execution Numbers',
    }
    return nb_execution_count


def get_nb_output_cell_count(repository_id):
    with connect() as session:
        nb_query = (
                "SELECT sum(code_cells) as sum_code_cells, sum(code_cells_with_output) as sum_code_cells_with_output "
                "FROM notebooks "
                "WHERE repository_id = {} "
            ).format(repository_id)
        notebooks = session.execute(nb_query).fetchone()

        total_code_cells = notebooks.sum_code_cells
        total_code_cells_with_output = notebooks.sum_code_cells_with_output
        total_code_cells_without_output = total_code_cells - total_code_cells_with_output
        nb_output_cell_count_data = [total_code_cells_with_output, total_code_cells_without_output]
        nb_output_cell_count_labels = ['Code Cells with Output', 'Code Cells without Output']
        nb_output_cell_count = {
            'data': nb_output_cell_count_data,
            'labels': nb_output_cell_count_labels,
            'title': 'Notebooks with Code cells with and without Output',
        }
        return nb_output_cell_count



def executions_with_skipped(executions):
    executions = executions[executions["reason"] == "<Skipping notebook>"]
    executions_with_skipped_total = len(executions)
    return executions_with_skipped_total

def get_repository_nb_info(repository_id):
    with connect() as session:
        repository = session.query(Repository).filter(
            Repository.id == repository_id
        ).first()
        notebooks = []
        if repository is None:
            return notebooks
        for name in repository.notebook_names:
            if not name:
                continue
            notebook = session.query(Notebook).filter(
                Notebook.repository_id == repository.id,
                Notebook.name == name,
            ).first()
            notebook_obj = {}
            notebook_obj['name'] = notebook.name
            notebook_obj['id'] = notebook.id
            notebook_obj['nbformat'] = notebook.nbformat
            notebook_obj['kernel'] = notebook.kernel
            notebook_obj['language'] = notebook.language
            notebook_obj['language_version'] = notebook.language_version
            notebook_obj['max_execution_count'] = notebook.max_execution_count
            notebook_obj['total_cells'] = notebook.total_cells
            notebook_obj['code_cells'] = notebook.code_cells
            notebook_obj['code_cells_with_output'] = notebook.code_cells_with_output
            notebook_obj['markdown_cells'] = notebook.markdown_cells
            notebook_obj['raw_cells'] = notebook.raw_cells
            notebook_obj['unknown_cell_formats'] = notebook.unknown_cell_formats
            notebook_obj['empty_cells'] = notebook.empty_cells
            notebooks.append(notebook_obj)
        return notebooks

def get_repository_requirements_info(repository_id):
    with connect() as session:
        query = (
            "SELECT name, reqformat, content "
            "FROM requirement_files "
            "WHERE repository_id = {}"
        ).format(repository_id)

        requirement_files = pd.read_sql(query, session.connection())

        if requirement_files["reqformat"].item() == 'requirements.txt':
            requirements = []
            requirement_files_content = requirement_files["content"].item()
            for rq in requirement_files_content.split('\r\n'):
                requirements.append(rq)
            return requirements
        return requirement_files["content"]


def get_cell_modules_info(repository_id):
    with connect() as session:
        query = (
            "SELECT * "
            "FROM cell_modules "
            "WHERE repository_id = {}"
        ).format(repository_id)
        cell_modules = pd.read_sql(query, session.connection())
        return cell_modules

def get_notebook_modules_info(repository_id):
    with connect() as session:
        repository = session.query(Repository).filter(
            Repository.id == repository_id
        ).first()
        notebook_modules = []
        if repository is None:
            return notebook_modules

        for name in repository.notebook_names:
            if not name:
                continue
            notebook = session.query(Notebook).filter(
                Notebook.repository_id == repository.id,
                Notebook.name == name,
            ).first()

            nb_modules_query = (
                "SELECT * "
                "FROM notebook_modules "
                "WHERE notebook_id = {} AND repository_id = {}"
            ).format(notebook.id, repository_id)
            nb_modules = session.execute(nb_modules_query)
            nb_module = nb_modules.fetchone()
            notebook_obj = {}
            notebook_obj['name'] = notebook.name
            if nb_module is not None:
                if 'any_any' in nb_module:
                    notebook_obj['modules'] = nb_module.any_any
                if 'any_any_count' in nb_module:
                    notebook_obj['totalmodules'] = nb_module.any_any_count
                notebook_modules.append(notebook_obj)
        return notebook_modules

def get_notebook_execution_info(repository_id):
    with connect() as session:
        repository = session.query(Repository).filter(
            Repository.id == repository_id
        ).first()
        notebook_execution = []
        if repository is None:
            return notebook_execution
        for name in repository.notebook_names:
            if not name:
                continue
            notebook = session.query(Notebook).filter(
                Notebook.repository_id == repository.id,
                Notebook.name == name,
            ).first()
            query = (
                "SELECT * "
                "FROM executions "
                "WHERE notebook_id = {} AND repository_id = {}"
            ).format(notebook.id, repository_id)
            executions = session.execute(query)

            execution = executions.fetchone()
            if execution is not None:
                notebook_obj = {}
                notebook_obj['name'] = notebook.name
                if execution["reason"] is None:
                    notebook_obj['executionreason'] = "Success"
                else:
                    notebook_obj['executionreason'] = execution["reason"]
                notebook_obj['diffoncell'] = execution["diff"]
                notebook_obj['diffcount'] = execution["diff_count"]
                notebook_obj['duration'] = human_readable_duration(execution["duration"])
                notebook_obj['msg'] = execution["msg"]
                notebook_execution.append(notebook_obj)
        return notebook_execution

def get_cell_type(repository_id):
    with connect() as session:
        query = (
                "SELECT * "
                "FROM cells "
                "WHERE repository_id = {}"
            ).format(repository_id)
        cells = pd.read_sql(query, session.connection())
        if not cells.empty:
            fig, counts = display_counts(cells["cell_type"].value_counts(), width=5, show_values=True, plot=False,
                title ='Types of cells in Notebooks')
            return fig

def get_nblanguage(repository_id):
    with connect() as session:
        query = (
                "SELECT * "
                "FROM notebooks "
                "WHERE repository_id = {}"
            ).format(repository_id)
        notebooks = pd.read_sql(query, session.connection())
        if not notebooks.empty:
            fig, counts = display_counts(notebooks["language"].value_counts(), width=5, show_values=True, plot=False,
                title ='Programming Language of Notebooks')
            return fig

def get_nblanguage_version(repository_id):
    with connect() as session:
        query = (
                "SELECT * "
                "FROM notebooks "
                "WHERE repository_id = {}"
            ).format(repository_id)
        notebooks = pd.read_sql(query, session.connection())
        if not notebooks.empty:
            series = notebooks.groupby(["language_version", "language"]).count()['kernel'].unstack()
            series.plot(kind="bar", title='Programming Language Version of Notebooks')
            fig = plt.gcf()
            return fig


def valid_python_notebooks(repository_id):
    with connect() as session:
        query = (
                "SELECT * "
                "FROM notebooks "
                "WHERE repository_id = {}"
            ).format(repository_id)
        notebooks = pd.read_sql(query, session.connection())

        valid_python_notebooks_count = len(notebooks[
                (notebooks["language"] == "python")
                & (notebooks["language_version"] != "unknown")
                & ~(
                    (notebooks["kernel"] == "no-kernel")
                    & (notebooks["nbformat"] == "0")
                )
                & (notebooks["total_cells"] != 0)
                & (np.bitwise_and(notebooks["processed"], 16) == 0)

            ])
        return valid_python_notebooks_count

def invalid_python_notebooks(repository_id):
    with connect() as session:
        query = (
                "SELECT * "
                "FROM notebooks "
                "WHERE repository_id = {}"
            ).format(repository_id)
        notebooks = pd.read_sql(query, session.connection())

        invalid_python_notebooks_count = len(notebooks[
                ~((notebooks["language"] == "python")
                & (notebooks["language_version"] != "unknown")
                & ~(
                    (notebooks["kernel"] == "no-kernel")
                    & (notebooks["nbformat"] == "0")
                )
                & (notebooks["total_cells"] != 0)
                & (np.bitwise_and(notebooks["processed"], 16) == 0)
                )
            ])

        return invalid_python_notebooks_count

def get_nb_without_execution_count(repository_id):
    with connect() as session:
        query = (
                "SELECT * "
                "FROM notebooks "
                "WHERE repository_id = {}"
            ).format(repository_id)
        notebooks = pd.read_sql(query, session.connection())

        without_execution_count = notebooks[notebooks.max_execution_count < 0]
        nb_without_execution_count = len(without_execution_count)
        return nb_without_execution_count

def get_nb_with_execution_count(repository_id):
    with connect() as session:
        query = (
                "SELECT * "
                "FROM notebooks "
                "WHERE repository_id = {}"
            ).format(repository_id)
        notebooks = pd.read_sql(query, session.connection())

        with_execution_count = notebooks[notebooks.max_execution_count >= -0]
        nb_with_execution_count = len(with_execution_count)
        return nb_with_execution_count