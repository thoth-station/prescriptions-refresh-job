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

"""Propagate information about container image size to users."""

import logging
from itertools import chain

from .common import get_image_containers_image_info
from .common import get_ps_s2i_image_names
from .common import QUAY_NAMESPACE_NAME
from .common import QUAY_URL
from .common import CONFIGURED_IMAGES

from thoth.prescriptions_refresh.prescriptions import Prescriptions

_LOGGER = logging.getLogger(__name__)

_IMAGE_SIZE_PRESCRIPTION_NAME = "quay_image_size.yaml"
_IMAGE_SIZE_BOOT = """\
  - name: {prescription_name}
    type: boot
    should_include:
      adviser_pipeline: true
      runtime_environments:
        base_images:
        - {image}
    run:
      stack_info:
      - type: INFO
        message: >-
          Container image {image!r} has a size of {size}
        link: {link}
"""


def quay_image_size(prescriptions: "Prescriptions") -> None:
    """Propagate information about container image size to users."""
    for image_name in chain(Prescriptions.get_configured_parameters(CONFIGURED_IMAGES), get_ps_s2i_image_names()):
        _LOGGER.info("Computing image size for container images available for image %r", image_name)
        content = ""
        for image_info, tag in get_image_containers_image_info(image_name):
            image_size = 0
            for layer in image_info["history"]:
                image_size += layer["size"]

            image_identifier = f"{QUAY_URL}/{QUAY_NAMESPACE_NAME}/{image_name}:{tag}"
            if image_size == 0:
                _LOGGER.error("Container image size computed for %r is 0 bytes", image_identifier)
                continue

            content += _IMAGE_SIZE_BOOT.format(
                image=image_identifier,
                prescription_name=prescriptions.get_prescription_name("QuayImageSizeBoot", image_name, tag),
                link=f"https://{image_identifier}",  # Redirects to the container image listing with tag selected.
                size=prescriptions.get_artifact_size_str(image_size),
            )

        if not content:
            _LOGGER.warning("No content computed for image %r (no version tag available?)", image_name)
            continue

        prescriptions.create_prescription(
            project_name=f"_containers/{image_name.replace('-', '_')}",
            prescription_name=_IMAGE_SIZE_PRESCRIPTION_NAME,
            content="units:\n  boots:\n" + content,
            commit_message=f"Container image size info for {image_name!r}",
        )
