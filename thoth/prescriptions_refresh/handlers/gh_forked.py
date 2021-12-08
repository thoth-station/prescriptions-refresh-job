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

"""Check if the given repository is a fork and eventually warn about it."""

import logging
import requests
from typing import TYPE_CHECKING

from .gh_link import iter_gh_info


if TYPE_CHECKING:
    from thoth.prescriptions_refresh.prescriptions import Prescriptions

_LOGGER = logging.getLogger(__name__)
_GH_LINK_PRESCRIPTION_NAME = "gh_forked.yaml"
_GH_LINK_PRESCRIPTION_CONTENT = """\
units:
  wraps:
  - name: {prescription_name}
    type: wrap
    should_include:
      adviser_pipeline: true
    match:
      state:
        resolved_dependencies:
        - name: {package_name}
    run:
      justification:
      - type: WARNING
        message: Package '{package_name}' is a GitHub fork
        link: {gh_link}
        package_name: {package_name}
"""


def gh_forked(prescriptions: "Prescriptions") -> None:
    """Check if the given project represents a fork."""
    for project_name, organization, repository in iter_gh_info(prescriptions):
        gh_link = f"https://github.com/{organization}/{repository}"

        response = requests.get(
            f"https://api.github.com/repos/{organization}/{repository}",
            headers={
                "Accept": "application/vnd.github.v3+json",
                "Authorization": f"token {prescriptions.get_github_token()}",
            },
        )
        if response.status_code == 404:
            _LOGGER.warning("Repository %r not found", gh_link)
            continue
        elif response.status_code != 200:
            _LOGGER.error(
                "Bad HTTP status code %r when obtaining info using GitHub API for %r: %s",
                response.status_code,
                gh_link,
                response.text,
            )
            continue

        is_forked = response.json().get("fork", False)

        if is_forked:
            prescription_name = prescriptions.get_prescription_name("GitHubForkedWrap", project_name)

            prescriptions.create_prescription(
                project_name=project_name,
                prescription_name=_GH_LINK_PRESCRIPTION_NAME,
                content=_GH_LINK_PRESCRIPTION_CONTENT.format(
                    package_name=project_name,
                    prescription_name=prescription_name,
                    gh_link=gh_link,
                ),
                commit_message=f"Project {project_name!r} is a fork on GitHub",
            )
