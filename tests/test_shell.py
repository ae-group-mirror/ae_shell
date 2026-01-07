""" ae.shell unit tests """
from unittest.mock import PropertyMock, patch

from ae.base import camel_to_snake, os_path_join, write_file
from ae.core import DEBUG_LEVEL_DISABLED, DEBUG_LEVEL_ENABLED, DEBUG_LEVEL_VERBOSE


from ae.shell import *


class TestHelpers:
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

    def test_debug_or_verbose_with_mocked_cons_app(self, cons_app):
        assert isinstance(cons_app, ConsoleApp)
        assert debug_or_verbose(app_obj=cons_app) is True

    def test_get_domain_user_var_from_cons_app_dotenv(self, cons_app, tmp_path):
        empty_repo_path = str(tmp_path)
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

        with in_os_env(empty_repo_path):  # load_env_var_defaults(empty_repo_path, os.environ)
            assert get_domain_user_var(var_name) == var_value
            assert get_domain_user_var(var_name, user=user) == var_value + user
            assert get_domain_user_var(var_name, domain=domain) == var_value + domain
            assert get_domain_user_var(var_name, domain=domain, user=user) == var_value + domain + user

        assert get_domain_user_var(var_name) is None
        assert get_domain_user_var(var_name, user=user) is None
        assert get_domain_user_var(var_name, domain=domain) is None
        assert get_domain_user_var(var_name, domain=domain, user=user) is None

    def test_get_domain_user_var_from_cons_app_fixture_dotenv(self, cons_app, tmp_path):
        empty_repo_path = str(tmp_path)
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

        assert get_domain_user_var(var_name) == var_value
        assert get_domain_user_var(var_name, user=user) == var_value + user
        assert get_domain_user_var(var_name, domain=domain) == var_value + domain
        assert get_domain_user_var(var_name, domain=domain, user=user) == var_value + domain + user

    def test_get_domain_user_var_from_cons_app_os_env(self, cons_app):
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

        assert get_domain_user_var(var_name) == var_value
        assert get_domain_user_var(var_name, user=user) == var_value + user
        assert get_domain_user_var(var_name, domain=domain) == var_value + domain
        assert get_domain_user_var(var_name, domain=domain, user=user) == var_value + domain + user

    def test_get_domain_user_var_from_mocked_cons_app_os_env(self, cons_app):
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

        assert get_domain_user_var(var_name) == var_value
        assert get_domain_user_var(var_name, user=user) == var_value + user
        assert get_domain_user_var(var_name, domain=domain) == var_value + domain
        assert get_domain_user_var(var_name, domain=domain, user=user) == var_value + domain + user

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

    def test_in_os_env_no_dotenv(self, tmp_path):
        empty_repo_path = str(tmp_path)
        os_env = os.environ.copy()

        with in_os_env(empty_repo_path) as loaded:
            assert not loaded
            assert os.environ == os_env
        assert os.environ == os_env

    def test_in_os_env_one_dotenv(self, tmp_path):
        empty_repo_path = str(tmp_path)
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

    def test_in_os_env_two_dotenvs(self, tmp_path):
        empty_repo_path = str(tmp_path)

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

    def test_mask_token(self):
        url_prefix_str = "https://"  # PDV_REPO_HOST_PROTOCOL

        token = "codeberg token does not have a prefix and only contains hex-digits followed by @ and codeberg.org"
        text = f"a text block containing a codeberg URL with a token: {url_prefix_str}UsaNäm:{token}@codeberg.org"

        assert token not in mask_token(text)
        assert token not in mask_token([text])[0]
        assert mask_token(text).count('codeberg.org') == 1
        assert mask_token(text).count(':') == 3

        token = "glpat-gitlab token format ending at the @/ampersand directly followed by the gitlab.com domain"
        text = "a text block containing a gitlab URL with a glpat-token: https://UsaNäm:" + token + "@gitlab.com"

        assert token not in mask_token(text)
        assert token not in mask_token([text])[0]
        assert mask_token(text).count('gitlab.com') == 1
        assert mask_token(text).count('glpat-') == 1

        token = "ghp_-github token format ending at the @/ampersand directly followed by the github.com domain"
        text = "a text block containing a github URL with a ghp_-token: https://YouSaNem:" + token + "@github.com"

        assert token not in mask_token(text)
        assert token not in mask_token([text])[0]
        assert mask_token(text).count('github.com') == 1
        assert mask_token(text).count('ghp_') == 1

        text = "NO masking if @codeberg.org/@github.com/@gitlab.com domains before token start str ':', ghp_ or glpat-:"

        assert mask_token(text) == text     # neither throws str.index()-ValueError nor stuck in endless-loop


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

    def test_sh_exit_if_git_err_with_trace(self, cons_app):
        output = []
        with patch('ae.console.ConsoleApp.verbose', new_callable=PropertyMock, return_value=True):
            _err = sh_exit_if_exec_err(0, "git", extra_args=("--version",), lines_output=output, exit_on_err=False)

        assert output       # e.g. == ['git version 2.43.0']
        assert len(output) == 1
        assert isinstance(output[0], str)

        # with explicit app_obj kwarg
        output = []
        with patch('ae.console.ConsoleApp.verbose', new_callable=PropertyMock, return_value=True):
            _err = sh_exit_if_exec_err(0, "git", extra_args=("--version",), lines_output=output, exit_on_err=False,
                                       app_obj=cons_app)

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

    def test_sh_exit_if_exec_err(self, capsys, cons_app, patched_shutdown_wrapper):
        sh_exit_if_exec_err(693, 'tst_command_line', exit_on_err=False)
        out, err = capsys.readouterr()
        assert 'tst_command_line' in out
        assert err == ""

        ret = patched_shutdown_wrapper(sh_exit_if_exec_err, 693, 'tst_command_line', exit_msg='tst exit message')

        assert len(ret) == 1
        assert ret[0]['exit_code'] == 693    # 1st arg == error code
        assert 'tst_command_line' in ret[0]['error_message']
        out, err = capsys.readouterr()
        assert 'tst_command_line' in out
        assert 'tst exit message' in out
        assert err == ""

        output = []
        sh_exit_if_exec_err(693, "", lines_output=output, exit_on_err=False)
        assert not output

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
