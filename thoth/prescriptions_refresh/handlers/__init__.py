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

"""Thoth's handlers for prescriptions refresh job."""


from .cve_warning import cve_warning
from .gh_archived import gh_archived
from .gh_contributors import gh_contributors
from .gh_forked import gh_forked
from .gh_link import gh_link
from .gh_popularity import gh_popularity
from .gh_release_notes import gh_release_notes
from .gh_updated import gh_updated
from .pypi_artifact_size import pypi_artifact_size
from .pypi_downloads import pypi_downloads
from .pypi_maintainers import pypi_maintainers
from .pypi_release import pypi_release
from .quay import quay_image_size
from .quay import quay_security
from .scorecards import scorecards
from .thoth_community import thoth_community

__all__ = [
    cve_warning.__name__,
    gh_archived.__name__,
    gh_contributors.__name__,
    gh_forked.__name__,
    gh_link.__name__,
    gh_popularity.__name__,
    gh_release_notes.__name__,
    gh_updated.__name__,
    pypi_artifact_size.__name__,
    pypi_downloads.__name__,
    pypi_maintainers.__name__,
    pypi_release.__name__,
    quay_image_size.__name__,
    quay_security.__name__,
    scorecards.__name__,
    thoth_community.__name__,
]
