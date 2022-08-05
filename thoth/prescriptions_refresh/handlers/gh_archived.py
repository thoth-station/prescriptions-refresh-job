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

"""Check archived repositories on GitHub."""

import logging
import requests
import sys

import thoth.prescriptions_refresh
from thoth.prescriptions_refresh.prescriptions import Prescriptions
from .gh_link import iter_gh_info


_LOGGER = logging.getLogger(__name__)
_PRESCRIPTIONS_DEFAULT_REPO = Prescriptions.DEFAULT_PRESCRIPTIONS_REPO
_PRESCRIPTIONS_VERSION = thoth.prescriptions_refresh.__version__

_GH_LINK_PRESCRIPTION_NAME = "gh_archived.yaml"
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
        message: Package '{package_name}' is marked as archived on GitHub
        link: {gh_link}
        package_name: {package_name}
        metadata:
        - prescriptions_repository: {default_prescriptions_repository}
          prescriptions_version: {prescriptions_version}
"""


def gh_archived(prescriptions: "Prescriptions") -> None:
    """Check GitHub links available in the project info on PyPI."""
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

        elif response.status_code == 429:
            _LOGGER.error(
                "Bad HTTP status code %s when trying to obtain information for project %r: too many requests."
                "Exiting code with status 3.",
                response.status_code,
                project_name,
            )
            sys.exit(3)

        elif response.status_code != 200:
            _LOGGER.error(
                "Bad HTTP status code %r when obtaining info using GitHub API for %r: %s",
                response.status_code,
                gh_link,
                response.text,
            )
            continue

        is_archived = response.json().get("archived", False)

        if is_archived:
            prescription_name = prescriptions.get_prescription_name("GitHubArchivedWrap", project_name)

            prescriptions.create_prescription(
                project_name=project_name,
                prescription_name=_GH_LINK_PRESCRIPTION_NAME,
                content=_GH_LINK_PRESCRIPTION_CONTENT.format(
                    package_name=project_name,
                    prescription_name=prescription_name,
                    gh_link=gh_link,
                    default_prescriptions_repository=_PRESCRIPTIONS_DEFAULT_REPO,
                    prescriptions_version=_PRESCRIPTIONS_VERSION,
                ),
                commit_message=f"Repository for {project_name!r} is marked as archived on GitHub",
            )
        else:
            prescriptions.delete_prescription(
                project_name,
                _GH_LINK_PRESCRIPTION_NAME,
                commit_message=f"Repository for {project_name!r} is no longer marked as archived on GitHub",
                nonexisting_ok=True,
            )
