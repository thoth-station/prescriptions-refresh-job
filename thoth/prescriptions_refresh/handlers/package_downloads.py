#!/usr/bin/env python3
# thoth-prescriptions-refresh
# Copyright(C) 2021 Red Hat, Inc.
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

"""Retrieve the number of downloads from PyPI for a given package"""


from datetime import datetime
from google.cloud import bigquery
import logging
import matplotlib.pyplot as plt
import os
from typing import TYPE_CHECKING
from typing import Any
from typing import Dict
from typing import Optional
from typing import Tuple

if TYPE_CHECKING:
    from thoth.prescriptions_refresh.prescriptions import Prescriptions

_LOGGER = logging.getLogger(__name__)

_PYPI_POPULARITY_LOW = int(os.getenv("THOTH_PRESCRIPTIONS_REFRESH_PYPI_POPULARITY_LOW", 20))
_PYPI_POPULARITY_MODERATE = int(os.getenv("THOTH_PRESCRIPTIONS_REFRESH_PYPI_POPULARITY_MODERATE", 100))
_PYPI_POPULARITY_HIGH = int(os.getenv("THOTH_PRESCRIPTIONS_REFRESH_PYPI_POPULARITY_HIGH", 1000))

_PACKAGE_DOWNLOADS_PRESCRIPTION_NAME = "package_downloads.yaml"
_PACKAGE_DOWNLOADS_PRESCRIPTION_CONTENT = """\
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
        message: |
            Project '{package_name}' is in the top {popularity_level}% most downloaded packages on PyPI in the last six months, with {downloads_count} downloads.
            Project versions popularity:
            {popularity_per_version_summary}
        link: {package_link}
        package_name: {package_name}
"""
_PACKAGE_DOWNLOADS_PRESCRIPTION_NAME_PER_VERSION = "package_downloads_per_version.yaml"
_PACKAGE_DOWNLOADS_PER_VERSION_PRESCRIPTION_CONTENT = """\
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
        message: Project '{package_name}' version {package_version} had a {popularity_level} popularity level on PyPI in the last six months, with {downloads_count} downloads.
        link: {package_link}
        package_name: {package_name}
"""


def _packages_total_downloads(package_downloads: Dict[Tuple[str, str], int]) -> Dict[str, int]:
    """Compute popularity of packages given their number of downloads"""
    project_popularity_dict = {}
    for project, downloads in package_downloads.items():
        if project_popularity_dict[project[0]] in project_popularity_dict.keys():
            project_popularity_dict[project[0]] += downloads
        else:
            project_popularity_dict[project[0]] = downloads

    return project_popularity_dict


def _plot_statistics(
    package_downloads: Dict[Any, int], plots_path: Optional[str] = ".", includes_versions: Optional[bool] = False
) -> None:
    """Plot downloads statistics for packages"""

    plt.bar(package_downloads.keys(), package_downloads.values())
    plt.suptitle("Number of downloads per package")
    plt.xticks()

    if includes_versions:
        plt.savefig(os.path.join(plots_path, f"package_downloads_with_versions_{datetime.now()}.png"))
    else:
        plt.savefig(os.path.join(plots_path, f"package_downloads_{datetime.now()}.png"))


def _popularity_level(packages_total_downloads: Dict[str, int], package_name: str) -> Tuple(str, str):
    """Compute the popularity level of a package"""
    downloads = sorted(list(packages_total_downloads.values()))
    percentile = downloads.index(packages_total_downloads[package_name]) / len(downloads) * 100
    return downloads, percentile


def _downloads_to_popularity(downloads: int) -> str:
    """Return the popularity of a package according to its number of downloads"""
    if downloads < _PYPI_POPULARITY_LOW:
        return "low"
    if downloads < _PYPI_POPULARITY_MODERATE:
        return "moderate"
    if downloads < _PYPI_POPULARITY_HIGH:
        return "high"
    return "very high"


def pypi_downloads(prescriptions: "Prescriptions") -> None:
    """Retrieve the number of downloads for PyPI packages"""
    _LOGGER.info("Querying number of package downloads available in BigQuery")
    client = bigquery.Client()

    query_job = client.query(
        """
    SELECT *
    FROM `bigquery-public-data.pypi.file_downloads`
    WHERE DATE(timestamp)
        BETWEEN DATE_SUB(CURRENT_DATE(), INTERVAL 180 DAY)
        AND CURRENT_DATE()
    """
    )

    rows = query_job.results()
    packages_downloads_dict = {}
    for row in rows:
        packages_downloads_dict[(row.file.project, row.file.version)] = (
            packages_downloads_dict.get((row.file.project, row.file.version), 0) + 1
        )

    concatenated_package_version_dict = {
        package[0] + " " + package[1]: downloads for package, downloads in packages_downloads_dict.items()
    }

    _LOGGER.info("Creating plots of the number of downloads per package and per package version")
    _plot_statistics(packages_downloads_dict)
    _plot_statistics(concatenated_package_version_dict, includes_versions=True)

    packages_total_downloads = _packages_total_downloads(packages_downloads_dict)
    for project_name in prescriptions.iter_projects():
        prescription_name = ""
        for part in map(str.capitalize, project_name.split("-")):
            prescription_name += part
        prescription_name += "PackagePopularityWrap"

        downloads_count, popularity_level = _popularity_level(packages_total_downloads, project_name)
        package_link = os.path.join("https://pypi.org/project/", project_name)

        package_versions_downloads = {
            (package[0], package[1]): downloads
            for package, downloads in packages_downloads_dict.items()
            if package[0] == project_name
        }
        popularity_per_version_summary = ""
        for package_version, downloads in package_versions_downloads:
            popularity_per_version_summary += f"'{package_version[0]}' version {package_version[1]} has a {_downloads_to_popularity(downloads)} popularity with {downloads} downloads in the last six months. \n"

        prescriptions.create_prescription(
            project_name=project_name,
            prescription_name=_PACKAGE_DOWNLOADS_PRESCRIPTION_NAME,
            content=_PACKAGE_DOWNLOADS_PRESCRIPTION_CONTENT.format(
                package_name=project_name,
                prescription_name=prescription_name,
                popularity_level=popularity_level,
                downloads_count=downloads_count,
                package_link=package_link,
                popularity_per_version_summary=popularity_per_version_summary,
            ),
        )

        for package_version, downloads_count in package_versions_downloads.items():
            prescription_name_per_version = ""
            for part in map(str.capitalize, package_version[0].split("-")):
                prescription_name_per_version += part
            prescription_name_per_version += f"{package_version[1]}PackagePopularityPerVersionWrap"

            prescriptions.create_prescription(
                project_name=project_name,
                prescription_name=_PACKAGE_DOWNLOADS_PRESCRIPTION_NAME,
                content=_PACKAGE_DOWNLOADS_PRESCRIPTION_CONTENT.format(
                    package_name=project_name,
                    prescription_name=prescription_name_per_version,
                    package_version=package_version[1],
                    popularity_level=_downloads_to_popularity(downloads_count),
                    downloads_count=downloads_count,
                    package_link=package_link,
                ),
            )
