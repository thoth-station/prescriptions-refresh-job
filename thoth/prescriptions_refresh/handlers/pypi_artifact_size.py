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
import os

import requests
from packaging.specifiers import SpecifierSet
from thoth.storages import GraphDatabase
from thoth.python.package_version import Version

import thoth.prescriptions_refresh
from thoth.prescriptions_refresh.prescriptions import Prescriptions

_LOGGER = logging.getLogger(__name__)
_PRESCRIPTIONS_DEFAULT_REPO = Prescriptions.DEFAULT_PRESCRIPTIONS_REPO
_PRESCRIPTIONS_VERSION = thoth.prescriptions_refresh.__version__

# Report only 3MiB+
_PYPI_ARTIFACT_REPORT_SIZE = int(os.getenv("THOTH_PRESCRIPTIONS_REFRESH_PYPI_ARTIFACT_REPORT_SIZE", 3 * 1024 * 1024))
_PYPI_ARTIFACT_SIZE_PRESCRIPTION_NAME = "pypi_artifact_size.yaml"
_PYPI_ARTIFACT_SIZE_PRESCRIPTION_CONTENT = """\
  - name: {prescription_name}
    type: wrap
    should_include:
      adviser_pipeline: true
    match:
      state:
        resolved_dependencies:
        - name: {package_name}
          version: =={package_version}
          index_url: https://pypi.org/simple
    run:
      justification:
      - type: INFO
        message: >-
          Installed artifact size for package '{package_name}' in version
          '{package_version}' can have up to {artifact_size}
        link: https://pypi.org/project/{package_name}/{package_version}/#files
        package_name: {package_name}
        metadata:
        - prescriptions_repository: {default_prescriptions_repository}
          prescriptions_version: {prescriptions_version}
"""


def pypi_artifact_size(prescriptions: "Prescriptions") -> None:
    """Produce messages that show artifact size."""
    graph = GraphDatabase()
    graph.connect()

    report_size_str = prescriptions.get_artifact_size_str(_PYPI_ARTIFACT_REPORT_SIZE)
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

        solver_rules = graph.get_python_rule_all(package_name=project_name, count=None)

        content = ""
        for package_version, release_info in response.json()["releases"].items():
            if not release_info:
                _LOGGER.warning("No release information found for %r in version %r", project_name, package_version)
                continue

            version = Version(package_version)
            if version.is_legacy_version:
                _LOGGER.warning(
                    "Skipping version %r: the version identifier is a legacy version identifier", package_version
                )
                continue

            for solver_rule in solver_rules:
                if solver_rule["index_url"] not in ("https://pypi.org/simple", None):
                    _LOGGER.debug("Solver rule skipped as it does not apply to PyPI: %r", solver_rule)
                    continue

                if not solver_rule["version_range"] or package_version in SpecifierSet(solver_rule["version_range"]):
                    _LOGGER.info(
                        "Skipping adding version %r of %r as it matches solver rule configured: %r",
                        package_version,
                        project_name,
                        solver_rule,
                    )
                    break
            else:
                artifact_size = max(i["size"] for i in release_info)

                if artifact_size < _PYPI_ARTIFACT_REPORT_SIZE:
                    _LOGGER.info(
                        "Artifact size for %r in version %s has less than %s: not creating prescription for it",
                        project_name,
                        package_version,
                        report_size_str,
                    )
                    continue

                content += _PYPI_ARTIFACT_SIZE_PRESCRIPTION_CONTENT.format(
                    package_name=project_name,
                    package_version=package_version,
                    artifact_size=prescriptions.get_artifact_size_str(artifact_size),
                    prescription_name=prescriptions.get_prescription_name(
                        "PyPIArtifactSizeWrap", project_name, package_version
                    ),
                    default_prescriptions_repository=_PRESCRIPTIONS_DEFAULT_REPO,
                    prescriptions_version=_PRESCRIPTIONS_VERSION,
                )

        if not content:
            _LOGGER.warning("No PyPI artifact size related prescriptions were computed for %r", project_name)
            continue

        prescriptions.create_prescription(
            project_name=project_name,
            prescription_name=_PYPI_ARTIFACT_SIZE_PRESCRIPTION_NAME,
            content=f"units:\n  wraps:\n{content}",
            commit_message=f"Artifact size info from PyPI for package {project_name!r}",
        )
