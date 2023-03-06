"""tee like run implementation."""
import asyncio
import os
import platform
import subprocess
import sys
from asyncio import StreamReader
from importlib.metadata import PackageNotFoundError, version  # type: ignore
from shlex import join
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Union

try:
    __version__ = version("subprocess-tee")
except PackageNotFoundError:  # pragma: no branch
    __version__ = "0.1.dev1"

__all__ = ["run", "CompletedProcess", "__version__"]

if TYPE_CHECKING:
    CompletedProcess = subprocess.CompletedProcess[Any]  # pylint: disable=E1136
else:
    CompletedProcess = subprocess.CompletedProcess


STREAM_LIMIT = 2**23  # 8MB instead of default 64kb, override it if you need


async def _read_stream(stream: StreamReader, callback: Callable[..., Any]) -> None:
    while True:
        line = await stream.readline()
        if line:
            callback(line)
        else:
            break


async def _stream_subprocess(args: str, **kwargs: Any) -> CompletedProcess:
    platform_settings: Dict[str, Any] = {}
    if platform.system() == "Windows":
        platform_settings["env"] = os.environ

    # this part keeps behavior backwards compatible with subprocess.run
    tee = kwargs.get("tee", True)
    stdout = kwargs.get("stdout", sys.stdout)

    with open(os.devnull, "w", encoding="UTF-8") as devnull:
        if stdout == subprocess.DEVNULL or not tee:
            stdout = devnull
        stderr = kwargs.get("stderr", sys.stderr)
        if stderr == subprocess.DEVNULL or not tee:
            stderr = devnull

        # We need to tell subprocess which shell to use when running shell-like
        # commands.
        # * SHELL is not always defined
        # * /bin/bash does not exit on alpine, /bin/sh seems bit more portable
        if "executable" not in kwargs and isinstance(args, str) and " " in args:
            platform_settings["executable"] = os.environ.get("SHELL", "/bin/sh")

        # pass kwargs we know to be supported
        for arg in ["cwd", "env"]:
            if arg in kwargs:
                platform_settings[arg] = kwargs[arg]

        # Some users are reporting that default (undocumented) limit 64k is too
        # low
        process = await asyncio.create_subprocess_shell(
            args,
            limit=STREAM_LIMIT,
            stdin=kwargs.get("stdin", False),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            **platform_settings,
        )
        out: List[str] = []
        err: List[str] = []

        def tee_func(line: bytes, sink: List[str], pipe: Optional[Any]) -> None:
            line_str = line.decode("utf-8").rstrip()
            sink.append(line_str)
            if not kwargs.get("quiet", False):
                if pipe and hasattr(pipe, "write"):
                    print(line_str, file=pipe)
                else:
                    print(line_str)

        loop = asyncio.get_running_loop()
        tasks = []
        if process.stdout:
            tasks.append(
                loop.create_task(
                    _read_stream(process.stdout, lambda x: tee_func(x, out, stdout))
                )
            )
        if process.stderr:
            tasks.append(
                loop.create_task(
                    _read_stream(process.stderr, lambda x: tee_func(x, err, stderr))
                )
            )

        await asyncio.wait(set(tasks))

        # We need to be sure we keep the stdout/stderr output identical with
        # the ones procued by subprocess.run(), at least when in text mode.
        check = kwargs.get("check", False)
        stdout = None if check else ""
        stderr = None if check else ""
        if out:
            stdout = os.linesep.join(out) + os.linesep
        if err:
            stderr = os.linesep.join(err) + os.linesep

        return CompletedProcess(
            args=args,
            returncode=await process.wait(),
            stdout=stdout,
            stderr=stderr,
        )


def run(args: Union[str, List[str]], **kwargs: Any) -> CompletedProcess:
    """Drop-in replacement for subprocess.run that behaves like tee.

    Extra arguments added by our version:
    echo: False - Prints command before executing it.
    quiet: False - Avoid printing output
    """
    if isinstance(args, str):
        cmd = args
    else:
        # run was called with a list instead of a single item but asyncio
        # create_subprocess_shell requires command as a single string, so
        # we need to convert it to string
        cmd = join(args)

    check = kwargs.get("check", False)

    if kwargs.get("echo", False):
        print(f"COMMAND: {cmd}")

    result = asyncio.run(_stream_subprocess(cmd, **kwargs))
    # we restore original args to mimic subproces.run()
    result.args = args

    if check and result.returncode != 0:
        raise subprocess.CalledProcessError(
            result.returncode, args, output=result.stdout, stderr=result.stderr
        )
    return result
