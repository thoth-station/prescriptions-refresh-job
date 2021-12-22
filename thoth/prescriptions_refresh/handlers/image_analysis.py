#!/usr/bin/env python3
# thoth-prescriptions-refresh
# Copyright(C) 2021 Francesco Murdaca
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

"""Create prescriptions from container image analysis results."""

import os
import requests
import logging
from itertools import chain
from typing import Dict, Any, Optional, Tuple

from thoth.python import Pipfile, PipfileLock

from thoth.prescriptions_refresh.prescriptions import Prescriptions
from .quay.common import get_configured_image_names
from .quay.common import get_ps_s2i_image_names
from .quay.common import get_image_containers
from .quay.common import QUAY_TOKEN
from .quay.common import QUAY_URL


_LOGGER = logging.getLogger(__name__)

_IMAGE_ANAYSIS_PRESCRIPTION_NAME = "thoth_image_analysis.yaml"
_THOTH_IMAGE_ANALYSIS_WRAP = """\
  - name: {prescription_name}BaseImageWrap
    type: wrap
    should_include:
      adviser_pipeline: true
      recommendation_types:
      - latest
      - performance
      - stable
      - testing
      runtime_environments:
        operating_systems:
        - name: {os_name}
          version: {os_version}
        python_version: =={python_version}
        base_images:
          not:
          - {image}
    match:
      state:
        resolved_dependencies:
        {resolved_dependencies}
    run:
      stack_info:
      - type: INFO
        message: >-
          Found predictive stack image that can be used with these dependencies
        link: {link}
      advised_manifest_changes:
      - file: .thoth.yaml
        patch:
        - name: base_image
          value: {link}
"""

USER_API_HOST = os.environ["THOTH_USER_API_HOST"]


def _get_latest_image_analyzed_info(image: str) -> Optional[Dict[str, Any]]:
    """Get latest image analyzed information."""
    url = f"http://{USER_API_HOST}/api/v1/container-images"
    response = requests.get(url, params={"image_name": f"{QUAY_URL}/thoth-station/{image}"})

    if response.status_code == 200:
        results = response.json()
        return results[0]
    else:
        return None


def _get_requirement_files_from_image_analysis(
    package_extract_document_id: str,
) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """Get requiremens files from image analysis result."""
    url = f"http://{USER_API_HOST}/api/v1/analyze"
    response = requests.get(url, params={"analysis_id": package_extract_document_id})

    if response.status_code == 200:
        document = response.json()

        # Get result and requirements files
        result = document["result"]
        pipfile_dict = result["aicoe-ci"].get("requirements")
        pipfile_lock_dict = result["aicoe-ci"].get("requirements_lock")

        return pipfile_dict, pipfile_lock_dict

    elif response.status_code == 404:
        _LOGGER.warning(f"Document {package_extract_document_id} does not exists.")
        return None, None

    else:
        return None, None


def _create_resolved_dependencies_section(pipfile: Dict[str, Any], pipfile_lock: Dict[str, Any]) -> str:
    """Create resolved dependencies section for adviser unit."""
    resolved_dependencies = ""

    pipfile = Pipfile.from_dict(pipfile)
    pipfile_lock = PipfileLock.from_dict(pipfile_lock)

    required_packages = []

    for package in pipfile.packages.packages:
        version = pipfile_lock.packages[package].version
        required_packages.append({"name": package, "version": version})  # Includes ==

    line = 0
    for package in required_packages:
        if line == 0:
            resolved_dependencies += f"- name: {package['name']}\n"
        else:
            resolved_dependencies += f"        - name: {package['name']}\n"

        resolved_dependencies += f"          version: {package['version']}\n"
        line += 1

    return resolved_dependencies


def _generate_prescription_name(image, tag) -> str:
    """Generate custom prescription name.

    Example: image='ps-cv-ocr' tag='1.0.2

        prescription name -> PsCvOcr102
    """
    return "".join([p.capitalize() for p in image.split("-")]) + tag.replace(".", "")


def thoth_image_analysis(prescriptions: "Prescriptions") -> None:
    """Create prescriptions from Thoth container images analysis results."""
    if not QUAY_TOKEN:
        raise ValueError("No Token to Quay API provided")

    for image in sorted(chain(get_ps_s2i_image_names(), get_configured_image_names())):

        # Get tag for Thoth images hosted on Quay
        for _, tag in get_image_containers(image):
            _LOGGER.info("Obtaining image information for %r in tag %r", image, tag)

            image_url = f"{QUAY_URL}/thoth-station/{image}:{tag}"

            # Get image analyzed IDs latest from database through USER-API endpoint
            info = _get_latest_image_analyzed_info(image=image)

            if not info:
                _LOGGER.warning("Could not find any data for {QUAY_URL}/thoth-station/{image}:{tag} in Thoth Database.")
                break

            # Software environment
            os_name = info["os_name"]
            os_version = info["os_version"]
            python_version = info["python_version"]

            # Latest package extract document ID
            package_extract_document_id = info["package_extract_document_id"]

            # Get Pipfile/Pipfile.lock from image analyzed result
            pipfile_dict, pipfile_lock_dict = _get_requirement_files_from_image_analysis(
                package_extract_document_id=package_extract_document_id
            )

            if pipfile_dict and pipfile_lock_dict:
                # Create section for locked packages versions for prescriptions
                resolved_dependencies = _create_resolved_dependencies_section(pipfile_dict, pipfile_lock_dict)

                # Create prescriptions for direct dependencies
                prescriptions.create_prescription(
                    project_name="_containers",
                    prescription_name=_IMAGE_ANAYSIS_PRESCRIPTION_NAME,
                    content=_THOTH_IMAGE_ANALYSIS_WRAP.format(
                        prescription_name=_generate_prescription_name(prefix="Thoth", image=image, tag=tag),
                        os_name=os_name,
                        os_version=os_version,
                        python_version=python_version,
                        image=image_url,
                        resolved_dependencies=resolved_dependencies,
                        link=image_url,
                    ),
                    commit_message=f"Created prescriptions from predictable stack image: {image_url}",
                )
            else:
                _LOGGER.warning(
                    f"Missing requirements files from package-extract document {package_extract_document_id}."
                    "Prescription cannot be created without them."
                )
