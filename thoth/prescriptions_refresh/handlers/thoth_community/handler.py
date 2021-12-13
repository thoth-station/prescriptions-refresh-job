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

"""Compute community statistics in Thoth - how Thoth users use packages."""

import logging
import os
from datetime import datetime
from collections import Counter
from datetime import date
from datetime import timedelta
from typing import Counter as CounterType
from typing import Optional
from typing import Tuple
from typing import TYPE_CHECKING

import attr
from thoth.common import datetime2datetime_str
from thoth.common import map_os_name
from thoth.common import normalize_os_version
from thoth.prescriptions_refresh.prescriptions_change import PrescriptionsChange
from thoth.storages import AdvisersResultsStore

from .content import PRESCRIPTION_TOP_PACKAGE_NAMES
from .content import PRESCRIPTION_TOP_PACKAGE_VERSIONS
from .content import PRESCRIPTION_TOP_DEV_PACKAGE_NAMES
from .content import PRESCRIPTION_TOP_DEV_PACKAGE_VERSIONS
from .content import PRESCRIPTION_TOP_BASE_IMAGES
from .content import PRESCRIPTION_TOP_BASE_IMAGE_VERSIONS
from .content import PRESCRIPTION_TOP_PYTHON_VERSIONS
from .content import PRESCRIPTION_TOP_OPERATING_SYSTEMS
from .content import PRESCRIPTION_THOTH_COMMUNITY_UPDATE


if TYPE_CHECKING:
    from git import Repo
    from thoth.prescriptions_refresh.prescriptions import Prescriptions


_LOGGER = logging.getLogger(__name__)

_PRESCRIPTION_NAME_PREFIX = "thoth_community"
_DAYS = int(os.getenv("THOTH_PRESCRIPTIONS_REFRESH_THOTH_COMMUNITY_DAYS", 365 // 2))

_TOP_PACKAGE_NAMES = int(os.getenv("THOTH_PRESCRIPTIONS_REFRESH_THOTH_COMMUNITY_TOP_PACKAGE_NAMES", 25))
_TOP_PACKAGE_VERSIONS = int(os.getenv("THOTH_PRESCRIPTIONS_REFRESH_THOTH_COMMUNITY_TOP_PACKAGE_VERSIONS", 50))
_TOP_DEV_PACKAGE_NAMES = int(os.getenv("THOTH_PRESCRIPTIONS_REFRESH_THOTH_COMMUNITY_TOP_DEV_PACKAGE_NAMES", 10))
_TOP_DEV_PACKAGE_VERSIONS = int(os.getenv("THOTH_PRESCRIPTIONS_REFRESH_THOTH_COMMUNITY_TOP_DEV_PACKAGE_VERSIONS", 20))
_TOP_BASE_IMAGES = int(os.getenv("THOTH_PRESCRIPTIONS_REFRESH_THOTH_COMMUNITY_TOP_BASE_IMAGES", 10))
_TOP_BASE_IMAGE_VERSIONS = int(os.getenv("THOTH_PRESCRIPTIONS_REFRESH_THOTH_COMMUNITY_TOP_BASE_IMAGE_VERSIONS", 10))
_TOP_PYTHON_VERSIONS = int(os.getenv("THOTH_PRESCRIPTIONS_REFRESH_THOTH_COMMUNITY_TOP_PYTHON_VERSIONS", 3))
_TOP_OPERATING_SYSTEMS = int(os.getenv("THOTH_PRESCRIPTIONS_REFRESH_THOTH_COMMUNITY_TOP_OPERATING_SYSTEMS", 5))


@attr.s(slots=True)
class ThothCommunityStats:
    """Aggregate Thoth community statistics from adviser result documents.."""

    counter_package_names = attr.ib(type=CounterType[str], factory=Counter, init=False)
    counter_package_versions = attr.ib(type=CounterType[Tuple[str, str]], factory=Counter, init=False)
    counter_dev_package_names = attr.ib(type=CounterType[str], factory=Counter, init=False)
    counter_dev_package_versions = attr.ib(type=CounterType[Tuple[str, str]], factory=Counter, init=False)
    counter_base_images = attr.ib(type=CounterType[str], factory=Counter, init=False)
    counter_base_image_versions = attr.ib(type=CounterType[Tuple[str, str]], factory=Counter, init=False)
    counter_python_versions = attr.ib(type=CounterType[str], factory=Counter, init=False)
    counter_operating_systems = attr.ib(
        type=CounterType[Tuple[Optional[str], Optional[str]]], factory=Counter, init=False
    )

    def aggregate(self, adviser_store: AdvisersResultsStore) -> None:
        """Aggregate Thoth community statistics."""
        today = date.today()
        start_date = today - timedelta(days=_DAYS)

        _LOGGER.info("Processing adviser documents starting %s located at %r", start_date, adviser_store.prefix)
        for adviser_id in adviser_store.get_document_listing(start_date=start_date):
            if adviser_id.endswith(".request"):
                continue

            adviser_document = adviser_store.retrieve_document(adviser_id)

            if adviser_document["result"]["error"]:
                _LOGGER.debug("Skipping adviser document %r as the recommendation was not given", adviser_id)
                continue

            lockfile = adviser_document["result"]["parameters"]["project"]["requirements_locked"]
            if not lockfile:
                _LOGGER.debug("No input lockfile provided in adviser document %r", adviser_id)
                continue

            _LOGGER.info("Processing adviser document %r", adviser_id)
            for package_name, package_info in (lockfile.get("default") or {}).items():
                self.counter_package_names[package_name] += 1
                package_version = package_info.get("version")
                if package_version and package_version.startswith("=="):
                    self.counter_package_versions[(package_name, package_version[len("==") :])] += 1

            for package_name, package_info in (lockfile.get("develop") or {}).items():
                self.counter_dev_package_names[package_name] += 1
                package_version = package_info.get("version")
                if package_version and package_version.startswith("=="):
                    self.counter_dev_package_versions[(package_name, package_version[len("==") :])] += 1

            runtime_environment = adviser_document["result"]["parameters"]["project"]["runtime_environment"]

            base_image = runtime_environment.get("base_image")
            if base_image:
                parts = base_image.rsplit(":", maxsplit=1)
                if parts == 2:
                    self.counter_base_images[base_image] += 1
                    self.counter_base_image_versions[(parts[0], parts[1])] += 1

            python_version = runtime_environment.get("python_version")
            if python_version:
                self.counter_python_versions[python_version] += 1

            operating_system = runtime_environment.get("operating_system")

            if operating_system and "name" in operating_system and "version" in operating_system:
                os_name = map_os_name(operating_system["name"])
                os_version = normalize_os_version(os_name, operating_system["version"])
                self.counter_operating_systems[(os_name, os_version)] += 1


def _clean_old_stats(repo: "Repo") -> None:
    """Clean old prescriptions related to Thoth community."""
    for root, _, files in os.walk(os.path.join(repo.workd_dir, "prescriptions")):
        for file_name in files:
            if not file_name.startswith(_PRESCRIPTION_NAME_PREFIX):
                continue

            to_remove = os.path.join(root, file_name)
            _LOGGER.debug("Removing old Thoth community statistics captured in file %r", to_remove)
            repo.index.remove(to_remove)


def thoth_community(prescriptions: "Prescriptions") -> None:
    """Compute community statistics in Thoth - how Thoth users use packages."""
    adviser_store = AdvisersResultsStore()
    adviser_store.connect()

    stats = ThothCommunityStats()
    stats.aggregate(adviser_store)

    current_datetime = datetime.utcnow()
    commit_message = "📊 Thoth community statistics update"
    branch_name = f"pres-thoth-community-{current_datetime.year}{current_datetime.month}{current_datetime.day}"
    with PrescriptionsChange(
        prescriptions=prescriptions, commit_message=commit_message, branch_name=branch_name
    ) as change:
        _clean_old_stats(prescriptions.repo)

        # Default packages packages.
        for package_name, _ in stats.counter_package_names.most_common(_TOP_PACKAGE_NAMES):
            prescription = PRESCRIPTION_TOP_PACKAGE_NAMES.format(
                prescription_name=prescriptions.get_prescription_name("", package_name),
                package_name=package_name,
            )
            change.add_prescription(package_name, f"{_PRESCRIPTION_NAME_PREFIX}_package_names.yaml", prescription)

        for info, _ in stats.counter_package_versions.most_common(_TOP_PACKAGE_VERSIONS):
            package_name, package_version = info
            prescription = PRESCRIPTION_TOP_PACKAGE_VERSIONS.format(
                prescription_name=prescriptions.get_prescription_name("", package_name, package_version),
                package_name=package_name,
                package_version=package_version,
            )
            change.add_prescription(
                package_name, f"{_PRESCRIPTION_NAME_PREFIX}_{package_version}_package_versions.yaml", prescription
            )

        # Dev packages.
        for package_name, _ in stats.counter_dev_package_names.most_common(_TOP_DEV_PACKAGE_NAMES):
            prescription = PRESCRIPTION_TOP_DEV_PACKAGE_NAMES.format(
                prescription_name=prescriptions.get_prescription_name("", package_name),
                package_name=package_name,
            )
            change.add_prescription(package_name, f"{_PRESCRIPTION_NAME_PREFIX}_dev_package_names.yaml", prescription)

        for info, _ in stats.counter_dev_package_versions.most_common(_TOP_DEV_PACKAGE_VERSIONS):
            package_name, package_version = info
            prescription = PRESCRIPTION_TOP_DEV_PACKAGE_VERSIONS.format(
                prescription_name=prescriptions.get_prescription_name("", package_name, package_version),
                package_name=package_name,
                package_version=package_version,
            )
            change.add_prescription(
                package_name, f"{_PRESCRIPTION_NAME_PREFIX}_{package_version}_dev_package_versions.yaml", prescription
            )

        # Base images.
        for base_image, _ in stats.counter_base_images.most_common(_TOP_BASE_IMAGES):
            base_image_name = base_image.rsplit("/", maxsplit=1)[-1]
            prescription = PRESCRIPTION_TOP_BASE_IMAGES.format(
                prescription_name=prescriptions.get_prescription_name("", base_image_name),
                base_image=base_image,
            )
            change.add_prescription(
                "_containers", f"{base_image_name}/{_PRESCRIPTION_NAME_PREFIX}_base_images.yaml", prescription
            )

        for base_image_info, _ in stats.counter_base_image_versions.most_common(_TOP_BASE_IMAGE_VERSIONS):
            base_image, base_image_version = base_image_info
            base_image_name = base_image.rsplit("/", maxsplit=1)[-1]

            prescription = PRESCRIPTION_TOP_BASE_IMAGE_VERSIONS.format(
                prescription_name=prescriptions.get_prescription_name("", base_image_name, base_image_version),
                base_image=base_image,
                base_image_version=base_image_version,
            )
            change.add_prescription(
                "_containers",
                f"{base_image_name}-{base_image_version}/{_PRESCRIPTION_NAME_PREFIX}_base_image_versions.yaml",
                prescription,
            )

        # Python version.
        for python_version, _ in stats.counter_python_versions.most_common(_TOP_PYTHON_VERSIONS):
            prescription = PRESCRIPTION_TOP_PYTHON_VERSIONS.format(
                prescription_name=prescriptions.get_prescription_name("", "Python", python_version),
                python_version=python_version,
            )
            change.add_prescription(
                "_python",
                f"{python_version}/{_PRESCRIPTION_NAME_PREFIX}_python_version.yaml",
                prescription,
            )

        # Operating system.
        for operating_system, _ in stats.counter_operating_systems.most_common(_TOP_OPERATING_SYSTEMS):
            operating_system_name, operating_system_version = operating_system

            prescription = PRESCRIPTION_TOP_OPERATING_SYSTEMS.format(
                prescription_name=prescriptions.get_prescription_name(
                    "", operating_system_name, operating_system_version
                ),
                operating_system_name=operating_system_name,
                operating_system_version=operating_system_version,
            )
            change.add_prescription(
                "_operating_systems",
                f"{operating_system_name}-{operating_system_version}/{_PRESCRIPTION_NAME_PREFIX}_operating_system.yaml",
                prescription,
            )

        change.add_prescription(
            "__generic",
            "thoth_community.yaml",
            PRESCRIPTION_THOTH_COMMUNITY_UPDATE.format(
                thoth_community_timestamp=datetime2datetime_str(current_datetime),
            ),
        )
