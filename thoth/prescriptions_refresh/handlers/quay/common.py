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

"""Common logic for computing Quay-related information on container images."""

import logging
import os

import requests

from typing import Any
from typing import Dict
from typing import Generator
from typing import Tuple

_LOGGER = logging.getLogger(__name__)
QUAY_TOKEN = os.getenv("THOTH_PRESCRIPTIONS_REFRESH_QUAY_TOKEN")
QUAY_NAMESPACE_NAME = os.getenv("THOTH_PRESCRIPTIONS_REFRESH_QUAY_PS_NAMESPACE_NAME", "thoth-station")
QUAY_NAMESPACE_PUBLIC = bool(int(os.getenv("THOTH_PRESCRIPTIONS_REFRESH_QUAY_PS_NAMESPACE_PUBLIC", 1)))
CONFIGURED_IMAGES = os.getenv("THOTH_PRESCRIPTIONS_REFRESH_CONFIGURED_IMAGES")
QUAY_URL = os.getenv("THOTH_PRESCRIPTIONS_REFRESH_QUAY_URL", "quay.io")


def get_configured_image_names() -> Generator[str, None, None]:
    """Get a list of container images configured via environment variables."""
    if not CONFIGURED_IMAGES:
        yield from ()
        return None

    for line in CONFIGURED_IMAGES.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        yield line


def get_ps_s2i_image_names() -> Generator[str, None, None]:
    """List all the predictable stack container image names."""
    response = requests.get(
        f"https://{QUAY_URL}/api/v1/repository",
        headers={"Authorization": f"Bearer {QUAY_TOKEN}"},
        params={"public": QUAY_NAMESPACE_PUBLIC, "namespace": QUAY_NAMESPACE_NAME},
    )
    response.raise_for_status()

    for repository in response.json()["repositories"]:
        if repository["name"].startswith(("ps-", "s2i-")):
            yield repository["name"]


def get_image_containers_info(image_name: str) -> Generator[Dict[str, Any], None, None]:
    """Get information about containers for the given image."""
    response = requests.get(
        f"https://{QUAY_URL}/api/v1/repository/{QUAY_NAMESPACE_NAME}/{image_name}/image",
        headers={"Authorization": f"Bearer {QUAY_TOKEN}"},
    )
    if response.status_code != 200:
        _LOGGER.error(
            "Failed to obtain available containers for image %r (%d): %s",
            image_name,
            response.status_code,
            response.text,
        )
        yield from ()
        return

    for container_image in sorted(response.json()["images"], key=lambda i: str(i["id"])):
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

        yield container_image


def get_image_containers_image_info(image_name: str) -> Generator[Tuple[Dict[str, Any], str], None, None]:
    """Get information about containers for the given image."""
    for image_info in get_image_containers_info(image_name):
        response = requests.get(
            f"https://{QUAY_URL}/api/v1/repository/{QUAY_NAMESPACE_NAME}/{image_name}/image/{image_info['id']}",
            headers={"Authorization": f"Bearer {QUAY_TOKEN}"},
        )
        if response.status_code != 200:
            _LOGGER.error(
                "Failed to obtain container info for image %r with id %r (%d): %s",
                image_name,
                image_info["id"],
                response.status_code,
                response.text,
            )
            continue

        for tag in image_info["tags"]:
            if not tag.startswith("v"):
                continue

            yield response.json(), tag


def get_image_containers(image_name: str) -> Generator[Tuple[str, str], None, None]:
    """List all containers ids for the given image."""
    for container_image in get_image_containers_info(image_name):
        for tag in container_image["tags"]:
            if tag.startswith("v"):
                # Allow multiple version tags per one container image built.
                yield container_image["id"], tag
