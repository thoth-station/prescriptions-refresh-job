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

"""Warn if projects are known to have a lot of vulnerabilities.."""

import logging
import os

import thoth.prescriptions_refresh
from thoth.storages import GraphDatabase
from thoth.prescriptions_refresh.prescriptions import Prescriptions


_LOGGER = logging.getLogger(__name__)
_PRESCRIPTIONS_DEFAULT_REPO = Prescriptions.DEFAULT_PRESCRIPTIONS_REPO
_PRESCRIPTIONS_VERSION = thoth.prescriptions_refresh.__version__

_CVE_WARNING_COUNT = int(os.getenv("THOTH_PRESCRIPTIONS_REFRESH_CVE_WARNING_COUNT", 3))
_CVE_WARNING_PRESCRIPTION_NAME = "cve_warning.yaml"
_CVE_WARNING_PRESCRIPTION_CONTENT = """\
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
          Package '{package_name}' is known to have at least {cve_warning_count} vulnerabilities reported in releases
        link: cve_warning
        package_name: {package_name}
    metadata:
    - prescriptions_repository: {default_prescriptions_repository}
      prescriptions_version: {prescriptions_version}
      last_cve_database_update: {last_cve_database_update}
"""


def cve_warning(prescriptions: "Prescriptions") -> None:
    """Warn if projects are known to have a lot of vulnerabilities.."""
    graph = GraphDatabase()
    graph.connect()

    cve_timestamp = graph.get_cve_timestamp()

    for project_name in prescriptions.iter_projects():
        if len(graph.get_python_cve_records_all(project_name)) >= _CVE_WARNING_COUNT:
            prescription_name = prescriptions.get_prescription_name("CVEWarningWrap", project_name)

            prescriptions.create_prescription(
                project_name=project_name,
                prescription_name=_CVE_WARNING_PRESCRIPTION_NAME,
                content=_CVE_WARNING_PRESCRIPTION_CONTENT.format(
                    package_name=project_name,
                    prescription_name=prescription_name,
                    cve_warning_count=_CVE_WARNING_COUNT,
                    default_prescriptions_repository=_PRESCRIPTIONS_DEFAULT_REPO,
                    prescriptions_version=_PRESCRIPTIONS_VERSION,
                    last_cve_database_update=cve_timestamp,
                ),
                commit_message=f"Project {project_name!r} has at least {_CVE_WARNING_COUNT} vulnerabilities reported",
            )
        else:
            prescriptions.delete_prescription(
                project_name,
                _CVE_WARNING_PRESCRIPTION_NAME,
                commit_message=f"Project {project_name!r} has less than {_CVE_WARNING_COUNT} vulnerabilities reported",
                nonexisting_ok=True,
            )
