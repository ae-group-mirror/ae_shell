"""
shell execution and environment helpers
=======================================

.. hint::
    this module is designed to provide a comprehensive set of constants and helper functions
    for executing and managing external shell commands.

- :func:`debug_or_verbose`: checks if the application is running in debug or verbose mode.
- :func:`get_domain_user_var`: retrieves an OS environment variable value for a specific domain and/or user.
- :func:`hint`: provides a hint message based on the provided arguments.
- :func:`in_os_env`: context manager to temporarily add environment variables from the dotenv files that not exist
  in os.environ to it.
- :func:`mask_token`: hide/mask tokens in a text block, to prevent to show them in logs or error messages.
- :func:`sh_exec`: generic/fundamental function for all other shell execution helpers.
- :func:`sh_exit_if_exec_err`: extended version of :func:`sh_exec` with automatically checks for errors
  after a command is executed and handles application termination gracefully.

- :data:`STDERR_BEG_MARKER`: marker used in the console output for the beginning of stderr output.
- :data:`STDERR_END_MARKER`: marker used in the console output for the end of stderr output.
"""
import os
import shlex
import subprocess

from contextlib import contextmanager
from typing import Any, Callable, Iterable, Iterator, MutableMapping, Optional, Union, cast, overload

from ae.base import UNSET, dummy_function, env_str, load_env_var_defaults, norm_name        # type: ignore
from ae.core import main_app_instance, AppBase                                              # type: ignore
from ae.console import MAIN_SECTION_NAME, ConsoleApp                                        # type: ignore


__version__ = '0.3.12'


STDERR_BEG_MARKER = "vvv   STDERR   vvv"                #: :paramref:`ae.shell.sh_exec.lines_output` begin stderr lines
STDERR_END_MARKER = "^^^   STDERR   ^^^"                #: end stderr lines in :paramref:`ae.shell.sh_exec.lines_output`


def debug_or_verbose(app_obj: Optional[ConsoleApp] = None) -> bool:
    """ determine if the current app runs in debug|verbose mode, while preventing early .get_option() call an app init.

    :param app_obj:             optional ConsoleApp instance (def=main_app_instance()).
    :return:                    a boolean False when the main app debug level is :data:`~ae.core.DEBUG_LEVEL_DISABLED`
                                and the app option 'more_verbose' is not specified (in cfg-file or at the command line),
                                else True.

    .. note:: the return value on app startup/initialization, before the command line parsing, is always True.

    .. hint::
        the debug mode can be activated via the :class:`~ae.console.ConsoleApp` option `debug_level`, specified either
        in a config file or via the command line options. the verbose mode get activated via the `more_verbose`  option.
    """
    app_obj = app_obj or main_app_instance()
    # noinspection PyProtectedMember
    return bool(
        not app_obj                                     # prevent exception in early app startup and in test runs
        or app_obj.debug                                # main_app.debug_level > DEBUG_LEVEL_DISABLED
        or not app_obj._parsed_arguments                # pylint: disable=protected-access
        or app_obj.get_option('more_verbose'))          # optional app option


def get_domain_user_var(variable_name: str, domain: str = "", user: str = "") -> Any:
    """ determine the value of an OS environment variable for a specific domain and/or username.

    :param variable_name:       name of the config variable.
    :param domain:              name of the domain.
    :param user:                name/id of the user to get a user-specific value of.
    :return:                    domain/user-specific value of the specified config variable.
    """
    parts = (MAIN_SECTION_NAME, variable_name.lower(), f'AT_{norm_name(domain)}'.lower(), norm_name(user).lower())
    value = None
    if domain:
        if user:
            value = env_str('_'.join(parts), convert_name=True)
        if value is None:
            value = env_str('_'.join(parts[:-1]), convert_name=True)
    elif user:
        value = env_str('_'.join(parts[:2] + parts[-1:]), convert_name=True)

    if value is None:
        value = env_str('_'.join(parts[:2]), convert_name=True)

    return value


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


@overload
def mask_token(text: str) -> str: ...


@overload
def mask_token(text: list[str]) -> list[str]: ...


def mask_token(text: Union[str, list[str]]) -> Union[str, list[str]]:
    """ hide most parts of any Codeberg/GitHub/GitHub URL tokens found in the specified text/-lines.

    :param text:                text, specified either as str object or as a list of str objects (lines),
                                each str/line get searched for URL tokens, to hide/mask the most part of them.
    :return:                    text with masked URL tokens (only leaving the first/last 3 token characters unmasked).

    .. note:: see also :func:`ae.base.mask_url` of a more generic way to hide passwords and tokens in URLs.
    """
    if is_str_arg := isinstance(text, str):
        lines = [text]
    else:
        lines = list(text)  # copy to not change text list content

    url_beg = 'https://'  # PDV_REPO_HOST_PROTOCOL
    url_beg_len = len(url_beg)
    for tok_beg, tok_end in ((':', '@codeberg.org'), ('glpat-', '@gitlab.com'), ('ghp_', '@github.com')):
        for idx, line in enumerate(lines):
            beg = -1
            while ((beg := line.find(url_beg, beg + 1)) != -1 and
                   (beg := line.find(tok_beg, beg + url_beg_len)) != -1 and
                   (end := line.find(tok_end, beg)) != -1):
                line = line[:beg + 3] + "***-masked-token-***" + line[end - 3:]
            lines[idx] = line

    return lines[0] if is_str_arg else lines


# pylint: disable-next=too-many-arguments,too-many-positional-arguments
def sh_exec(command_line: str, extra_args: Iterable[str] = (), console_input: str = "",
            lines_output: Optional[list[str]] = None, app_obj: Optional[AppBase] = None, shell: bool = False,
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
    :param app_obj:             optional :class:`~ae.core.AppBase`/:class:`~ae.console.ConsoleApp` instance, used for
                                logging. if not specified or None and if :func:`~ae.core.main_app_instance()` returns
                                None then the Python :func:`print` function is used.
                                specify :data:`~ae.base.UNSET` to suppress any printing/logging output.
    :param shell:               pass True to execute command in the default OS shell (see :meth:`subprocess.run`).
    :param env_vars:            OS shell environment variables to be used instead of the console/bash defaults.
    :return:                    return code of the executed command or 126 if execution raised any other exception.
    """
    args = command_line + " " + " ".join(extra_args) if shell else shlex.split(command_line) + list(extra_args)
    ret_out = lines_output is not None  # == isinstance(lines_output, list)
    merge_err = bool(lines_output)      # == -''- and len(lines_output) > 0
    app_obj = app_obj or main_app_instance()
    print_out = app_obj.po if app_obj else dummy_function if app_obj is UNSET else print
    debug_out = app_obj.dpo if app_obj else dummy_function if app_obj is UNSET else print
    debug_out(f"    . executing at {os.getcwd()}: {mask_token(args)}")

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
        debug_out(f"****  subprocess.run({mask_token(args)}) returned non-zero exit code {ex.returncode}; {ex=}")
        result = ex
    except Exception as ex:                                         # pylint: disable=broad-except  # pragma: no cover
        print_out(f"****  subprocess.run({mask_token(args)}) raised exception {ex}")
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
                        extra_args: Iterable[str] = (), lines_output: Optional[list[str]] = None,
                        exit_on_err: bool = True, exit_msg: str = "", app_obj: Optional[ConsoleApp] = None,
                        shell: bool = False, env_vars: Optional[dict[str, str]] = None) -> int:
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
    :param app_obj:             :class:`~ae.console.ConsoleApp` instance, used for logging/force-ignorable error.
    :param shell:               pass True to execute command in the default OS shell (see :meth:`subprocess.run`).
    :param env_vars:            OS shell environment variables to be used instead of the console/bash defaults.
    :return:                    0 on success or the error number if an error occurred.
    """
    assert exit_on_err or not exit_msg, "specified exit message will never be shown because exit_on_err is False"
    if lines_output is None:
        lines_output = []
    app_obj = app_obj or cast(ConsoleApp, main_app_instance())  # calls app_obj./ConsoleApp.chk() method

    sh_err = sh_exec(command_line, extra_args=extra_args,
                     lines_output=lines_output, app_obj=app_obj, shell=shell, env_vars=env_vars)

    if app_obj and (sh_err and exit_on_err or app_obj.debug):
        for line in lines_output:
            if app_obj.verbose or not line.startswith("LOG:  "):  # if verbose show mypy's endless (stderr) log entries
                app_obj.po(" " * 6 + line)
        msg = f"command: {command_line} " + " ".join('"' + arg + '"' if " " in arg else arg for arg in extra_args)
        if not sh_err:
            app_obj.dpo(f"    = successfully executed {mask_token(msg)}")
        else:
            if exit_msg:
                app_obj.po(f"      {exit_msg}")
            app_obj.chk(err_code, not exit_on_err, f"sh_exit_if_exec_err error {sh_err} in {mask_token(msg)}")  # quit

    return sh_err
