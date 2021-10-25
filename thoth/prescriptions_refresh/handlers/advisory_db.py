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

"""Check advisory-db as published by PyPA."""

import logging
import os
import tempfile
import yaml
from urllib.parse import urlparse

from git import Repo
from thoth.common.helpers import datetime2datetime_str
from thoth.common import get_justification_link as jl

from typing import Any
from typing import Dict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from thoth.prescriptions_refresh.prescriptions import Prescriptions

_LOGGER = logging.getLogger(__name__)
_ADVISORY_DB_GIT = os.getenv("THOTH_PRESCRIPTIONS_REFRESH_ADVISORY_DB_GIT", "https://github.com/pypa/advisory-db.git")
_CVE_PENALIZATION = float(os.getenv("THOTH_PRESCRIPTIONS_REFRESH_CVE_PENALIZATION", -0.1))

_ADVISORY_DB_JUSTIFICATION = """\
units:
  sieves:
  - name: {prescription_name}AdvisoryDBNotAcceptableSieve
    type: sieve
    should_include:
      adviser_pipeline: true
      recommendation_types:
      - security
    match:
      package_version:
        name: {package_name}
        version: {package_version}
        index_url: https://pypi.org/simple
    run:
      log:
        type: WARNING
        message: >-
          Package {package_name} in version {package_version} has a vulnerability {cve_name}, trying
          to find another resolution path
      stack_info:
      - type: WARNING
        message: >-
          Package {package_name} in version {package_version} has a vulnerability {cve_name}, trying
          to find another resolution path
        link: {link}

  steps:
  - name: {prescription_name}AdvisoryDBWarningStep
    type: step
    should_include:
      adviser_pipeline: true
      recommendation_types:
      - latest
      - testing
    match:
      package_version:
        name: {package_name}
        version: {package_version}
        index_url: https://pypi.org/simple
    run:
      justification:
      - type: WARNING
        message: Package {package_name} has a vulnerability {cve_name}
        link: {link}
        package_name: {package_name}
        cve_name: {cve_name}
        advisory: "{advisory}"

  - name: {prescription_name}AdvisoryDBPenalizeStep
    type: step
    should_include:
      adviser_pipeline: true
      recommendation_types:
      - performance
      - stable
    match:
      package_version:
        name: {package_name}
        version: {package_version}
        index_url: https://pypi.org/simple
    run:
      log:
        type: WARNING
        message: >-
          Penalizing resolution of {package_name} in versions {package_version} due to vulnerability {cve_name}
      stack_info:
      - type: WARNING
        message: >-
          Penalizing resolution of {package_name} in versions {package_version} due to vulnerability {cve_name}
        link: {link}
      justification:
      - type: WARNING
        message: Package {package_name} has a vulnerability {cve_name}
        link: {link}
        package_name: {package_name}
        cve_name: {cve_name}
        advisory: "{advisory}"
      score: {score}
"""

_ADVISORY_DB_TIMESTAMP = """\
units:
  boots:
  - name: AdvisoryDBTimestampInfoBoot
    type: boot
    should_include:
      adviser_pipeline: true
    run:
      stack_info:
      - type: INFO
        message: >-
          Using security information from PyPA/advisory-db as of {datetime!r}
        link: https://github.com/pypa/advisory-db
"""


def _get_vulnerability_link(vulnerability_record: Dict[str, Any]) -> None:
    """Get a link for the given vulnerability."""
    link = jl("cve")
    for reference in vulnerability_record.get("references") or []:
        if reference.get("type") != "WEB":
            _LOGGER.debug("Skipping reference %r: not a WEB reference", reference)
            continue

        if "redhat" in urlparse(reference["url"]).netloc:
            # Get first reference to a Red Hat bugzilla or a similar Red Hat source.
            link = reference["url"]
            break

    return link


def _create_prescriptions(prescriptions: "Prescriptions", vulnerability: str, vulnerability_record: Dict[str, Any]) -> None:
    """Create a prescription out of a vulnerability record in PyPA/advisory-db.

    See https://ossf.github.io/osv-schema/
    """
    for affected_idx, affected in enumerate(vulnerability_record["affected"]):
        if affected["package"]["ecosystem"] != "PyPI":
            _LOGGER.warning("Skipping vulnerability record for %r, not a PyPI record", affected["package"]["ecosystem"])
            continue

        if not affected.get("versions"):
            _LOGGER.warning("No versions found for vulnerability record %r", vulnerability)
            continue

        package_name = affected["package"]["name"]
        for version in affected["versions"]:
            prescription_name = f"{vulnerability.lower().replace('-', '_')}-{version}.yaml"
            prescriptions.create_prescription(
                project_name=package_name,
                prescription_name=prescription_name,
                content=_ADVISORY_DB_JUSTIFICATION.format(
                    advisory=vulnerability_record["details"].replace('\\', '\\\\').replace('"', '\\"'),
                    cve_name=vulnerability_record["id"],
                    link=_get_vulnerability_link(vulnerability_record),
                    package_name=package_name,
                    package_version=f"==={version}",
                    prescription_name=prescription_name,
                    score=_CVE_PENALIZATION,
                ),
                commit_message=f"New vulnerability record {vulnerability} for {package_name}",
            )


def _process_advisory_db(prescriptions: "Prescriptions", path: str) -> None:
    """Process the advisory db and create prescriptions out of it."""
    vulns_dir_listing = os.listdir(os.path.join(path, "vulns"))
    for package_name in vulns_dir_listing:
        vulnerability_records_dir = os.path.join(path, "vulns", package_name)
        if not os.path.isdir(vulnerability_records_dir):
            _LOGGER.debug("Skipping %r: not a directory", vulnerability_records_dir)
            continue

        for file_record in os.listdir(vulnerability_records_dir):
            file_path = os.path.join(vulnerability_records_dir, file_record)
            if not os.path.isfile(file_path):
                _LOGGER.warning("Skipping %r: not a file", file_path)
                continue

            with open(file_path) as f:
                vulnerability_record = yaml.safe_load(f)

            vulnerability_name = os.path.basename(file_record)
            if vulnerability_name.endswith(".yaml"):
                vulnerability_name = vulnerability_name[:-len(".yaml")]

            try:
                _create_prescriptions(prescriptions, vulnerability_name, vulnerability_record)
            except Exception:
                _LOGGER.exception("Failed to create prescriptions for %r", file_record)


def advisory_db(prescriptions: "Prescriptions") -> None:
    """Obtain CVE information from PyPA's advisory database."""
    datetime = datetime2datetime_str()

    with tempfile.TemporaryDirectory() as tmpdir:
        _LOGGER.info("Cloning PyPA/advisory-db from %r", _ADVISORY_DB_GIT)
        repo = Repo.clone_from(_ADVISORY_DB_GIT, tmpdir, depth=1)
        _process_advisory_db(prescriptions, repo.working_tree_dir)

    prescriptions.create_prescription(
        project_name=f"_generic",
        prescription_name="advisory_db.yaml",
        content=_ADVISORY_DB_TIMESTAMP.format(
            datetime=datetime,
        ),
        commit_message="CVE database from PyPA/advisory-db has been successfully updated",
    )
