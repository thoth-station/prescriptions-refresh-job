#!/usr/bin/env python3
# thoth-prescriptions-refresh
# Copyright(C) 2021 Fridolin Pokorny
#
# This program is free software: you can redistribute it and / or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
# type: ignore

"""Thoth's prescriptions refresh CLI."""

import logging
from typing import Optional

import click
from thoth.common import init_logging

from thoth.prescriptions_refresh import __version__
import thoth.prescriptions_refresh.handlers as handlers
from thoth.prescriptions_refresh.prescriptions import Prescriptions
from thoth.prescriptions_refresh.knowledge import Knowledge

init_logging()

_LOGGER = logging.getLogger("thoth.prescriptions_refresh")


def _print_version(ctx: click.Context, _, value: str):
    """Print version and exit."""
    if not value or ctx.resilient_parsing:
        return

    click.echo(__version__)
    ctx.exit()


@click.group()
@click.pass_context
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    envvar="THOTH_PRESCRIPTIONS_REFRESH_DEBUG",
    help="Be verbose about what's going on.",
)
@click.option(
    "--version",
    is_flag=True,
    is_eager=True,
    callback=_print_version,
    expose_value=False,
    help="Print version and exit.",
)
@click.option(
    "--prescriptions-repo",
    type=str,
    default=Prescriptions.DEFAULT_PRESCRIPTIONS_REPO,
    envvar="THOTH_PRESCRIPTIONS_REFRESH_REPO",
    show_default=True,
    help="Prescriptions repository to be used",
)
@click.option(
    "--token",
    metavar="TOKEN",
    type=str,
    envvar="THOTH_PRESCRIPTIONS_REFRESH_GITHUB_TOKEN",
    required=False,
    help="GitHub token to be used with GitHub, multiple can be supplied delimited by comma or new line.",
)
@click.option(
    "--labels",
    metavar="LABEL1,LABEL2",
    type=str,
    envvar="THOTH_PRESCRIPTIONS_REFRESH_GITHUB_LABELS",
    default=Prescriptions.DEFAULT_LABELS,
    show_default=True,
    help="Labels added to opened pull requests and issues..",
)
def cli(ctx: click.Context, prescriptions_repo: str, token: Optional[str], labels: Optional[str], verbose: bool):
    """Thoth's prescription-refresh command line interface."""
    if ctx:
        ctx.auto_envvar_prefix = "THOTH_PRESCRIPTIONS_REFRESH"

    if verbose:
        _LOGGER.setLevel(logging.DEBUG)

    Prescriptions.PRESCRIPTIONS_REPO = prescriptions_repo
    Prescriptions.LABELS = [i for i in labels.split(",") if i]

    _LOGGER.debug("Debug mode is on")
    _LOGGER.info("Version: %s", __version__)


@cli.command("gh-link")
def gh_link_command() -> None:
    """Check project links to GitHub."""
    with Knowledge() as knowledge:
        handlers.gh_link(knowledge)


@cli.command("gh-archived")
def gh_archived_command() -> None:
    """Check for archived projects on GitHub."""
    with Prescriptions() as prescriptions:
        handlers.gh_archived(prescriptions)


@cli.command("gh-forked")
def gh_forked_command() -> None:
    """Check for forks."""
    with Prescriptions() as prescriptions:
        handlers.gh_forked(prescriptions)


@cli.command("gh-popularity")
def gh_popularity() -> None:
    """Compute popularity of projects."""
    with Prescriptions() as prescriptions:
        handlers.gh_popularity(prescriptions)


@cli.command("gh-updated")
def gh_updated() -> None:
    """Check when projects were last updated."""
    with Prescriptions() as prescriptions:
        handlers.gh_updated(prescriptions)


@cli.command("gh-contributors")
def gh_contributors() -> None:
    """Check number of collaborators on GitHub."""
    with Prescriptions() as prescriptions:
        handlers.gh_contributors(prescriptions)


@cli.command("gh-release-notes")
def gh_release_notes() -> None:
    """Check release notes for projects hosted on GitHub."""
    with Prescriptions() as prescriptions:
        handlers.gh_release_notes(prescriptions)


@cli.command("scorecards")
def scorecards() -> None:
    """Check for scorecards published by OSSF."""
    with Prescriptions() as prescriptions:
        handlers.scorecards(prescriptions)


@cli.command("cve-warning")
def cve_warning() -> None:
    """Warn if projects are known to have a lot of vulnerabilities.."""
    with Prescriptions() as prescriptions:
        handlers.cve_warning(prescriptions)


@cli.command("quay-security")
def quay_security() -> None:
    """Check container images with predictable stacks for security related aspects."""
    with Prescriptions() as prescriptions:
        handlers.quay_security(prescriptions)


@cli.command("thoth-community")
def thoth_community() -> None:
    """Compute Thoth community statistics."""
    with Prescriptions() as prescriptions:
        handlers.thoth_community(prescriptions)


@cli.command("pypi-artifact-size")
def pypi_artifact_size() -> None:
    """Compute size of artifact eventually downloaded."""
    with Prescriptions() as prescriptions:
        handlers.pypi_artifact_size(prescriptions)


@cli.command("pypi-downloads")
def pypi_downloads() -> None:
    """Compute downloads statistics for a package from PyPI."""
    with Prescriptions() as prescriptions:
        handlers.pypi_downloads(prescriptions)


@cli.command("pypi-maintainers")
def pypi_maintainers() -> None:
    """Warn about projects that do not have good maintainer base."""
    with Prescriptions() as prescriptions:
        handlers.pypi_maintainers(prescriptions)


@cli.command("pypi-release")
def pypi_release() -> None:
    """Warn about packages that haven't been released for some time."""
    with Prescriptions() as prescriptions:
        handlers.pypi_release(prescriptions)


__name__ == "__main__" and cli()
