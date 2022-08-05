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

"""Retrieve the number of downloads from PyPI for a given package."""


from datetime import datetime
from google.cloud import bigquery
import logging
import os
from typing import Any
from typing import Dict
from typing import Optional
from typing import Tuple

import thoth.prescriptions_refresh
from thoth.prescriptions_refresh.prescriptions import Prescriptions

_LOGGER = logging.getLogger(__name__)
_PRESCRIPTIONS_DEFAULT_REPO = Prescriptions.DEFAULT_PRESCRIPTIONS_REPO
_PRESCRIPTIONS_VERSION = thoth.prescriptions_refresh.__version__

_PYPI_POPULARITY_LOW = int(os.getenv("THOTH_PRESCRIPTIONS_REFRESH_PYPI_POPULARITY_LOW", 20))
_PYPI_POPULARITY_MODERATE = int(os.getenv("THOTH_PRESCRIPTIONS_REFRESH_PYPI_POPULARITY_MODERATE", 100))
_PYPI_POPULARITY_HIGH = int(os.getenv("THOTH_PRESCRIPTIONS_REFRESH_PYPI_POPULARITY_HIGH", 1000))

_PYPI_DOWNLOADS_TIME_INTERVAL = int(os.getenv("THOTH_PRESCRIPTIONS_REFRESH_PYPI_DOWNLOADS_TIME_INTERVAL", 180))

_PACKAGE_DOWNLOADS_PRESCRIPTION_NAME = "pypi_downloads.yaml"
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
        message: >-
          Project '{package_name}' is in the top {popularity_level}%
          most downloaded packages on PyPI in the last {days} days,
          with {downloads_count} downloads.
          The most downloaded package version is {most_downloaded_version} with {max_downloads} downloads.
        link: {package_link}
        package_name: {package_name}
        metadata:
        - prescriptions_repository: {default_prescriptions_repository}
          prescriptions_version: {prescriptions_version}
"""
_PACKAGE_DOWNLOADS_PRESCRIPTION_NAME_PER_VERSION = "pypi_downloads_per_version.yaml"
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
          version: "=={package_version}"
    run:
      justification:
      - type: INFO
        message: >-
          Project '{package_name}' version {package_version} had a {popularity_level} popularity level
          on PyPI in the last {days} days, with {downloads_count} downloads.
        link: {package_link}
        package_name: {package_name}
        metadata:
        - prescriptions_repository: {default_prescriptions_repository}
          prescriptions_version: {prescriptions_version}
"""


def _packages_total_downloads(package_downloads: Dict[Tuple[str, str], int]) -> Dict[str, int]:
    """Compute popularity of packages given their number of downloads."""
    project_popularity_dict: Dict[str, int] = {}
    for project, downloads in package_downloads.items():
        if project_popularity_dict[project[0]] in project_popularity_dict.keys():
            project_popularity_dict[project[0]] += downloads
        else:
            project_popularity_dict[project[0]] = downloads

    return project_popularity_dict


def _plot_statistics(
    package_downloads: Dict[Any, int],
    plots_path: str = ".",
    includes_versions: Optional[bool] = False,
) -> None:
    """Plot downloads statistics for packages."""
    import matplotlib.pyplot as plt

    plt.bar(package_downloads.keys(), package_downloads.values())
    plt.suptitle("Number of downloads per package")
    plt.xticks()

    if includes_versions:
        plt.savefig(os.path.join(plots_path, f"package_downloads_with_versions_{datetime.now()}.png"))
    else:
        plt.savefig(os.path.join(plots_path, f"package_downloads_{datetime.now()}.png"))


def _popularity_level(packages_total_downloads: Dict[str, int], package_name: str) -> Tuple[str, str]:
    """Compute the popularity level of a package."""
    downloads = sorted(list(packages_total_downloads.values()))
    percentile = downloads.index(packages_total_downloads[package_name]) / len(downloads) * 100
    return str(max(downloads)), str(percentile)


def _downloads_to_popularity(downloads: int) -> str:
    """Return the popularity of a package according to its number of downloads."""
    if downloads < _PYPI_POPULARITY_LOW:
        return "low"
    if downloads < _PYPI_POPULARITY_MODERATE:
        return "moderate"
    if downloads < _PYPI_POPULARITY_HIGH:
        return "high"
    return "very high"


def pypi_downloads(prescriptions: "Prescriptions") -> None:
    """Retrieve the number of downloads for PyPI packages."""
    _LOGGER.info("Querying number of package downloads available in BigQuery")

    client = bigquery.Client()
    dataset_id = "pypi_downloads"
    dataset_id_full = f"{client.project}.{dataset_id}"
    dataset = bigquery.Dataset(dataset_id_full)
    dataset = client.create_dataset(dataset)

    job_labels = {"query_target": "pypi-file_downloads"}
    job_config = bigquery.QueryJobConfig(labels=job_labels)

    query = f"""
    SELECT *
    FROM `bigquery-public-data.pypi.file_downloads`
    WHERE DATE(timestamp)
        BETWEEN DATE_SUB(CURRENT_DATE(), INTERVAL {_PYPI_DOWNLOADS_TIME_INTERVAL} DAY)
        AND CURRENT_DATE()
    """
    query_job = client.query(query=query, job_config=job_config)

    rows = query_job.result()
    packages_downloads_dict: Dict[Tuple[str, str], int] = {}
    for row in rows:
        packages_downloads_dict[(row.file.project, row.file.version)] = (
            packages_downloads_dict.get((row.file.project, row.file.version), 0) + 1
        )

    # plot statistics:

    # concatenated_package_version_dict = {
    #     package[0] + " " + package[1]: downloads for package, downloads in packages_downloads_dict.items()
    # }

    # _LOGGER.info("Creating plots of the number of downloads per package and per package version")
    # _plot_statistics(packages_downloads_dict)
    # _plot_statistics(concatenated_package_version_dict, includes_versions=True)

    packages_total_downloads = _packages_total_downloads(packages_downloads_dict)
    for project_name in prescriptions.iter_projects():
        prescription_name = prescriptions.get_prescription_name("PackagePopularityWrap", project_name)

        downloads_count, popularity_level = _popularity_level(packages_total_downloads, project_name)
        package_link = f"https://pypi.org/project/{project_name}"

        package_versions_downloads = {
            (package[0], package[1]): downloads
            for package, downloads in packages_downloads_dict.items()
            if package[0] == project_name
        }
        max_downloaded_version_name, max_downloaded_version_downloads_count = max(
            zip(package_versions_downloads.keys(), package_versions_downloads.values())
        )
        most_downloaded_version = max_downloaded_version_name[0] + "version" + max_downloaded_version_name[1]

        prescriptions.create_prescription(
            project_name=project_name,
            prescription_name=_PACKAGE_DOWNLOADS_PRESCRIPTION_NAME,
            content=_PACKAGE_DOWNLOADS_PRESCRIPTION_CONTENT.format(
                days=_PYPI_DOWNLOADS_TIME_INTERVAL,
                package_name=project_name,
                prescription_name=prescription_name,
                popularity_level=popularity_level,
                downloads_count=downloads_count,
                package_link=package_link,
                most_downloaded_version=most_downloaded_version,
                max_downloads=max_downloaded_version_downloads_count,
                default_prescriptions_repository=_PRESCRIPTIONS_DEFAULT_REPO,
                prescriptions_version=_PRESCRIPTIONS_VERSION,
            ),
        )

        for package_version, version_downloads_count in package_versions_downloads.items():
            prescription_name_per_version = prescriptions.get_prescription_name(
                "PackagePopularityPerVersionWrap", package_version[0], package_version[1]
            )

            prescriptions.create_prescription(
                project_name=project_name,
                prescription_name=_PACKAGE_DOWNLOADS_PRESCRIPTION_NAME_PER_VERSION,
                content=_PACKAGE_DOWNLOADS_PER_VERSION_PRESCRIPTION_CONTENT.format(
                    days=_PYPI_DOWNLOADS_TIME_INTERVAL,
                    package_name=project_name,
                    prescription_name=prescription_name_per_version,
                    package_version=package_version[1],
                    popularity_level=_downloads_to_popularity(int(version_downloads_count)),
                    downloads_count=version_downloads_count,
                    package_link=package_link,
                    default_prescriptions_repository=_PRESCRIPTIONS_DEFAULT_REPO,
                    prescriptions_version=_PRESCRIPTIONS_VERSION,
                ),
            )
