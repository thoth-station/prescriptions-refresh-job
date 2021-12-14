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

"""Inform users about large artifacts on PyPI."""

import logging
from typing import TYPE_CHECKING

import requests

if TYPE_CHECKING:
    from thoth.prescriptions_refresh.prescriptions import Prescriptions

_LOGGER = logging.getLogger(__name__)
_PYPI_ARTIFACT_SIZE_PRESCRIPTION_NAME = "pypi_artifact_size.yaml"
_PYPI_ARTIFACT_SIZE_PRESCRIPTION_CONTENT = """\
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
          version: {package_version}
          index_url: https://pypi.org/simple
    run:
      justification:
      - type: INFO
        message: >-
          Installed artifact size for package '{package_name}' in version
          '{package_version}' can have up to {artifact_size}
        link: https://pypi.org/project/{package_name}/{package_version}/#files
        package_name: {package_name}
"""


def _get_artifact_size_str(artifact_size: int) -> str:
    """Get size of artifact in a human-readable form."""
    suffix = "B"
    artifact_size_float = float(artifact_size)
    if artifact_size_float >= 1024:
        artifact_size_float /= 1024
        suffix = "KiB"
    if artifact_size_float >= 1024:
        artifact_size_float /= 1024
        suffix = "MiB"
    if artifact_size_float >= 1024:
        artifact_size_float /= 1024
        suffix = "GiB"

    return f"{artifact_size_float:0.2f}{suffix}"


def pypi_artifact_size(prescriptions: "Prescriptions") -> None:
    """Produce messages that show artifact size."""
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

        for package_version, release_info in response.json()["releases"].items():
            if not release_info:
                _LOGGER.warning("No release information found for %r in version %r", project_name, package_version)
                continue

            artifact_size = max(i["size"] for i in release_info)
            prescriptions.create_prescription(
                project_name=project_name,
                prescription_name=_PYPI_ARTIFACT_SIZE_PRESCRIPTION_NAME,
                content=_PYPI_ARTIFACT_SIZE_PRESCRIPTION_CONTENT.format(
                    package_name=project_name,
                    package_version=package_version,
                    artifact_size=_get_artifact_size_str(artifact_size),
                    prescription_name=prescriptions.get_prescription_name(
                        "PyPIArtifactSizeWrap", project_name, package_version
                    ),
                ),
                commit_message=f"Artifact size info for package {project_name!r} in version {package_version!r}",
            )
