#!/usr/bin/env python3
# thoth-prescriptions-refresh
# Copyright(C) 2021 Bjoern Hasemann
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

"""Check project URLs leading to GitHub."""

import logging
import requests
import yaml
import os
from urllib.parse import urlparse
from typing import Generator
from typing import List
from typing import Optional
from typing import Tuple
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from thoth.prescriptions_refresh.knowledge import Knowledge
    from thoth.prescriptions_refresh.prescriptions import Prescriptions

_LOGGER = logging.getLogger(__name__)
_GH_LINK_PRESCRIPTION_NAME = "gh_link.yaml"
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
      - type: INFO
        message: Package '{package_name}' is hosted on GitHub
        link: {gh_url}
        package_name: {package_name}
"""


def _get_urls(project_name: str) -> List[str]:
    """Get GitHub URL candidates for the given project."""
    response = requests.get(f"https://pypi.org/pypi/{project_name}/json")
    if response.status_code == 404:
        _LOGGER.warning("Package %r not found on PyPI", project_name)
        return []
    elif response.status_code != 200:
        _LOGGER.error(
            "Bad HTTP status code (%s) when obtaining information about %r",
            response.status_code,
            project_name,
            response.text,
        )
        return []

    package_info = response.json().get("info") or {}

    url_candidates = []
    if package_info.get("home_page"):
        url_candidates.append(package_info["home_page"])

    if package_info.get("package_url"):
        url_candidates.append(package_info["package_url"])

    if package_info.get("project_urls"):
        url_candidates.extend(package_info["project_urls"].values())

    return url_candidates


def _get_gh_url(project_name: str) -> Optional[str]:
    """Check URL candidates for any which match GitHub or GitLab."""
    for url in _get_urls(project_name):
        if not url:
            _LOGGER.debug(
                "Skipping URL as it is not recognized as a GitHub repository: %r",
                url,
            )
            continue

        url_netloc = urlparse(url).netloc
        if not url_netloc.startswith("github.com"):
            _LOGGER.debug(
                "Skipping URL as it is not recognized as a GitHub repository: %r",
                url,
            )
            continue

        _LOGGER.debug("Processing URL: %r", url)
        url_path_parts = urlparse(url).path.split("/")[1:]

        if len(url_path_parts) < 2:
            _LOGGER.warning("Skipping URL as GitHub repository and organization cannot be parsed: %r", url)
            continue

        org, repo = url_path_parts[:2]
        source_url = f"https://{url_netloc}/{org}/{repo}"
        try:
            response = requests.head(source_url)
        except Exception:
            _LOGGER.exception("Failed to obtain %r information for %r with requests.head()", source_url, project_name)
        else:
            if response.status_code == 200:
                return source_url
            else:
                _LOGGER.debug(
                    "%r is an invalid GitHub URL based on HTTP status code %r: %s",
                    source_url,
                    response.status_code,
                    response.text,
                )

    return None


def iter_gh_info(prescriptions: "Prescriptions") -> Generator[Tuple[str, str, str], None, None]:
    """Get GitHub link from already stored prescriptions.

    This method is suitable to be used in other handlers that reuse GitHub URL link.
    """
    for prescription_path, prescription in prescriptions.iter_prescriptions_yaml():
        if prescriptions.get_prescription_name_from_path(prescription_path) != "gh_link.yaml":
            continue

        # We obtain GitHub URL from gh_link.yaml prescriptions and check if the given project is archived on GitHub.
        with open(os.path.join(prescriptions.repo.working_dir, prescription_path), "r") as prescription_file:
            content = yaml.safe_load(prescription_file)

        try:
            gh_link = content["units"]["wraps"][0]["run"]["justification"][0]["link"]
        except (KeyError, IndexError):
            _LOGGER.error("Failed to parse GitHub link from %r, skipping...", prescription_path)
            continue

        _LOGGER.debug("Using GitHub link %r", gh_link)
        parsed_url = urlparse(gh_link)
        parts = parsed_url.path.split("/")
        if len(parts) != 3:
            _LOGGER.error(
                "Failed to parse organization and repository from %r in prescription %r",
                parts,
                prescription_path,
            )
            continue

        organization = parts[1]
        repository = parts[2]
        project_name = prescriptions.project_name_from_prescription_path(prescription_path)

        yield project_name, organization, repository


def gh_link(knowledge: "Knowledge") -> None:
    """Check GitHub links available in the project info on PyPI."""
    for project_name in knowledge.iter_projects():
        gh_url = _get_gh_url(project_name)
        if gh_url:
            prescription_name = ""
            for part in map(str.capitalize, project_name.split("-")):
                prescription_name += part
            prescription_name += "GitHubURLWrap"

            prescription_content = _GH_LINK_PRESCRIPTION_CONTENT.format(
                package_name=project_name,
                gh_url=gh_url,
                prescription_name=prescription_name,
            )

            knowledge.prescriptions.create_prescription(
                project_name=project_name,
                prescription_name=_GH_LINK_PRESCRIPTION_NAME,
                content=prescription_content,
                commit_message=f"Package {project_name!r} is hosted on GitHub",
            )
        else:
            _LOGGER.info("Project %r has no GitHub URL associated", project_name)
            knowledge.prescriptions.delete_prescription(
                project_name,
                _GH_LINK_PRESCRIPTION_NAME,
                commit_message=f"GitHub URL for {project_name!r} is not active anymore",
                nonexisting_ok=True,
            )
