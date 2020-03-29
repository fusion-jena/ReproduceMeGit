import os

import nbformat

from reproducemegit.jupyter_reproducibility import config
from reproducemegit.jupyter_reproducibility import consts
from reproducemegit.jupyter_reproducibility import load_repository
from reproducemegit.jupyter_reproducibility import s1_notebooks_and_cells, s2_requirement_files, s3_compress, s4_markdown_features
from reproducemegit.jupyter_reproducibility import s5_extract_files, s6_cell_features
from reproducemegit.jupyter_reproducibility import s7_execute_repositories, s8_execute_cellorder
from reproducemegit.jupyter_reproducibility import p0_local_possibility, p1_notebook_aggregate, p2_sha1_exercises
from reproducemegit.jupyter_reproducibility.db import Cell, Notebook, Repository, connect
from reproducemegit.jupyter_reproducibility.utils import StatusLogger, mount_basedir, check_exit, savepid, SafeSession
from reproducemegit.jupyter_reproducibility.utils import timeout, TimeoutError, vprint
from reproducemegit.jupyter_reproducibility.execution_rules import mode_rules
from reproducemegit.rmegit import nb2rdf

def github_crawler(github_url):
    status = None
    count=None
    interval=None
    reverse=None
    check='all'
    keep_uncompressed='False'
    dispatches = set()
    script_name = None
    skip_env=False
    skip_extract=0
    dry_run=0
    status = StatusLogger(script_name)
    status.report()

    with connect() as session, mount_basedir(), savepid():
        repository = load_repository.load_repository_from_url(
                session, github_url
            )
        s1_notebooks_and_cells.apply(
            SafeSession(session, interrupted=consts.N_STOPPED),
            status,
            [repository.id] or True,
            consts.R_N_ERROR,
            count,
            interval,
            reverse,
            set(check)
        )
        s2_requirement_files.apply(
            session,
            status,
            [repository.id] or True,
            consts.R_REQUIREMENTS_ERROR,
            count,
            interval,
            reverse,
            set(check)
        )
        s3_compress.apply(
            session,
            status,
            keep_uncompressed,
            count,
            interval,
            reverse,
            set(check)
        )
        s4_markdown_features.apply(
            session,
            status,
            consts.C_PROCESS_ERROR,
            count,
            interval,
            reverse,
            set(check)
        )
        s5_extract_files.apply(
            session,
            status,
            consts.R_COMPRESS_ERROR,
            count,
            interval,
            reverse,
            set(check)
        )
        s6_cell_features.apply(
                SafeSession(session),
                status,
                dispatches,
                True,
                consts.C_PROCESS_ERROR,
                consts.C_SYNTAX_ERROR,
                consts.C_TIMEOUT,
                count,
                interval,
                reverse,
                set(check)
            )
        result = s7_execute_repositories.apply(
            session,
            repository.id,
            status,
            script_name,
            config.EXECUTION_MODE,
            config.WITH_EXECUTION,
            config.WITH_DEPENDENCY,
            consts.R_COMPRESS_ERROR,
            3,
            consts.R_TROUBLESOME,
            consts.R_UNAVAILABLE_FILES,
            skip_env,
            skip_extract,
            dry_run,
            mode_rules,
            s7_execute_repositories.notebook_exec_mode,
            count,
            interval,
            reverse,
            set(check)
        )
        p0_local_possibility.apply(
            session,
            status,
            count,
            interval,
            reverse,
            set(check)
        )
        p1_notebook_aggregate.apply(
            session,
            status,
            consts.N_AGGREGATE_ERROR,
            count,
            interval,
            reverse,
            set(check)
        )
        p2_sha1_exercises.apply(
            session,
            status,
            count,
            interval,
            reverse,
            set(check)
        )
        return repository.id

def get_notebook(repository_id, notebook_id):
    with connect() as session:
        filters = [
                Repository.id == repository_id
            ]
        repository = session.query(Repository).filter(*filters).first()

        notebook_filters = [
                Notebook.id == notebook_id,
                Notebook.repository_id == repository_id

            ]
        notebook_query = session.query(Notebook).filter(*notebook_filters).first()
        name = notebook_query.name
        with mount_basedir():
            if repository.path.exists():
                execution_path = (config.EXECUTION_DIR / repository.hash_dir2)
            try:
                with open(str(execution_path / name)) as ofile:
                    notebook = ofile.read()
                    nbtordfconverter = nb2rdf.NBToRDFConverter()
                    notebook_json = nbformat.reads(notebook, as_version=4)
                    nbconvert_rdf= nbtordfconverter.convert_to_rdf(name, notebook_json)
                    output_file_extension = 'ttl'
                    output_file = os.path.join(repository.path, name + "." + output_file_extension)
                    open(output_file, 'w').write(str(nbconvert_rdf))
                    return str(nbconvert_rdf), name
            except OSError as e:
                vprint(3, "Failed to open notebook {}".format(e))
