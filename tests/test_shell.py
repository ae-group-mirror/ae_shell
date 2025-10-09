""" ae.shell unit tests

more unit tests of the git commands that involve git remote hosts (like GitLab or GitHub) are implemented
in the :mod:`aedev.project_manager` project.
"""
import contextlib
import datetime
import os
import shutil
import subprocess
import tempfile

from unittest.mock import PropertyMock, patch

import pytest

from tests.conftest import skip_gitlab_ci

from ae.base import (
    DEF_PROJECT_PARENT_FOLDER, PY_CACHE_FOLDER,
    camel_to_snake, in_wd, load_dotenvs, load_env_var_defaults, norm_name, norm_path, on_ci_host,
    os_path_basename, os_path_dirname, os_path_isdir, os_path_isfile, os_path_join, os_path_relpath,
    project_main_file, read_file, write_file, UNSET)
from ae.core import DEBUG_LEVEL_DISABLED, DEBUG_LEVEL_ENABLED, DEBUG_LEVEL_VERBOSE
from ae.paths import path_items
from ae.console import MAIN_SECTION_NAME, ConsoleApp
try:
    from ae.dev_ops import code_file_version
except ImportError:
    code_file_version = None

# noinspection PyProtectedMember
from ae.shell import (
    COMMIT_MSG_FILE_NAME, DEF_MAIN_BRANCH, EXEC_GIT_ERR_PREFIX, GIT_CLONE_CACHE_CONTEXT, GIT_FOLDER_NAME,
    GIT_RELEASE_REF_PREFIX, GIT_REMOTE_ORIGIN, GIT_REMOTE_UPSTREAM, GIT_VERSION_TAG_PREFIX, SHELL_LOG_FILE_NAME_SUFFIX,
    activate_venv, active_venv, bytes_file_diff, check_commit_msg_file, check_if, debug_or_verbose, exit_error,
    get_domain_user_variable, get_main_app, get_pypi_versions,
    git_add, git_any, git_branches, git_branch_files, git_branch_remotes, git_checkout, git_clone, git_commit,
    git_current_branch, git_diff, git_fetch, git_init_if_needed, git_merge, git_push,
    git_remote_domain_group, git_remotes, git_renew_remotes, git_status,
    git_tag_add, git_ref_in_branch, git_tag_list, git_tag_remotes, git_uncommitted,
    hint, in_os_env, in_prj_dir_venv, in_venv, owner_project_from_url, project_name_version,
    sh_exec, sh_exit_if_exec_err, sh_exit_if_git_err, sh_log, sh_logs,
    temp_context_cleanup, temp_context_folders, temp_context_get_or_create, _temp_folders, venv_bin_path,
    MockedMainApp)


# initialize test environment and declare test constants and fixtures (reduced tests on GitLab CI)
try:
    LOCAL_VENV = read_file(".python-version").strip()
except FileNotFoundError:       # fails at GitLab CI
    LOCAL_ENV = ""
tst_repo_domain = "gitlab.com"

curr_env = os.environ
os.environ = curr_env.copy()
load_dotenvs()
# env-var==AE_OPTIONS_REPO_TOKEN_AT_GITLAB_COM
mtn_tst_repo_token = get_domain_user_variable(get_main_app(), 'repo_token', domain=tst_repo_domain)
# test contributor personal access token, if defined/not-None it enables local integration tests
# itg_tst_repo_token = env_str('TEST_CONTRIBUTOR_TOKEN')
os.environ = curr_env

skip_if_not_maintainer = pytest.mark.skipif('not bool(mtn_tst_repo_token)',
                                            reason=f"missing {tst_repo_domain} maintainer personal-access-token")
# skip_if_no_integration_tests = pytest.mark.skipif('not bool(int_tst_repo_token)',
#                                                 reason="GitLab integration tests personal-access-token not available")

mtn_tst_pkg_name = tst_prj_name = "unit_tst_prj_name"
mtn_tst_root_url = f"https://oauth2:{mtn_tst_repo_token}@{tst_repo_domain}/aetst-group"
mtn_tst_repo_url = f"{mtn_tst_root_url}/{mtn_tst_pkg_name}.git"


def teardown_module():
    """ check if the tested module is still set up correctly at the end of this test module. """
    print(f"##### teardown_module {os_path_basename(__file__)} BEG {get_main_app()=}")

    temp_context_cleanup(GIT_CLONE_CACHE_CONTEXT)       # remove temporary dirs like e.g. the cloned template projects
    temp_context_cleanup()

    print(f"##### teardown_module {os_path_basename(__file__)} END {get_main_app()=}")


@contextlib.contextmanager
def _init_parent():
    with tempfile.TemporaryDirectory() as temp_path, patch('ae.shell.debug_or_verbose', return_value=False):
        parent_path = os_path_join(temp_path, DEF_PROJECT_PARENT_FOLDER)
        os.makedirs(parent_path)
        yield parent_path


@contextlib.contextmanager
def _init_repo(pkg_name: str = ""):
    with _init_parent() as parent_path:
        project_path = os_path_join(parent_path, pkg_name or mtn_tst_pkg_name)
        write_file(os_path_join(project_path, '.gitignore'),
                   COMMIT_MSG_FILE_NAME + "\n" + 'IgnoreD' + "\n", make_dirs=True)
        with in_prj_dir_venv(project_path):
            sh_exec("git init")
            sh_exec("git config", extra_args=("user.email", "testy@test.tst"))
            sh_exec("git config", extra_args=("user.name", "TestUserName"))
            sh_exec("git checkout", extra_args=("-b", DEF_MAIN_BRANCH))
            sh_exec("git commit", extra_args=("-v", "--allow-empty", "-m", "unit tst repo init"))
        yield project_path


@pytest.fixture
def cloned_repo_project_dir():
    """ temporary clone of unit test remote repo project, yielding the local project root folder path. """
    with _init_parent() as parent_path:
        yield git_clone(mtn_tst_root_url, tst_prj_name, parent_path=parent_path)


@pytest.fixture
def changed_repo_path():
    """ provide a git repository with uncommitted changes, yielding the project's temporary working tree root path. """
    with _init_repo() as project_path:
        with in_prj_dir_venv(project_path):
            write_file(os_path_join(project_path, 'ChangeD.y'), "# will be changed")
            write_file(os_path_join(project_path, 'deleteD.x'), "--will be deleted")
            write_file(os_path_join(project_path, 'rename.it'), "! will be renamed")

            sh_exec("git add", extra_args=["-A"])
            sh_exec("git commit", extra_args=["-m", "git commit message"])

            write_file(os_path_join(project_path, 'addEd.ooo'), "# added/staged to repo")
            write_file(os_path_join(project_path, 'ChangeD.y'), "# got changed")
            os.remove(os_path_join(project_path, 'deleteD.x'))
            os.rename(os_path_join(project_path, 'rename.it'), os_path_join(project_path, 'reNamed'))
            write_file(os_path_join(project_path, 'IgnoreD'), "untracked file excluded via .gitignore")

        yield project_path


@pytest.fixture
def empty_repo_path():
    """ provide an empty git repository, yielding the path of the project's temporary working tree root. """
    with _init_repo() as project_path:
        yield project_path


@pytest.fixture
def patched_exit_call_wrapper():
    """ log :func:`ae.shell.exit_error` function calls and args, while preventing main app shutdown. """
    exit_call_args = []

    class _ExitCaller(Exception):
        """ exception to recognize and simulate app exit for function to be tested. """

    def _exit_(*args, **kwargs):
        # nonlocal exit_call_args
        exit_call_args.append((args, kwargs))
        raise _ExitCaller("to be caught by the _call_wrapper() of the patched_exit_call_wrapper unit test fixture")

    def _call_wrapper(fun, *args, **kwargs):
        exit_call_args.clear()
        try:
            ret = fun(*args, **kwargs)
        except _ExitCaller:
            ret = None
        print(f"patched_exit_call_wrapper._call_wrapper {ret=}")
        return exit_call_args

    with patch('ae.shell.exit_error', new=_exit_):
        yield _call_wrapper


class TestGitCommands:
    def test_a_pre_test_if_git_cl_is_setup_on_system(self, capsys):
        output = []

        assert sh_exec("git", extra_args=("--version",), lines_output=output) == 0

        assert output
        with capsys.disabled():
            print(f">>>>>> git --version output: {output}")

    def test_all_file_tracking_git_commands(self, changed_repo_path):
        """ test&doc which git commands can be used to get the status of files in the index and worktree """
        branch = "tst_all_file_tracking_branch"

        def _git_dif(*_args) -> list:
            return git_diff(changed_repo_path, "--name-only", *_args)

        def _git_lsf(*_args) -> list:
            _output = []
            with in_prj_dir_venv(changed_repo_path):
                sh_exit_if_git_err(0, "git ls-files", extra_args=_args, lines_output=_output)
            return _output

        def _git_sta() -> list:
            gst = git_status(changed_repo_path)
            return [_line[3:] for _line in gst]

        def _always_all_files() -> set:
            return set(_git_lsf("--cached", "--others")
                       + _git_sta()
                       + _git_dif("--diff-filter=ABCDMRTUX", DEF_MAIN_BRANCH))

        all_fil = {'addEd.ooo', 'ChangeD.y', 'deleteD.x', 'rename.it', 'reNamed', 'IgnoreD', '.gitignore'}

        assert git_current_branch(changed_repo_path) == DEF_MAIN_BRANCH
        assert (set([os_path_relpath(_, changed_repo_path) for _ in path_items(os_path_join(changed_repo_path, "*"))])
                == {'addEd.ooo', 'ChangeD.y', 'reNamed', 'IgnoreD'})    # plus .gitignore (not seen via "*" wildcard)
        assert set(_git_dif()) == {'ChangeD.y', 'deleteD.x', 'rename.it'}
        assert set(_git_dif("--cached")) == set()
        assert set(_git_dif("--cached", "--diff-filter=ABCDMRTUX", "HEAD")) == set()
        assert set(_git_dif("--diff-filter=ABCDMRTUX")) == {'ChangeD.y', 'deleteD.x', 'rename.it'}
        assert set(_git_dif("--diff-filter=ABCDMRTUX", "HEAD")) == {'ChangeD.y', 'deleteD.x', 'rename.it'}
        assert set(_git_lsf("--cached")) == {'.gitignore', 'ChangeD.y', 'deleteD.x', 'rename.it'}
        assert set(_git_lsf("--deleted")) == {'deleteD.x', 'rename.it'}
        assert set(_git_lsf("--modified")) == {'ChangeD.y', 'deleteD.x', 'rename.it'}
        assert set(_git_lsf("--others")) == {'addEd.ooo', 'reNamed', 'IgnoreD'}
        assert set(_git_lsf("--unmerged")) == set()
        assert set(_git_sta()) == {'addEd.ooo', 'ChangeD.y', 'deleteD.x', 'rename.it', 'reNamed'}
        assert set(_git_lsf("--cached", "--others")) == all_fil
        assert set(_git_lsf("--cached", "--others") + _git_sta()) == all_fil
        assert set(_git_dif("--diff-filter=ABCDMRTUX", DEF_MAIN_BRANCH)) == {'ChangeD.y', 'deleteD.x', 'rename.it'}
        assert _always_all_files() == all_fil

        assert git_branch_files(changed_repo_path) == all_fil - {'.gitignore', 'addEd.ooo', 'reNamed', 'IgnoreD'}
        assert git_branch_files(changed_repo_path, untracked=True) == all_fil
        assert git_uncommitted(changed_repo_path) == all_fil - {'.gitignore', 'IgnoreD'}
        assert git_uncommitted(changed_repo_path) == {
            'addEd.ooo', 'ChangeD.y', 'deleteD.x', 'rename.it', 'reNamed'}

        add2_subdir = os_path_join("subdir", "sub_subdir")
        add2_path = os_path_join(add2_subdir, "add2.yml")
        all_fil |= {add2_path}
        os.makedirs(os_path_join(changed_repo_path, add2_subdir))
        write_file(os_path_join(changed_repo_path, add2_path), "# new file content")        # ADD add2.yml in subdir
        assert git_checkout(changed_repo_path, new_branch=branch) == ""  # reNEW branch
        assert git_current_branch(changed_repo_path) == branch
        assert set(_git_dif()) == {'ChangeD.y', 'deleteD.x', 'rename.it'}
        assert set(_git_dif("--cached")) == set()
        assert set(_git_dif("--cached", "--diff-filter=ABCDMRTUX", "HEAD")) == set()
        assert set(_git_dif("--diff-filter=ABCDMRTUX")) == {'ChangeD.y', 'deleteD.x', 'rename.it'}
        assert set(_git_dif("--diff-filter=ABCDMRTUX", "HEAD")) == {'ChangeD.y', 'deleteD.x', 'rename.it'}
        assert set(_git_dif("--diff-filter=ABCDMRTUX", branch)) == {'ChangeD.y', 'deleteD.x', 'rename.it'}
        assert set(_git_lsf("--cached")) == {'.gitignore', 'ChangeD.y', 'deleteD.x', 'rename.it'}
        assert set(_git_lsf("--deleted")) == {'deleteD.x', 'rename.it'}
        assert set(_git_lsf("--modified")) == {'ChangeD.y', 'deleteD.x', 'rename.it'}
        assert set(_git_lsf("--others")) == {'addEd.ooo', add2_path, 'reNamed', 'IgnoreD'}
        assert set(_git_lsf("--unmerged")) == set()     # unknown option "--format='%(path)'"
        assert set(_git_sta()) == {'addEd.ooo', add2_path, 'ChangeD.y', 'deleteD.x', 'rename.it', 'reNamed'}
        assert set(_git_lsf("--cached", "--others")) == all_fil
        assert set(_git_lsf("--cached", "--others") + _git_sta()) == all_fil
        assert set(_git_dif("--diff-filter=ABCDMRTUX", DEF_MAIN_BRANCH)) == {'ChangeD.y', 'deleteD.x', 'rename.it'}
        assert _always_all_files() == all_fil

        assert git_branch_files(changed_repo_path) == all_fil - {
            '.gitignore', 'addEd.ooo', add2_path, 'reNamed', 'IgnoreD'}
        assert git_branch_files(changed_repo_path, untracked=True) == all_fil
        assert git_uncommitted(changed_repo_path) == all_fil - {'.gitignore', 'IgnoreD'}
        assert git_uncommitted(changed_repo_path) == {
            'addEd.ooo', add2_path, 'ChangeD.y', 'deleteD.x', 'rename.it', 'reNamed'}

        git_add(changed_repo_path)                                                          # ADD changes to the branch
        chg_file = os_path_join(changed_repo_path, 'ChangeD.y')
        write_file(chg_file, read_file(chg_file) + os.linesep + "# changed")                # UPDATE changed.py
        nearly_all_fil = {'addEd.ooo', add2_path, 'ChangeD.y', 'deleteD.x', 'reNamed'}    # .gitignore missing
        assert set(_git_dif()) == {'ChangeD.y'}
        assert set(_git_dif("--cached")) == nearly_all_fil
        assert set(_git_dif("--cached", "--diff-filter=ABCDMRTUX", "HEAD")) == nearly_all_fil
        assert set(_git_dif("--diff-filter=ABCDMRTUX")) == {'ChangeD.y'}
        assert set(_git_dif("--diff-filter=ABCDMRTUX", "HEAD")) == nearly_all_fil
        assert set(_git_dif("--diff-filter=ABCDMRTUX", branch)) == nearly_all_fil
        assert set(_git_lsf("--cached")) == {'.gitignore', 'addEd.ooo', add2_path, 'ChangeD.y', 'reNamed'}
        assert set(_git_lsf("--deleted")) == set()
        assert set(_git_lsf("--modified")) == {'ChangeD.y'}
        assert set(_git_lsf("--others")) == {'IgnoreD'}
        assert set(_git_lsf("--unmerged")) == set()     # unknown option "--format='%(path)'"
        assert set(_git_sta()) == {'addEd.ooo', add2_path, 'ChangeD.y', 'deleteD.x', 'rename.it' + ' -> ' + 'reNamed'}
        assert set(_git_lsf("--cached", "--others") + _git_sta()) == all_fil - {'rename.it'} | {
            'rename.it' + ' -> ' + 'reNamed'}
        assert set(_git_dif("--diff-filter=ABCDMRTUX", DEF_MAIN_BRANCH)) == all_fil - {
            '.gitignore', 'rename.it', 'IgnoreD'}
        assert _always_all_files() == all_fil - {'rename.it'} | {'rename.it' + ' -> ' + 'reNamed'}

        assert git_branch_files(changed_repo_path) == all_fil - {'.gitignore', 'rename.it', 'IgnoreD'}
        assert git_branch_files(changed_repo_path, untracked=True) == all_fil - {'rename.it'} | {
            'rename.it' + ' -> ' + 'reNamed'}
        assert git_uncommitted(changed_repo_path) == all_fil - {
            '.gitignore', 'rename.it', 'reNamed', 'IgnoreD'} | {'rename.it' + ' -> ' + 'reNamed'}
        assert git_uncommitted(changed_repo_path) == {
            'addEd.ooo', add2_path, 'ChangeD.y', 'deleteD.x', 'rename.it' + ' -> ' + 'reNamed'}

        write_file(os_path_join(changed_repo_path, COMMIT_MSG_FILE_NAME), "commit tst msg")
        git_commit(changed_repo_path, "")                                                   # COMMIT 1
        all_fil = all_fil - {'rename.it'} | {'.commit_msg.txt'}
        assert set(_git_dif()) == {'ChangeD.y'}
        assert set(_git_dif("--cached")) == set()
        assert set(_git_dif("--cached", "--diff-filter=ABCDMRTUX", "HEAD")) == set()
        assert set(_git_dif("--diff-filter=ABCDMRTUX")) == {'ChangeD.y'}
        assert set(_git_dif("--diff-filter=ABCDMRTUX", "HEAD")) == {'ChangeD.y'}
        assert set(_git_dif("--diff-filter=ABCDMRTUX", branch)) == {'ChangeD.y'}
        assert set(_git_lsf("--cached")) == {'.gitignore', 'addEd.ooo', add2_path, 'ChangeD.y', 'reNamed'}
        assert set(_git_lsf("--deleted")) == set()
        assert set(_git_lsf("--modified")) == {'ChangeD.y'}
        assert set(_git_lsf("--others")) == {'.commit_msg.txt', 'IgnoreD'}
        assert set(_git_lsf("--unmerged")) == set()     # unknown option "--format='%(path)'"
        assert set(_git_sta()) == {'ChangeD.y'}
        assert set(_git_lsf("--cached", "--others") + _git_sta()) == all_fil - {'deleteD.x'}
        assert set(_git_dif("--diff-filter=ABCDMRTUX", DEF_MAIN_BRANCH)) == all_fil - {
            '.commit_msg.txt', '.gitignore', 'IgnoreD'}
        assert _always_all_files() == all_fil

        assert git_branch_files(changed_repo_path) == all_fil - {
            '.gitignore', COMMIT_MSG_FILE_NAME, 'IgnoreD'}
        assert git_branch_files(changed_repo_path, untracked=True) == all_fil
        assert git_uncommitted(changed_repo_path) == {'ChangeD.y'}

        chg_file = os_path_join(changed_repo_path, 'ChangeD.y')
        write_file(chg_file, read_file(chg_file) + os.linesep + "# change 2")               # CHANGE 2 of changed.py
        add3_path = os_path_join(add2_subdir, 'module.py')
        write_file(os_path_join(changed_repo_path, add3_path), "# new")                     # ADD module.py in subdir
        all_fil |= {add3_path}
        assert set(_git_dif()) == {'ChangeD.y'}
        assert set(_git_dif("--cached")) == set()
        assert set(_git_dif("--cached", "--diff-filter=ABCDMRTUX", "HEAD")) == set()
        assert set(_git_dif("--diff-filter=ABCDMRTUX")) == {'ChangeD.y'}
        assert set(_git_dif("--diff-filter=ABCDMRTUX", "HEAD")) == {'ChangeD.y'}
        assert set(_git_dif("--diff-filter=ABCDMRTUX", branch)) == {'ChangeD.y'}
        assert set(_git_lsf("--cached")) == {'.gitignore', 'addEd.ooo', add2_path, 'ChangeD.y', 'reNamed'}
        assert set(_git_lsf("--deleted")) == set()
        assert set(_git_lsf("--modified")) == {'ChangeD.y'}
        assert set(_git_lsf("--others")) == {'.commit_msg.txt', add3_path, 'IgnoreD'}
        assert set(_git_lsf("--unmerged")) == set()     # unknown option "--format='%(path)'"
        assert set(_git_sta()) == {add3_path, 'ChangeD.y'}
        assert set(_git_lsf("--cached", "--others") + _git_sta()) == all_fil - {'deleteD.x'}
        assert set(_git_dif("--diff-filter=ABCDMRTUX", DEF_MAIN_BRANCH)) == all_fil - {
            '.commit_msg.txt', '.gitignore', add3_path, 'IgnoreD'}
        assert _always_all_files() == all_fil

        assert git_branch_files(changed_repo_path) == all_fil - {
            '.gitignore', COMMIT_MSG_FILE_NAME, add3_path, 'IgnoreD'}
        assert git_branch_files(changed_repo_path, untracked=True) == all_fil
        assert git_uncommitted(changed_repo_path) == all_fil - {
            '.gitignore', COMMIT_MSG_FILE_NAME, 'addEd.ooo', add2_path, 'deleteD.x', 'reNamed', 'IgnoreD'}
        assert git_uncommitted(changed_repo_path) == {add3_path, 'ChangeD.y'}

        add2_ren_path = os_path_join(add2_subdir, 'renamed_add2.yml')                       # RENAME add2.yml
        os.rename(os_path_join(changed_repo_path, add2_path), os_path_join(changed_repo_path, add2_ren_path))
        all_fil |= {add2_ren_path}
        assert set(_git_dif()) == {add2_path, 'ChangeD.y'}
        assert set(_git_dif("--cached")) == set()
        assert set(_git_dif("--cached", "--diff-filter=ABCDMRTUX", "HEAD")) == set()
        assert set(_git_dif("--diff-filter=ABCDMRTUX")) == {add2_path, 'ChangeD.y'}
        assert set(_git_dif("--diff-filter=ABCDMRTUX", "HEAD")) == {add2_path, 'ChangeD.y'}
        assert set(_git_dif("--diff-filter=ABCDMRTUX", branch)) == {add2_path, 'ChangeD.y'}
        assert set(_git_lsf("--cached")) == {'.gitignore', 'addEd.ooo', add2_path, 'ChangeD.y', 'reNamed'}
        assert set(_git_lsf("--deleted")) == {add2_path}
        assert set(_git_lsf("--modified")) == {add2_path, 'ChangeD.y'}
        assert set(_git_lsf("--others")) == {'.commit_msg.txt', add2_ren_path, add3_path, 'IgnoreD'}
        assert set(_git_lsf("--unmerged")) == set()     # unknown option "--format='%(path)'"
        assert set(_git_sta()) == {add2_path, add2_ren_path, add3_path, 'ChangeD.y'}
        assert set(_git_lsf("--cached", "--others") + _git_sta()) == all_fil - {'deleteD.x'}
        assert set(_git_dif("--diff-filter=ABCDMRTUX", DEF_MAIN_BRANCH)) == all_fil - {
            '.commit_msg.txt', '.gitignore', add2_path, add2_ren_path, add3_path, 'IgnoreD'} == {
                   'addEd.ooo', 'ChangeD.y', 'deleteD.x', 'reNamed'}
        assert _always_all_files() == all_fil

        assert git_branch_files(changed_repo_path) == all_fil - {
            '.gitignore', COMMIT_MSG_FILE_NAME, add2_path, add2_ren_path, add3_path, 'IgnoreD'}
        assert git_branch_files(changed_repo_path, untracked=True) == all_fil
        assert git_uncommitted(changed_repo_path) == all_fil - {
            '.gitignore', COMMIT_MSG_FILE_NAME, 'addEd.ooo', 'deleteD.x', 'reNamed', 'IgnoreD'}
        assert git_uncommitted(changed_repo_path) == {add2_path, add2_ren_path, add3_path, 'ChangeD.y'}

        git_add(changed_repo_path)
        git_commit(changed_repo_path, "")                                                   # COMMIT 2
        all_fil -= {add2_path}
        assert set(_git_dif()) == set()
        assert set(_git_dif("--cached")) == set()
        assert set(_git_dif("--cached", "--diff-filter=ABCDMRTUX", "HEAD")) == set()
        assert set(_git_dif("--diff-filter=ABCDMRTUX")) == set()
        assert set(_git_dif("--diff-filter=ABCDMRTUX", "HEAD")) == set()
        assert set(_git_dif("--diff-filter=ABCDMRTUX", branch)) == set()
        assert set(_git_lsf("--cached")) == {
            '.gitignore', 'addEd.ooo', add2_ren_path, add3_path, 'ChangeD.y', 'reNamed'}
        assert set(_git_lsf("--deleted")) == set()
        assert set(_git_lsf("--modified")) == set()
        assert set(_git_lsf("--others")) == {'.commit_msg.txt', 'IgnoreD'}
        assert set(_git_lsf("--unmerged")) == set()     # unknown option "--format='%(path)'"
        assert set(_git_sta()) == set()
        assert set(_git_lsf("--cached", "--others") + _git_sta()) == all_fil - {'deleteD.x'}
        assert set(_git_dif("--diff-filter=ABCDMRTUX", DEF_MAIN_BRANCH)) == all_fil - {
            '.commit_msg.txt', '.gitignore', 'IgnoreD'}
        assert _always_all_files() == all_fil     # nearly all files, only missing deleted/renamed file

        assert git_branch_files(changed_repo_path) == all_fil - {'.gitignore', COMMIT_MSG_FILE_NAME, 'IgnoreD'}
        assert git_branch_files(changed_repo_path, untracked=True) == all_fil
        assert git_uncommitted(changed_repo_path) == set()

    def test_git_add_file_checks(self, changed_repo_path):
        assert git_branch_files(changed_repo_path) == {'ChangeD.y', 'deleteD.x', 'rename.it'}
        assert git_branch_files(changed_repo_path, untracked=True) == {
            '.gitignore', 'IgnoreD', 'addEd.ooo', 'ChangeD.y', 'deleteD.x', 'rename.it', 'reNamed'}
        assert git_uncommitted(changed_repo_path) == {'addEd.ooo', 'ChangeD.y', 'deleteD.x', 'rename.it', 'reNamed'}
        pth_files = set(path_items(os_path_join(changed_repo_path, "**")))
        assert len(git_diff(changed_repo_path, "--name-only")) == 3         # 'ChangeD.y', 'deleteD.x', 'rename.it'

        git_add(changed_repo_path)

        assert git_branch_files(changed_repo_path) == {'addEd.ooo', 'ChangeD.y', 'deleteD.x', 'reNamed'}
        assert git_branch_files(changed_repo_path, untracked=True) == {
            '.gitignore', 'IgnoreD', 'addEd.ooo', 'ChangeD.y', 'deleteD.x',
            'reNamed', 'rename.it' + ' -> ' + 'reNamed'}
        assert git_uncommitted(changed_repo_path) == {
            'addEd.ooo', 'ChangeD.y', 'deleteD.x', 'rename.it' + ' -> ' + 'reNamed'}
        assert pth_files == set(path_items(os_path_join(changed_repo_path, "**")))
        assert git_diff(changed_repo_path, "--name-only") == []

    def test_git_add_status_checks(self, changed_repo_path):
        def _fil_sta(_file_path: str, _verbose: bool = False) -> str:
            output = git_status(changed_repo_path, verbose=_verbose)
            if _verbose:
                _file_path = '\t'.join(reversed(_file_path.split(' -> ')))
                return {line.rsplit(' ')[-1]: "?" if line[0] == "?" else line[2:4]
                        for line in output
                        if line[0] != "#"}.get(_file_path, "¿")
            else:
                return {line[3:]: line[0:2] for line in output}.get(_file_path, "¿")  # line[0:2]==status line[3:]==file

        assert _fil_sta('addEd.ooo') == "??"
        assert _fil_sta('addEd.ooo', _verbose=True) == "?"
        assert _fil_sta('ChangeD.y') == " M"
        assert _fil_sta('ChangeD.y', _verbose=True) == ".M"
        assert _fil_sta('deleteD.x') == " D"
        assert _fil_sta('deleteD.x', _verbose=True) == ".D"
        assert _fil_sta('rename.it') == " D"
        assert _fil_sta('rename.it', _verbose=True) == ".D"
        assert _fil_sta('rename.it' + ' -> ' + 'reNamed') == "¿"
        assert _fil_sta('rename.it' + ' -> ' + 'reNamed', _verbose=True) == "¿"

        git_add(changed_repo_path)

        assert _fil_sta('addEd.ooo') == "A "
        assert _fil_sta('addEd.ooo', _verbose=True) == "A."
        assert _fil_sta('ChangeD.y') == "M "
        assert _fil_sta('ChangeD.y', _verbose=True) == "M."
        assert _fil_sta('deleteD.x') == "D "
        assert _fil_sta('deleteD.x', _verbose=True) == "D."
        assert _fil_sta('rename.it') == "¿"
        assert _fil_sta('rename.it', _verbose=True) == "¿"
        assert _fil_sta('rename.it' + ' -> ' + 'reNamed') == "R "
        assert _fil_sta('rename.it' + ' -> ' + 'reNamed', _verbose=True) == "R."

    def test_git_any(self, changed_repo_path):
        # also tests the results of alternative git commands
        branch = git_current_branch(changed_repo_path)
        assert git_any(changed_repo_path, 'rev-parse',  "--abbrev-ref", "HEAD") == [branch]

        project_path = os_path_join(os_path_dirname(os.getcwd()), "ae_base")
        if os_path_isdir(project_path):  # only test if exists on local machine and under the same parent dir
            branch = git_current_branch(project_path)
            output = git_any(project_path, 'for-each-ref', "--format=%(objectname)", f"refs/heads/{branch}")
            assert git_any(project_path, 'rev-parse', f"refs/heads/{branch}") == output

    def test_git_branches(self, empty_repo_path):
        assert git_branches(empty_repo_path) == [DEF_MAIN_BRANCH]
        assert git_checkout(empty_repo_path, new_branch='empty_repo_new_branch') == ""

        assert set(git_branches(empty_repo_path)) == {DEF_MAIN_BRANCH, 'empty_repo_new_branch'}

    @skip_gitlab_ci
    def test_git_branch_files_between_versions(self):
        prj_path = norm_path("../ae_base")
        exp = {
            'README.md',
            'ae/base.py',
            'setup.py',
            'tests/test_base.py',
        }

        assert git_branch_files(prj_path, branch_or_tag="v0.3.69..v0.3.70") == exp
        assert git_branch_files(prj_path, branch_or_tag="v0.3.70..v0.3.71") == exp
        assert git_branch_files(prj_path, branch_or_tag="v0.3.71..v0.3.72") == exp
        assert git_branch_files(prj_path, branch_or_tag="v0.3.69..v0.3.72") == exp
        assert git_branch_files(prj_path, branch_or_tag="v0.3.69..v0.3.71") == exp
        assert git_branch_files(prj_path, branch_or_tag="v0.3.70..v0.3.72") == exp

        exp = {
            '.gitignore',
            '.gitlab-ci.yml',
            'CONTRIBUTING.rst',
            'LICENSE.md',
            'README.md',
            'SECURITY.md',
            'ae/base.py',
            'dev_requirements.txt',
            'setup.py',
            'tests/conftest.py',
            'tests/requirements.txt',
            'tests/test_base.py',
        }

        assert git_branch_files(prj_path, branch_or_tag="v0.3.64..v0.3.65") == exp
        assert git_branch_files(prj_path, branch_or_tag="v0.3.65..v0.3.66") == exp
        assert git_branch_files(prj_path, branch_or_tag="v0.3.66..v0.3.67") == exp | {'pyproject.toml'}
        assert git_branch_files(prj_path, branch_or_tag="v0.3.67..v0.3.68") == exp | {'pyproject.toml'}
        assert git_branch_files(prj_path, branch_or_tag="v0.3.68..v0.3.69") == (
                exp | {'pyproject.toml'}) - {'tests/test_base.py'}

        assert git_branch_files(prj_path, branch_or_tag="v0.3.64..v0.3.69") == exp | {'pyproject.toml'}
        assert git_branch_files(prj_path, branch_or_tag="v0.3.64..v0.3.72") == exp | {'pyproject.toml'}

    def test_git_branch_files_excludes(self, changed_repo_path):
        assert git_branch_files(changed_repo_path) == {'ChangeD.y', 'deleteD.x', 'rename.it'}

        assert git_branch_files(changed_repo_path, untracked=True) == {
            '.gitignore', 'addEd.ooo', 'ChangeD.y', 'deleteD.x', 'rename.it', 'reNamed', 'IgnoreD'}

        assert git_branch_files(changed_repo_path, skip_file_path=lambda _: _ != 'deleteD.x') == {'deleteD.x'}

        assert git_branch_files(changed_repo_path, skip_file_path=lambda _: True) == set()

    def test_git_branch_remotes(self, empty_repo_path):
        assert not git_branch_remotes(empty_repo_path, "*")
        assert not git_branch_remotes(empty_repo_path, "*", remote_names=["ori0", "ups1"])
        assert GIT_REMOTE_ORIGIN in git_branch_remotes(git_clone(f"https://gitlab.com/ae-group", 'ae_base'), "*")

    def test_git_checkout_renew_workflow(self, changed_repo_path):
        main_branch = git_current_branch(changed_repo_path)
        assert main_branch == DEF_MAIN_BRANCH
        old_files = set(path_items(os_path_join(changed_repo_path, "**")))
        old_uncommitted = git_uncommitted(changed_repo_path)  # {'addEd.ooo', 'ChangeD.y', 'deleteD.x', 'rename.it'}
        new_branch = "new_tst_branch"
        new_file = 'new_branch_file_commit_tst.py'

        assert git_checkout(changed_repo_path, new_branch=new_branch) == ""

        assert git_current_branch(changed_repo_path) == new_branch
        assert set(path_items(os_path_join(changed_repo_path, "**"))) == old_files  # changed files are in new_branch
        assert git_uncommitted(changed_repo_path) == old_uncommitted

        git_add(changed_repo_path)
        write_file(os_path_join(changed_repo_path, COMMIT_MSG_FILE_NAME), "commit title of develop branch commit")

        assert set(path_items(os_path_join(changed_repo_path, "**"))) == old_files
        assert git_uncommitted(changed_repo_path) == old_uncommitted - {
            'rename.it', 'reNamed'} | {'rename.it' + ' -> ' + 'reNamed'}
        old_uncommitted = git_uncommitted(changed_repo_path)    # {'addEd.ooo', ... 'rename.it -> reNamed'}

        assert git_checkout(changed_repo_path, DEF_MAIN_BRANCH) == ""

        assert git_current_branch(changed_repo_path) == DEF_MAIN_BRANCH
        assert set(path_items(os_path_join(changed_repo_path, "**"))) == old_files
        assert git_uncommitted(changed_repo_path) == old_uncommitted

        err_msg = git_checkout(changed_repo_path, new_branch=new_branch)
        assert new_branch in err_msg and DEF_MAIN_BRANCH in err_msg and "has uncommitted_files=" in err_msg
        err_msg = git_checkout(changed_repo_path, new_branch=new_branch, force=True)
        assert new_branch in err_msg
        assert git_checkout(changed_repo_path, new_branch) == ""   # finally checkout of new_branch without error

        assert set(path_items(os_path_join(changed_repo_path, "**"))) == old_files
        assert git_uncommitted(changed_repo_path) == old_uncommitted

        assert git_checkout(changed_repo_path, DEF_MAIN_BRANCH) == ""  # double check if files are still also in develop

        assert set(path_items(os_path_join(changed_repo_path, "**"))) == old_files
        assert git_uncommitted(changed_repo_path) == old_uncommitted

        assert git_checkout(changed_repo_path, new_branch) == ""   # finally checkout of new_branch without error

        assert git_current_branch(changed_repo_path) == new_branch
        assert set(path_items(os_path_join(changed_repo_path, "**"))) == old_files
        assert git_uncommitted(changed_repo_path) == old_uncommitted

        git_commit(changed_repo_path, "444.777.9")  # COMMIT new_branch ---------------------------

        assert set(path_items(os_path_join(changed_repo_path, "**"))) == old_files
        assert not git_uncommitted(changed_repo_path)

        assert git_checkout(changed_repo_path, DEF_MAIN_BRANCH) == ""

        assert git_current_branch(changed_repo_path) == DEF_MAIN_BRANCH
        assert (com_files := set(path_items(os_path_join(changed_repo_path, "**")))) != old_files
        assert len(com_files) == len(old_files)     # committed: +'deleteD.x'+'rename.it' old: +'addEd.ooo'+'reNamed'
        assert not git_uncommitted(changed_repo_path)

        assert git_checkout(changed_repo_path, new_branch) == ""

        assert git_current_branch(changed_repo_path) == new_branch
        assert set(path_items(os_path_join(changed_repo_path, "**"))) == old_files
        assert not git_uncommitted(changed_repo_path)

        write_file(os_path_join(changed_repo_path, new_file), f"# new test file{os.linesep}")
        assert (new_files := set(path_items(os_path_join(changed_repo_path, "**")))) != old_files

        assert git_checkout(changed_repo_path, new_branch) == ""      # duplicate checkout does not change anything

        assert git_current_branch(changed_repo_path) == new_branch
        assert set(path_items(os_path_join(changed_repo_path, "**"))) == new_files
        assert git_uncommitted(changed_repo_path)

        assert git_checkout(changed_repo_path, new_branch=new_branch)       # ERROR does not change anything

        assert git_current_branch(changed_repo_path) == new_branch
        assert set(path_items(os_path_join(changed_repo_path, "**"))) == new_files
        assert git_uncommitted(changed_repo_path)

        git_add(changed_repo_path)
        write_file(os_path_join(changed_repo_path, COMMIT_MSG_FILE_NAME), "new-branch commit message tst file content")
        git_commit(changed_repo_path, "")

        assert git_current_branch(changed_repo_path) == new_branch
        assert set(path_items(os_path_join(changed_repo_path, "**"))) == new_files
        assert not git_uncommitted(changed_repo_path)

        assert git_checkout(changed_repo_path, new_branch=DEF_MAIN_BRANCH)  # error because main branch already exists

        assert git_checkout(changed_repo_path, DEF_MAIN_BRANCH) == ""

        assert git_current_branch(changed_repo_path) == DEF_MAIN_BRANCH
        assert set(path_items(os_path_join(changed_repo_path, "**"))) == com_files
        assert not git_uncommitted(changed_repo_path)

        assert git_checkout(changed_repo_path, new_branch) == ""

        assert git_current_branch(changed_repo_path) == new_branch
        assert set(path_items(os_path_join(changed_repo_path, "**"))) == new_files
        assert not git_uncommitted(changed_repo_path)

    def test_git_checkout_to_restore_deleted_file(self, changed_repo_path):
        del_path = os_path_join(changed_repo_path, 'deleteD.x')
        old_files = set(path_items(os_path_join(changed_repo_path, "**")))
        uncommitted = git_uncommitted(changed_repo_path)

        assert git_checkout(changed_repo_path, "HEAD", "--", 'deleteD.x') == ""

        assert git_current_branch(changed_repo_path) == DEF_MAIN_BRANCH
        assert set(path_items(os_path_join(changed_repo_path, "**"))) == old_files | {del_path}
        assert git_uncommitted(changed_repo_path) == uncommitted - {'deleteD.x'}

    def test_git_checkout_to_restore_renamed_file(self, changed_repo_path):
        ren_from_path = os_path_join(changed_repo_path, 'rename.it')
        ren_to_path = os_path_join(changed_repo_path, 'reNamed')
        old_files = set(path_items(os_path_join(changed_repo_path, "**")))
        uncommitted = git_uncommitted(changed_repo_path)

        assert git_checkout(changed_repo_path, "HEAD", "--", 'rename.it') == ""

        assert git_current_branch(changed_repo_path) == DEF_MAIN_BRANCH
        assert ren_to_path in set(path_items(os_path_join(changed_repo_path, "**")))    # renamed keeps in worktree
        assert set(path_items(os_path_join(changed_repo_path, "**"))) == old_files | {ren_from_path}
        assert git_uncommitted(changed_repo_path) == uncommitted - {'rename.it'} | {'reNamed'}

    def test_git_checkout_new_branch_already_existing(self):
        project_path = git_clone(f"https://gitlab.com/ae-group", 'ae_base')
        assert project_path

        err_msg = git_checkout(project_path, new_branch=DEF_MAIN_BRANCH)

        assert "exists already on the remote" in err_msg

    def test_git_clone_ae_base_again_into_cached_temp_folder_with_git_logging_enabled(self):
        cur_dir = os.getcwd()
        project_name = 'ae_base'

        parent_dir = temp_context_get_or_create(context=GIT_CLONE_CACHE_CONTEXT, folder_name=DEF_PROJECT_PARENT_FOLDER)
        project_path = os_path_join(parent_dir, project_name)
        assert os_path_isdir(project_path)
        assert not os_path_isfile(os_path_join(project_path, 'git' + SHELL_LOG_FILE_NAME_SUFFIX))

        prj_path = git_clone(f"https://gitlab.com/ae-group", project_name, enable_log=True)

        assert prj_path == ""
        assert os_path_isdir(project_path)
        # git logging activated although git_clone of ae_base failed, because got already cached by previous test method
        assert os_path_isfile(os_path_join(project_path, 'git' + SHELL_LOG_FILE_NAME_SUFFIX))
        assert os.getcwd() == cur_dir
        assert _temp_folders

    def test_git_clone_ae_base_release(self):
        import_name = "ae.base"
        version = "0.3.60"
        project_name = norm_name(import_name)

        assert _temp_folders
        tmp_dir = temp_context_get_or_create(context=GIT_CLONE_CACHE_CONTEXT, folder_name=DEF_PROJECT_PARENT_FOLDER)
        project_path = os_path_join(tmp_dir, project_name)
        assert os_path_isdir(project_path)

        ret = git_clone("https://gitlab.com/ae-group", project_name, branch_or_tag=GIT_RELEASE_REF_PREFIX + version)

        assert not ret     # fails because ae_base is already in temp_folders from previous test method

        shutil.rmtree(project_path)

        ret = git_clone("https://gitlab.com/ae-group", project_name, branch_or_tag=GIT_RELEASE_REF_PREFIX + version)

        assert ret.endswith(project_name)
        assert ret == project_path

        assert _temp_folders
        tmp_dir = temp_context_get_or_create(context=GIT_CLONE_CACHE_CONTEXT, folder_name=DEF_PROJECT_PARENT_FOLDER)
        assert os_path_isdir(os_path_join(tmp_dir, project_name))
        if callable(code_file_version):
            # noinspection PyCallingNonCallable
            assert version == code_file_version(project_main_file(import_name, project_path=project_path))

    def test_git_clone_ae_base_version_tag_to_test(self, tmp_path):
        import_name = "ae.base"
        version = "0.3.60"
        project_name = norm_name(import_name)
        parent_dir = os_path_join(str(tmp_path), DEF_PROJECT_PARENT_FOLDER)
        os.makedirs(parent_dir)

        project_path = git_clone("https://gitlab.com/ae-group", project_name, branch_or_tag=f"v{version}",
                                 parent_path=parent_dir)

        assert project_path.startswith(norm_path(parent_dir))
        assert os_path_isdir(os_path_join(parent_dir, project_name))
        if callable(code_file_version):
            # noinspection PyCallingNonCallable
            assert version == code_file_version(project_main_file(import_name, project_path=project_path))

    def test_git_clone_ae_files_with_trace(self):
        cur_dir = os.getcwd()
        project_name = 'ae_files'

        with patch('ae.shell.MockedMainApp.verbose', new_callable=PropertyMock, return_value=True):
            project_path = git_clone(f"https://gitlab.com/ae-group", project_name)

        assert os.getcwd() == cur_dir
        assert _temp_folders
        tmp_dir = temp_context_get_or_create(context=GIT_CLONE_CACHE_CONTEXT, folder_name=DEF_PROJECT_PARENT_FOLDER)
        assert project_path.startswith(tmp_dir)
        assert os_path_isdir(os_path_join(tmp_dir, project_name))

    def test_git_clone_fail(self):
        cur_dir = os.getcwd()

        assert git_clone("_invalid_repo_", "_invalid_project_name", "_invalid_arg", branch_or_tag="9.99.999") == ""

        assert os.getcwd() == cur_dir

    def test_git_clone_fail_with_trace(self):
        cur_dir = os.getcwd()

        with patch('ae.shell.MockedMainApp.verbose', new_callable=PropertyMock, return_value=True):
            assert git_clone("_invalid_repo_", "_invalid_project_name", branch_or_tag="9.99.999") == ""

        assert os.getcwd() == cur_dir

    def test_git_commit_on_changed_repo(self, changed_repo_path, patched_exit_call_wrapper):
        files = set(path_items(os_path_join(changed_repo_path, "**")))

        assert len(patched_exit_call_wrapper(git_commit, changed_repo_path, "")) == 1

        assert files == set(path_items(os_path_join(changed_repo_path, "**")))

        write_file(os_path_join(changed_repo_path, 'tst.py'), "# new test file")
        files = set(path_items(os_path_join(changed_repo_path, "**")))

        assert len(patched_exit_call_wrapper(git_commit, changed_repo_path, "")) == 1

        assert files == set(path_items(os_path_join(changed_repo_path, "**")))

        assert not patched_exit_call_wrapper(git_add, changed_repo_path)

        assert len(patched_exit_call_wrapper(git_commit, changed_repo_path, "")) == 1

        assert files == set(path_items(os_path_join(changed_repo_path, "**")))

        write_file(os_path_join(changed_repo_path, COMMIT_MSG_FILE_NAME), "commit title")

        assert not patched_exit_call_wrapper(git_commit, changed_repo_path, "")

    def test_git_commit_on_empty_repo(self, empty_repo_path, patched_exit_call_wrapper):
        files = set(path_items(os_path_join(empty_repo_path, "**")))
        assert git_uncommitted(empty_repo_path) == {'.gitignore'}

        calls = patched_exit_call_wrapper(git_commit, empty_repo_path, "")

        assert len(calls) == 1
        assert calls[0][0][0] == 381     # (381, err code for missing commit msg file
        assert "commit message" in calls[0][0][1]
        assert set(path_items(os_path_join(empty_repo_path, "**"))) == files
        assert git_uncommitted(empty_repo_path) == {'.gitignore'}

        msg_file = os_path_join(empty_repo_path, COMMIT_MSG_FILE_NAME)
        write_file(msg_file, f"commit message title{os.linesep}{os.linesep}commit message body")
        assert git_uncommitted(empty_repo_path) == {'.gitignore'}

        git_commit(empty_repo_path, "")     # COMMIT without git add of '.gitignore'

        assert git_uncommitted(empty_repo_path) == {'.gitignore'}

        git_add(empty_repo_path)

        git_commit(empty_repo_path, "")

        assert not git_uncommitted(empty_repo_path)

        new_file = os_path_join(empty_repo_path, 'tst.py')
        write_file(new_file, "# new test file")
        git_add(empty_repo_path)
        assert git_uncommitted(empty_repo_path) == {os_path_basename(new_file)}

        git_commit(empty_repo_path, "")

        assert set(path_items(os_path_join(empty_repo_path, "**"))) > files
        assert os_path_isfile(new_file)
        assert not git_uncommitted(empty_repo_path)

    def test_git_current_branch(self, empty_repo_path):
        assert git_current_branch(os_path_dirname(empty_repo_path)) == ""

        assert git_current_branch(empty_repo_path) == DEF_MAIN_BRANCH

    def test_git_diff_on_changed_repo(self, changed_repo_path):
        git_files = git_diff(changed_repo_path, "--name-only")
        assert set(git_files) == {'ChangeD.y', 'deleteD.x', 'rename.it'}

        pth_files = set(path_items(os_path_join(changed_repo_path, "**")))
        assert (set(os_path_relpath(_, changed_repo_path) for _ in pth_files if os_path_isfile(_))
                == {'addEd.ooo', 'ChangeD.y', 'reNamed', 'IgnoreD'})

        compact_output = git_diff(changed_repo_path, "--compact-summary")

        for file in pth_files:
            if os_path_basename(file) in {'addEd.ooo', 'reNamed', 'IgnoreD'}:
                assert os_path_basename(file) not in "".join(compact_output)
            else:
                assert os_path_basename(file) in "".join(compact_output)
        assert pth_files == set(path_items(os_path_join(changed_repo_path, "**")))

        verbose_output = git_diff(changed_repo_path)

        for file in pth_files:
            if os_path_basename(file) in {'addEd.ooo', 'reNamed', 'IgnoreD'}:
                assert os_path_basename(file) not in "".join(verbose_output)
            else:
                assert os_path_basename(file) in "".join(verbose_output)
        assert len("".join(verbose_output)) > len("".join(compact_output))

    def test_git_diff_on_empty_repo(self, empty_repo_path):
        git_files = git_diff(empty_repo_path, "--name-only")
        pth_files = set(path_items(os_path_join(empty_repo_path, "**")))

        assert set(git_files) == set()
        assert set(os_path_relpath(_, empty_repo_path) for _ in pth_files if os_path_isfile(_)) == set()

        assert not git_diff(empty_repo_path)

        assert git_files == git_diff(empty_repo_path, "--name-only")
        assert pth_files == set(path_items(os_path_join(empty_repo_path, "**")))

    def test_git_fetch(self, changed_repo_path, patched_exit_call_wrapper):
        assert git_fetch(changed_repo_path) == []
        assert git_fetch(changed_repo_path, "not_existing_tst_remote")

        assert patched_exit_call_wrapper(git_fetch, changed_repo_path, "not_existing_tst_remote", exit_on_err=True)

    def test_git_init_if_needed(self, tmp_path):
        parent_dir = os_path_join(str(tmp_path), DEF_PROJECT_PARENT_FOLDER)
        project_path = os_path_join(parent_dir, 'tst_git_init_dir')
        os.makedirs(project_path)

        assert git_init_if_needed(project_path, author='TstAuthor SurName', email='tst@email.tst')

        assert os_path_isdir(os_path_join(project_path, GIT_FOLDER_NAME))
        assert not git_uncommitted(project_path)
        assert git_current_branch(project_path) == DEF_MAIN_BRANCH
        assert git_any(project_path, "config", "--get", 'user.name')[0] == 'TstAuthor SurName'
        assert git_any(project_path, "config", "--get", 'user.email')[0] == 'tst@email.tst'

        assert not git_init_if_needed(project_path)  # now this call does nothing and return False because it is created

    def test_git_ls_files_vs_git_status(self, empty_repo_path):
        ls_uncommitted = []
        with in_prj_dir_venv(empty_repo_path):
            sh_exit_if_exec_err(0, "git ls-files -m", lines_output=ls_uncommitted)
        assert ls_uncommitted == []

        st_uncommitted = git_status(empty_repo_path)

        assert st_uncommitted == ['?? .gitignore']
        assert git_uncommitted(empty_repo_path) == {'.gitignore'}

    def test_git_ls_files_vs_git_status_on_changed_repo(self, changed_repo_path):
        ls_uncommitted = []

        with in_prj_dir_venv(changed_repo_path):
            sh_exit_if_exec_err(0, "git ls-files -m", lines_output=ls_uncommitted)

        st_uncommitted = [_[3:] for _ in git_status(changed_repo_path)]

        assert len(ls_uncommitted) >= 2 and 'addEd.ooo' not in ls_uncommitted
        assert all(lsi in st_uncommitted for lsi in ls_uncommitted)

    def test_git_merge(self, changed_repo_path):
        branch, version = 'changes_to_merge', 'new_version999'
        commit_msg = f"git-merge unit test {branch=}"
        changed_file_content = read_file(os_path_join(changed_repo_path, 'ChangeD.y'))
        git_checkout(changed_repo_path, new_branch=branch)
        git_add(changed_repo_path)
        git_tag_add(changed_repo_path, version)
        git_commit(changed_repo_path, version, commit_msg_text=commit_msg)
        git_checkout(changed_repo_path, DEF_MAIN_BRANCH)
        assert read_file(os_path_join(changed_repo_path, 'ChangeD.y')) != changed_file_content

        output = git_merge(changed_repo_path, branch, commit_msg_text=commit_msg)

        assert output
        assert not output[0].startswith(EXEC_GIT_ERR_PREFIX)
        assert output and any("Fast-forward (no commit created; -m option ignored)" in _ for _ in output)
        assert read_file(os_path_join(changed_repo_path, 'ChangeD.y')) == changed_file_content

    def test_git_merge_with_commit_msg_file(self, changed_repo_path):
        branch, version = 'changes_to_merge', 'new_version999'
        changed_file_content = read_file(os_path_join(changed_repo_path, 'ChangeD.y'))
        write_file(os_path_join(changed_repo_path, COMMIT_MSG_FILE_NAME), f"git-merge unit test {branch=}")
        git_checkout(changed_repo_path, new_branch=branch)
        git_add(changed_repo_path)
        git_tag_add(changed_repo_path, version)
        git_commit(changed_repo_path, version)
        git_checkout(changed_repo_path, DEF_MAIN_BRANCH)
        assert read_file(os_path_join(changed_repo_path, 'ChangeD.y')) != changed_file_content

        output = git_merge(changed_repo_path, branch)

        assert output
        assert not output[0].startswith(EXEC_GIT_ERR_PREFIX)
        assert output and any("Fast-forward (no commit created; -m option ignored)" in _ for _ in output)
        assert read_file(os_path_join(changed_repo_path, 'ChangeD.y')) == changed_file_content

    @skip_if_not_maintainer
    def test_git_push(self, cloned_repo_project_dir):
        now = datetime.datetime.now(tz=datetime.timezone.utc)
        version = now.strftime("%y%m%d.%H%M.%S")
        new_branch = f"git_push_unit_test_{version}"
        version_tag = f"v{version}"
        git_checkout(cloned_repo_project_dir, new_branch=new_branch)
        file_content = f"git push unit test {version_tag=}"

        write_file(os_path_join(cloned_repo_project_dir, 'README.md'), file_content)
        write_file(os_path_join(cloned_repo_project_dir, COMMIT_MSG_FILE_NAME), f"git-push unit test {new_branch=}")

        git_add(cloned_repo_project_dir)
        git_tag_add(cloned_repo_project_dir, version_tag)
        git_commit(cloned_repo_project_dir, version_tag)

        output = git_push(cloned_repo_project_dir, mtn_tst_repo_url, "--set-upstream", new_branch, version_tag,
                          exit_on_err=False)

        assert not output or not output[0].startswith(EXEC_GIT_ERR_PREFIX)

        prj_path = git_clone(mtn_tst_root_url, tst_prj_name, branch_or_tag=new_branch)

        assert read_file(os_path_join(prj_path, 'README.md')) == file_content

    def test_git_ref_in_branch(self, changed_repo_path):
        assert not git_ref_in_branch(changed_repo_path, DEF_MAIN_BRANCH)    # branches are not tags

        assert not git_ref_in_branch(changed_repo_path, 'test_tag')
        write_file(os_path_join(changed_repo_path, COMMIT_MSG_FILE_NAME),
                   f"commit message title V{{project_version}}{os.linesep}{os.linesep}commit message body")
        assert not git_tag_add(changed_repo_path, 'test_tag')

        assert not git_ref_in_branch(changed_repo_path, 'test_tag')

        assert git_ref_in_branch(changed_repo_path, 'test_tag', branch=DEF_MAIN_BRANCH)

    def test_git_remote_domain_group(self, empty_repo_path):
        user_name = 'user_name'
        group_name = 'group_name'
        domain_name = 'host.domain'
        uncompleted_url = f"https://auth_usr:auth_pwd@{domain_name}"
        origin_url = f"{uncompleted_url}/{user_name}/project_name"
        upstream_url = f"{uncompleted_url}/{group_name}/project_name"

        dom_nam, usr_nam = git_remote_domain_group(empty_repo_path)

        assert dom_nam == ""
        assert usr_nam == ""

        assert not git_renew_remotes(empty_repo_path, uncompleted_url)

        dom_nam, usr_nam = git_remote_domain_group(empty_repo_path)

        assert dom_nam == domain_name + ".git"
        assert usr_nam == ""

        assert not git_renew_remotes(empty_repo_path, origin_url)

        dom_nam, usr_nam = git_remote_domain_group(empty_repo_path)

        assert dom_nam == domain_name
        assert usr_nam == user_name

        assert not git_renew_remotes(empty_repo_path, origin_url, upstream_url=upstream_url)

        dom_nam, usr_nam = git_remote_domain_group(empty_repo_path)

        assert dom_nam == domain_name
        assert usr_nam == group_name

    def test_git_remotes(self, changed_repo_path):
        origin_url = 'https://host.domain/user_name/project_name.git'
        upstream_url = 'https://host.domain/group_name/project_name.git'

        remotes = git_remotes(changed_repo_path)

        assert not remotes

        assert not git_renew_remotes(changed_repo_path, origin_url, remotes=remotes)

        remotes = git_remotes(changed_repo_path)

        assert len(remotes) == 1
        assert remotes == {GIT_REMOTE_ORIGIN: origin_url}

        assert not git_renew_remotes(changed_repo_path, origin_url, upstream_url=upstream_url, remotes=remotes)

        remotes = git_remotes(changed_repo_path)

        assert len(remotes) == 2
        assert remotes == {GIT_REMOTE_ORIGIN: origin_url, GIT_REMOTE_UPSTREAM: upstream_url}

    def test_git_renew_remotes(self, changed_repo_path):
        remotes = git_remotes(changed_repo_path)
        assert not remotes

        assert not git_renew_remotes(changed_repo_path, 'origin-url',  remotes=remotes)

        new_remotes = git_remotes(changed_repo_path)
        assert GIT_REMOTE_ORIGIN in new_remotes
        assert new_remotes[GIT_REMOTE_ORIGIN] == 'origin-url' + ".git"
        assert GIT_REMOTE_UPSTREAM not in new_remotes

        with in_prj_dir_venv(changed_repo_path):
            sh_exit_if_git_err(42333, "git remote", extra_args=("add", GIT_REMOTE_UPSTREAM, 'upstream-url'))
        new_remotes = git_remotes(changed_repo_path)
        assert GIT_REMOTE_ORIGIN in new_remotes
        assert new_remotes[GIT_REMOTE_ORIGIN] == 'origin-url' + ".git"
        assert GIT_REMOTE_UPSTREAM in new_remotes
        assert new_remotes[GIT_REMOTE_UPSTREAM] == 'upstream-url'

        assert not git_renew_remotes(changed_repo_path, 'new-ori-url', upstream_url='new-up-url', remotes=new_remotes)

        new_remotes = git_remotes(changed_repo_path)
        assert GIT_REMOTE_ORIGIN in new_remotes
        assert new_remotes[GIT_REMOTE_ORIGIN] == 'new-ori-url' + ".git"
        assert GIT_REMOTE_UPSTREAM in new_remotes
        assert new_remotes[GIT_REMOTE_UPSTREAM] == 'new-up-url' + ".git"

        with in_prj_dir_venv(changed_repo_path):
            sh_exit_if_git_err(42333, "git remote", extra_args=("remove", GIT_REMOTE_UPSTREAM))
        new_remotes = git_remotes(changed_repo_path)
        assert GIT_REMOTE_ORIGIN in new_remotes
        assert new_remotes[GIT_REMOTE_ORIGIN] == 'new-ori-url' + ".git"
        assert GIT_REMOTE_UPSTREAM not in new_remotes

        assert not git_renew_remotes(changed_repo_path, 'newer-ori-url', upstream_url='added-up-url',
                                     remotes=new_remotes)

        new_remotes = git_remotes(changed_repo_path)
        assert GIT_REMOTE_ORIGIN in new_remotes
        assert new_remotes[GIT_REMOTE_ORIGIN] == 'newer-ori-url' + ".git"
        assert GIT_REMOTE_UPSTREAM in new_remotes
        assert new_remotes[GIT_REMOTE_UPSTREAM] == 'added-up-url' + ".git"

    def test_git_status_on_changed_repo(self, changed_repo_path):
        files = set(path_items(os_path_join(changed_repo_path, "**")))

        output = git_status(changed_repo_path)
        for file in files:
            if os_path_basename(file) == 'IgnoreD':
                assert os_path_basename(file) not in "".join(output)
            else:
                assert os_path_basename(file) in "".join(output)
        assert files == set(path_items(os_path_join(changed_repo_path, "**")))

        verbose_output = git_status(changed_repo_path, verbose=True)

        assert len(verbose_output) > len(output)
        for file in files:
            if os_path_basename(file) == 'IgnoreD':
                assert os_path_basename(file) not in "".join(output)
            else:
                assert os_path_basename(file) in "".join(verbose_output)

    def test_git_status_on_empty_repo(self, empty_repo_path):
        files = set(path_items(os_path_join(empty_repo_path, "**")))

        assert git_status(empty_repo_path) == ['?? .gitignore']

        assert git_status(empty_repo_path, verbose=True)[-1] == '? .gitignore'

        assert files == set(path_items(os_path_join(empty_repo_path, "**")))

    def test_git_tag_add(self, changed_repo_path):
        assert not git_tag_list(changed_repo_path)
        write_file(os_path_join(changed_repo_path, COMMIT_MSG_FILE_NAME),
                   f"commit message title V{{project_version}}{os.linesep}{os.linesep}commit message body")

        assert not git_tag_add(changed_repo_path, 'tst_tag')

        assert git_tag_list(changed_repo_path) == ['tst_tag']

    def test_git_tag_add_errors(self, changed_repo_path, patched_exit_call_wrapper):
        calls = patched_exit_call_wrapper(git_tag_add, changed_repo_path, 'err_tag')    # error if no commit msg file

        assert len(calls) == 1
        assert calls[0][0][0] == 381    # (381, err code
        assert COMMIT_MSG_FILE_NAME in calls[0][0][1]

        write_file(os_path_join(changed_repo_path, COMMIT_MSG_FILE_NAME), "")

        calls = patched_exit_call_wrapper(git_tag_add, changed_repo_path, 'err2_tag')   # error on EMPTY commit msg file

        assert len(calls) == 1
        assert calls[0][0][0] == 381    # (381, err code
        assert COMMIT_MSG_FILE_NAME in calls[0][0][1]

        write_file(os_path_join(changed_repo_path, COMMIT_MSG_FILE_NAME),
                   f"commit message title V{{project_version}}{os.linesep}{os.linesep}commit message body")

        assert git_tag_add(changed_repo_path, "")       # no exit_error() call, but an error showing git tag usage/help

        assert not git_tag_list(changed_repo_path)

    def test_git_tag_add_other_commit_msg_file(self, changed_repo_path):
        other_msg_file = 'other_commit_msg_file'
        write_file(os_path_join(changed_repo_path, other_msg_file), "commit msg title\n\nbody")

        assert not git_tag_add(changed_repo_path, GIT_VERSION_TAG_PREFIX + '3.66.999', commit_msg_file=other_msg_file)

        assert git_tag_list(changed_repo_path) == [GIT_VERSION_TAG_PREFIX + '3.66.999']
        assert git_tag_list(changed_repo_path, tag_pattern=GIT_VERSION_TAG_PREFIX + "*") == ['v3.66.999']

    def test_git_tag_list(self, changed_repo_path):
        write_file(os_path_join(changed_repo_path, COMMIT_MSG_FILE_NAME),
                   f"commit message title V{{project_version}}{os.linesep}{os.linesep}commit message body")
        assert git_tag_add(changed_repo_path, 'test_xxx_tag') == []

        tag_list = git_tag_list(changed_repo_path)
        assert len(tag_list) == 1
        assert tag_list[0] == 'test_xxx_tag'

        tag_list = git_tag_list(changed_repo_path, tag_pattern="*xxx*")
        assert len(tag_list) == 1
        assert tag_list[0] == 'test_xxx_tag'

        assert git_tag_list(changed_repo_path, remote=GIT_REMOTE_ORIGIN) == []
        assert git_tag_list(changed_repo_path, remote=GIT_REMOTE_UPSTREAM) == []
        with patch('ae.shell.sh_exit_if_git_err', return_value=["ref-id\trefs/heads/branch_name"]):
            assert git_tag_list(changed_repo_path, remote=GIT_REMOTE_UPSTREAM) == ['branch_name']

        assert git_tag_list(changed_repo_path, tag_pattern="*xxx") == []
        assert git_tag_list(changed_repo_path, tag_pattern="xxx*") == []
        assert git_tag_list(changed_repo_path, tag_pattern=GIT_VERSION_TAG_PREFIX + "*") == []

        with patch('ae.shell.sh_exit_if_git_err', return_value=['tst tag lst']):
            assert git_tag_list(changed_repo_path) == ['tst tag lst']

    def test_git_tag_list_errors(self, changed_repo_path):
        assert git_tag_list(os_path_join(changed_repo_path, "..")) == []

        assert git_tag_list(changed_repo_path) == []
        assert git_tag_list(changed_repo_path, tag_pattern=GIT_VERSION_TAG_PREFIX + "*") == []

        assert git_tag_list(changed_repo_path, remote=GIT_REMOTE_ORIGIN) == []
        assert git_tag_list(changed_repo_path, remote=GIT_REMOTE_UPSTREAM) == []
        with patch('ae.shell.sh_exit_if_git_err', return_value=["ref-id\trefs/heads/branch_name"]):
            assert git_tag_list(changed_repo_path, remote=GIT_REMOTE_UPSTREAM) == ['branch_name']

        assert git_tag_list(changed_repo_path, tag_pattern="*xxx") == []
        assert git_tag_list(changed_repo_path, tag_pattern="xxx*") == []
        assert git_tag_list(changed_repo_path, tag_pattern=GIT_VERSION_TAG_PREFIX + "*") == []

        with patch('ae.shell.sh_exit_if_git_err', return_value=[EXEC_GIT_ERR_PREFIX + str(999) + "tst err msg"]):
            assert git_tag_list(changed_repo_path) == []

    def test_git_tag_remotes(self, empty_repo_path):
        assert not git_tag_remotes(empty_repo_path, "*")
        assert not git_tag_remotes(empty_repo_path, "*", remote_names={'ori', 'ups'})

        with (patch('ae.shell.git_remotes', return_value={GIT_REMOTE_ORIGIN: 'any url'}),
              patch('ae.shell.git_any', return_value=[GIT_REMOTE_ORIGIN])):
            assert git_tag_remotes(empty_repo_path, "*") == [GIT_REMOTE_ORIGIN]

    def test_git_uncommitted_no_git_folder_err(self):
        assert git_uncommitted("..") == set()
        assert git_uncommitted("any not existing project path") == set()


class TestHelpers:
    def test_bytes_file_diff(self, tmp_path):
        tst_fil_nam = os_path_join(str(tmp_path), 'tst_fil_nam.tst')
        write_file(tst_fil_nam, b"")
        diff = bytes_file_diff(b"", tst_fil_nam)
        assert not diff

        diff = bytes_file_diff(b'tst-diff-bytes-string', tst_fil_nam, line_sep=" " * 6)
        assert 'tst-diff-bytes-string' in diff

    def test_check_commit_msg_file(self, empty_repo_path):
        file_name = 'any_other_commit_message_file_name.txt'
        file_path = os_path_join(empty_repo_path, file_name)
        write_file(file_path, "test commit message file title\n\n.. and body")

        assert check_commit_msg_file(empty_repo_path, commit_msg_file=file_name) == file_path

        file_path = os_path_join(empty_repo_path, COMMIT_MSG_FILE_NAME)
        write_file(file_path, "test commit message file title\n\n.. and body")

        assert check_commit_msg_file(empty_repo_path) == file_path

    def test_check_commit_msg_file_errors(self, empty_repo_path, patched_exit_call_wrapper):
        tst_command_hint = 'tst_command_hint'

        def _hint_callable():
            pass

        with patch('ae.shell.debug_or_verbose', return_value=True):
            ret = patched_exit_call_wrapper(check_commit_msg_file, empty_repo_path, tst_command_hint, _hint_callable)
        assert len(ret) == 1
        assert os_path_join(empty_repo_path, COMMIT_MSG_FILE_NAME) in ret[0][0][1]  # in 2nd arg == error message
        assert tst_command_hint in ret[0][0][1]
        assert _hint_callable.__name__ in ret[0][0][1]

        ret = patched_exit_call_wrapper(check_commit_msg_file, empty_repo_path, tst_command_hint, _hint_callable)
        assert len(ret) == 1
        assert os_path_join(empty_repo_path, COMMIT_MSG_FILE_NAME) in ret[0][0][1]
        assert tst_command_hint not in ret[0][0][1]
        assert _hint_callable.__name__ not in ret[0][0][1]

    def test_check_if(self, patched_exit_call_wrapper):
        check_if(-69, True, "unused error message")     # no exit_error() call because 2nd arg (check_result) is True

        with patch('ae.shell.MockedMainApp.get_option', return_value=1):
            # no exit_error() call because 'force' app option got patched to be 1/True
            assert not patched_exit_call_wrapper(check_if, -99, False, "error message printed to console")

        err_msg = "error message passed onto exit_error()"
        ret = patched_exit_call_wrapper(check_if, 969, False, err_msg)
        assert len(ret) == 1
        assert ret[0][0][0]     # 1st arg == error code
        assert err_msg in ret[0][0][1]

    def test_debug_or_verbose_with_cons_app_debug(self, cons_app):
        assert debug_or_verbose() is True   # run_app() not called: command line args unparsed and with debug_level set
        assert cons_app.debug_level == DEBUG_LEVEL_VERBOSE
        cons_app.debug_level = DEBUG_LEVEL_ENABLED

        assert debug_or_verbose() is True   # debug level still set

        cons_app.debug_level = DEBUG_LEVEL_DISABLED

        assert debug_or_verbose() is False

        cons_app.add_option('more_verbose', "enables a more verbose console output", UNSET)

        assert debug_or_verbose() is True   # because add_option() call resets _parsed_arguments back to None

        cons_app.parse_arguments()          # parsing args resets debug_level to DEBUG_LEVEL_VERBOSE
        cons_app.debug_level = DEBUG_LEVEL_DISABLED
        assert cons_app.get_option('more_verbose') is False

        assert debug_or_verbose() is False

    def test_debug_or_verbose_with_cons_app_more_verbose(self, cons_app):
        cons_app.add_option('more_verbose', "more_verbose option desc", UNSET)
        cons_app.debug_level = DEBUG_LEVEL_DISABLED

        assert debug_or_verbose() is False

        cons_app.set_option('more_verbose', True, save_to_config=False)

        assert debug_or_verbose() is True

    def test_debug_or_verbose_with_mocked_cons_app(self):
        main_app = get_main_app()
        assert isinstance(main_app, MockedMainApp)
        assert debug_or_verbose() is True  # is always verbose because of MockedMainApp.debug==True

    def test_exit_error(self, cons_app):
        po, show_help, shutdown = cons_app.po, cons_app.show_help, cons_app.shutdown
        try:
            po_args = None

            def _po(*args):
                nonlocal po_args
                po_args = args

            cons_app.po = _po

            called = 0

            def _sh():
                nonlocal called
                called += 1

            cons_app.show_help = _sh

            sd_args = None

            def _sd(*args):
                nonlocal sd_args
                sd_args = args

            cons_app.po = _po
            cons_app.shutdown = _sd

            exit_error(3, "")

            assert po_args is None
            assert called == 1
            assert sd_args == (3, )

            exit_error(6, 'err')

            assert po_args == ('***** err', )
            assert called == 2
            assert sd_args == (6, )

            exit_error(9, "")

            assert po_args == ('***** err', )
            assert called == 3
            assert sd_args == (9, )

            exit_error(123456, "")

            assert po_args == ('***** err', )
            assert called == 3
            assert sd_args == (123456, )

        finally:
            cons_app.po, cons_app.show_help, cons_app.shutdown = po, show_help, shutdown

    def test_get_domain_user_variable_from_cons_app_dotenv(self, cons_app, empty_repo_path):
        var_value = 'ConfVarValue'
        var_name = 'conf_var'
        domain = "tst_host.tst"
        user = "TstUserName"
        prefix = norm_name(camel_to_snake(MAIN_SECTION_NAME)).upper()
        var_name_part = norm_name(camel_to_snake(var_name.lower())).upper()
        domain_part = norm_name(camel_to_snake(domain.lower())).upper()
        user_part = norm_name(camel_to_snake(user.lower())).upper()
        write_file(os_path_join(empty_repo_path, ".env"),
                   f"{prefix}_{var_name_part} = {var_value}\n"
                   f"{prefix}_{var_name_part}_{user_part} = {var_value + user}\n"
                   f"{prefix}_{var_name_part}_AT_{domain_part} = {var_value + domain}\n"
                   f"{prefix}_{var_name_part}_AT_{domain_part}_{user_part} = {var_value + domain + user}\n")

        with in_prj_dir_venv(empty_repo_path):  # load_env_var_defaults(empty_repo_path, os.environ)
            assert get_domain_user_variable(cons_app, var_name) == var_value
            assert get_domain_user_variable(cons_app, var_name, user=user) == var_value + user
            assert get_domain_user_variable(cons_app, var_name, domain=domain) == var_value + domain
            assert get_domain_user_variable(cons_app, var_name, domain=domain, user=user) == var_value + domain + user

        assert get_domain_user_variable(cons_app, var_name) is None
        assert get_domain_user_variable(cons_app, var_name, user=user) is None
        assert get_domain_user_variable(cons_app, var_name, domain=domain) is None
        assert get_domain_user_variable(cons_app, var_name, domain=domain, user=user) is None

    def test_get_domain_user_variable_from_mocked_cons_app_dotenv(self, empty_repo_path):
        main_app = get_main_app()
        var_value = 'ConfVarValue'
        var_name = 'conf_var'
        domain = "tst_host.tst"
        user = "TstUserName"
        prefix = norm_name(camel_to_snake(MAIN_SECTION_NAME)).upper()
        var_name_part = norm_name(camel_to_snake(var_name.lower())).upper()
        domain_part = norm_name(camel_to_snake(domain.lower())).upper()
        user_part = norm_name(camel_to_snake(user.lower())).upper()
        write_file(os_path_join(empty_repo_path, ".env"),
                   f"{prefix}_{var_name_part} = {var_value}\n"
                   f"{prefix}_{var_name_part}_{user_part} = {var_value + user}\n"
                   f"{prefix}_{var_name_part}_AT_{domain_part} = {var_value + domain}\n"
                   f"{prefix}_{var_name_part}_AT_{domain_part}_{user_part} = {var_value + domain + user}\n")
        load_env_var_defaults(empty_repo_path, os.environ)

        assert get_domain_user_variable(main_app, var_name) == var_value
        assert get_domain_user_variable(main_app, var_name, user=user) == var_value + user
        assert get_domain_user_variable(main_app, var_name, domain=domain) == var_value + domain
        assert get_domain_user_variable(main_app, var_name, domain=domain, user=user) == var_value + domain + user

    def test_get_domain_user_variable_from_cons_app_os_env(self, cons_app):
        var_value = 'ConfVarValue'
        var_name = 'conf_var'
        domain = "tst_host.tst"
        user = "TstUserName"
        prefix = norm_name(camel_to_snake(MAIN_SECTION_NAME)).upper()
        var_name_part = norm_name(camel_to_snake(var_name.lower())).upper()
        domain_part = norm_name(camel_to_snake(domain.lower())).upper()
        user_part = norm_name(camel_to_snake(user.lower())).upper()
        os.environ[f'{prefix}_{var_name_part}'] = var_value
        os.environ[f'{prefix}_{var_name_part}_{user_part}'] = var_value + user
        os.environ[f'{prefix}_{var_name_part}_AT_{domain_part}'] = var_value + domain
        os.environ[f'{prefix}_{var_name_part}_AT_{domain_part}_{user_part}'] = var_value + domain + user

        assert get_domain_user_variable(cons_app, var_name) == var_value
        assert get_domain_user_variable(cons_app, var_name, user=user) == var_value + user
        assert get_domain_user_variable(cons_app, var_name, domain=domain) == var_value + domain
        assert get_domain_user_variable(cons_app, var_name, domain=domain, user=user) == var_value + domain + user

    def test_get_domain_user_variable_from_mocked_cons_app_os_env(self):
        main_app = get_main_app()
        var_value = 'ConfVarValue'
        var_name = 'conf_var'
        domain = "tst_host.tst"
        user = "TstUserName"
        prefix = norm_name(camel_to_snake(MAIN_SECTION_NAME)).upper()
        var_name_part = norm_name(camel_to_snake(var_name.lower())).upper()
        domain_part = norm_name(camel_to_snake(domain.lower())).upper()
        user_part = norm_name(camel_to_snake(user.lower())).upper()
        os.environ[f'{prefix}_{var_name_part}'] = var_value
        os.environ[f'{prefix}_{var_name_part}_{user_part}'] = var_value + user
        os.environ[f'{prefix}_{var_name_part}_AT_{domain_part}'] = var_value + domain
        os.environ[f'{prefix}_{var_name_part}_AT_{domain_part}_{user_part}'] = var_value + domain + user

        assert get_domain_user_variable(main_app, var_name) == var_value
        assert get_domain_user_variable(main_app, var_name, user=user) == var_value + user
        assert get_domain_user_variable(main_app, var_name, domain=domain) == var_value + domain
        assert get_domain_user_variable(main_app, var_name, domain=domain, user=user) == var_value + domain + user

    def test_get_main_app_from_cons_app(self, cons_app):
        assert isinstance(cons_app, ConsoleApp)
        main_app = get_main_app()
        assert isinstance(main_app, ConsoleApp)

    def test_get_main_app_from_mocked_app(self):
        main_app = get_main_app()
        assert isinstance(main_app, MockedMainApp)

    def test_get_pypi_versions(self):
        assert get_pypi_versions("") == [""]
        assert get_pypi_versions("non_existing_pypi_package") == [""]
        assert "0.3.54" in get_pypi_versions('ae_base')
        assert "0.3.81" in get_pypi_versions('ae_console')

        assert "0.3.3" in get_pypi_versions('aetst_aetst', pypi_test=True)  # force to use test domain test.pypi.org
        assert get_pypi_versions('aetst_aetst', pypi_test=False) == [""]    # force to use live domain pypi.org

    def test_hint(self):
        def _hint_tst_callable():
            pass

        assert "hint command" in hint("hint command", _hint_tst_callable, "extra message")
        assert _hint_tst_callable.__name__ in hint("hint command", _hint_tst_callable, "extra message")
        assert _hint_tst_callable.__name__ in hint("hint command", _hint_tst_callable.__name__, "extra message")
        assert "extra message" in hint("hint command", _hint_tst_callable, "extra message")

        with patch('ae.shell.debug_or_verbose', return_value=False):
            assert not hint("hint command", _hint_tst_callable, "extra message")
            assert not hint("hint command", _hint_tst_callable.__name__, "extra message")

    def test_owner_project_from_url(self):
        assert owner_project_from_url("owner/project") == "owner/project"
        assert owner_project_from_url("owner/project.git") == "owner/project"
        assert owner_project_from_url("/owner/project") == "owner/project"
        assert owner_project_from_url("//domain.org/owner/project") == "owner/project"
        assert owner_project_from_url("//domain.org/owner/project.git") == "owner/project"
        assert owner_project_from_url("https://domain.org/owner/project.git") == "owner/project"
        assert owner_project_from_url("https://user:password@domain.org/owner/project.git") == "owner/project"

    def test_project_name_version(self):
        pkg, ver = project_name_version('', ['a_b', 'b_c'])
        assert pkg == ""
        assert ver == ""

        pkg, ver = project_name_version('x.z', [])
        assert pkg == ""
        assert ver == ""

        pkg, ver = project_name_version('x.z', ['a_b', 'b_c'])
        assert pkg == ""
        assert ver == ""

        pkg, ver = project_name_version('a.b', ['a_b', 'b_c'])
        assert pkg == 'a_b'
        assert ver == ""

        pkg, ver = project_name_version('a.b', ['bc', 'c_d', 'a_b==1.2.3'])
        assert pkg == 'a_b'
        assert ver == "1.2.3"


RETURN_CODE = 123456789
STDOUT_LINE = b'std___out'
STDERR_LINE = b'std___err'


def subprocess_run_return(*_args, **_kwargs):
    """ mock to simulate subprocess.run return object. """
    class _Return:
        returncode = RETURN_CODE
        stdout = STDOUT_LINE
        stderr = STDERR_LINE
    return _Return()


class TestShellExecuteAndLogging:
    @patch.object(subprocess, 'run', autospec=True)
    def test_sh_exec_args(self, mock_method):
        cmd_line = "cmd arg1 arg2"
        extra_args = ['extra_arg1', 'extra_arg2']

        sh_exec(cmd_line, extra_args)
        mock_method.assert_called_with(
            cmd_line.split(" ") + extra_args, stdout=None, stderr=None, input=b'', check=True, shell=False, env=None)

        sh_exec(cmd_line, extra_args, console_input='con_inp')
        mock_method.assert_called_with(
            cmd_line.split(" ") + extra_args, stdout=None, stderr=None, input=b'con_inp',
            check=True, shell=False, env=None)

        sh_exec(cmd_line, extra_args, lines_output=[])
        mock_method.assert_called_with(
            cmd_line.split(" ") + extra_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, input=b'',
            check=True, shell=False, env=None)

        sh_exec(cmd_line, extra_args, console_input='con_inp', lines_output=[])
        mock_method.assert_called_with(
            cmd_line.split(" ") + extra_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, input=b'con_inp',
            check=True, shell=False, env=None)

        env_vars = {'A': "1", 'C': "tst_string value"}
        sh_exec(cmd_line, extra_args, env_vars=env_vars)
        mock_method.assert_called_with(
            cmd_line.split(" ") + extra_args, stdout=None, stderr=None, input=b'',
            check=True, shell=False, env=env_vars)

    def test_sh_exit_if_exec_err(self, capsys, patched_exit_call_wrapper):
        sh_exit_if_exec_err(693, 'tst_command_line', exit_on_err=False)
        out, err = capsys.readouterr()
        assert 'tst_command_line' in out
        assert err == ""

        ret = patched_exit_call_wrapper(sh_exit_if_exec_err, 693, 'tst_command_line', exit_msg='tst exit message')

        assert len(ret) == 1
        assert ret[0][0][0] == 693    # 1st arg == error code
        assert 'tst_command_line' in ret[0][0][1]
        out, err = capsys.readouterr()
        assert 'tst_command_line' in out
        assert 'tst exit message' in out
        assert err == ""

        output = []
        sh_exit_if_exec_err(693, "", lines_output=output, exit_on_err=False)
        assert not output

    def test_sh_exit_if_git_err_with_trace(self):
        with patch('ae.shell.MockedMainApp.verbose', new_callable=PropertyMock, return_value=True):
            output = sh_exit_if_git_err(0, "git", extra_args=("--version",), exit_on_err=False)
        assert output       # e.g. == ['git version 2.43.0']
        assert len(output) == 1
        assert isinstance(output[0], str)

    @patch.object(subprocess, 'run', new=subprocess_run_return)
    def test_sh_exec_run_returned_values(self):
        cmd_line = "cmd arg1 arg2"
        extra_args = ['extra_arg1', 'extra_arg2']
        lines_output = []

        assert sh_exec(cmd_line, extra_args, lines_output=lines_output) == RETURN_CODE
        assert STDOUT_LINE.decode() in lines_output
        assert STDERR_LINE.decode() in lines_output
        assert sum("STDERR" in _ for _ in lines_output) == 2

    @patch.object(subprocess, 'run', new_callable=subprocess_run_return)
    def test_sh_exec_run_exception(self, _return_obj):
        cmd_line = "cmd arg1 arg2"
        extra_args = ['extra_arg1', 'extra_arg2']
        lines_output = []
        assert sh_exec(cmd_line, extra_args, lines_output=lines_output) == 126     # _Return() is not callable exc

    def test_sh_log_disabled_enabled(self, tmp_path):
        log_dir = str(tmp_path)
        log_file = os_path_join(log_dir, SHELL_LOG_FILE_NAME_SUFFIX)
        log_command = "log file command"

        with in_wd(log_dir):
            sh_log(log_command)

        assert not os_path_isfile(log_file)

        log_files = sh_logs(log_enable_dir=log_dir)

        assert len(log_files) >= 1
        assert log_file in log_files

        with in_wd(log_dir):
            sh_log(log_command)

        assert os_path_isfile(log_file)
        assert log_command in read_file(log_file)

    def test_sh_log_hiding_private_access_token(self, tmp_path):
        log_dir = str(tmp_path)
        log_file = os_path_join(log_dir, SHELL_LOG_FILE_NAME_SUFFIX)
        tok_end = "xyz" + "@gitlab.com"
        token = "glpat-" + "secret-personal_access-token" + tok_end
        log_comment = "# log file comment with token" + token
        sh_logs(log_enable_dir=log_dir)

        with in_wd(log_dir):
            sh_log(log_comment, extra_args=[token, token], cl_err=99, lines_output=token)

        assert os_path_isfile(log_file)
        assert token not in read_file(log_file)
        assert tok_end in read_file(log_file)

    def test_sh_logs(self, tmp_path):
        cmd_dir = str(tmp_path)
        prefix = "LOG_TST"
        log_file = norm_path(os_path_join(cmd_dir, prefix + SHELL_LOG_FILE_NAME_SUFFIX))

        with in_wd(cmd_dir):
            log_files = sh_logs(log_name_prefix=prefix)

        assert log_file not in log_files
        assert len(log_files) == 0

        with in_wd(cmd_dir):
            log_files = sh_logs(log_enable_dir=".", log_name_prefix=prefix)

        assert log_file in log_files
        assert len(log_files) == 1

        home_log = norm_path(os_path_join("~", prefix + SHELL_LOG_FILE_NAME_SUFFIX))
        assert not os_path_isfile(home_log)     # left-over from previous unit test run?
        try:
            with in_wd(cmd_dir):
                log_files = sh_logs(log_enable_dir="~", log_name_prefix=prefix)

            assert log_file in log_files
            assert home_log in log_files
            assert len(log_files) == 2

            with in_wd(cmd_dir):
                log_comment = "# log comment"
                sh_log(log_comment, log_name_prefix=prefix)
                log_files = sh_logs(log_enable_dir=".", log_name_prefix=prefix)  # test 2nd run, keeping old log-entries

            assert log_file in log_files
            assert home_log in log_files
            assert len(log_files) == 2
            assert log_comment in read_file(log_file)
            assert log_comment in read_file(home_log)

            with in_wd(cmd_dir):
                log_files = sh_logs(log_name_prefix=prefix)

            assert log_file in log_files
            assert home_log in log_files
            assert len(log_files) == 2

        finally:
            os.remove(home_log)


class TestTempContextDirectories:
    def test_temp_context_cleanup(self):
        path = temp_context_get_or_create()
        assert path == temp_context_get_or_create()
        assert os_path_isdir(path)

        temp_context_cleanup()
        
        assert not os_path_isdir(path)

        new_path = temp_context_get_or_create()
        assert os_path_isdir(new_path)
        assert new_path != path

        temp_context_cleanup()

        assert not os_path_isdir(new_path)

    def test_temp_context_folders(self):
        folder_name = "tst_tmp_dir"
        path = temp_context_get_or_create(folder_name=folder_name)

        assert path.endswith(folder_name)
        assert set(temp_context_folders()) == {folder_name}

        assert temp_context_folders(context="any not existing context") == []

    def test_temp_context_get_or_create(self):
        path = temp_context_get_or_create()
        assert os_path_isdir(path)
        temp_context_cleanup()

    def test_temp_context_get_or_create_named(self):
        ctx_name = "any string to name a temp dir"

        path = temp_context_get_or_create(context=ctx_name)

        assert os_path_isdir(path)
        temp_context_cleanup()
        assert os_path_isdir(path)
        temp_context_cleanup(context=ctx_name)
        assert not os_path_isdir(path)

    def test_temp_context_get_or_create_with_folder(self):
        dir1 = "name of the first temp dir"
        dir2 = "TempDirFolder2"

        path = temp_context_get_or_create(folder_name=dir1)

        assert path.endswith(dir1)
        assert os_path_isdir(path)

        path2 = temp_context_get_or_create(folder_name=dir2)

        assert path2.endswith(dir2)
        assert os_path_isdir(path)
        assert os_path_isdir(path2)
        assert set(temp_context_folders()) == {dir1, dir2}

        path2a = temp_context_get_or_create(folder_name=dir2)

        assert path2a == path2
        assert path2a.endswith(dir2)
        assert os_path_isdir(path)
        assert os_path_isdir(path2a)
        assert set(temp_context_folders()) == {dir1, dir2}

        temp_context_cleanup()

        assert not os_path_isdir(path)
        assert not os_path_isdir(path2)


@pytest.fixture
def old_and_new_env():
    old_venv = active_venv()
    new_venv = 'aedev312' if old_venv == 'aedev39' else 'aedev39'
    yield old_venv, new_venv


@skip_gitlab_ci             # pyenv not available on GitLab CI
class TestVenv:
    def test_activate_venv(self):
        cur_venv = active_venv()
        activate_venv(LOCAL_VENV)
        assert active_venv() == '' if 'CI_PROJECT_ID' in os.environ else LOCAL_VENV
        if cur_venv:
            activate_venv(cur_venv)
            assert active_venv() == cur_venv

    def test_activate_venv_old_and_new(self, old_and_new_env):
        old_venv, new_venv = old_and_new_env
        try:
            assert activate_venv(name=new_venv) == old_venv
        finally:
            assert activate_venv(name=old_venv) == new_venv

    def test_activate_venv_errors(self, capsys):
        main_app = get_main_app()
        with patch('ae.shell.get_main_app', return_value=main_app), patch('ae.shell.venv_bin_path', return_value=""):
            with patch('ae.shell.active_venv', return_value='mocked_active_venv'):
                venv_name = activate_venv(name='mocked_new_venv')

            assert venv_name == ""
            out, err = capsys.readouterr()
            assert "does not exists - skipping switch from current venv" in out
            assert 'mocked_new_venv' in out
            assert 'mocked_active_venv' in out

            main_app.verbose = True

            with patch('ae.shell.active_venv', return_value=""):
                venv_name = activate_venv(name='new_mocked_venv')

            assert venv_name == ""
            out, err = capsys.readouterr()
            assert "activation skipped" in out
            assert 'new_mocked_venv' in out

        with patch('ae.shell.venv_bin_path', return_value=""):
            assert activate_venv() == ""

        with patch('ae.shell.venv_bin_path', return_value="any_ : invalid : or not existing path"):
            assert activate_venv() == ""

        assert activate_venv(name=active_venv()) == ""

    def test_active_venv(self):
        assert not bool(active_venv()) == 'CI_PROJECT_ID' in os.environ      # active_venv()=='' on gitlab CI

    def test_active_venv_old_and_new(self, old_and_new_env):
        old_venv, new_venv = old_and_new_env
        try:
            activate_venv(name=new_venv)

            assert active_venv() == new_venv
        finally:
            activate_venv(name=old_venv)

    def test_in_os_env_no_dotenv(self, empty_repo_path):
        os_env = os.environ.copy()

        with in_os_env(empty_repo_path) as loaded:
            assert not loaded
            assert os.environ == os_env
        assert os.environ == os_env

    def test_in_os_env_one_dotenv(self, empty_repo_path):
        os_env = os.environ.copy()

        new_var, new_val = 'VarName', 'VarValue'
        exi_var, not_val = 'PATH', 'Existing_Vars_Never_Get_Overwritten'
        exi_val = os.environ.get(exi_var, "")
        assert exi_val, "the PATH env var should exist in all OS (at least in Linux/UNIX/android/iOS/macOS/MS Windows)"
        write_file(os_path_join(empty_repo_path, '.env'),
                   f"{new_var}={new_val}\n"
                   f"{exi_var}={not_val}\n")
        write_file(os_path_join(empty_repo_path, "..", '.env'),
                   f"{new_var}=NotUsedValue_Because_Already_Declared_In_Level0\n"
                   f"# dotenv file comment\n")
        with in_os_env(empty_repo_path) as loaded:
            assert new_var in os.environ
            assert os.environ[new_var] == new_val
            assert os.environ.get(exi_var, "") == exi_val
            assert len(loaded) == 1
            assert loaded[new_var] == new_val
            assert os.environ == os_env | loaded    # | since Python 3.9 (or {**os_env, **loaded} since 3.5+)
        assert new_var not in os.environ
        assert os.environ.get(exi_var, "") == exi_val
        assert os.environ == os_env

    def test_in_os_env_two_dotenvs(self, empty_repo_path):
        os_env = os.environ.copy()

        var1, val1 = 'MixCaseVarName', 'TempOsEnvVarValue'
        var2, val2 = 'LEVEL_1_VARNAME', 'Lev1VarVal'
        var3, val3 = 'PATH', 'Existing_Vars_Never_Get_Overwritten'
        var3_old_val = os.environ.get(var3, "")
        assert var3_old_val
        write_file(os_path_join(empty_repo_path, '.env'),
                   f"{var1}={val1}\n"
                   f"{var3}={val3}\n")
        write_file(os_path_join(empty_repo_path, "..", '.env'),
                   f"{var1}=AlreadyDeclaredInLevel0\n"
                   f"{var2}={val2}\n")
        with in_os_env(empty_repo_path) as loaded:
            assert var1 in os.environ
            assert os.environ[var1] == val1
            assert var2 in os.environ
            assert os.environ[var2] == val2
            assert os.environ.get(var3, "") == var3_old_val
            assert len(loaded) == 2
            assert loaded[var1] == val1
            assert loaded[var2] == val2
            assert os.environ == os_env | loaded
        assert var1 not in os.environ
        assert var2 not in os.environ
        assert os.environ.get(var3, "") == var3_old_val
        assert os.environ == os_env

    def test_in_prj_dir_venv(self, empty_repo_path, old_and_new_env):
        old_venv, new_venv = old_and_new_env

        assert os.getcwd() != empty_repo_path
        assert new_venv not in venv_bin_path().split(os.path.sep)
        with in_prj_dir_venv(project_path=empty_repo_path, venv_name=new_venv):
            assert os.getcwd() == empty_repo_path
            assert new_venv in venv_bin_path().split(os.path.sep)
        assert os.getcwd() != empty_repo_path
        assert new_venv not in venv_bin_path().split(os.path.sep)

    def test_in_venv(self):
        cur_venv = active_venv()
        with in_venv(LOCAL_VENV):
            assert active_venv() == '' if 'CI_PROJECT_ID' in os.environ else LOCAL_VENV
        assert active_venv() == cur_venv

    def test_in_venv_old_and_new(self, old_and_new_env):
        old_venv, new_venv = old_and_new_env
        assert active_venv() == old_venv
        with in_venv(name=new_venv):
            assert active_venv() == new_venv
        assert active_venv() == old_venv

    def test_in_venv_and_local_python_version(self, old_and_new_env):
        old_venv, new_venv = old_and_new_env

        assert active_venv() == old_venv
        with in_venv():
            assert active_venv() == old_venv
        assert active_venv() == old_venv

        assert active_venv() == old_venv
        assert new_venv not in venv_bin_path().split(os.path.sep)
        assert new_venv not in venv_bin_path(name=old_venv).split(os.path.sep)
        with in_venv(name=new_venv):
            assert active_venv() == new_venv
            assert new_venv not in venv_bin_path().split(os.path.sep)
            assert new_venv in venv_bin_path(name=new_venv).split(os.path.sep)
        assert active_venv() == old_venv
        assert new_venv not in venv_bin_path().split(os.path.sep)
        assert new_venv not in venv_bin_path(name=old_venv).split(os.path.sep)

    def test_venv_bin_path_ae_shell(self):
        curr_venv = active_venv()

        assert venv_bin_path(name=curr_venv) == os_path_join(os.getenv('PYENV_ROOT'), 'versions', curr_venv, 'bin')

        with patch('ae.shell.os_path_isfile', return_value=False):
            assert venv_bin_path() == os_path_join(os.getenv('PYENV_ROOT'), 'versions', curr_venv, 'bin')

        with patch('ae.shell.os_path_isfile', return_value=False), patch('ae.shell.active_venv', return_value=""):
            assert venv_bin_path() == ""

        filed_venv = read_file('.python-version').split(os.linesep)[0]
        assert venv_bin_path() == os_path_join(os.getenv('PYENV_ROOT'), 'versions', filed_venv, 'bin')

        any_venv = 'any_tst_venv_name'
        with patch('ae.shell.read_file', return_value=any_venv), patch('ae.shell.os_path_isdir', return_value=True):
            assert venv_bin_path() == os_path_join(os.getenv('PYENV_ROOT'), 'versions', any_venv, 'bin')

    def test_venv_bin_path_with_python_version_file_in_parent_dirs(self, empty_repo_path):
        any_venv = 'above_tst_venv_name'
        write_file(os_path_join(empty_repo_path, '.python-version'), any_venv)
        with in_wd(empty_repo_path):
            for dir_deepness in range(1, 6):
                sub_dir = 'sub_dir' + str(dir_deepness)
                os.mkdir(sub_dir)
                os.chdir(sub_dir)

                with patch('ae.shell.os_path_isdir', return_value=True):
                    assert venv_bin_path() == os_path_join(os.getenv('PYENV_ROOT'), 'versions', any_venv, 'bin')

    def test_venv_bin_path_errors(self, monkeypatch):
        curr_venv = active_venv()

        assert venv_bin_path(name=curr_venv) == os_path_join(os.getenv('PYENV_ROOT'), 'versions', curr_venv, 'bin')

        monkeypatch.delenv('PYENV_ROOT', raising=False)
        assert venv_bin_path() == ""


class TestMockedMainApp:
    def test_app_instance(self):
        main_app = get_main_app()

        assert isinstance(main_app, MockedMainApp)

        assert main_app.debug is True
        assert main_app.verbose is False

        assert callable(main_app.po)
        assert callable(main_app.dpo)
        assert callable(main_app.vpo)
        assert callable(main_app.get_option)
        assert callable(main_app.get_argument)
        assert callable(main_app.get_variable)
        assert callable(main_app.set_option)
        assert callable(main_app.set_variable)
        assert callable(main_app.show_help)
        assert callable(main_app.shutdown)

        assert debug_or_verbose() is True  # is always verbose because of MockedMainApp.debug==True

    def test_get_main_app_from_mocked_cons_app(self):
        main_app = get_main_app()
        assert isinstance(main_app, MockedMainApp)

    def test_get_option(self, capsys):
        main_app = get_main_app()
        main_app.verbose = True

        assert main_app.get_option('force') is False
        assert main_app.get_option('name_of_opt') is True
        assert main_app.get_option('name_of_opt', default_value='value_of_opt') == 'value_of_opt'

        out, err = capsys.readouterr()
        assert str(main_app) in out
        assert 'name_of_opt' in out
        assert 'force' in out
        assert err == ""

    def test_get_variable(self, capsys, monkeypatch):
        main_app = get_main_app()
        main_app.verbose = True
        monkeypatch.setenv("AE_OPTIONS_NAME_OF_VAR", 'value_of_var')

        ret = main_app.get_variable('name_of_var')

        assert ret == 'value_of_var'
        out, err = capsys.readouterr()
        assert err == "" and str(main_app) in out and 'name_of_var' in out

    def test_show_help(self, capsys):
        main_app = get_main_app()

        main_app.show_help()

        out, err = capsys.readouterr()
        assert err == "" and str(main_app) in out
