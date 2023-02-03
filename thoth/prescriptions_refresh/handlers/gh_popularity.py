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

"""Check popularity of the given package."""

import logging
import os
import requests
import sys
from typing import Any
from typing import Tuple
from typing import Dict

import thoth.prescriptions_refresh
from thoth.prescriptions_refresh.prescriptions import Prescriptions
from .gh_link import iter_gh_info


_LOGGER = logging.getLogger(__name__)
_PRESCRIPTIONS_DEFAULT_REPO = Prescriptions.DEFAULT_PRESCRIPTIONS_REPO
_PRESCRIPTIONS_VERSION = thoth.prescriptions_refresh.__version__

_GH_POPULARITY_LOW = int(os.getenv("THOTH_PRESCRIPTIONS_REFRESH_GH_POPULARITY_LOW", 20))
_GH_POPULARITY_MODERATE = int(os.getenv("THOTH_PRESCRIPTIONS_REFRESH_GH_POPULARITY_MODERATE", 100))
_GH_POPULARITY_HIGH = int(os.getenv("THOTH_PRESCRIPTIONS_REFRESH_GH_POPULARITY_HIGH", 1000))
_GH_LINK_PRESCRIPTION_NAME = "gh_popularity.yaml"
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
      - type: {message_type}
        message: Project '{package_name}' has {popularity_score} popularity on GitHub
        link: {gh_link}
        package_name: {package_name}
    metadata:
    - prescriptions_repository: {default_prescriptions_repository}
      prescriptions_version: {prescriptions_version}
"""


def _compute_popularity(github_response: Dict[str, Any]) -> Tuple[str, str]:
    """Compute popularity based on GitHub statistics."""
    # This computation is pretty simple as of now. Based on the data aggregated from the dataset on 16th
    # September, median is 108 and the distribution was very wide (hence a simple comparision). We could
    # also introduce more sophisticated computation that would involve historical data and community behavior.
    score = github_response["forks_count"] + github_response["stargazers_count"] + github_response["watchers_count"]

    if score < _GH_POPULARITY_LOW:
        return "low", "WARNING"

    if score < _GH_POPULARITY_MODERATE:
        return "moderate", "INFO"

    if score < _GH_POPULARITY_HIGH:
        return "high", "INFO"

    return "very high", "INFO"


def gh_popularity(prescriptions: "Prescriptions") -> None:
    """Check popularity of the given project."""
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

        popularity_score, message_type = _compute_popularity(response.json())

        prescription_name = prescriptions.get_prescription_name("GitHubPopularityWrap", project_name)

        prescriptions.create_prescription(
            project_name=project_name,
            prescription_name=_GH_LINK_PRESCRIPTION_NAME,
            content=_GH_LINK_PRESCRIPTION_CONTENT.format(
                gh_link=gh_link,
                package_name=project_name,
                popularity_score=popularity_score,
                message_type=message_type,
                prescription_name=prescription_name,
                default_prescriptions_repository=_PRESCRIPTIONS_DEFAULT_REPO,
                prescriptions_version=_PRESCRIPTIONS_VERSION,
            ),
            commit_message=f"Update of GitHub popularity statistics for project {project_name!r}",
        )
