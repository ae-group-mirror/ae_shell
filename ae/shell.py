"""
shell execution and environment helpers
=======================================

.. hint::
    this module is designed to provide a comprehensive set of constants, types, and helper functions
    for executing and managing external commands, particularly those related to the Git and Pip
    command-line interfaces and Python virtual environments.


fundamental shell execution helpers
-----------------------------------

provided helper functions that simplify the execution of shell commands:

- :func:`sh_exec`: generic/fundamental function for all other shell execution helpers.
- :func:`sh_exit_if_exec_err`: extended version of :func:`sh_exec` with automatically checks for errors
  after a command is executed and handles application termination gracefully.
- :func:`sh_exit_if_git_err`: enables Git command tracing for in-depth debugging, a feature inherited
  by the Git helper functions within this portion.
- :func:`sh_which`: determines the absolute path of a command executable (e.g., `git`, `pip`).
- :func:`is_executable`: checks if a given file path corresponds to a valid executable file.

shell command logging
^^^^^^^^^^^^^^^^^^^^^

the logging of executed command lines and their console output is highly useful for debugging and protocolling
purposes. this portion provides the following helper functions to implement logging for external commands.
logging will be automatically enabled, if the corresponding log file exists.

- :func:`sh_log`: writes a single command execution log entry.
- :func:`sh_logs`: determines the file paths of the currently existing/enabled log files.
- :data:`SHELL_LOG_FILE_NAME_SUFFIX`: the default filename suffix for shell command log files.

.. hint::
    this feature is implemented in :func:`sh_exit_if_git_err` for all the git command execution helpers (``git_*()``)
    of this portion. to enable logging of all executed git commands simply create a log file with the name
    ``git_sh.log``, situated in the current working directory and/or in the users home directory (~).


temporary directories
---------------------

multiple temporary directories are easily managed with three helper functions provided by this portion. each of them is
identified by a context id. the first call of :func:`temp_context_get_or_create` does create a new temporary directory
with an optional subfolder. further calls to this function will either create new contexts or subfolders to an existing
context. the already created folders of each context can be determined via the function :func:`temp_context_folders`.
if the context is no longer needed it can be released/cleaned-up by calling the function
:func:`temp_context_cleanup`.

- :func:`temp_context_get_or_create`: creates a new temporary directory for a specific context or
  retrieves the path of an existing one.
- :func:`temp_context_folders`: retrieves a list of folders within a temporary directory context.
- :func:`temp_context_cleanup`: cleans up and removes a temporary directory for a specific context.

- :data:`GIT_CLONE_CACHE_CONTEXT`: the context identifier used for Git clone downloads.
- :data:`TempContextType`: type hint for the temporary directory context key.
- :data:`_temp_folders`: internal variable that stores the temporary folder contexts.


git command helpers
-------------------

this portion is providing helper functions for lots of git commands, most of them allow to activate git trace
for debugging or intensive testing.

git commands will be executed in repo root folder of a project. the current working directory will be changed
accordingly before a git command get executed (and restored to the old working directory after the execution).

to support `GIT HOOKS <https://git-scm.com/book/ms/v2/Customizing-Git-Git-Hooks>`__ that execute Python code,
the Python virtual environment of a project will be activated
before the git command get executed, and restored to the old value after the git command has finished.

extensive debugging using the `GIT TRACE <https://git-scm.com/docs/api-trace>`__ feature of the git commands
will be activating if your app based on :mod:`~ae.console.ConsoleApp` got executed with
the --debug_level/-D option specified.

- :func:`git_add`: executes the `git add` command to stage changes.
- :func:`git_any`: executes any generic Git command.
- :func:`git_branches`: determines branch names in a Git repository.
- :func:`git_branch_files`: finds added, changed, or deleted files on a specified branch.
- :func:`git_branch_is_dirty`: checks if a Git branch has uncommitted or unstaged changes.
- :func:`git_checkout`: executes the `git checkout` command to switch branches.
- :func:`git_clean`: executes the `git clean` command to remove untracked files.
- :func:`git_commit`: executes the `git commit` command.
- :func:`git_commit_files_count`: determines the number of changed files in the last commit.
- :func:`git_config`: executes the `git config` command.
- :func:`git_conflicts`: lists any merge conflicts in the repository.
- :func:`git_describe`: executes the `git describe` command.
- :func:`git_fetch`: executes the `git fetch` command.
- :func:`git_init_branch`: initializes a new Git branch.
- :func:`git_is_clean`: checks if the repository has a clean working directory (no untracked or
  uncommitted files).
- :func:`git_log_last_commit_date`: determines the date of the last commit.
- :func:`git_pull`: executes the `git pull` command.
- :func:`git_push`: executes the `git push` command.
- :func:`git_remotes`: retrieves the remote URLs of the repository.
- :func:`git_repo_is_init`: checks if a project directory contains a Git repository.
- :func:`git_tags`: lists the Git tags.
- :func:`git_uncommitted`: lists all uncommitted files.
- :func:`git_user_email`: retrieves the Git user's email.
- :func:`git_user_name`: retrieves the Git user's name.
- :func:`git_version_tag`: determines the current version tag of the repository.


git command constants and types
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- :data:`COMMIT_MSG_FILE_NAME`: the default filename for commit messages.
- :data:`DEF_MAIN_BRANCH`: the name of the default/main branch.
- :data:`EXEC_GIT_ERR_PREFIX`: the prefix used to mark Git execution errors.
- :data:`GIT_FOLDER_NAME`: the default name of the Git-internal subfolder.
- :data:`GIT_REMOTE_ORIGIN`: the default name for the origin remote.
- :data:`GIT_REMOTE_UPSTREAM`: the default name for the upstream remote.
- :data:`GIT_RELEASE_REF_PREFIX`: the default prefix, used for release branches.
- :data:`GIT_VERSION_TAG_PREFIX`: the default prefix, used for version tags.
- :data:`GitRemotesType`: the type hint for a dictionary of Git remotes.


pip command helpers
-------------------

this section groups the helpers for executing Pip commands within a project's virtual environment.

- :func:`pip_freeze`: executes `pip freeze` to list all installed packages.
- :func:`pip_install`: executes `pip install` to install packages.
- :func:`pip_show`: executes `pip show` to get detailed information about a package.
- :func:`pip_versions`: determines the available versions of a package from PyPI.


pip command constants
^^^^^^^^^^^^^^^^^^^^^

- :data:`PIP_CMD`: the pip command.
- :data:`PIP_INSTALL_CMD`: the `pip install` command.
- :data:`PYPI_ROOT_URL`: the production PyPI URL.
- :data:`PYPI_ROOT_URL_TEST`: the test PyPI URL.
- :data:`PROJECT_VERSION_SEP`: the separator used in Pip requirements files to ty/fix a project to a version.


virtual environment helpers
---------------------------

these helper functions are provided to assist with the management of Python virtual environments.

- :func:`activate_venv`: ensures that a virtual environment is activated if it's different from the
  current one.
- :func:`active_venv`: determines the name of the currently active virtual environment.
- :func:`in_prj_dir_venv`: a context manager that temporarily changes the working directory and activates
  the project's virtual environment.
- :func:`venv_bin_path`: determines the bin/scripts path of a virtual environment.
- :func:`venv_project_path`: finds the project root path associated with a virtual environment.

the following example installs the required packages of a project into its local virtual environment by
using the :func:`in_prj_dir_venv` context manager together with the shell execution function :func:`sh_exec`
and the constant :data:`PIP_INSTALL_CMD`::

    with in_prj_dir_venv(project_root_path):
        sh_err = sh_exec(PIP_INSTALL_CMD + "-r requirements.txt")


miscellaneous helpers
---------------------

this section includes various other utility functions and classes.

- :func:`bytes_file_diff`: returns the differences between a byte buffer and a file, using the `git diff`
  command.
- :func:`check_commit_msg_file`: checks for the existence of a commit message file.
- :func:`check_if`: terminates the application with an error message if a specified condition is not met.
- :func:`debug_or_verbose`: checks if the application is running in debug or verbose mode.
- :func:`exit_error`: terminates the application with a specific exit code and a custom message.
- :func:`get_domain_user_variable`: retrieves a configuration variable value for a specific domain and/or user.
- :func:`get_main_app`: retrieves the main application instance, or a mock instance if one does not exist.
- :func:`get_pypi_versions`: determines all available release versions of a package on PyPI.
- :func:`hint`: provides a hint message based on the provided arguments.
- :func:`prg_git_project_path`: determines the project root path from the current working directory.

- :class:`MockedMainApp`: a mock class for a main application instance.

- :data:`PPF`: a pre-configured :mod:`pprint` formatter for pretty indented console output.
- :data:`STDERR_BEG_MARKER`: marker used in the console output for the beginning of stderr output.
- :data:`STDERR_END_MARKER`: marker used in the console output for the end of stderr output.
"""
# pylint: disable=too-many-lines
import os
import pprint
import shlex
import subprocess
import sys
import tempfile

from contextlib import contextmanager
from urllib.parse import urlparse
from typing import Optional, Iterator, Iterable, cast, Callable, Any, Union, MutableMapping

import requests
from packaging.version import Version

from ae.base import (                                                                       # type: ignore
    DEF_PROJECT_PARENT_FOLDER, dummy_function, env_str, in_wd, load_env_var_defaults, norm_name, norm_path, now_str,
    os_path_isdir, os_path_isfile, os_path_join, os_path_sep, read_file, write_file)
from ae.core import main_app_instance                                                       # type: ignore
from ae.console import MAIN_SECTION_NAME, ConsoleApp                                        # type: ignore


__version__ = '0.3.3'


COMMIT_MSG_FILE_NAME = '.commit_msg.txt'                #: name of the file containing the commit message
DEF_MAIN_BRANCH = 'develop'                             #: main/develop/default branch name
EXEC_GIT_ERR_PREFIX = "sh_exec() returned error "       #: used by sh_exit_if_exec_err to mark error in 1st output line
GIT_CLONE_CACHE_CONTEXT = 'shell.git_clone'             #: temp directory context for git clone downloads
GIT_FOLDER_NAME = '.git'                                #: git subfolder in project path root of local repository
GIT_REMOTE_ORIGIN = 'origin'                            #: git origin remote name of (fork) repository in user account
GIT_REMOTE_UPSTREAM = 'upstream'                        #: git upstream remote name of original/forked repository
GIT_RELEASE_REF_PREFIX = 'release'                      #: git repository release branch name prefix
GIT_VERSION_TAG_PREFIX = 'v'                            #: git repository version tag prefix
PIP_CMD = "python -m pip"                               #: pip command using python venvs, especially on Windows
PIP_INSTALL_CMD = f"{PIP_CMD} install"                  #: pip install command
PPF = pprint.PrettyPrinter(indent=6, width=189, depth=12).pformat   #: formatter for console printouts
PROJECT_VERSION_SEP = '=='                              #: separates package name and version in pip req files
PYPI_ROOT_URL = "https://pypi.org"                      #: PyPI cheeseshop production domain with service
PYPI_ROOT_URL_TEST = "https://test.pypi.org"            #: PyPI cheeseshop test domain with service
SHELL_LOG_FILE_NAME_SUFFIX = "_sh.log"                  #: default file name (suffix) of the shell log file
STDERR_BEG_MARKER = "vvv   STDERR   vvv"                #: :paramref:`ae.shell.sh_exec.lines_output` begin stderr lines
STDERR_END_MARKER = "^^^   STDERR   ^^^"                #: end stderr lines in :paramref:`ae.shell.sh_exec.lines_output`


# types ---------------------------------------------------------------------------------------------------------------

GitRemotesType = dict[str, str]                         #: git remote urls dict with keys like 'origin'/'upstream'
TempContextType = str                                   #: id/key of a temporary directory context


# global variables ----------------------------------------------------------------------------------------------------

_temp_folders: dict[TempContextType, tuple[tempfile.TemporaryDirectory, list[str]]] = {}  #: temporary folders


# helper functions ----------------------------------------------------------------------------------------------------

def activate_venv(name: str = "") -> str:
    """ ensure to activate a virtual environment if it is different to the current one (the one on Python/app start).

    :param name:                the name of the venv to activate. if this arg is empty or not specified, then the venv
                                of the project in the current working directory tree will be activated.
    :return:                    the name of the previously active venv
                                or an empty string if the requested or no venv was active, or if venv is not supported.
    """
    main_app = get_main_app()    # only for console outputs
    old_name = active_venv()
    bin_path = venv_bin_path(name)
    if not bin_path:
        if name and old_name:
            main_app.dpo(f"    * the venv '{name}' does not exists - skipping switch from current venv '{old_name}'")
        else:
            main_app.vpo(f"    # venv {name=} activation skipped {os.getcwd()=} {old_name=} {bin_path=}")
        return ""

    activate_script_path = os_path_join(bin_path, 'activate')
    if not os_path_isfile(activate_script_path):
        main_app.po(f"    * skipping venv activation, because activate script '{activate_script_path}' not found")
        return ""

    new_name = bin_path.split(os_path_sep)[-2]
    if old_name == new_name:
        main_app.vpo(f"    _ skipped activation of venv '{new_name}' because it is already activated")
        return ""

    main_app.dpo(f"    - activating venv: switching from current venv '{old_name}' to '{new_name}'")
    output: list[str] = []    # venv activation command line inspired by https://stackoverflow.com/questions/7040592
    sh_exit_if_exec_err(323, f"env -i bash -c 'set -a && source {activate_script_path} && env -0'",
                        lines_output=output, shell=True)
    if output and "\0" in output[0]:      # fix error for APP_PRJ (e.g. kivy_lisz)
        os.environ.update(line.split("=", maxsplit=1) for line in output[0].split("\0"))   # type: ignore

    return old_name


def active_venv() -> str:
    """ determine the virtual environment that is currently active.

    .. note:: the current venv gets set via `data:`os.environ` on start of this Python app or by :func:`activate_venv`.

    :return:                    the name of the currently active venv.
    """
    return os.getenv('VIRTUAL_ENV', "").split(os_path_sep)[-1]


def bytes_file_diff(file_content: bytes, file_path: str, line_sep: str = os.linesep) -> str:
    """ return the differences between the content of a file against the specified file content buffer.

    :param file_content:        older file bytes to be compared against the file content of the file specified by the
                                :paramref:`~bytes_file_diff.file_path` argument.
    :param file_path:           path to the file of which newer content gets compared against the file bytes specified
                                by the :paramref:`~bytes_file_diff.file_content` argument.
    :param line_sep:            string used to prefix, separate and indent the lines in the returned output string.
    :return:                    differences between the two file contents, compiled with the `git diff` command.
    """
    with tempfile.NamedTemporaryFile('w+b', delete=False) as tfp:  # delete_on_close kwarg available in Python 3.12+
        tfp.write(file_content)
        tfp.close()
        output = sh_exit_if_git_err(72, "git diff", extra_args=("--no-index", tfp.name, file_path), exit_on_err=False)
        os.remove(tfp.name)

    if output and not output[0].startswith(line_sep):
        output[0] = line_sep + output[0]

    return line_sep.join(output)


def check_commit_msg_file(project_path: str, *hint_args, commit_msg_file: str = COMMIT_MSG_FILE_NAME) -> str:
    """ check if the commit message file exists and if yes return the path of it.

    :param project_path:        project root path.
    :param hint_args:           hint arguments.
    :param commit_msg_file:     name of the git commit message file (def=COMMIT_MSG_FILE_NAME).
    :return:                    the path of the git commit message file of this project.
    :raises:                    exit_error(381) if the commit message file does not exist.
    """
    commit_msg_file = os_path_join(project_path, commit_msg_file)
    if not os_path_isfile(commit_msg_file) or not read_file(commit_msg_file):
        hint_msg = hint(*hint_args) if hint_args else ""
        exit_error(381, f"missing or unreadable commit message/file {commit_msg_file}{hint_msg}")
    return commit_msg_file


def check_if(error_code: int, check_result: bool, error_message: str):
    """ exit/quit this console app if the `check_result` argument is False and the `force` app option is False. """
    if not check_result:
        main_app = get_main_app()
        if left_forces := main_app.get_option('force'):
            main_app.set_option('force', left_forces - 1, save_to_config=False)
            main_app.po(f"  ### forced to ignore/skip error {error_code}: {error_message}")
        else:
            exit_error(error_code, error_message + os.linesep + "      add (another) --force to ignore&skip this error")


def debug_or_verbose() -> bool:
    """ determine if the current app runs in debug|verbose mode, while preventing early .get_option() call an app init.

    :return:                    a boolean False when the main app debug level is :data:`~ae.core.DEBUG_LEVEL_DISABLED`
                                and the app option 'more_verbose' is not specified (in cfg-file or at the command line),
                                else True.

    .. note:: the return value on app startup/initialization, before the command line parsing, is always True.

    .. hint::
        the debug mode can be activated via the :class:`~ae.console.ConsoleApp` option `debug_level`, specified either
        in a config file or via the command line options. the verbose mode get activated via the `more_verbose`  option.
    """
    main_app = get_main_app()
    # noinspection PyProtectedMember
    return bool(
        main_app.debug                                  # main_app.debug_level > DEBUG_LEVEL_DISABLED
        or not main_app._parsed_arguments               # pylint: disable=protected-access
        or main_app.get_option('more_verbose'))         # optional app option


def exit_error(error_code: int, error_message: str):
    """ quit this shell script, optionally displaying an error message. """
    main_app = get_main_app()
    if error_code <= 9:
        main_app.show_help()
    if error_message:
        main_app.po("***** " + error_message)

    if not main_app.verbose:                    # if not in verbose debug mode then
        temp_context_cleanup()                  # cleanup default context and git clone context
        temp_context_cleanup(GIT_CLONE_CACHE_CONTEXT)

    main_app.shutdown(error_code)


def get_domain_user_variable(main_app: ConsoleApp, variable_name: str, domain: str = "", user: str = "") -> Any:
    """ determine the value of a config variable for a specific domain and/or username.

    :param main_app:            main app instance.
    :param variable_name:       name of the config variable.
    :param domain:              name of the domain.
    :param user:                name/id of the user to get a user-specific value of.
    :return:                    domain/user-specific value of the specified config variable.
    """
    value = None
    if domain:
        if user:
            value = main_app.get_variable(f'{variable_name}_AT_{norm_name(domain)}_{norm_name(user)}'.lower())
        if value is None:
            value = main_app.get_variable(f'{variable_name}_AT_{norm_name(domain)}'.lower())
    elif user:
        value = main_app.get_variable(f'{variable_name}_{norm_name(user)}'.lower())

    if value is None:
        value = main_app.get_variable(variable_name.lower())

    return value


def get_main_app() -> ConsoleApp:
    """ determine the main ConsoleApp instance..

    :return:                    ConsoleApp instance of the main app (after their instantiation).
    """
    main_app = main_app_instance()
    if not main_app:
        main_app = MockedMainApp()

    return cast(ConsoleApp, main_app)


def get_pypi_versions(pip_name: str, pypi_test: Optional[bool] = None) -> list[str]:
    """ determine all the available release versions of a package hosted at the PyPI 'Cheese Shop'.

    :param pip_name:            pip|package|project name to get release versions from.
    :param pypi_test:           pass True to use the test version of PyPI (at test.pypi.org). if not specified or None
                                then the test version of PyPI will be used if :paramref:`~get_pypi_versions.pip_name`
                                starts with 'aetst' (the projects namespace used for the pjm integration tests).
    :return:                    list of released versions (the latest last) or
                                on error a list with a single empty string item.
    """
    if pypi_test is None:
        pypi_test = pip_name.startswith('aetst')    # no project path available to check for 'TsT' parent folder
    pypi_root_url = PYPI_ROOT_URL_TEST if pypi_test else PYPI_ROOT_URL

    try:
        response = requests.get(f"{pypi_root_url}/pypi/{pip_name}/json")   # pylint: disable=missing-timeout
        response.raise_for_status()             # raise HTTPError
        data = response.json()
        versions = list(data['releases'].keys())
        versions.sort(key=Version)
        return versions

    except (KeyError, ValueError, Exception):   # pylint: disable=broad-exception-caught
        # catching too: requests.exceptions.HTTPError/.JSONDecodeError
        return [""]         # ignore error on invalid pip_name/page-not-found/never released to PyPi


def git_add(project_path: str, *extra_args: str):
    """ execute the git add command.

    :param project_path:        project path.
    :param extra_args:          additional arguments passed onto git add command. default=["-A"].
    """
    with in_prj_dir_venv(project_path):
        sh_exit_if_git_err(331, "git add", extra_args=extra_args or ["-A"])


def git_any(project_path: str, *args: str) -> list[str]:
    """ execute any git command.

    :param project_path:        path to project root folder.
    :param args:                arguments passed onto the git executable. first arg is the git command.
    :return:                    list of console output lines of the git command optionally including the exit error code
                                (marked with :data:`EXEC_GIT_ERR_PREFIX` in the first returned list item),
                                like returned by :func:`sh_exit_if_git_err`.
    """
    with in_prj_dir_venv(project_path):
        output = sh_exit_if_git_err(329, "git", extra_args=args)
    return output


def git_branches(project_path: str, *extra_args: str) -> list[str]:
    """ determine all branch names with the git branch command.

    :param project_path:        path to project root folder.
    :param extra_args:          additional arguments passed onto git branch command. default=("-a", "--no-color").
    :return:                    list of branch names of the project repo.
    """
    with in_prj_dir_venv(project_path):
        all_branches = sh_exit_if_git_err(327, "git branch", extra_args=extra_args or ("-a", "--no-color"))
    return [branch_name[2:] for branch_name in all_branches]


def git_branch_files(project_path: str, branch_or_tag: str = DEF_MAIN_BRANCH, untracked: bool = False,
                     skip_file_path: Callable[[str], bool] = lambda _: False) -> set[str]:
    """ find all added/changed/deleted/renamed/unstaged worktree files that are not merged into the main branch.

    :param project_path:        path of the project root folder. pass empty string to use the current working directory.
    :param branch_or_tag:       branch(es)/tag(s)/commit(s) passed to `git diff <https://git-scm.com/docs/git-diff>`__
                                to specify the changed files between version(s).
    :param skip_file_path:      called for each found file passing the file path relative to the project root folder
                                (specified by the :paramref:`~find_git_branch_files.project_path` argument), returning
                                True to exclude/skip the file with passed file path.
    :param untracked:           pass True to include untracked files from the returned result set.
    :return:                    set of file paths relative to worktree root specified by the project root path
                                specified by the :paramref:`~find_git_branch_files.project_path` argument.

    .. hint:: see also func:`git_uncommitted` and the unit tests for the differences between them.
    """
    file_paths = set()

    def _call(_cmd: str, _args: tuple[str, ...], _dedent: int = 0):
        _output = sh_exit_if_git_err(318, _cmd, extra_args=_args, exit_on_err=False)
        for _fil_path in _output:
            _fil_path = _fil_path[_dedent:]
            if not skip_file_path(_fil_path):
                file_paths.add(_fil_path)

    with in_prj_dir_venv(project_path):
        if untracked:
            _call("git ls-files", ("--cached", "--others"))
            _call("git status", ("--find-renames", "--porcelain",  "--untracked-files", "-v"), _dedent=3)
        # --compact-summary is alternative to --name-only
        _call("git diff", ("--find-renames", "--full-index", "--name-only", "--no-color", branch_or_tag))

    return file_paths


def git_branch_remotes(project_path: str, branch_pattern: str, remote_names: Iterable[str] = ()) -> list[str]:
    """ return the remote names where the specified branch name exists.

    :param project_path:        path of the project root folder.
    :param branch_pattern:      branch name pattern to search for.
    :param remote_names:        iterable with the remote names. determined with :func:`git_remotes` if not specified.
    :return:                    list of remote names where the branch exists.
    """
    if not remote_names:
        remote_names = git_remotes(project_path)

    remotes = []
    for remote_name in remote_names:
        output = git_any(project_path, 'ls-remote', '--heads', remote_name, branch_pattern)  # --branches in future
        if output and not output[0].startswith(EXEC_GIT_ERR_PREFIX):
            remotes.append(remote_name)
    return remotes


def git_checkout(project_path: str, *extra_args: str,
                 new_branch: str = "", exit_on_err: bool = True, force: bool = False, remote_names: Iterable[str] = ()
                 ) -> str:
    """ checkout git branch.

    :param project_path:        path of the project root folder.
    :param extra_args:          additional arguments passed onto git checkout command.
    :param new_branch:          new branch name to create and check out.
    :param exit_on_err:         specify False to not exit the Python app on any git checkout error.
    :param force:               pass True to ignore uncommitted files and if undefined branch.
    :param remote_names:        iterable with the remote names. determined with :func:`git_remotes` if not specified.
    :return:                    error message or empty string if no error occurred.
    """
    if not force and new_branch:
        if (uncommitted_files := git_uncommitted(project_path)) and new_branch in git_branches(project_path):
            current_branch = git_current_branch(project_path)
            return f"{new_branch=} exists already and {current_branch=} has {uncommitted_files=}"
        if branch_remotes := git_branch_remotes(project_path, new_branch, remote_names=remote_names):
            return f"{new_branch} exists already on the remote(s): {', '.join(branch_remotes)}"

    args = ["--quiet"]
    if new_branch:
        args.extend(["-b", new_branch])
    args.extend(extra_args)

    with in_prj_dir_venv(project_path):
        output = sh_exit_if_git_err(357, "git checkout", extra_args=args, exit_on_err=exit_on_err)

    return os.linesep.join(output)


def git_clone(repo_root: str, project_name: str, *extra_args: str,
              branch_or_tag: str = "", parent_path: str = "", enable_log: bool = False) -> str:
    """ clone a git remote repository onto your local machine.

    :param repo_root:           repository root url without the project name to clone.
    :param project_name:        project name to clone.
    :param extra_args:          extra arguments passed onto the git clone command.
    :param branch_or_tag:       repo branch to clone. if not specified then the main branch will be cloned.
    :param parent_path:         destination path on the local machine to clone onto. if not specified a temporary folder
                                will be used.
    :param enable_log:          pass True to enable git shell command logging.
    :return:                    path to the cloned repository folder or empty string if an error occurred.

    .. hint:: there could occur a user/password prompt if repo is private/invalid!
    """
    if not parent_path:
        parent_path = temp_context_get_or_create(context=GIT_CLONE_CACHE_CONTEXT, folder_name=DEF_PROJECT_PARENT_FOLDER)
    project_path = norm_path(os_path_join(parent_path, project_name))

    args = []
    if branch_or_tag:
        # https://stackoverflow.com/questions/791959/download-a-specific-tag-with-git says:
        # add -b <tag> to specify a release tag/branch to clone, adding --single-branch will speed up the download
        args.append("--branch")
        args.append(branch_or_tag)
        args.append("--single-branch")
    if extra_args:
        args.extend(extra_args)
    args.append(f"{repo_root}/{project_name}.git")

    with in_prj_dir_venv(parent_path):
        output = sh_exit_if_git_err(315, "git clone", extra_args=args, exit_on_err=False,
                                    log_enable_dir=project_path if enable_log else "")

    if output and output[0].startswith(EXEC_GIT_ERR_PREFIX):
        return ""
    return project_path


def git_commit(project_path: str, project_version: str, *extra_args: str,
               commit_msg_text: str = "", commit_msg_file: str = COMMIT_MSG_FILE_NAME):
    """ execute the command 'git commit' for the specified project.

    :param project_path:        path of the project root folder, in which this git command gets executed.
    :param project_version:     project version string.
    :param extra_args:          additional options or args passed to the `git commit` command line,
                                e.g., ["--patch", "--dry-run"]. except from the --file option, which will be added
                                by this function with the name of the git commit message file.
    :param commit_msg_text:     used commit message. if specified then the argument
                                in :paramref:`~git_commit.commit_msg_file` will be ignored.
    :param commit_msg_file:     name of the git commit message file (def=:data:`COMMIT_MSG_FILE_NAME`).
    """
    file_name = check_commit_msg_file(project_path, commit_msg_file=commit_msg_file)
    if commit_msg_text:
        args = ["-m", commit_msg_text]
    else:
        commit_msg = read_file(file_name)
        commit_msg = commit_msg.replace('{apk_ext}', '{{apk_ext}}').format(project_version=project_version)
        write_file(file_name, commit_msg)
        args = [f"--file={file_name}"]  # not valid: "--file <file>" nor "--file='<file>'
    args.extend(extra_args)

    with in_prj_dir_venv(project_path):
        sh_exit_if_git_err(382, "git commit", extra_args=args)


def git_current_branch(project_path: str) -> str:
    """ determine the currently checked-out branch of the specified git repository.

    :param project_path:        project root folder of the git repo.
    :return:                    name of the current branch, or an empty string if no branch is checked out.
    """
    if not os_path_isdir(os_path_join(project_path, GIT_FOLDER_NAME)):
        return ""

    with in_prj_dir_venv(project_path):
        cur_branch = sh_exit_if_git_err(328, "git branch --show-current")
    return cur_branch[0] if cur_branch else ""


def git_diff(project_path: str, *extra_args: str) -> list[str]:
    """ determine the uncommited/unstaged changes of a git project-

    :param project_path:        project root folder.
    :param extra_args:          additional options and refs passed onto the git diff command, apart from the
                                always added options: --no-color, --find-copies-harder, --find-renames and --full-index.
                                pass e.g. --compact-summary or --name-only for a more compact output/return.
    :return:                    list of console output lines of the git diff command, optionally including the exit
                                error code (marked with :data:`EXEC_GIT_ERR_PREFIX` in the first returned list item),
                                like returned by :func:`sh_exit_if_git_err`.
    """
    args = ["--no-color", "--find-copies-harder", "--find-renames", "--full-index"]
    args.extend(extra_args)

    with in_prj_dir_venv(project_path):
        output = sh_exit_if_git_err(370, "git diff", extra_args=args, exit_on_err=False)

    return output


def git_fetch(project_path: str, *extra_args: str, exit_on_err: bool = False) -> list[str]:
    """ fetch repository from remotes.

    :param project_path:        project root folder.
    :param extra_args:          additional options and arguments (remote name) for the git fetch command.
    :param exit_on_err:         specify True to exit the Python app on any git fetch error.
    :return:                    list of lines from the console output that record an error (e.g. if no .git folder).
    """
    with in_prj_dir_venv(project_path):
        output = sh_exit_if_git_err(375, "git fetch", extra_args=extra_args, exit_on_err=exit_on_err)

    return [_ for _ in output if _.lstrip().startswith((EXEC_GIT_ERR_PREFIX, "!", 'fatal:'))]


def git_init_if_needed(project_path: str,
                       author: str = "", email: str = "", main_branch: str = DEF_MAIN_BRANCH) -> bool:
    """ check if a git repository already exists in the specified project root folder, and create it if not.

    :param project_path:        project root path
    :param author:              author of the project/repo added to git config (if specified).
    :param email:               email address of the author added to git config (if specified).
    :param main_branch:         first main branch name to be checked out if repo did not exist / got created.
                                if not specified then the module constant :data:`DEF_MAIN_BRANCH` is used.
                                pass empty string to not do the initial checkout on a not existing repository.
    :return:                    boolean True if a new repo got created and initialized, else False.
    """
    if os_path_isdir(os_path_join(project_path, GIT_FOLDER_NAME)):
        return False

    with in_prj_dir_venv(project_path):
        # the next two config commands prevent error in test systems/containers
        sh_exit_if_git_err(351, "git init")
        if author:
            sh_exit_if_git_err(352, "git config", extra_args=("user.name", author))
        if email:
            sh_exit_if_git_err(353, "git config", extra_args=("user.email", email))
        if main_branch:
            sh_exit_if_git_err(354, "git checkout", extra_args=("-b", main_branch))
        sh_exit_if_git_err(355, "git commit", extra_args=("--allow-empty", "-m", "git repository initialization"))

    return True


def git_merge(project_path: str, from_branch: str, *extra_options: str,
              commit_msg_text: str = "", commit_msg_file: str = COMMIT_MSG_FILE_NAME, exit_on_err: bool = False
              ) -> list[str]:
    """ merge current worktree with the specified [remote/]branch (exit app if an error occurred).

    :param project_path:        project root path of worktree to merge.
    :param from_branch:         branch (or commit/tag) to merge into current worktree with (optional with a leading
                                upstream/origin remote name, e.g. "upstream/main_branch").
    :param extra_options:       extra arguments for the git command
    :param commit_msg_text:     commit message used for the optional merge commit. if specified then the argument
                                in :paramref:`~git_merge.commit_msg_file` will be ignored.
    :param commit_msg_file:     name of the git commit message file (def=COMMIT_MSG_FILE_NAME).
    :param exit_on_err:         specify True to exit the Python app on any git push error.
    :return:                    list with output lines of the git merge command (like returned by the function
                                :func:`sh_exit_if_git_err`, used to execute this git command).
                                if the git command returned with an error code and the argument in
                                :paramref:`~git_merge.exit_on_err` got not specified or as a `True` argument, then
                                the app will quit. if :paramref:`~git_merge.exit_on_err` got specified as 'False' and
                                git push returned an error code, then it will be returned in the first line/list-item
                                (prefixed with :data:`EXEC_GIT_ERR_PREFIX`).
    """
    extra_args: tuple[str, ...]
    if commit_msg_text:
        extra_args = ("-m", commit_msg_text)
    else:
        commit_msg_file = check_commit_msg_file(project_path, commit_msg_file=commit_msg_file)
        extra_args = ("--file", commit_msg_file)
    extra_args += extra_options + ("--log", "--no-stat", from_branch)

    with in_prj_dir_venv(project_path):
        output = sh_exit_if_git_err(377, "git merge", extra_args=extra_args, exit_on_err=exit_on_err)

    return output


def git_push(project_path: str, remote_repo_url: str, *options_and_refs: str, exit_on_err: bool = True) -> list[str]:
    """ push the repo of the specified project with the specified branch/tags to the specified remote.

    :param project_path:        project root folder.
    :param remote_repo_url:     remote repo url. if git credentials are not configured on the local system, then
                                a user token or password has to be included for the authentication against remote.
    :param options_and_refs:    extra arguments for the git command. pass additional options, e.g. "--delete" or
                                "--set-upstream" or "-u", and any references like branch/tag names to be pushed.
    :param exit_on_err:         specify False to not exit the Python app on any git push error.
    :return:                    list with output lines of the git push command (like returned by the function
                                :func:`sh_exit_if_git_err`, used to execute this git push command).
                                if git push returned with an error code and the argument in
                                :paramref:`~git_push.exit_on_err` got not specified or as a `True` argument, then
                                the app will quit. if :paramref:`~git_push.exit_on_err` got specified as 'False' and
                                git push returned an error code, then it will be returned in the first line/list-item
                                (prefixed with :data:`EXEC_GIT_ERR_PREFIX`).
    """
    options = []
    refs = []
    for arg in options_and_refs:
        if arg.startswith("-"):
            options.append(arg)
        else:
            refs.append(arg)

    with in_prj_dir_venv(project_path):
        output = sh_exit_if_git_err(380, "git push",
                                    extra_args=options + [remote_repo_url] + refs, exit_on_err=exit_on_err)

    return output


def git_ref_in_branch(project_path: str, ref: str, branch: str = f'{GIT_REMOTE_ORIGIN}/{DEF_MAIN_BRANCH}') -> bool:
    """ check if branch/tag/ref is in the specified branch.

    :param project_path:        project worktree root path.
    :param ref:                 any ref like a tag or another branch, to be searched within
                                :paramref:`~_git_ref_in_branch.branch`.
    :param branch:              branch to be searched in for :paramref:`~_git_ref_in_branch.tag`. if not specified
                                then it defaults to the remote/origin main branch.
    :return:                    boolean True if the ref got found in the branch, else False.
    """
    with in_prj_dir_venv(project_path):
        extra_args = ("--all", "--contains", ref, "--format=%(refname:short)")
        output = sh_exit_if_git_err(388, "git branch", extra_args=extra_args, exit_on_err=False)
    return bool(output) and not output[0].startswith(EXEC_GIT_ERR_PREFIX) and branch in output


def git_remote_domain_group(project_path: str,
                            origin_name: str = GIT_REMOTE_ORIGIN, upstream_name: str = GIT_REMOTE_UPSTREAM,
                            remote_urls: Optional[GitRemotesType] = None) -> tuple[str, str]:
    """ determine the domain and the repository owner group-/user-name from the git remote configuration (.git/config).

    :param project_path:        path to the project root folder of the repository.
    :param origin_name:         name of the origin git remote (to push to).
    :param upstream_name:       name of the upstream git remote (to request a merge from).
    :param remote_urls:         remote urls. defaults to :func:`git_remotes` if not provided.
    :return:                    tuple with the domain and the user/group of the upstream repository url. if no upstream
                                url is set/configured (not forked) then the origin url is used. if there is no remote
                                configured at all, then the returned tuple contains two empty strings.
    """
    if remote_urls is None:
        remote_urls = git_remotes(project_path)

    remote_url = remote_urls.get(upstream_name, remote_urls.get(origin_name))
    if not remote_url:
        return "", ""

    url_parts = urlparse(remote_url)
    return url_parts.hostname or "", url_parts.path[1:].split('/')[0]


def git_remotes(project_path: str) -> GitRemotesType:
    """ get mapping of hte project repository remotes.

    :param project_path:        path to the project root folder of the repository.
    :return:                    dict with the remote ids as keys and the url as the values.
    """
    remotes = {}
    if os_path_isdir(os_path_join(project_path, GIT_FOLDER_NAME)):
        with in_prj_dir_venv(project_path):
            remote_ids = sh_exit_if_git_err(321, "git remote")
            for remote_id in remote_ids:
                remote_url = sh_exit_if_git_err(322, "git remote", extra_args=("get-url", "--push", remote_id))
                remotes[remote_id] = remote_url[0]
    return remotes


# pylint: disable-next=too-many-arguments,too-many-positional-arguments
def git_renew_remotes(project_path: str, origin_url: str, upstream_url: str = "",
                      origin_name: str = GIT_REMOTE_ORIGIN, upstream_name: str = GIT_REMOTE_UPSTREAM,
                      remotes: Optional[GitRemotesType] = None) -> list[str]:
    """ renew the origin remote and optionally (if repo is forked) also the upstream remote.

    :param project_path:        project root folder.
    :param origin_url:          new url of the origin repo. will append a missing .git extension to the specified url.
    :param upstream_url:        new url of the upstream repo if forked. if specified and differs to the actual upstream
                                url and to the specified origin url, then it will be automatically added.
                                appends a missing .git extension to the specified url.
    :param origin_name:         name of the origin git remote (to push to). if not specified defaults
                                to :data:`GIT_REMOTE_ORIGIN`.
    :param upstream_name:       name of the upstream git remote (to request a merge from). if not specified defaults
                                to :data:`GIT_REMOTE_UPSTREAM`.
    :param remotes:             pass the actual git remotes to prevent multiple execution of the git remote command.
                                determined via :func:`git_remotes` if not specified.
    :return:                    list of console output lines of the executed git remote commands.
                                an empty list no errors/warnings got outputted by the git remote command.
    """
    if not origin_url.endswith(".git"):
        origin_url += ".git"
    if upstream_url and not upstream_url.endswith(".git"):
        upstream_url += ".git"
    if not remotes:
        remotes = git_remotes(project_path)

    err = []
    with in_prj_dir_venv(project_path):
        if upstream_url:
            if upstream_name not in remotes:
                if upstream_url != origin_url:
                    err.extend(sh_exit_if_git_err(340, "git remote", extra_args=("add", upstream_name, upstream_url)))
            elif remotes[upstream_name] != upstream_url:
                err.extend(sh_exit_if_git_err(341, "git remote", extra_args=("set-url", upstream_name, upstream_url)))

        if origin_name not in remotes:
            err.extend(sh_exit_if_git_err(342, "git remote", extra_args=("add", origin_name, origin_url)))
        elif remotes[origin_name] != origin_url:
            err.extend(sh_exit_if_git_err(343, "git remote", extra_args=("set-url", origin_name, origin_url)))

    return err


def git_status(project_path: str, verbose: bool = False) -> list[str]:
    """ get the status of the project repository.

    :param project_path:        project root path.
    :param verbose:             pass True to return a more verbose console output (using --branch -vv --porcelain=2).
    :return:                    console output of the git status command.
    """
    args = ["--find-renames",  "--untracked-files"]  # --untracked-files=normal is missing a full subdir-rel-file-path
    if verbose:
        args.append("--branch")
        args.append("-vv")
        args.append("--porcelain=2")
    else:
        args.append("-v")
        args.append("--porcelain")

    with in_prj_dir_venv(project_path):
        output = sh_exit_if_git_err(376, "git status", extra_args=args)

    return output


def git_tag_add(project_path: str, tag: str, commit_msg_file: str = COMMIT_MSG_FILE_NAME) -> list[str]:
    """ add a new tag onto the project in the specified project root path

    :param project_path:        project root path.
    :param tag:                 tag to add.
    :param commit_msg_file:     name of the git commit message file (def=COMMIT_MSG_FILE_NAME).
    :return:                    console output of the git tag --annotate command.
    """
    with in_prj_dir_venv(project_path):
        output = sh_exit_if_git_err(387, "git tag --annotate",
                                    extra_args=("--file",
                                                check_commit_msg_file(project_path, commit_msg_file=commit_msg_file),
                                                tag))
    return output


def git_tag_list(project_path: str, remote="", tag_pattern: str = "*") -> list[str]:
    """ determine a list of matching tags of a local or remote git repository.

    :param project_path:        project root folder.
    :param remote:              name of a remote.
                                if not specified then only local tags will be determined.
    :param tag_pattern:         matching pattern. if not specified then all tags will be returned.
    :return:                    list of matching repo tags, ordered via the git ls-remote option --sort=version:refname.
                                an empty list will be returned if no tag is matching the specified tag pattern
                                or an error occurred or if the project has no .git folder.
    """
    output: list[str] = []
    if not os_path_isdir(os_path_join(project_path, GIT_FOLDER_NAME)):
        return output

    with in_prj_dir_venv(project_path):
        if remote:
            output = sh_exit_if_git_err(389, "git ls-remote",
                                        extra_args=("--tags", "--refs", "--sort=version:refname", remote, tag_pattern),
                                        exit_on_err=False)
            if output and output[0].startswith(EXEC_GIT_ERR_PREFIX):
                output = []
            else:
                output = [line.split("\t")[-1].split("/")[-1] for line in output]
        else:
            output = sh_exit_if_git_err(389, "git tag",
                                        extra_args=("--list", "--sort=version:refname", tag_pattern),
                                        exit_on_err=False)
            if output and output[0].startswith(EXEC_GIT_ERR_PREFIX):
                output = []

    return output


def git_tag_remotes(project_path: str, tag_pattern: str, remote_names: Iterable[str] = ()) -> list[str]:
    """ return the remote names where the specified tag name exists.

    :param project_path:        path of the project root folder.
    :param tag_pattern:         tag pattern to search for.
    :param remote_names:        iterable with the remote names. determined with :func:`git_remotes` if not specified.
    :return:                    list of remote names where the tag exists.
    """
    if not remote_names:
        remote_names = git_remotes(project_path)

    remotes = []
    for remote_name in remote_names:
        output = git_any(project_path, 'ls-remote', '--tags', remote_name, tag_pattern)
        if output and not output[0].startswith(EXEC_GIT_ERR_PREFIX):
            remotes.append(remote_name)
    return remotes


def git_uncommitted(project_path: str) -> set[str]:
    """ determine the changed/untracked/uncommitted files of a git repository/project.

    :param project_path:        project root folder.
    :return:                    set of changed/untracked/uncommitted file names.
                                an empty set will be returned if the git repo is not initialized or
                                if there are no uncommitted files in the git repo specified by project_path.

    .. hint:: see also func:`git_branch_files` and the unit tests for the differences between them.
    """
    if not os_path_isdir(os_path_join(project_path, GIT_FOLDER_NAME)):
        return set()

    with in_prj_dir_venv(project_path):
        output = sh_exit_if_git_err(379, "git status",
                                    extra_args=("--find-renames", "--untracked-files=all", "--porcelain"))
    return {_[3:] for _ in output}


def hint(command: str, action: Union[Callable, str], message_suffix: str = "") -> str:
    """ return hint string in debug/verbose mode, to be appended onto a shell/console output.

    :param command:             shell command.
    :param action:              shell command action function/method.
    :param message_suffix:      extra message text, added to the end of the returned console output string.
    :return:                    in debug/verbose mode return a string with leading line feed to be sent
                                to console output, else return an empty string.
    """
    if not isinstance(action, str):
        action = action.__name__
    return f"{os.linesep}      (run: {command} {action}{message_suffix})" if debug_or_verbose() else ""


@contextmanager
def in_os_env(start_dir: str = "") -> Iterator[MutableMapping[str, str]]:
    """ temporarily add environment variables from the dotenv files that not exist in os.environ to it.

    :param start_dir:           path to the folder where the first dotenv file (with the highest priority) is stored.
    :return:                    yielding the os env variables that got added to os.environ in this temporary context.
    """
    loaded_env_vars = load_env_var_defaults(start_dir, os.environ)
    try:
        yield loaded_env_vars
    finally:
        for var_name in loaded_env_vars:
            os.environ.pop(var_name)


@contextmanager
def in_prj_dir_venv(project_path: str, venv_name: str = "") -> Iterator[None]:
    """ ensure the current working directory and the specified or .python-version-configured Python Virtual Environment.

    :param project_path:        path to the project root folder to switch the current working directory in this context.
    :param venv_name:           name of the Python Virtual Environment to activate in this context. if not specified
                                (or as empty string), then the venv configured via the file .python-version will be
                                activated.
    :return:
    """
    with in_wd(project_path), in_os_env(project_path), in_venv(name=venv_name):
        yield


@contextmanager
def in_venv(name: str = "") -> Iterator[None]:
    """ ensure the virtual environment gets activated within the context.

    :param name:                the name of the venv to activate. if not specified, then the venv of the project in the
                                current working directory tree will be activated.
    """
    old_venv = activate_venv(name)
    yield
    if old_venv:
        activate_venv(old_venv)


def on_ci_host() -> bool:
    """ check and return True if this tool is running on the GitLab/GitHub CI host/server.

    :return:                    True if running on CI host, else False
    """
    return 'CI' in os.environ or 'CI_PROJECT_ID' in os.environ


def owner_project_from_url(remote_url: str) -> str:
    """ determine the owner and project name path from the specified git remote repository url.

    :param remote_url:          remote repository url.
    :return:                    the owner name and the project name, separated with a slash character.
    """
    url_parts = urlparse(remote_url)
    url_path = url_parts.path
    if url_path.startswith("/"):
        url_path = url_path[1:]
    if url_path.endswith(".git"):
        url_path = url_path[:-4]
    return url_path


def project_name_version(imp_or_pkg_name: str, packages_versions: Iterable[str]) -> tuple[str, str]:
    """ determine package name and version in the specified list of package/version strings.

    :param imp_or_pkg_name:     import or package name to search.
    :param packages_versions:   an Iterable with project package name and optional version strings, like specified in
                                requirements.txt files (format: <project_name>[<PROJECT_VERSION_SEP><project_version>]).
    :return:                    tuple of package name and version number. the package name is an empty string if it
                                is not in :paramref:`~project_version.packages_versions`. the version number is an
                                empty string if no package version is specified in
                                :paramref:`~project_version.packages_versions`.
    """
    project_name = norm_name(imp_or_pkg_name)
    for imp_or_pkg_name_and_ver in packages_versions:
        imp_or_pkg_name, *ver = imp_or_pkg_name_and_ver.split(PROJECT_VERSION_SEP)
        prj_name = norm_name(imp_or_pkg_name)
        if prj_name == project_name:
            return project_name, ver[0] if ver else ""
    return "", ""


# pylint: disable-next=too-many-arguments,too-many-positional-arguments
def sh_exec(command_line: str, extra_args: Iterable = (), console_input: str = "",
            lines_output: Optional[list[str]] = None, main_app: Optional[Any] = None, shell: bool = False,
            env_vars: Optional[dict[str, str]] = None) -> int:
    """ execute command in the current working directory of the OS console/shell.

    :param command_line:        command line string to execute on the console/shell. could contain command line args
                                separated by whitespace characters (alternatively use :paramref:`~sh_exec.extra_args`).
    :param extra_args:          optional sequence of extra command line arguments.
    :param console_input:       optional string to be sent to the stdin stream of the console/shell.
    :param lines_output:        optional list to be extended with the lines printed to stdout/stderr on execution.
                                by passing an empty list, the stdout and stderr streams/pipes will be separated,
                                resulting in having the stderr output lines at the end of the list, enclosed by
                                the list items :data:`STDERR_BEG_MARKER` and :data:`STDERR_END_MARKER`.
    :param main_app:            optional :class:`~ae.console.ConsoleApp` instance, only used for logging. to suppress
                                any logging output, pass :data:`~ae.base.UNSET`.
    :param shell:               pass True to execute command in the default OS shell (see :meth:`subprocess.run`).
    :param env_vars:            OS shell environment variables to be used instead of the console/bash defaults.
    :return:                    return code of the executed command or 126 if execution raised any other exception.
    """
    args = command_line + " " + " ".join(extra_args) if shell else shlex.split(command_line) + list(extra_args)
    ret_out = lines_output is not None  # == isinstance(lines_output, list)
    merge_err = bool(lines_output)      # == -''- and len(lines_output) > 0
    print_out = main_app.po if main_app else print if main_app is None else dummy_function
    debug_out = main_app.dpo if main_app else dummy_function
    debug_out(f"    . executing at {os.getcwd()}: {args}")

    result: Union[subprocess.CompletedProcess, subprocess.CalledProcessError]   # having: stdout/stderr/returncode
    try:
        result = subprocess.run(args,
                                stdout=subprocess.PIPE if ret_out else None,
                                stderr=subprocess.STDOUT if merge_err else subprocess.PIPE if ret_out else None,
                                input=console_input.encode(),
                                check=True,
                                shell=shell,
                                env=env_vars)
    except subprocess.CalledProcessError as ex:                     # pragma: no cover
        debug_out(f"****  subprocess.run({args=}) returned non-zero exit code {ex.returncode}; {ex=}")
        result = ex
    except Exception as ex:                                         # pylint: disable=broad-except  # pragma: no cover
        print_out(f"****  subprocess.run({args}) raised exception {ex}")
        return 126

    if ret_out:
        assert isinstance(lines_output, list), "silly mypy doesn't recognize ret_out"
        if result.stdout:
            lines_output.extend([line for line in result.stdout.decode().split(os.linesep) if line])
        if not merge_err and result.stderr:
            lines_output.append(STDERR_BEG_MARKER)
            lines_output.extend([line for line in result.stderr.decode().split(os.linesep) if line])
            lines_output.append(STDERR_END_MARKER)

    return result.returncode


# pylint: disable-next=too-many-arguments,too-many-positional-arguments
def sh_exit_if_exec_err(err_code: int, command_line: str,
                        extra_args: Iterable = (), lines_output: Optional[list[str]] = None,
                        exit_on_err: bool = True, exit_msg: str = "", shell: bool = False,
                        env_vars: Optional[dict[str, str]] = None) -> int:
    """ execute command in the current working directory of the OS console/shell, dump error, and exit app if needed.

    :param err_code:            error code to pass to the console as exit code if :paramref:`.exit_on_err` is True.
    :param command_line:        command line string to execute on the console/shell. could contain command line args
                                separated by whitespace characters (alternatively use :paramref:`~sh_exec.extra_args`).
    :param extra_args:          optional iterable of extra command line arguments.
    :param lines_output:        optional list to return the lines printed to stdout/stderr on execution.
                                by passing an empty list, the stdout and stderr streams/pipes will be separated,
                                resulting in having the stderr output lines at the end of the list. specify at
                                least on list item to merge-in the stderr output (into the stdout output and return).
    :param exit_on_err:         pass False to **not** exit the app on error (:paramref:`.exit_msg` has then to be
                                empty).
    :param exit_msg:            additional text to print on stdout/console if the app debug level is greater or equal
                                to 1 or if an error occurred and :paramref:`~sh_exit_if_exec_err.exit_on_err` is True.
    :param shell:               pass True to execute command in the default OS shell (see :meth:`subprocess.run`).
    :param env_vars:            OS shell environment variables to be used instead of the console/bash defaults.
    :return:                    0 on success or the error number if an error occurred.
    """
    assert exit_on_err or not exit_msg, "specified exit message will never be shown because exit_on_err is False"
    if lines_output is None:
        lines_output = []
    main_app = get_main_app()

    sh_err = sh_exec(command_line, extra_args=extra_args,
                     lines_output=lines_output, main_app=main_app, shell=shell, env_vars=env_vars)

    if (sh_err and exit_on_err) or main_app.debug:
        for line in lines_output:
            if main_app.verbose or not line.startswith("LOG:  "):  # if verbose show mypy's endless (stderr) log entries
                main_app.po(" " * 6 + line)
        msg = f"command: {command_line} " + " ".join('"' + arg + '"' if " " in arg else arg for arg in extra_args)
        if not sh_err:
            main_app.dpo(f"    = successfully executed {msg}")
        else:
            if exit_msg:
                main_app.po(f"      {exit_msg}")
            check_if(err_code, not exit_on_err, f"sh_exit_if_exec_err error {sh_err} in {msg}")        # app exit

    return sh_err


# pylint: disable-next=too-many-arguments,too-many-positional-arguments,too-many-locals
def sh_exit_if_git_err(err_code: int, command_line: str,
                       extra_args: Iterable = (), lines_output: Optional[list[str]] = None, exit_on_err: bool = False,
                       log_enable_dir: str = "") -> list[str]:
    """ execute git command with optional git trace output, returning the stdout lines cleaned from any trace messages.

    :param err_code:            error code to pass to the console as exit code if :paramref:`.exit_on_err` is True.
    :param command_line:        command line string to execute on the console/shell. could contain command line args
                                separated by whitespace characters (alternatively use :paramref:`~sh_exec.extra_args`).
    :param extra_args:          optional iterable of extra command line arguments.
    :param lines_output:        optional list to return the lines printed to stdout/stderr on execution.
                                by passing an empty list, the stdout and stderr streams/pipes will be separated,
                                resulting in having the stderr output lines at the end of the list. specify at
                                least on list item to merge-in the stderr output (into the stdout output and return).
    :param exit_on_err:         pass True to exit the app on error.
    :param log_enable_dir:      pass the path of the directory in which git shell command logging have to get enabled.
    :return:                    output lines of git command - cleaned from GIT_TRACE messages,
                                if :paramref:`~sh_exit_if_git_err.exit_on_err` got specified as 'False' and the executed
                                git command returned an error code, then the error code will be returned in the first
                                line/list-item (prefixed with :data:`EXEC_GIT_ERR_PREFIX`).
    """
    if lines_output is None:
        lines_output = []

    main_app = get_main_app()
    git_debug = main_app.verbose
    git_trace_vars = ('GIT_TRACE', 'GIT_TRACE_PACK_ACCESS', 'GIT_TRACE_PACKET', 'GIT_TRACE_SETUP')
    env_vars = {'GIT_TERMINAL_PROMPT': "0"}
    if git_debug:
        env_vars['GIT_CURL_VERBOSE'] = "1"
        env_vars['GIT_MERGE_VERBOSITY'] = "5"
        for var in git_trace_vars:
            env_vars[var] = "1"

    cl_err = sh_exit_if_exec_err(err_code, command_line,
                                 extra_args=extra_args, lines_output=lines_output, exit_on_err=exit_on_err,
                                 env_vars={**os.environ, **env_vars})

    if log_files := sh_logs(log_enable_dir=log_enable_dir, log_name_prefix='git'):
        sh_log(command_line, extra_args=extra_args, cl_err=cl_err, lines_output=lines_output, log_file_paths=log_files)

    if cl_err:  # if cl_err and exit_on_err then it would have exit the Python interpreter (so never would run to here)
        main_app.vpo(f"    # ignored error {cl_err} of {command_line=} with {extra_args=} and git trace {env_vars=}")
        lines_output.insert(0, EXEC_GIT_ERR_PREFIX + str(cl_err) + f" in {command_line=} with {extra_args=}")

    if STDERR_BEG_MARKER in lines_output and (  # output marker only if stderr not got merged/called w/ lines_output==[]
            git_debug or any(os.environ.get(_, "0") in ("true", "1", "2") for _ in git_trace_vars)):
        start = lines_output.index(STDERR_BEG_MARKER)
        if git_debug:  # if not already printed by sh_exit_if_exec_err()
            sep = " " * 6
            main_app.po(sep + "git trace output:")
            for line_no in range(start + 1, len(lines_output) - 1):
                main_app.po(sep + lines_output[line_no])
        lines_output[:] = lines_output[:start]      # del output[start:]

    return lines_output


# pylint: disable-next=too-many-arguments,too-many-positional-arguments
def sh_log(comment_or_command: str, extra_args: Iterable[str] = (), cl_err: int = 0, lines_output: Iterable[str] = (),
           log_file_paths: Iterable[str] = (), log_name_prefix: str = ""):
    """ append a log entry to each existing/enabled shell command log file.

    :param comment_or_command:  command line or comment line (if starts with the # character).
    :param extra_args:          extra arguments (added to the command line).
    :param cl_err:              command exit code.
    :param lines_output:        console output lines.
    :param log_file_paths:      log file paths - if specified then the search of the default locations for log files
                                will be skipped and therefore :paramref:`~sh_log.log_name_prefix` will be ignored.
    :param log_name_prefix:     log file name prefix. extended with the :data:`SHELL_LOG_FILE_NAME_SUFFIX` results in
                                the file name to search for (and to log into if exists).
    """
    if not comment_or_command.startswith("#"):
        comment_or_command = " > " + comment_or_command

    sep = os.linesep
    log_lines = (now_str(sep='-') + sep +
                 comment_or_command + " " + " ".join('"' + _ + '"' if " " in _ else _ for _ in extra_args) + sep +
                 (f" * {cl_err=}" + sep if cl_err else "") +
                 ("   " + (sep + "   ").join(lines_output) + sep if lines_output else ""))

    while "glpat-" in log_lines:    # hide the gitlab private token, e.g. from git-push-urls with authentication
        start = log_lines.index("glpat-")
        end = log_lines.index("@gitlab.com", start)
        log_lines = log_lines[:start] + "private-token-" + log_lines[end - 3:]

    for log_path in log_file_paths or sh_logs(log_name_prefix=log_name_prefix):
        write_file(log_path, log_lines, extra_mode='a')


def sh_logs(log_enable_dir: str = "", log_name_prefix: str = "") -> list[str]:
    """ determine paths of the existing/enabled shell command log files, optionally enabling/creating a new log file.

    :param log_enable_dir:      specify the directory/folder path in which to enable shell command logging, by creating
                                a new log file (and the folder) if they not exist. valid folder paths are
                                either the CWD where the shell command get executed (e.g. the project root folder)
                                or the users home directory (~).
    :param log_name_prefix:     log file name prefix. extended with the :data:`SHELL_LOG_FILE_NAME_SUFFIX` results in
                                the file name to search for (and to log into if exists).
    :return:                    list of existing/enabled shell log file name paths.
    """
    file_name = log_name_prefix + SHELL_LOG_FILE_NAME_SUFFIX
    log_files = []

    if os_path_isfile(file_name):
        log_files.append(norm_path(file_name))
    if os_path_isfile(file_path := norm_path(os_path_join("~", file_name))):
        log_files.append(file_path)

    if log_enable_dir:
        file_path = norm_path(os_path_join(log_enable_dir, file_name))
        if file_path not in log_files:
            log_files.append(file_path)
        if not os_path_isfile(file_path):
            write_file(file_path, f"# enabled shell command logging into {file_path}{os.linesep}", make_dirs=True)

    return log_files


def temp_context_cleanup(context: TempContextType = ""):
    """ clean up temporary folders and files.

    :param context:             temporary directory context name. if not specified or passed as an empty string then
                                the default context will be cleaned up.
    """
    if ctx := _temp_folders.pop(context, None):
        ctx[0].cleanup()


def temp_context_folders(context: TempContextType = "") -> list[str]:
    """ determine the folders created under the specified temporary directory context.

    :param context:             temporary directory context name. if not specified or passed as an empty string then
                                the default context will be cleaned up.
    :return:                    list of folders created underneath the temporary directory of the specified context.
                                or an empty list if the context does not exist (or got cleaned up).
    """
    if context in _temp_folders:
        return _temp_folders[context][1]
    return []


def temp_context_get_or_create(context: TempContextType = "", folder_name: str = "") -> str:
    """ get or create (if not exists) a temporary directory context with optional sub-folder.

    :param context:             temporary folder context name. if not specified or passed as an empty string then
                                the default context will be used/created
    :param folder_name:         optional name of a sub-folder.
    :return:                    absolute path of the temporary directory (including the optional sub-folder).
    """
    if context in _temp_folders:
        temp_obj, folders = _temp_folders[context]
    else:
        temp_obj = tempfile.TemporaryDirectory()    # pylint: disable=consider-using-with
        folders = []
        _temp_folders[context] = (temp_obj, folders)

    folder_path = norm_path(os_path_join(temp_obj.name, folder_name))

    if folder_name not in folders:
        if folder_name:
            os.makedirs(folder_path, exist_ok=True)
        folders.append(folder_name)

    return folder_path


def venv_bin_path(name: str = "") -> str:
    """ determine the absolute bin/executables folder path of a virtual pyenv environment.

    :param name:                the name of the venv. if not specified, then the venv name will be determined from the
                                first found ``.python-version`` file, starting in the current working directory (cwd)
                                and up to 5 parent directories above. if no ``.python-version`` file could be found
                                then the name of the currently active venv will be used (via the function
                                :func:`active_venv` respectively the ``VIRTUAL_ENV`` shell environment variable).
    :return:                    absolute path of the "bin" folder in the specified/determined virtual environment or
                                an empty string if pyenv is not installed or no venv name or bin folder could be found.

                                .. note::
                                    under Windows/win32 the base name of the returned path is 'Scripts' (not 'bin'), and
                                    the executables have a file extension (e.g., pip.exe, activate.bat, python.exe).
    """
    venv_root = os.getenv('PYENV_ROOT')
    if not venv_root:   # pyenv is not installed
        return ""

    if not name:
        loc_env_file = '.python-version'
        for _ in range(6):
            if os_path_isfile(loc_env_file):
                name = read_file(loc_env_file).split(os.linesep)[0]
                break
            loc_env_file = ".." + os_path_sep + loc_env_file
        else:
            name = active_venv()
            if not name:
                return ""

    bin_path = os_path_join(venv_root, 'versions', name, 'Scripts' if sys.platform == "win32" else 'bin')
    return bin_path if os_path_isdir(bin_path) else ""


class MockedMainApp:
    """ minimal main app class supporting essential printouts for debugging and testing. """
    debug = True
    verbose = False

    def po(self, *args):
        """ redirect printouts of this mocked main app instance to Python's print() function. """
        if self.verbose:
            print(f"    : print-out via mocked main app instance {self}")
        print(*args)

    dpo = vpo = po  #: other mocked print out methods of this mocked main app instance

    def get_option(self, name: str, default_value: Optional[Any] = None) -> Any:
        """ return simulated/mocked option value.

        :param name:            name of the option.
        :param default_value:   default value.
        :return:                the default value if specified and has a value that will result in True (passing it to
                                the :func:`bool` function), else a boolean True value for all option names except of
                                'force' and 'more_verbose' (for which this function will return a boolean True value).
        """
        if self.verbose:
            print(f"    : get option {name} via mocked main app instance {self}")
        return default_value or name not in ('force', 'more_verbose')

    get_argument = get_option

    def get_variable(self, name: str, **_kwargs) -> Any:
        """ determine value of a config variable (only .env variables, no command line options, nor config/ini vars)

        :param name:            name of the config variable.
        :param _kwargs:         ignored kwargs (see original/mocked method :meth:`~ae.console.ConsoleApp,get_variable`).
        :return:                value of the config variable (str values only) or None if the variable does not exist.
        """
        if self.verbose:
            print(f"    : get variable {name} via mocked main app instance {self}")
        return env_str(MAIN_SECTION_NAME + '_' + name, convert_name=True)

    def set_option(self, *args, **kwargs) -> str:
        """ ignoring any change/update of config variables or options """
        print(f"    : {self} dummy method ignores any change/update of config variable or options! {args=} {kwargs=}")
        return ""

    set_variable = set_option

    def show_help(self):
        """ print hint to console to simulate the :meth:`~ae.console.ConsoleApp,show_help` method. """
        print(f"    : no help for mocked main_app instance {self}")

    def shutdown(self, exit_code: Optional[int] = 0, timeout: Optional[float] = None):
        """ simulate :meth:`~ae.console.ConsoleApp.shutdown` but never shutdown/exit the Python interpreter. """
        print(f"    : shutdown function called with {exit_code=} and {timeout=} for mocked main_app instance {self}")
