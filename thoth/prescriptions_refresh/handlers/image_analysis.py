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


_QUAY_IMAGE_ANALYSIS_WRAP = """\
  - name: {prescription_name}QuayBaseImageWrap
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


def _get_latest_image_analyzed_info(image: str) -> Dict[str, Any]:
    """Get image analyzed IDs latest from database through USER-API endpoint."""
    url = f"http://{USER_API_HOST}/api/v1/container-images"
    response = requests.get(url, params={"image_name": f"{QUAY_URL}/thoth-station/{image}"})
    results = response.json()

    return results[0]


def _get_requirement_files_from_image_analysis(
    package_extract_document_id: str
) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """Get requiremens files from image analysis result."""
    url = f"http://{USER_API_HOST}/api/v1/analyze"
    response = requests.get(url, params={"analysis_id": package_extract_document_id})
    results = response.json()

    # Get latest result
    document = results[0]
    result = document["result"]
    pipfile_dict = result["aicoe-ci"].get("requirements")
    pipfile_lock_dict = result["aicoe-ci"].get("requirements_lock")

    return pipfile_dict, pipfile_lock_dict


def thoth_image_analysis(prescriptions: "Prescriptions") -> None:
    """Create prescriptions from Thoth container images analysis results."""
    if not QUAY_TOKEN:
        raise ValueError("No Token to Quay API provided")

    for image in sorted(chain(get_ps_s2i_image_names(), get_configured_image_names())):

        ## Get tag for Thoth images hosted on Quay
        for _, tag in get_image_containers(image):
            _LOGGER.info("Obtaining image information for %r in tag %r", image, tag)

            # Get image analyzed IDs latest from database through USER-API endpoint
            result = _get_latest_image_analyzed_info(image=image)

            package_extract_document_id = result["package_extract_document_id"]
            os_name = result["os_name"]
            os_version = result["os_version"]
            python_version = result["python_version"]

            ## Get Pipfile/Pipfile.lock from image analyzed result
            pipfile_dict, pipfile_lock_dict = _get_requirement_files_from_image_analysis(
                package_extract_document_id=package_extract_document_id
            )

            ## Retrieve direct locked packages versions for prescriptions
            resolved_dependencies = ""

            if pipfile_dict and pipfile_lock_dict:
                pipfile = Pipfile.from_dict(pipfile_dict)
                pipfile_lock = PipfileLock.from_dict(pipfile_dict)

                required_packages = []
                for package in pipfile.packages.packages:
                    version = pipfile_lock[package]
                    required_packages.append({"name": package, "version": version})  # Includes ==

                n = 0
                for package in required_packages:
                    if n == 0:
                        resolved_dependencies += f"- name: {package['name']}\n"
                    else:
                        resolved_dependencies += f"        - name: {package['name']}\n"

                    resolved_dependencies += f"          version: {package['version']}\n"
                    n += 1

                # Create prescriptions for direct dependencies
                prescriptions.create_prescription(
                    project_name="_containers",
                    prescription_name="quay_image_analysis.yaml",
                    content=_QUAY_IMAGE_ANALYSIS_WRAP.format(
                        prescription_name=image,
                        os_name=os_name,
                        os_version=os_version,
                        python_version=python_version,
                        image=f"{QUAY_URL}/thoth-station/{image}:{tag}",
                        resolved_dependencies=resolved_dependencies,
                        link=f"{QUAY_URL}/thoth-station/{image}:{tag}",
                    ),
                    commit_message=f"Created prescriptions from predictable stack image: {image}",
                )
            else:
              _LOGGER.warning(
                  f"Missing requirements file from package-extract document {package_extract_document_id}."
                  "Prescription cannot be created without them."
              )
