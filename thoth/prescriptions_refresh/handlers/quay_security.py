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

"""Check security related information in predictable stacks container images."""

import logging
import os

import requests
from thoth.common.helpers import datetime2datetime_str

from typing import Any
from typing import Dict
from typing import Generator
from typing import List
from typing import Set
from typing import Tuple
from itertools import chain
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from thoth.prescriptions_refresh.prescriptions import Prescriptions

_LOGGER = logging.getLogger(__name__)
_QUAY_TOKEN = os.getenv("THOTH_PRESCRIPTIONS_REFRESH_QUAY_TOKEN")
_QUAY_NAMESPACE_NAME = os.getenv("THOTH_PRESCRIPTIONS_REFRESH_QUAY_PS_NAMESPACE_NAME", "thoth-station")
_QUAY_NAMESPACE_PUBLIC = bool(int(os.getenv("THOTH_PRESCRIPTIONS_REFRESH_QUAY_PS_NAMESPACE_PUBLIC", 1)))
_CONFIGURED_IMAGES = os.getenv("THOTH_PRESCRIPTIONS_REFRESH_CONFIGURED_IMAGES")
_QUAY_URL = os.getenv("THOTH_PRESCRIPTIONS_REFRESH_QUAY_URL", "quay.io")

_QUAY_SECURITY_BOOT = """\
  - name: {prescription_name}QuaySecurityErrorBoot
    type: boot
    should_include:
      adviser_pipeline: true
      recommendation_types:
      - security
      runtime_environments:
        base_images:
        - {image}
    run:
      stack_info:
      - type: ERROR
        message: >-
          {message}
        link: {link}
      not_acceptable: >-
        The base image used has a CVE: {cve_name}
"""

_QUAY_SECURITY_WRAP = """\
  - name: {prescription_name}QuaySecurityWarningWrap
    type: wrap
    should_include:
      adviser_pipeline: true
      recommendation_types:
      - latest
      - performance
      - stable
      - testing
      runtime_environments:
        base_images:
        - {image}
    run:
      justification:
      - type: ERROR
        message: >-
          {message}
        link: {link}
        cve_name: {cve_name}
"""

_QUAY_SECURITY_TIMESTAMP = """\
units:
  boots:
  - name: QuaySecurityTimestampInfoBoot
    type: boot
    should_include:
      adviser_pipeline: true
      runtime_environments:
        base_images:
          not: [null]
    run:
      stack_info:
      - type: INFO
        message: >-
          Using security information for predictable stacks based on Quay
          scanners for {quay_url}/organization/{quay_namespace} as of {datetime!r}
        link: https://www.projectquay.io/
"""


def _get_configured_image_names() -> Generator[str, None, None]:
    """Get a list of container images configured via environment variables."""
    if not _CONFIGURED_IMAGES:
        yield from ()
        return None

    for line in _CONFIGURED_IMAGES.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        yield line


def _get_ps_s2i_image_names() -> Generator[str, None, None]:
    """List all the predictable stack container image names."""
    response = requests.get(
        f"https://{_QUAY_URL}/api/v1/repository",
        headers={"Authorization": f"Bearer {_QUAY_TOKEN}"},
        params={"public": _QUAY_NAMESPACE_PUBLIC, "namespace": _QUAY_NAMESPACE_NAME},
    )
    response.raise_for_status()

    for repository in response.json()["repositories"]:
        if repository["name"].startswith(("ps-", "s2i-")):
            yield repository["name"]


def _get_image_containers(image_name: str) -> Generator[Tuple[str, str], None, None]:
    """List all containers ids for the given image."""
    response = requests.get(
        f"https://{_QUAY_URL}/api/v1/repository/{_QUAY_NAMESPACE_NAME}/{image_name}/image",
        headers={"Authorization": f"Bearer {_QUAY_TOKEN}"},
    )
    response.raise_for_status()

    for container_image in response.json()["images"]:
        if container_image.get("uploading", False):
            _LOGGER.warning(
                "Skipping container image %r with id %r as it is currently being uploaded",
                image_name,
                container_image["id"],
            )
            continue

        for tag in container_image["tags"]:
            if tag.startswith("v"):
                break
        else:
            if container_image["tags"]:  # Skip warning for layers.
                _LOGGER.warning(
                    "Skipping container image %r with id %r as no version tag found: %r",
                    image_name,
                    container_image["id"],
                    container_image["tags"],
                )
            continue

        yield container_image["id"], tag


def _quay_get_security_info(image_name: str, container_id: str) -> List[Dict[str, Any]]:
    """Obtain security related information for the given container specified by the given container id."""
    response = requests.get(
        f"https://{_QUAY_URL}/api/v1/repository/{_QUAY_NAMESPACE_NAME}/{image_name}/image/{container_id}/security",
        headers={"Authorization": f"Bearer {_QUAY_TOKEN}"},
        params={"vulnerabilities": True},
    )
    response.raise_for_status()

    vulnerabilities = []
    for feature in ((response.json().get("data") or {}).get("Layer") or {}).get("Features") or []:
        if feature["Vulnerabilities"]:
            vulnerabilities.extend(feature["Vulnerabilities"])

    return vulnerabilities


def _create_prescriptions(
    prescriptions: "Prescriptions", image: str, tag: str, vulnerabilities: List[Dict[str, Any]]
) -> None:
    """Create prescriptions for the vulnerabilities listed."""
    if not vulnerabilities:
        # No vulnerabilities, noop.
        return

    prescription_name = ""
    for part in map(str.capitalize, image.split("-")):
        prescription_name += part

    # Remove duplicates.
    cve_seen: Set[str] = set()
    units = "units:\n  boots:\n"
    for idx, vulnerability in enumerate(vulnerabilities):
        if vulnerability["Name"] in cve_seen:
            continue

        vulnerability_description = vulnerability["Description"].replace("\\", "\\\\").replace('"', '\\"')
        cve_seen.add(vulnerability["Name"])

        units += _QUAY_SECURITY_BOOT.format(
            prescription_name=f"{prescription_name}Vuln{idx}",
            image=f"{_QUAY_URL}/{_QUAY_NAMESPACE_NAME}/{image}:{tag}",
            message=f"Found {vulnerability['Name']} in the base image used: {vulnerability_description}",
            link=vulnerability["Link"],
            cve_name=vulnerability["Name"],
        )

    units += "  wraps:\n"
    cve_seen.clear()
    for idx, vulnerability in enumerate(vulnerabilities):
        if vulnerability["Name"] in cve_seen:
            continue

        vulnerability_description = vulnerability["Description"].replace("\\", "\\\\").replace('"', '\\"')
        cve_seen.add(vulnerability["Name"])

        units += _QUAY_SECURITY_WRAP.format(
            prescription_name=f"{prescription_name}Vuln{idx}",
            image=f"{_QUAY_URL}/{_QUAY_NAMESPACE_NAME}/{image}:{tag}",
            message=vulnerability_description,
            link=vulnerability["Link"],
            cve_name=vulnerability["Name"],
        )

    prescriptions.create_prescription(
        project_name=f"_containers/{image.replace('-', '_')}",
        prescription_name="quay_security.yaml",
        content=units,
        commit_message=f"Security info update for {image!r} based on Quay.io scanners",
    )


def quay_security(prescriptions: "Prescriptions") -> None:
    """Check security related information in predictable stacks container images."""
    if not _QUAY_TOKEN:
        raise ValueError("No Token to Quay API provided")

    datetime = datetime2datetime_str()

    for image in chain(_get_ps_s2i_image_names(), _get_configured_image_names()):
        for container_id, tag in _get_image_containers(image):
            _LOGGER.info("Obtaining security-related information for %r in tag %r", image, tag)
            vulnerabilities = _quay_get_security_info(image, container_id)
            if vulnerabilities:
                _create_prescriptions(prescriptions, image, tag, vulnerabilities)

    prescriptions.create_prescription(
        project_name="_containers",
        prescription_name="quay_security.yaml",
        content=_QUAY_SECURITY_TIMESTAMP.format(
            quay_namespace=_QUAY_NAMESPACE_NAME,
            quay_url=_QUAY_URL,
            datetime=datetime,
        ),
        commit_message=f"Security scans from Quay.io has been successfully updated for {_QUAY_NAMESPACE_NAME}",
    )
