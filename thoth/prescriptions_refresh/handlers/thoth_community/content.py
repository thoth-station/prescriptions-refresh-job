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

"""Prescription content used in Thoth community statistics."""


PRESCRIPTION_TOP_PACKAGE_NAMES = """\
units:
  wraps:
  - name: {prescription_name}TopPackageNamesWrap
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
        message: Package '{package_name}' is popular within Thoth community
        link: thoth_community
        package_name: {package_name}
"""


PRESCRIPTION_TOP_PACKAGE_VERSIONS = """\
units:
  wraps:
  - name: {prescription_name}ConsiderTopPackageVersionsWrap
    type: wrap
    should_include:
      adviser_pipeline: true
    match:
      state:
        resolved_dependencies:
        - name: {package_name}
          version: "!={package_version}"
    run:
      justification:
      - type: INFO
        message: >-
          Consider using '{package_name}' in version '{package_version}' which is popular within Thoth community
        link: thoth_community
        package_name: {package_name}
  - name: {prescription_name}TopPackageVersionsWrap
    type: wrap
    should_include:
      adviser_pipeline: true
    match:
      state:
        resolved_dependencies:
        - name: {package_name}
          version: =={package_version}
    run:
      justification:
      - type: INFO
        message: >-
          Package '{package_name}' in version '{package_version}' is popular within Thoth community
        link: thoth_community
        package_name: {package_name}
"""


PRESCRIPTION_TOP_DEV_PACKAGE_NAMES = """\
units:
  wraps:
  - name: {prescription_name}TopDevPackageNamesWrap
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
        message: Package '{package_name}' is popular as a development dependency within Thoth community
        link: thoth_community
        package_name: {package_name}
"""


PRESCRIPTION_TOP_DEV_PACKAGE_VERSIONS = """\
units:
  wraps:
  - name: {prescription_name}ConsiderTopDevPackageVersionsWrap
    type: wrap
    should_include:
      adviser_pipeline: true
    match:
      state:
        resolved_dependencies:
        - name: {package_name}
          version: "!={package_version}"
    run:
      justification:
      - type: INFO
        message: >-
          Consider using '{package_name}' in version '{package_version}' is popular
          as a development dependency within Thoth community
        link: thoth_community
        package_name: {package_name}
  - name: {prescription_name}TopDevPackageVersionsWrap
    type: wrap
    should_include:
      adviser_pipeline: true
    match:
      state:
        resolved_dependencies:
        - name: {package_name}
          version: =={package_version}
    run:
      justification:
      - type: INFO
        message: >-
          Package '{package_name}' in version '{package_version}' is popular as a development dependency
          within Thoth community
        link: thoth_community
        package_name: {package_name}
"""


PRESCRIPTION_TOP_BASE_IMAGES = """\
units:
  boots:
  - name: {prescription_name}TopBaseImageBoot
    type: boot
    should_include:
      adviser_pipeline: true
      runtime_environments:
        base_images:
        - {base_image}
    run:
      stack_info:
      - type: INFO
        message: Container image '{base_image}' is popular within Thoth community
        link: thoth_community
"""


PRESCRIPTION_TOP_BASE_IMAGE_VERSIONS = """\
units:
  boots:
  - name: {prescription_name}ConsiderTopBaseImageVersionsBoot
    type: boot
    should_include:
      adviser_pipeline: true
      runtime_environments:
        base_images:
        - {base_image}
    run:
      stack_info:
      - type: INFO
        message: Container image '{base_image}' in tag '{base_image_version}' is popular within Thoth community
        link: thoth_community
"""


PRESCRIPTION_TOP_PYTHON_VERSIONS = """\
units:
  boots:
  - name: {prescription_name}TopPythonVersionsBoot
    type: boot
    should_include:
      adviser_pipeline: true
      runtime_environments:
        python_version: =={python_version}
    run:
      stack_info:
      - type: INFO
        message: >-
          Python in version '{python_version}' is popular within Thoth community
        link: thoth_community
  - name: {prescription_name}ConsiderTopPythonVersionsBoot
    type: boot
    should_include:
      adviser_pipeline: true
      runtime_environments:
        python_version: "!={python_version}"
    run:
      stack_info:
      - type: INFO
        message: >-
          Consider switching to Python in version '{python_version}' which is popular within Thoth community
        link: thoth_community
"""


PRESCRIPTION_TOP_OPERATING_SYSTEMS = """\
units:
  boots:
  - name: {prescription_name}TopOperatingSystemsBoot
    type: boot
    should_include:
      adviser_pipeline: true
      runtime_environments:
        operating_systems:
        - name: {operating_system_name}
    run:
      stack_info:
      - type: INFO
        message: >-
          Operating system '{operating_system_name}' in version '{operating_system_version}' is
          popular within Thoth community
        link: thoth_community
"""


PRESCRIPTION_THOTH_COMMUNITY_UPDATE = """\
units:
  boots:
  - name: ThothCommunityUpdateTimestampBoot
    type: boot
    should_include:
      adviser_pipeline: true
    run:
      stack_info:
      - type: INFO
        message: >-
          Using Thoth community statistics computed at {thoth_community_timestamp}
        link: thoth_community
"""
