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

"""Warn users if a project has low number of maintainers or maintainers maintain small number of projects."""


import logging
import os
import datetime
from typing import Optional
from typing import List

import requests
from bs4 import BeautifulSoup
from dateutil import parser as datetime_parser

import thoth.prescriptions_refresh
from thoth.prescriptions_refresh.prescriptions import Prescriptions

_LOGGER = logging.getLogger(__name__)
_PRESCRIPTIONS_DEFAULT_REPO = Prescriptions.DEFAULT_PRESCRIPTIONS_REPO
_PRESCRIPTIONS_VERSION = thoth.prescriptions_refresh.__version__

_PYPI_MAINTAINER_PROJECTS_COUNT = int(os.getenv("THOTH_PRESCRIPTIONS_REFRESH_PYPI_MAINTAINER_PROJECTS_COUNT", 3))
_PYPI_PROJECT_MAINTAINERS_COUNT = int(os.getenv("THOTH_PRESCRIPTIONS_REFRESH_PYPI_PROJECT_MAINTAINERS_COUNT", 3))
_PYPI_MAINTAINER_JOINED_AGE_DAYS = int(os.getenv("THOTH_PRESCRIPTIONS_REFRESH_PYPI_MAINTAINER_JOINED_AGE_DAYS", 180))

_PYPI_MAINTAINER_PROJECTS_PRESCRIPTION_NAME = "pypi_maintainers.yaml"
_PYPI_MAINTAINER_PROJECTS_PRESCRIPTION_CONTENT = """\
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
          index_url: https://pypi.org/simple
    run:
      justification:
      - type: WARNING
        message: >-
          Project '{package_name}' is maintained by maintainers that maintain small
          number of projects on PyPI (less than {maintainer_projects_count})
        link: https://pypi.org/project/{package_name}/
        package_name: {package_name}
    metadata:
    - prescriptions_repository: {default_prescriptions_repository}
      prescriptions_version: {prescriptions_version}
"""

_PYPI_PROJECT_MAINTAINERS_PRESCRIPTION_NAME = "pypi_project_maintainers.yaml"
_PYPI_PROJECT_MAINTAINERS_PRESCRIPTION_CONTENT = """\
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
          index_url: https://pypi.org/simple
    run:
      justification:
      - type: WARNING
        message: Project '{package_name}' has low number of maintainers on PyPI (less than {project_maintainers_count})
        link: https://pypi.org/project/{package_name}/
        package_name: {package_name}
    metadata:
    - prescriptions_repository: {default_prescriptions_repository}
      prescriptions_version: {prescriptions_version}
"""


_PYPI_PROJECT_MAINTAINER_JOINED_AGE_PRESCRIPTION_NAME = "pypi_maintainers_joined.yaml"
_PYPI_PROJECT_MAINTAINER_JOINED_AGE_PRESCRIPTION_CONTENT = """\
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
          index_url: https://pypi.org/simple
    run:
      justification:
      - type: WARNING
        message: >-
          Project '{package_name}' has maintainers that joined PyPI
          recently (less than {maintainers_join_days} days ago)
        link: https://pypi.org/project/{package_name}/
        package_name: {package_name}
    metadata:
    - prescriptions_repository: {default_prescriptions_repository}
      prescriptions_version: {prescriptions_version}
"""


def _list_maintainers(project_name: str) -> Optional[List[str]]:
    """List all maintainers for the given project."""
    response = requests.get(f"https://pypi.org/project/{project_name}/")
    if response.status_code != 200:
        _LOGGER.error(
            "Failed to obtain project page from PyPI for %r (%d): %s", project_name, response.status_code, response.text
        )
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    maintainer_spans = soup.find_all("span", class_="sidebar-section__maintainer")
    return [m.text.strip() for m in maintainer_spans]


def _do_project_maintainers(prescriptions: "Prescriptions", project_name: str, maintainers: List[str]) -> None:
    """Warn if a project is maintained by a small number of maintainers on PyPI."""
    if len(maintainers) >= _PYPI_PROJECT_MAINTAINERS_COUNT:
        # Enough of maintainers.
        prescriptions.delete_prescription(
            project_name,
            _PYPI_PROJECT_MAINTAINERS_PRESCRIPTION_NAME,
            commit_message=f"Project {project_name!r} has at least "
            f"{_PYPI_PROJECT_MAINTAINERS_COUNT} maintainers on PyPI",
            nonexisting_ok=True,
        )
        return

    prescriptions.create_prescription(
        project_name=project_name,
        prescription_name=_PYPI_PROJECT_MAINTAINERS_PRESCRIPTION_NAME,
        content=_PYPI_PROJECT_MAINTAINERS_PRESCRIPTION_CONTENT.format(
            package_name=project_name,
            prescription_name=prescriptions.get_prescription_name("PyPIProjectMaintainersWrap", project_name),
            project_maintainers_count=_PYPI_PROJECT_MAINTAINERS_COUNT,
            default_prescriptions_repository=_PRESCRIPTIONS_DEFAULT_REPO,
            prescriptions_version=_PRESCRIPTIONS_VERSION,
        ),
        commit_message=f"Project {project_name!r} has less than {_PYPI_PROJECT_MAINTAINERS_COUNT} maintainers on PyPI",
    )


def _list_maintainer_projects(maintainer: str) -> Optional[List[str]]:
    """Get a listing of projects that the given maintainer maintainers."""
    response = requests.get(f"https://pypi.org/user/{maintainer}/")
    if response.status_code != 200:
        _LOGGER.error(
            "Failed to obtain user page from PyPI for %r (%d): %s", maintainer, response.status_code, response.text
        )
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    maintainer_spans = soup.find_all("h3", class_="package-snippet__title")
    return [m.text.strip() for m in maintainer_spans]


def _do_maintainer_projects(prescriptions: "Prescriptions", project_name: str, maintainers: List[str]) -> None:
    """Warn if all maintainers of a project maintain small number of projects on PyPI."""
    # TODO: we can do more sophisticated things here - e.g. check how relevant the given maintainer
    #   is based on popularity of projects she/he maintains.
    for maintainer in maintainers:
        maintainer_projects = _list_maintainer_projects(maintainer)
        if maintainer_projects is None:
            continue

        if len(maintainer_projects) >= _PYPI_MAINTAINER_PROJECTS_COUNT:
            _LOGGER.info(
                "Project %r is maintained by %r who has at least %d projects maintained",
                project_name,
                maintainer,
                _PYPI_MAINTAINER_PROJECTS_COUNT,
            )
            break
    else:
        # No trusted enough maintainer found.
        prescriptions.create_prescription(
            project_name=project_name,
            prescription_name=_PYPI_MAINTAINER_PROJECTS_PRESCRIPTION_NAME,
            content=_PYPI_MAINTAINER_PROJECTS_PRESCRIPTION_CONTENT.format(
                package_name=project_name,
                prescription_name=prescriptions.get_prescription_name("PyPIMaintainerProjectsWrap", project_name),
                maintainer_projects_count=_PYPI_PROJECT_MAINTAINERS_COUNT,
                default_prescriptions_repository=_PRESCRIPTIONS_DEFAULT_REPO,
                prescriptions_version=_PRESCRIPTIONS_VERSION,
            ),
            commit_message=f"Project {project_name!r} has no maintainer with at least "
            f"{_PYPI_MAINTAINER_PROJECTS_COUNT} projects on PyPI,",
        )
        return

    # A trusted maintainer found.
    prescriptions.delete_prescription(
        project_name,
        _PYPI_MAINTAINER_PROJECTS_PRESCRIPTION_NAME,
        commit_message=f"Project {project_name!r} has a maintainer with at least "
        f"{_PYPI_MAINTAINER_PROJECTS_COUNT} projects on PyPI",
        nonexisting_ok=True,
    )


def _get_maintainer_join_date(maintainer: str) -> Optional[datetime.datetime]:
    """Parse information when the given maintainer joined PyPI."""
    response = requests.get(f"https://pypi.org/user/{maintainer}/")
    if response.status_code != 200:
        _LOGGER.error(
            "Failed to obtain user page from PyPI for %r (%d): %s", maintainer, response.status_code, response.text
        )
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    for metadiv in soup.find_all("div", class_="author-profile__metadiv"):
        if metadiv.time and metadiv.time.get("datetime"):
            dt: datetime.datetime = datetime_parser.parse(metadiv.time.get("datetime"), ignoretz=True)
            return dt

    return None


def _do_maintainer_joined_warning(prescriptions: "Prescriptions", project_name: str, maintainers: List[str]) -> None:
    """Warn if a project is maintained by maintainers that joined recently."""
    today = datetime.datetime.today()
    for maintainer in maintainers:
        maintainer_join_date = _get_maintainer_join_date(maintainer)
        if maintainer_join_date is None:
            # This usually happens for maintainers that are on PyPI for some time. Recent users have datetime assigned.
            # Mind that if the datetime is not parsed for recent users, join date parsing logic needs to be adjusted.
            _LOGGER.warning("No join date parsed for maintainer %r, assuming old maintainer on PyPI", maintainer)
            break

        if (today - maintainer_join_date).days >= _PYPI_MAINTAINER_JOINED_AGE_DAYS:
            _LOGGER.info(
                "Project %r is maintained by %r who was registered on PyPI more than %d days ago",
                project_name,
                maintainer,
                _PYPI_MAINTAINER_JOINED_AGE_DAYS,
            )
            break
    else:
        # All maintainers joined PyPI recently.
        prescriptions.create_prescription(
            project_name=project_name,
            prescription_name=_PYPI_PROJECT_MAINTAINER_JOINED_AGE_PRESCRIPTION_NAME,
            content=_PYPI_PROJECT_MAINTAINER_JOINED_AGE_PRESCRIPTION_CONTENT.format(
                package_name=project_name,
                prescription_name=prescriptions.get_prescription_name("PyPIMaintainersJoinWrap", project_name),
                maintainers_join_days=_PYPI_MAINTAINER_JOINED_AGE_DAYS,
                default_prescriptions_repository=_PRESCRIPTIONS_DEFAULT_REPO,
                prescriptions_version=_PRESCRIPTIONS_VERSION,
            ),
            commit_message=f"Project {project_name!r} has maintainers who joined PyPI recently",
        )
        return

    # A trusted maintainer found.
    prescriptions.delete_prescription(
        project_name,
        _PYPI_PROJECT_MAINTAINER_JOINED_AGE_PRESCRIPTION_NAME,
        commit_message=f"Project {project_name!r} has maintainers who are on PyPI for a longer period of time",
        nonexisting_ok=True,
    )


def pypi_maintainers(prescriptions: "Prescriptions") -> None:
    """Warn users if a project has low number of maintainers or maintainers maintain small number of projects."""
    for project_name in prescriptions.iter_projects():
        _LOGGER.debug("Computing warnings for PyPI maintainers for %r", project_name)
        maintainers = _list_maintainers(project_name)
        if maintainers is None:
            continue

        _do_project_maintainers(prescriptions, project_name, maintainers)
        _do_maintainer_projects(prescriptions, project_name, maintainers)
        _do_maintainer_joined_warning(prescriptions, project_name, maintainers)
