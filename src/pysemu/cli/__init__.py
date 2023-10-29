#!/usr/bin/env python3
from __future__ import annotations

import logging
import os
import sys
from typing import Optional

import structlog
import typer
from structlog.types import FilteringBoundLogger, Processor

from .._version import __version__
from .sub import cli_sub

logger: FilteringBoundLogger = structlog.get_logger(__name__)

"""
https://click.palletsprojects.com/en/7.x/api/#parameters
https://click.palletsprojects.com/en/7.x/options/
https://click.palletsprojects.com/en/7.x/arguments/
https://typer.tiangolo.com/
https://typer.tiangolo.com/tutorial/options/
"""


cli = typer.Typer(pretty_exceptions_enable=False)
cli.add_typer(cli_sub, name="sub")


@cli.callback()
def cli_callback(
    ctx: typer.Context, verbosity: int = typer.Option(0, "--verbose", "-v", count=True)
) -> None:
    if verbosity is not None:
        logging.root.propagate = True
        new_level = (
            logging.root.getEffectiveLevel()
            - (min(1, verbosity)) * 10
            - min(max(0, verbosity - 1), 9) * 1
        )
        logging.root.setLevel(new_level)
    logger.debug(
        "entry",
        ctx_parent_params=({} if ctx.parent is None else ctx.parent.params),
        ctx_params=ctx.params,
    )
    logger.debug(
        "log info",
        logging_effective_level=logging.getLogger("").getEffectiveLevel(),
    )


@cli.command("version")
def cli_version(ctx: typer.Context) -> None:
    sys.stderr.write(f"{__version__}\n")


def main() -> None:
    setup_logging()
    cli()


def setup_logging(console: bool = False) -> None:
    shared_processors: list[Processor] = []
    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.filter_by_level,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    use_console: Optional[bool] = None
    console_env = os.environ.get("STRUCTLOG_CONSOLE")
    if console_env is not None:
        if console_env == "true":
            use_console = True
        elif console_env == "false":
            use_console = False
        else:
            raise ValueError(
                "invalid value for STRUCTLOG_CONSOLE - must be 'true' or 'false'"
            )
    if use_console is None:
        use_console = console

    renderer: Processor
    if use_console:
        renderer = structlog.dev.ConsoleRenderer()
    else:
        renderer = structlog.processors.JSONRenderer()
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=[structlog.stdlib.ExtraAdder(), *shared_processors],
        keep_stack_info=True,
        processors=[
            structlog.processors.CallsiteParameterAdder(
                {
                    structlog.processors.CallsiteParameter.FUNC_NAME,
                    structlog.processors.CallsiteParameter.FILENAME,
                    structlog.processors.CallsiteParameter.LINENO,
                    structlog.processors.CallsiteParameter.THREAD,
                }
            ),
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )
    log_handler = logging.StreamHandler(stream=sys.stderr)
    log_handler.setFormatter(formatter)
    logging.root.propagate = True
    logging.root.setLevel(os.environ.get("PYTHON_LOGGING_LEVEL", logging.INFO))
    logging.root.addHandler(log_handler)


if __name__ == "__main__":
    main()
