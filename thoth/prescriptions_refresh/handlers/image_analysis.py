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


import logging
from itertools import chain

from thoth.prescriptions_refresh.prescriptions import Prescriptions
from .quay.common import get_configured_image_names
from .quay.common import get_ps_s2i_image_names
from .quay.common import get_image_containers
from .quay.common import QUAY_TOKEN


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
        resolved_dependencies: {resolved_dependencies}
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


def thoth_image_analysis(prescriptions: "Prescriptions") -> None:
    """Create prescriptions from Thoth container images analysis results."""
    if not QUAY_TOKEN:
        raise ValueError("No Token to Quay API provided")

    for image in sorted(chain(get_ps_s2i_image_names(), get_configured_image_names())):
        # wraps_ps_images = ""

        ## Get last tag for ps images hosted on Quay
        for container_id, tag in get_image_containers(image):
            _LOGGER.info("Obtaining image information for %r in tag %r", image, tag)
            print(container_id, tag)

    ## Get image analyzed IDs latest from database

    ## Retrieve document from Ceph

    ## Get Pipfile/Pipfile.lock from document

    ## Create prescriptions for direct dependencies

    # prescriptions.create_prescription(
    #     project_name="_containers",
    #     prescription_name="quay_image_analysis.yaml",
    #     content=_QUAY_IMAGE_ANALYSIS_WRAP.format(
    #         os_name=os_name,
    #         os_version=os_version,
    #         python_version=python_version,
    #         image=image,
    #         resolved_dependencies=resolved_dependencies,
    #         link=link
    #     ),
    #     commit_message=f"Packages from Quay.io ps images have been successfully updated for {QUAY_NAMESPACE_NAME}",
    # )
