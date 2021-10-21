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
from .scorecards import scorecards

__all__ = [
    cve_warning.__name__,
    gh_archived.__name__,
    gh_contributors.__name__,
    gh_forked.__name__,
    gh_link.__name__,
    gh_popularity.__name__,
    gh_release_notes.__name__,
    gh_updated.__name__,
    scorecards.__name__,
]
