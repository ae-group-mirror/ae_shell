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
* :func:`run_cmd`: execute command in the current working directory of the OS console/shell.
* :func:`run_logged_cmd`: extended version of :func:`run_cmd` with logging and error checking.
  after a command is executed and handles application shutdown/termination gracefully.

* :data:`STDERR_BEG_MARKER`: marker used in the console/shell printouts for the beginning of merged-in `stderr` output.
* :data:`STDERR_END_MARKER`: marker used in the console/shell printouts for the end of merged-in `stderr` output.
"""
import os
import subprocess

from collections.abc import Callable, Iterator, MutableMapping
from contextlib import contextmanager
from typing import Any, Sequence, cast, overload

from ae.base import UNSET, UnsetType, dummy_function, env_str, norm_name                    # type: ignore
from ae.system import load_env_var_defaults, os_env_venv                                    # type: ignore
from ae.core import main_app_instance, AppBase                                              # type: ignore
from ae.console import MAIN_SECTION_NAME, ConsoleApp                                        # type: ignore


__version__ = '0.3.18'


STDERR_BEG_MARKER = 'vvv   STDERR   vvv'  #: :paramref:`ae.shell.run_cmd.output_lines` begin `stderr` lines marker
STDERR_END_MARKER = '^^^   STDERR   ^^^'  #: end `stderr` lines marker in :paramref:`ae.shell.run_cmd.output_lines`


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
def mask_token(text: str) -> str: ...       # type: ignore[overload-overlap]


@overload
def mask_token(text: Sequence[str]) -> list[str]: ...


def mask_token(text: str | Sequence[str]) -> str | list[str]:
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

    :param output:              captured `stdout`/`stderr` output from an executed OS shell command.
    :return:                    list of non-empty shell/console output lines, decoded into string.
    """
    return [line for line in output.decode().splitlines() if line.strip()]


def output_zero_split(output: bytes) -> list[str]:
    """ decode and split the specified shell/console output streams separated by `NUL` (\\0) characters.

    :param output:              captured `stdout`/`stderr` output from an executed OS shell command (e.g. `env -0`).
    :return:                    list of non-empty shell/console output chunks, decoded into string.
    """
    return [line for line in output.decode().split('\0') if line.strip()]


def run_cmd(*cmd_args: str,
            output_lines: list[str] | None = None,
            app_obj: AppBase | UnsetType | None = None,
            decoder_splitter: Callable[[bytes], list[str]] = output_line_split,
            **run_kwargs) -> int:
    """ run command in the current working directory, capturing/logging errors and optionally returning console output.

    :param cmd_args:            command line string or args sequence of command name and arguments
                                to be run/executed on the console/shell via :func:`subprocess.run`.
    :param output_lines:        specify a list to be extended with the lines printed on the console/shell `stdout`
                                stream, and to also hide this output on the console. if and how the `stderr` stream get
                                also either hidden, captured or to be redirected to this list can be controlled via the
                                value passed in the kwarg :paramref:`~subprocess.Popen.stderr`: if this argument is a
                                list, and you specified the argument value :data:`subprocess.PIPE`, then the `stderr`
                                output will get added at the end of this list (enclosed between the list items
                                :data:`STDERR_BEG_MARKER` and :data:`STDERR_END_MARKER`). if this argument is a list,
                                and you specified the argument value :data:`subprocess.STDOUT` then the `stderr` outputs
                                will get merged without any markers into this list in the order they get printed.
                                specify :data:`subprocess.DEVNULL` in :paramref:`~subprocess.Popen.stderr` to hide any
                                `stderr` output onto the console/shell as well as in this list argument.
                                specifying `None` as :paramref:`~subprocess.Popen.stderr` argument value
                                (the default argument) then the `stderr` output will be printed only on the console.
    :param app_obj:             optional :class:`~ae.core.AppBase`/:class:`~ae.console.ConsoleApp` instance, used for
                                logging. if not specified or None and if :func:`~ae.core.main_app_instance()` returns
                                None then the Python :func:`print` function is used.
                                specify :data:`~ae.base.UNSET` to suppress any printing/logging output.
    :param decoder_splitter:    callable to decode and split the output from the `stdout`/`stderr` streams into a list
                                of string chunks/lines, to be added to and returned by :paramref:`.output_lines`.
    :param run_kwargs:          kwargs to be passed onto :func:`subprocess.run`, most of them unchanged, like e.g.
                                :paramref:`~subprocess.run.input`. some of them, will get adopted/changed before
                                they get passed onto :func:`subprocess.run`:

                                * :paramref:`~subprocess.run.check`: will get passed onto :func:`subprocess.run`
                                  as `True` if not specified in this kwarg (in order to catch and log the
                                  :class:`subprocess.CalledProcessError` exception in debug mode).
                                * :paramref:`~subprocess.Popen.env`: shell environment variables to be used instead of
                                  the currently set OS shell variable values.
                                  only if the value of this argument does not get specified or has the value `UNSET`,
                                  then an isolated dict copy of :attr:`os.environ` will get passed onto
                                  :func:`subprocess.run` in order to avoid potential runtime errors, caused by a parent
                                  process (or a concurrent thread) if it modifies :attr:`os.environ` during the creation
                                  of this subprocess. additionally, with the convertion of the special :class:`_Environ`
                                  object into a standard dict, the execution will result slightly faster and avoids
                                  any special method overrides interfering with the child process creation. it also is
                                  preventing rare errors with multithread-processes that try to change OS env variable
                                  (e.g. Conda in relation with pip could lead to raise a `RuntimeError: dictionary
                                  changed size during iteration` exception). specify `None` as the :paramref:`.env`
                                  value in order to use the original/unisolated :attr:`os.environ` object.
                                * :paramref:`~subprocess.Popen.stdout`: will be passed to :func:`subprocess.run`
                                  as :data:`subprocess.PIPE` (instead of None) if a list instance got specified
                                  as the :paramref:`.output_lines` argument.

    :return:                    return code of the executed command or 126 if execution raised any other exception.
    """
    masked_args = mask_token(cmd_args)

    if app_obj is None:
        app_obj = main_app_instance()
    print_out = dummy_function if app_obj is UNSET else app_obj.print_out if isinstance(app_obj, AppBase) else print
    debug_out = dummy_function if app_obj is UNSET else app_obj.debug_out if isinstance(app_obj, AppBase) else print

    run_kwargs.setdefault('check', True)
    if run_kwargs.get('env', UNSET) is UNSET:
        run_kwargs['env'] = os.environ.copy()
    if isinstance(output_lines, list):
        run_kwargs.setdefault('stdout', subprocess.PIPE)

    debug_out(f"    . executing {masked_args} at {os.getcwd()=} in {os_env_venv()=}")

    result: subprocess.CompletedProcess | subprocess.CalledProcessError         # having: stdout/stderr/returncode
    try:
        result = subprocess.run(cmd_args, **run_kwargs)                         # pylint: disable=subprocess-run-check
    except subprocess.CalledProcessError as exc:
        debug_out(f"****  subprocess.run({masked_args}) returned non-zero exit code {exc.returncode}; {exc=}")
        result = exc
    except Exception as exc:                                         # pylint: disable=broad-except
        print_out(f"****  subprocess.run({masked_args}) raised exception {exc}")
        return (126, )[0]       # put return/exit code into tuple for global code search

    if isinstance(output_lines, list):
        if result.stdout:
            output_lines.extend(decoder_splitter(result.stdout))
        if result.stderr and run_kwargs.get('stderr', None) == subprocess.PIPE:
            output_lines.append(STDERR_BEG_MARKER)
            output_lines.extend(decoder_splitter(result.stderr))
            output_lines.append(STDERR_END_MARKER)

    return result.returncode


def run_logged_cmd(err_code: int, *cmd_args: str,
                   output_lines: list[str] | None = None,
                   exit_on_err: bool | str = True,
                   app_obj: ConsoleApp | UnsetType | None = None,
                   decoder_splitter: Callable[[bytes], list[str]] = output_line_split,
                   **run_kwargs) -> int:
    """ run command in the current working directory, optionally capturing/logging console output and exiting on error.

    :param err_code:            error code to be passed onto the console as exit code if the command set an error code
                                and the value of the :paramref:`.exit_on_err` argument is `True` or a nonempty string.
    :param cmd_args:            command line string or a sequence of command name and separate line arguments
                                to be run/executed on the console/shell.
    :param output_lines:        optional list extended with the lines printed to `stdout`/`stderr` on execution.
                                see the :paramref:`~run_cmd.output_lines` argument of :func:`run_cmd` for more details.
    :param exit_on_err:         specifying `True` (the default) or a nonempty string will shut-down/quit/exit the
                                currently running app (the Python interpreter) if the executed command set an
                                error code. a nonempty string will get printed/logged to `stdout` before the exit.
                                pass `False` or an empty string to not exit the app if a command error occurred.
    :param app_obj:             optional :class:`~ae.console.ConsoleApp` instance, used for logging and error checking
                                (with the option to ignore errors if the app got started with the `--force` option).
                                if not specified or None and if :func:`~ae.core.main_app_instance()` returns
                                None then the Python :func:`print` function is used for logging.
                                specify :data:`~ae.base.UNSET` to suppress any printing/logging output.
    :param decoder_splitter:    callable to decode and split the output from the `stdout`/`stderr` streams into a list
                                of string chunks/lines, to be added to and returned by :paramref:`.output_lines`.
    :param run_kwargs:          extra kwargs to be passed onto :func:`run_cmd` and :func:`subprocess.run`. some kwargs
                                like e.g. :paramref:`~subprocess.run.input` and :paramref:`~subprocess.Popen.shell`
                                will get passed unchanged onto :func:`run_cmd`, others like
                                :paramref:`~run_cmd.env` or :paramref:`~run_cmd.stderr`, will be first processed by
                                this function and/or :func:`run_cmd` before they get passed onto :func:`subprocess.run`:

                                * :paramref:`~subprocess.Popen.stderr`: controls how the output onto `stderr` will get
                                  captured, redirected and/or returned. if this argument is not specified then the value
                                  :data:`subprocess.DEVNULL` will get passed onto :func:`run_cmd` and
                                  :func:`subprocess.run`, which is suppressing any output sent onto `stderr` on the
                                  console as well as any addition of it to the list argument specified in
                                  :paramref:`.output_lines`. if you specify the value :data:`subprocess.PIPE` or
                                  :data:`subprocess.STDOUT` together with a list in the :paramref:`.output_lines`
                                  argument, then any output onto `stderr` will get added to this list.
                                  see also the description of the :paramref:`~run_cmd.output_lines` parameter of
                                  :func:`run_cmd` for more details on the supported values of this parameter.

    :return:                    0 on success, or if an error occurred the error number set by the executed command.
    """
    if output_lines is None:
        output_lines = []
        output_len = 0
    else:
        output_len = len(output_lines)

    if app_obj is None:
        app_obj = cast(ConsoleApp, main_app_instance())  # calls ConsoleApp./app_obj.chk() method

    run_kwargs.setdefault('stderr', subprocess.DEVNULL)

    sh_err = run_cmd(*cmd_args, output_lines=output_lines, app_obj=app_obj, decoder_splitter=decoder_splitter,
                     **run_kwargs)

    if isinstance(app_obj, ConsoleApp) and (app_obj.debug or sh_err and exit_on_err):
        for line in output_lines[output_len:]:
            if app_obj.verbose or not line.startswith("LOG:  "):  # if verbose show mypy's endless (stderr) log entries
                app_obj.po(" " * 6 + line)
        command = mask_token(cmd_args)
        if sh_err == 0:
            app_obj.dpo(f"    = successfully executed {command=}")
        else:
            if isinstance(exit_on_err, str):
                app_obj.po(f"      {exit_on_err}")
            app_obj.chk(err_code, not bool(exit_on_err), f"run_logged_cmd({err_code}, {command!r}) error {sh_err}")

    return sh_err
