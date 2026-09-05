""" ae.shell unit tests """
import os
import shlex
import sys
import subprocess
from unittest.mock import PropertyMock, patch

from ae.base import UNSET, camel_to_snake, norm_name, os_path_join, write_file
from ae.system import load_env_var_defaults, os_env_venv
from ae.core import DEBUG_LEVEL_DISABLED, DEBUG_LEVEL_ENABLED, DEBUG_LEVEL_VERBOSE
from ae.console import MAIN_SECTION_NAME, ConsoleApp


from ae.shell import (
    STDERR_BEG_MARKER, STDERR_END_MARKER,
    debug_or_verbose, get_domain_user_var, hint, in_os_env, mask_token,
    output_line_split, output_zero_split, sh_exec, sh_exit_if_exec_err)


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
            # noinspection PyTypeChecker
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
            # noinspection PyTypeChecker
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


class TestShellExecutions:
    def test_output_line_split(self):
        assert output_line_split(STDOUT_LINE) == [STDOUT_LINE.decode()]

        assert output_line_split(STDOUT_LINE + b"\n" + STDERR_LINE + b"\n") == [STDOUT_LINE.decode(),
                                                                                STDERR_LINE.decode()]

        assert output_line_split(STDOUT_LINE + b"\n\0" + STDERR_LINE + b"\0") == [
            STDOUT_LINE.decode(), "\0" + STDERR_LINE.decode() + "\0"]

        assert output_line_split(STDOUT_LINE + b"\r" + STDERR_LINE + b"\r\n\r\0\r") == [
            STDOUT_LINE.decode(), STDERR_LINE.decode(), "\0"]

    def test_output_zero_split(self):
        assert output_zero_split(STDOUT_LINE) == [STDOUT_LINE.decode()]

        assert output_zero_split(STDOUT_LINE + b"\0" + STDERR_LINE + b"\0") == [STDOUT_LINE.decode(),
                                                                                STDERR_LINE.decode()]

        assert output_zero_split(STDOUT_LINE + b"\0" + STDERR_LINE + b" = multi\nval\rlines\r\n" + STDERR_LINE) == [
            STDOUT_LINE.decode(), STDERR_LINE.decode() + " = multi\nval\rlines\r\n" + STDERR_LINE.decode()]

        assert output_zero_split(STDOUT_LINE + b"\n" + STDERR_LINE + b"\r\n\r\0\r") == [
            STDOUT_LINE.decode() + "\n" + STDERR_LINE.decode() + "\r\n\r"]

    def test_sh_exec_catch_any_exception(self, capsys):
        with patch("subprocess.run", side_effect=Exception('broad tst exception')):
            assert sh_exec('any_cmd') == (126, )[0]

        output = capsys.readouterr().out
        assert 'any_cmd' in output
        assert " raised exception " in output
        assert 'broad tst exception' in output

    def test_sh_exec_catch_exit_code_exception(self, capsys):
        assert sh_exec("exit 69", shell=True) == 69

        output = capsys.readouterr().out
        assert " returned non-zero exit code " in output

        assert sh_exec(sys.executable, extra_args=["-c", "import sys; sys.exit(96)"]) == 96

        output = capsys.readouterr().out
        assert " returned non-zero exit code 96" in output

    def test_sh_exec_console_output(self, capsys, cons_app):
        sh_exec('any command')

        out, err = capsys.readouterr()
        assert "    . executing ['any', 'command']" in out
        assert os.getcwd() in out
        assert os_env_venv() in out
        assert "****  subprocess.run(['any', 'command']) raised exception" in out
        assert err == ""

        with patch('ae.console.ConsoleApp.debug_level', new_callable=PropertyMock, return_value=DEBUG_LEVEL_DISABLED):
            sh_exec('any command')

        out, err = capsys.readouterr()
        assert "    . executing" not in out
        assert "****  subprocess.run(['any', 'command']) raised exception" in out
        assert err == ""

        with patch('ae.console.ConsoleApp.debug_level', new_callable=PropertyMock, return_value=DEBUG_LEVEL_DISABLED):
            sh_exec('any command', app_obj=cons_app)    # strange: patch('ae.core.AppBase.debug_level') does not work

        out, err = capsys.readouterr()
        assert "    . executing" not in out
        assert "****  subprocess.run(['any', 'command']) raised exception" in out
        assert err == ""

        sh_exec('any command', app_obj=UNSET)

        out, err = capsys.readouterr()
        assert out == ""
        assert err == ""

    def test_sh_exec_console_output_shell(self, capsys):
        ret = sh_exec("echo hello world", shell=True)

        out, err = capsys.readouterr()
        assert ret == 0
        assert "    . executing echo hello world at " in out
        assert out.count("hello world") == 1   # strange: capsys does not get the echo command output w/ shell=True arg
        assert err == ""

        ret = sh_exec("echo hello world", app_obj=UNSET, shell=True)

        out, err = capsys.readouterr()
        assert ret == 0
        assert out == ""
        assert err == ""

    @patch.object(subprocess, 'run', autospec=True)
    def test_sh_exec_run_args(self, mock_method):
        cmd_line = "cmd arg1 arg2"
        extra_args = ['extra_arg1', 'extra_arg2']
        env = os.environ.copy()

        sh_exec(cmd_line, tuple(extra_args))

        mock_method.assert_called_with(
            shlex.split(cmd_line) + extra_args, stdout=None, stderr=None, input=b'', check=True, shell=False, env=env)

        sh_exec(cmd_line, shell=True)

        mock_method.assert_called_with(
            cmd_line, stdout=None, stderr=None, input=b'', check=True, shell=True, env=env)

        sh_exec(cmd_line, {_: "any" for _ in extra_args}, shell=True, err_redirect=subprocess.DEVNULL)

        mock_method.assert_called_with(
            cmd_line + " " + " ".join(extra_args), stdout=None, stderr=subprocess.DEVNULL, input=b'', check=True,
            shell=True, env=env)

        sh_exec(cmd_line, extra_args, console_input='con_inp')

        mock_method.assert_called_with(
            shlex.split(cmd_line) + extra_args, stdout=None, stderr=None, input=b'con_inp',
            check=True, shell=False, env=env)

        sh_exec(cmd_line, extra_args, output_lines=[])

        mock_method.assert_called_with(
            shlex.split(cmd_line) + extra_args, stdout=subprocess.PIPE, stderr=None, input=b'',
            check=True, shell=False, env=env)

        sh_exec(cmd_line, extra_args, console_input='con_inp', output_lines=[], err_redirect=subprocess.STDOUT)

        mock_method.assert_called_with(
            shlex.split(cmd_line) + extra_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, input=b'con_inp',
            check=True, shell=False, env=env)

        env_vars = {'A': "1", 'C': "tst_string value"}

        sh_exec(cmd_line, extra_args, env_vars=env_vars)

        mock_method.assert_called_with(
            shlex.split(cmd_line) + extra_args, stdout=None, stderr=None, input=b'',
            check=True, shell=False, env=env_vars)

        sh_exec(cmd_line, extra_args, env_vars=None)

        mock_method.assert_called_with(
            shlex.split(cmd_line) + extra_args, stdout=None, stderr=None, input=b'',
            check=True, shell=False, env=None)

    def test_sh_exec_run_returned_values(self):
        def _run_return(*_args, **_kwargs):
            """ mock to simulate subprocess.run return object. """
            class _Return:
                returncode = RETURN_CODE
                stdout = STDOUT_LINE
                stderr = STDERR_LINE
            return _Return()

        with patch('ae.shell.subprocess.run', new=_run_return):  # @patch.object(subprocess, 'run', new=_run_return)
            output_lines = []

            assert sh_exec("cmd_line", output_lines=output_lines, err_redirect=subprocess.PIPE) == RETURN_CODE

            assert output_lines[0] == STDOUT_LINE.decode()
            assert output_lines[1] == STDERR_BEG_MARKER
            assert output_lines[2] == STDERR_LINE.decode()
            assert output_lines[3] == STDERR_END_MARKER

            output_lines = []

            assert sh_exec("cmd_line", output_lines=output_lines) == RETURN_CODE

            assert len(output_lines) == 1
            assert output_lines[0] == STDOUT_LINE.decode()
            assert STDERR_LINE.decode() not in output_lines
            assert STDERR_BEG_MARKER not in output_lines
            assert STDERR_END_MARKER not in output_lines

            output_lines = ['first line', 'second line']

            assert sh_exec("cmd_line", output_lines=output_lines, err_redirect=subprocess.STDOUT) == RETURN_CODE

            assert len(output_lines) == 3
            assert output_lines[0] == 'first line'
            assert output_lines[1] == 'second line'
            assert output_lines[2] == STDOUT_LINE.decode()
            assert STDERR_LINE.decode() not in output_lines
            assert STDERR_BEG_MARKER not in output_lines
            assert STDERR_END_MARKER not in output_lines

    def test_sh_exec_stderr_redirection(self, capfd, cons_app):  # pytest/capsys replaces sys.stdout/.stderr
        args = {'command_line': sys.executable,
                'extra_args': ["-c", "import sys; print('tst_std_err', file=sys.stderr); print('tst_std_out')"]}

        assert sh_exec(**args) == 0

        out, err = capfd.readouterr()
        assert out.count('tst_std_out') == 2
        assert out.endswith("\n" + 'tst_std_out' + "\n")
        assert err == 'tst_std_err' + "\n"

        redirected = []

        assert sh_exec(**args, output_lines=redirected) == 0

        out, err = capfd.readouterr()
        assert out.count('tst_std_out') == 1
        assert not out.endswith("\n" + 'tst_std_out' + "\n")
        assert err == 'tst_std_err' + "\n"
        assert redirected == ['tst_std_out']

        redirected = []

        assert sh_exec(**args, output_lines=redirected, err_redirect=subprocess.DEVNULL) == 0

        out, err = capfd.readouterr()
        assert err == ''
        assert redirected == ['tst_std_out']

        redirected = []

        assert sh_exec(**args, output_lines=redirected, err_redirect=subprocess.PIPE) == 0

        out, err = capfd.readouterr()
        assert err == ''
        assert redirected == ['tst_std_out', STDERR_BEG_MARKER, 'tst_std_err', STDERR_END_MARKER]

        redirected = []

        assert sh_exec(**args, output_lines=redirected, err_redirect=subprocess.STDOUT) == 0

        out, err = capfd.readouterr()
        assert err == ''
        assert redirected == ['tst_std_err', 'tst_std_out']

    def test_sh_exit_if_exec_err_any_command(self, capsys, cons_app):
        output = ['old output']

        with patch('ae.console.ConsoleApp.debug', new_callable=PropertyMock, return_value=True):  # with app_obj kwarg
            ret = sh_exit_if_exec_err(0, 'git --version', output_lines=output,
                                      exit_on_err=False, exit_msg='tst exit message', app_obj=cons_app)

        assert ret == 0
        assert len(output) >= 2
        assert output[0] == 'old output'
        assert isinstance(output[1], str)   # e.g. == 'git version 2.55.0'
        out, err = capsys.readouterr()
        assert 'old output' not in out
        assert 'git --version' in out
        assert 'tst exit message' not in out
        assert err == ""

    def test_sh_exit_if_exec_err_any_invalid_command(self, capsys, cons_app, patched_shutdown_wrapper):
        ret = sh_exit_if_exec_err(693, 'tst_command_line', exit_on_err=False, exit_msg='tst exit message')

        assert ret == (126, )[0]
        out, err = capsys.readouterr()
        assert out.count('tst_command_line') == 3
        assert 'tst exit message' in out
        assert err == ""

    def test_sh_exit_if_exec_err_caught_shutdown_exception(self, capsys, cons_app, patched_shutdown_wrapper):
        ret = patched_shutdown_wrapper(sh_exit_if_exec_err, 693, 'tst_command_line', exit_msg='tst exit message')

        assert len(ret) == 1
        assert ret[0]['exit_code'] == 693    # 1st arg == error code
        assert 'tst_command_line' in ret[0]['error_message']
        assert 'sh_exit_if_exec_err(' in ret[0]['error_message']
        assert "(693, " in ret[0]['error_message']
        out, err = capsys.readouterr()
        assert out.count('tst_command_line') == 3
        assert 'tst exit message' in out
        assert err == ""

    def test_sh_exit_if_exec_err_exception(self, capsys, cons_app):
        output = ['old output']

        ret = sh_exit_if_exec_err(693, "", output_lines=output, exit_on_err=False, exit_msg='tst exit message')

        assert ret == (126, )[0]
        assert output == ['old output']
        out, err = capsys.readouterr()
        assert f". executing [] at os.getcwd()='{os.getcwd()}' in os_env_venv()='{os_env_venv()}'" in out
        assert 'tst exit message' in out
        assert err == ""

    def test_sh_exit_if_exec_err_with_app(self, capsys, cons_app):
        output = []

        with patch('ae.console.ConsoleApp.debug', new_callable=PropertyMock, return_value=False):
            ret = sh_exit_if_exec_err(0, "_err", output_lines=output, exit_on_err=False, err_redirect=subprocess.STDOUT)

        assert ret == (126, )[0]
        assert output == []
        out, err = capsys.readouterr()
        assert out.count('_err') == 3
        assert err == ""

    def test_sh_exit_if_exec_err_with_app_kwarg_and_exit_msg(self, capsys, cons_app):
        output = []

        with patch('ae.console.ConsoleApp.debug', new_callable=PropertyMock, return_value=True):  # with app_obj kwarg
            ret = sh_exit_if_exec_err(0, 'error-command', output_lines=output,
                                      exit_on_err=False, exit_msg='tst exit message', app_obj=cons_app)

        assert ret == (126, )[0]
        assert output == []
        out, err = capsys.readouterr()
        assert out.count('error-command') == 3
        assert 'tst exit message' in out
        assert err == ""

    def test_sh_exit_if_exec_err_with_app_extending_output(self, capsys, cons_app):
        output = ['any old line output']

        with (patch('ae.shell.sh_exec', new=lambda *_, **kwargs: kwargs['output_lines'].append('new out line') or 0),
              patch('ae.console.ConsoleApp.debug', new_callable=PropertyMock, return_value=True)):
            ret = sh_exit_if_exec_err(369, "any_cmd", output_lines=output)  # extended output_lines and ret==0

        assert ret == 0
        assert output == ['any old line output', 'new out line']
        out, err = capsys.readouterr()
        assert 'any old line output' not in out
        assert 'new out line' in out
        assert '    = successfully executed command' in out
        assert out.count('any_cmd') == 1
        assert err == ""

    def test_sh_exit_if_exec_err_without_app(self, capsys):
        output = []

        ret = sh_exit_if_exec_err(0, "_err_cmd", output_lines=output, exit_on_err=False, exit_msg='tst exit message')

        assert ret == (126, )[0]
        assert output == []
        out, err = capsys.readouterr()
        assert out.count('_err_cmd') == 3
        assert 'tst exit message' not in out
        assert err == ""
