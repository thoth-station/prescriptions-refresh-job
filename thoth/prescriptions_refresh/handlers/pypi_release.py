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

"""Warn if the project has no recent releases."""

import datetime
import logging
import os

import requests
from dateutil import parser as datetime_parser

import thoth.prescriptions_refresh
from thoth.prescriptions_refresh.prescriptions import Prescriptions

_LOGGER = logging.getLogger(__name__)
_PRESCRIPTIONS_DEFAULT_REPO = Prescriptions.DEFAULT_PRESCRIPTIONS_REPO
_PRESCRIPTIONS_VERSION = thoth.prescriptions_refresh.__version__

_PYPI_RELEASE_DAYS = int(os.getenv("THOTH_PRESCRIPTIONS_PYPI_RELEASE_DAYS", 180))
_PYPI_RELEASE_WARNING_PRESCRIPTION_NAME = "pypi_release.yaml"
_PYPI_RELEASE_WARNING_PRESCRIPTION_CONTENT = """\
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
        message: >-
          Package '{package_name}' has no recent release, last release dates back to {last_release_datetime}
        link: https://pypi.org/project/{package_name}/#history
        package_name: {package_name}
    metadata:
    - prescriptions_repository: {default_prescriptions_repository}
      prescriptions_version: {prescriptions_version}
"""


def pypi_release(prescriptions: "Prescriptions") -> None:
    """Warn if the project has no recent releases."""
    today = datetime.datetime.now()

    for project_name in prescriptions.iter_projects():
        _LOGGER.debug("Checking PyPI release information for project %r", project_name)
        response = requests.get(f"https://pypi.org/pypi/{project_name}/json")
        if response.status_code != 200:
            _LOGGER.error(
                "Failed to obtain information about project %r from PyPI's JSON API (%d): %s",
                project_name,
                response.status_code,
                response.text,
            )
            continue

        if not response.json()["urls"]:
            # XXX: we could check the preceding one here to be more accurate.
            _LOGGER.warning("No releases found for %r on PyPI JSON API", project_name)
            continue

        # We take information from artifact upload time. If there is no recent artifact uploaded, create a prescription.
        last_release_datetime = max(
            datetime_parser.parse(i["upload_time_iso_8601"], ignoretz=True) for i in response.json()["urls"]
        )

        if (today - last_release_datetime).days > _PYPI_RELEASE_DAYS:
            prescriptions.create_prescription(
                project_name=project_name,
                prescription_name=_PYPI_RELEASE_WARNING_PRESCRIPTION_NAME,
                content=_PYPI_RELEASE_WARNING_PRESCRIPTION_CONTENT.format(
                    package_name=project_name,
                    prescription_name=prescriptions.get_prescription_name("PyPIReleaseWrap", project_name),
                    last_release_datetime=last_release_datetime,
                    default_prescriptions_repository=_PRESCRIPTIONS_DEFAULT_REPO,
                    prescriptions_version=_PRESCRIPTIONS_VERSION,
                ),
                commit_message=f"Project {project_name!r} has no recent releases",
            )
        else:
            prescriptions.delete_prescription(
                project_name,
                _PYPI_RELEASE_WARNING_PRESCRIPTION_NAME,
                commit_message=f"Project {project_name!r} has a recent release",
                nonexisting_ok=True,
            )
