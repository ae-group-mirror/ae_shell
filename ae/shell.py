"""
shell execution and environment helpers
=======================================

this module is designed to provide a comprehensive set of constants and helper functions
to manage shell printouts, OS environment variables and to execute shell commands.

* :func:`debug_or_verbose`: checks if the application is running in debug or verbose mode.
* :func:`get_domain_user_var`: retrieves an OS environment variable value for a specific domain and/or user.
* :func:`hint`: provides a hint message for console printouts based on the provided arguments.
* :func:`in_os_env`: context manager to temporarily add environment variables from the ``.env`` files onto `os.environ`.
* :func:`mask_token`: hide/mask tokens in a text block, to prevent to show them in logs and printouts.
* :func:`output_line_split`: decode and split the specified shell/console output streams into line chunks.
* :func:`output_zero_split`: decode and split the specified shell/console output streams separated by `NUL` (\\0) chars.
* :func:`sh_exec`: execute command in the current working directory of the OS console/shell.
* :func:`sh_exit_if_exec_err`: extended version of :func:`sh_exec` with automatically checks for errors
  after a command is executed and handles application shutdown/termination gracefully.

* :data:`STDERR_BEG_MARKER`: marker used in the console/shell printouts for the beginning of merged-in stderr output.
* :data:`STDERR_END_MARKER`: marker used in the console/shell printouts for the end of merged-in stderr output.
"""
import os
import shlex
import subprocess

from collections.abc import Callable, Iterable, Iterator, MutableMapping
from contextlib import contextmanager
from typing import Any, cast, overload

from ae.base import UNSET, UnsetType, dummy_function, env_str, norm_name                    # type: ignore
from ae.system import load_env_var_defaults, os_env_venv                                    # type: ignore
from ae.core import main_app_instance, AppBase                                              # type: ignore
from ae.console import MAIN_SECTION_NAME, ConsoleApp                                        # type: ignore


__version__ = '0.3.17'


STDERR_BEG_MARKER = 'vvv   STDERR   vvv'  #: :paramref:`ae.shell.sh_exec.output_lines` begin stderr lines marker
STDERR_END_MARKER = '^^^   STDERR   ^^^'  #: end stderr lines marker in :paramref:`ae.shell.sh_exec.output_lines`


def debug_or_verbose(app_obj: ConsoleApp | UnsetType | None = None) -> bool:
    """ determine if the current app runs in debug|verbose mode, while preventing early .get_option() call an app init.

    :param app_obj:             optional ConsoleApp instance (def=main_app_instance()).
    :return:                    a boolean False when the main app debug level is :data:`~ae.core.DEBUG_LEVEL_DISABLED`
                                and the app option --more_verbose is not specified (in cfg-file or at the command line),
                                else True.

    .. note:: the return value on app startup/initialization, before the command line parsing, is always True.

    .. hint::
        the debug mode can be activated via the :class:`~ae.console.ConsoleApp` option `debug_level`, specified either
        in a config file or via the command line options. the verbose mode get activated via the `more_verbose`  option.
    """
    if app_obj is None:
        app_obj = main_app_instance()

    return bool(
        not isinstance(app_obj, AppBase)                    # prevent exception in early app startup and unit test runs
        or app_obj.debug                                    # main_app.debug_level > DEBUG_LEVEL_DISABLED
        or not isinstance(app_obj, ConsoleApp)              # return True for pure ae.core.AppBase instances
        or not getattr(app_obj, '_parsed_arguments', None)  # ConsoleApp._parsed_arguments args Namespace not created
        or app_obj.get_option('more_verbose'))              # optional ConsoleApp instance verbose option


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


def hint(command: str, action: Callable | str, message_suffix: str = "") -> str:
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
    """ temporarily add environment variables from the ``.env`` files that not exist in :attr:`os.environ` to it.

    :param start_dir:           path to the folder where the first dotenv file (with the highest priority) is stored.
    :return:                    yielding the OS env variables that got added to os.environ in this temporary context.
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


@overload
def mask_token(text: str | list[str]) -> str | list[str]: ...


def mask_token(text: str | list[str]) -> str | list[str]:
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


def output_line_split(output: bytes) -> list[str]:
    """ decode and split the specified shell/console output streams into line chunks.

    :param output:              captured stdout/stderr output from an executed OS shell command.
    :return:                    list of non-empty shell/console output lines, decoded into string.
    """
    return [line for line in output.decode().splitlines() if line.strip()]


def output_zero_split(output: bytes) -> list[str]:
    """ decode and split the specified shell/console output streams separated by `NUL` (\\0) characters.

    :param output:              captured stdout/stderr output from an executed OS shell command (e.g. `env -0`).
    :return:                    list of non-empty shell/console output chunks, decoded into string.
    """
    return [line for line in output.decode().split('\0') if line.strip()]


# pylint: disable-next=too-many-arguments,too-many-positional-arguments
def sh_exec(command_line: str, extra_args: Iterable[str] = (), console_input: str = "",
            output_lines: list[str] | None = None, app_obj: AppBase | UnsetType | None = None, shell: bool = False,
            env_vars: dict[str, str] | UnsetType | None = UNSET, err_redirect: int | None = None,
            decoder_splitter: Callable[[bytes], list[str]] = output_line_split) -> int:
    """ execute command in the current working directory of the OS console/shell.

    :param command_line:        command line string to execute on the console/shell. could contain command line args
                                separated by whitespace characters (alternatively use :paramref:`.extra_args`).
    :param extra_args:          optional iterable with extra command line arguments.
    :param console_input:       optional string to be sent to the stdin stream of the console/shell.
    :param output_lines:        specify a list to be extended with the lines printed on the console/shell stdout stream,
                                and to also hide this output on the console. if and how the stderr stream get also
                                hidden/redirected to this list can be controlled via the value passed in the argument
                                :paramref:`.err_redirect`.
    :param app_obj:             optional :class:`~ae.core.AppBase`/:class:`~ae.console.ConsoleApp` instance, used for
                                logging. if not specified or None and if :func:`~ae.core.main_app_instance()` returns
                                None then the Python :func:`print` function is used.
                                specify :data:`~ae.base.UNSET` to suppress any printing/logging output.
    :param shell:               pass True to execute command in the default OS shell (for more info check the
                                documentation of the parameter :paramref:`~subprocess.run.shell` of the
                                :func:`subprocess.run` function).
    :param env_vars:            OS shell environment variables to be used instead of the console/bash defaults.
                                if not specified or `UNSET` then an isolated dict copy of :attr:`os.environ` will get
                                passed onto :func:`subprocess.run` in order to avoid potential runtime errors, if the
                                parent process (or a concurrent thread) modifies :attr:`os.environ` during the creation
                                of the subprocess. Additionally, with the convertion of the special :class:`_Environ`
                                object into a standard dict, the execution will result slightly faster and avoids
                                any special method overrides interfering with the child process creation. it also is
                                preventing rare errors with multithread-processes that try to change OS env variable
                                (e.g. Conda in relation with pip could lead to raise a `RuntimeError: dictionary
                                changed size during iteration` exception).
                                specify `None` in order to use the original/unisolated :attr:`os.environ` object.
    :param err_redirect:        this argument controls if and how the output of the executed command onto the console
                                stderr stream gets captured/redirected. it gets passed directly onto the
                                :paramref:`~subprocess.run.stderr` argument of :func:`subprocess.run` function.
                                if the argument of :paramref:`.output_lines` is a list, and you specified the
                                argument value :data:`subprocess.PIPE`, then the stderr output will get added at the
                                end of this list (enclosed between the list items :data:`STDERR_BEG_MARKER` and
                                :data:`STDERR_END_MARKER`). if the argument of :paramref:`.output_lines` is a
                                list, and you specified the argument value :data:`subprocess.STDOUT` then the stderr
                                output will get merged without any markers into this list in the order they get printed.
                                specify :data:`subprocess.DEVNULL` to hide any stderr output onto the console/shell
                                as well as in the :paramref:`.output_lines` list. if you specify `None`
                                (the default argument) then the stderr output will be printed only on the console.
    :param decoder_splitter:    callable to decode and split the output from the stdout/stderr streams into a list
                                of string chunks/lines, to be added to and returned by :paramref:`.output_lines`.
    :return:                    return code of the executed command or 126 if execution raised any other exception.
    """
    if shell:
        all_args: str | list[str] = command_line + (" " + " ".join(extra_args) if extra_args else "")
    else:
        all_args = shlex.split(command_line) + list(extra_args)
    masked_args = mask_token(all_args)
    if app_obj is None:
        app_obj = main_app_instance()
    print_out = dummy_function if app_obj is UNSET else app_obj.print_out if isinstance(app_obj, AppBase) else print
    debug_out = dummy_function if app_obj is UNSET else app_obj.debug_out if isinstance(app_obj, AppBase) else print
    if env_vars is UNSET:
        env_vars = os.environ.copy()

    debug_out(f"    . executing {masked_args} at {os.getcwd()=} in {os_env_venv()=}")
    result: subprocess.CompletedProcess | subprocess.CalledProcessError     # having: stdout/stderr/returncode
    try:
        result = subprocess.run(all_args,
                                stdout=subprocess.PIPE if isinstance(output_lines, list) else None,
                                stderr=err_redirect,
                                input=console_input.encode(),
                                check=True,
                                shell=shell,
                                env=env_vars)
    except subprocess.CalledProcessError as exc:
        debug_out(f"****  subprocess.run({masked_args}) returned non-zero exit code {exc.returncode}; {exc=}")
        result = exc
    except Exception as exc:                                         # pylint: disable=broad-except
        print_out(f"****  subprocess.run({masked_args}) raised exception {exc}")
        return (126, )[0]       # put return/exit code into tuple for global code search

    if isinstance(output_lines, list):
        if result.stdout:
            output_lines.extend(decoder_splitter(result.stdout))
        if err_redirect == subprocess.PIPE and result.stderr:
            output_lines.append(STDERR_BEG_MARKER)
            output_lines.extend(decoder_splitter(result.stderr))
            output_lines.append(STDERR_END_MARKER)

    return result.returncode


# pylint: disable-next=too-many-arguments,too-many-positional-arguments
def sh_exit_if_exec_err(err_code: int, command_line: str,
                        extra_args: Iterable[str] = (), output_lines: list[str] | None = None, exit_on_err: bool = True,
                        exit_msg: str = "", app_obj: ConsoleApp | UnsetType | None = None, shell: bool = False,
                        env_vars: dict[str, str] | UnsetType | None = UNSET,
                        err_redirect: int | None = subprocess.DEVNULL,
                        decoder_splitter: Callable[[bytes], list[str]] = output_line_split) -> int:
    """ execute command in the current working directory, optionally capturing console output and exit app on error.

    :param err_code:            error code to pass to the console as exit code if the command set an error code and
                                value of the :paramref:`.exit_on_err` argument is `True`.
    :param command_line:        command line string to execute. this argument could contain additional command line
                                arguments, separated by whitespace characters. alternatively use the argument
                                :paramref:`.extra_args` which allows to pass command line argument values,
                                with containing space characters.
    :param extra_args:          optional iterable of extra command line arguments.
    :param output_lines:        optional list extended with the lines printed to stdout/stderr on execution.
    :param exit_on_err:         pass False to not exit the app on error.
    :param exit_msg:            additional text to print on stdout/console if the app debug level is greater or equal
                                to 1 (:data:`~ae.core.DEBUG_LEVEL_ENABLED`) or if an error occurred.
    :param app_obj:             :class:`~ae.console.ConsoleApp` instance, used for logging/force-ignorable error.
    :param shell:               pass True to execute command in the default OS shell (see :func:`sh_exec`).
    :param env_vars:            OS shell environment variables to be used instead of the console/bash defaults.
    :param err_redirect:        control how the output on stderr gets captured, redirected and returned. see also
                                :paramref:`sh_exec.err_redirect` for more details to the supported argument values.
                                if this argument is not specified or has the value :data:`subprocess.DEVNULL` then the
                                stderr output will get suppressed on the console and will also not get added to the
                                list argument in :paramref:`.output_lines`.
    :param decoder_splitter:    callable to decode and split the output from the stdout/stderr streams into a list
                                of string chunks/lines, to be added to and returned by :paramref:`.output_lines`.
    :return:                    0 on success, or if an error occurred the error number set by the executed command.
    """
    if output_lines is None:
        output_lines = []
        output_len = 0
    else:
        output_len = len(output_lines)
    if app_obj is None:
        app_obj = cast(ConsoleApp, main_app_instance())  # calls app_obj./ConsoleApp.chk() method

    sh_err = sh_exec(command_line, extra_args=extra_args, output_lines=output_lines, app_obj=app_obj, shell=shell,
                     env_vars=env_vars, err_redirect=err_redirect, decoder_splitter=decoder_splitter)

    if isinstance(app_obj, ConsoleApp) and (app_obj.debug or sh_err and exit_on_err):
        for line in output_lines[output_len:]:
            if app_obj.verbose or not line.startswith("LOG:  "):  # if verbose show mypy's endless (stderr) log entries
                app_obj.po(" " * 6 + line)
        command = mask_token(f"{command_line} " + " ".join('"' + _a + '"' if " " in _a else _a for _a in extra_args))
        if sh_err == 0:
            app_obj.dpo(f"    = successfully executed {command=}")
        else:
            if exit_msg:
                app_obj.po(f"      {exit_msg}")
            app_obj.chk(err_code, not exit_on_err, f"sh_exit_if_exec_err({err_code}, {command!r}) error {sh_err}")

    return sh_err
