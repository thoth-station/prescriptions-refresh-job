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

"""Check links to the project release notes."""

import logging
import requests
import sys
from typing import TYPE_CHECKING

from .gh_link import iter_gh_info

if TYPE_CHECKING:
    from thoth.prescriptions_refresh.prescriptions import Prescriptions

_LOGGER = logging.getLogger(__name__)
_GH_LINK_PRESCRIPTION_NAME = "gh_release_notes.yaml"
_GH_LINK_PRESCRIPTION_CONTENT = """\
units:
  wraps:
  - name: {prescription_name}
    type: wrap.GHReleaseNotes
    should_include:
      adviser_pipeline: true
    match:
      state:
        resolved_dependencies:
        - name: {package_name}
    run:
      release_notes:
        organization: {organization}
        repository: {repository}
"""


def gh_release_notes(prescriptions: "Prescriptions") -> None:
    """Check links to the project release notes."""
    for project_name, organization, repository in iter_gh_info(prescriptions):
        pypi_link = f"https://pypi.org/pypi/{project_name}/json"

        response = requests.get(pypi_link)
        if response.status_code == 404:
            _LOGGER.warning("Project %r was not found on PyPI, skipping...", project_name)
            continue
        elif response.status_code != 200:
            _LOGGER.error(
                "Unable to obtain project information for %r from PyPI (%s), skipping: %s",
                project_name,
                response.status_code,
                response.text,
            )
            continue

        # Pick the last version to see if it has a tag on GitHub.
        version = next(reversed(response.json()["releases"]))
        _LOGGER.debug("Checking version %r of %r", version, project_name)

        prescription_name = prescriptions.get_prescription_name("GitHubReleaseNotesWrap", project_name)

        # Try without `v' prefix.
        release_url = f"https://github.com/{organization}/{repository}/releases/tag/{version}"
        try:
            response = requests.head(release_url, allow_redirects=True)
        except Exception as exc:
            _LOGGER.error("Obtaining information from %r failed: %s", release_url, str(exc))
            continue

        if response.status_code == 200:
            prescriptions.create_prescription(
                project_name,
                _GH_LINK_PRESCRIPTION_NAME,
                content=_GH_LINK_PRESCRIPTION_CONTENT.format(
                    prescription_name=prescription_name,
                    package_name=project_name,
                    organization=organization,
                    repository=repository,
                ),
                commit_message=f"Project {project_name!r} hosts release notes on GitHub",
            )
            continue

        # Try with `v' prefix.
        release_url = f"https://github.com/{organization}/{repository}/releases/tag/v{version}"
        try:
            response = requests.head(release_url, allow_redirects=True)
        except Exception as exc:
            _LOGGER.error("Obtaining information from %r failed: %s", release_url, str(exc))
            continue

        if response.status_code == 200:
            # Dirty, but keep no entry by default as the prescriptions schema is strict with this.
            content = _GH_LINK_PRESCRIPTION_CONTENT + "        tag_version_prefix: v\n"
            prescriptions.create_prescription(
                project_name,
                _GH_LINK_PRESCRIPTION_NAME,
                content=content.format(
                    prescription_name=prescription_name,
                    package_name=project_name,
                    organization=organization,
                    repository=repository,
                ),
                commit_message=f"Project {project_name!r} hosts release notes on GitHub",
            )
            continue

        if response.status_code == 429:
            _LOGGER.error(
                "Bad HTTP status code %s when trying to obtain information for project %r: too many requests."
                "Exiting code with status 0.",
                response.status_code,
                project_name,
            )
            sys.exit(0)

        _LOGGER.info("No GitHub release notes detected for %r", project_name)
