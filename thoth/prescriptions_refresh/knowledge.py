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

"""Encapsulation of Thoth's prescriptions and data stored in the main database."""

import logging
from typing import Generator

import attr
from thoth.storages import GraphDatabase
from .prescriptions import Prescriptions


_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class Knowledge:
    """Encapsulation of Thoth's prescriptions and data stored in the main database."""

    prescriptions = attr.ib(type=Prescriptions, default=attr.Factory(Prescriptions))
    graph = attr.ib(type=GraphDatabase)

    @graph.default
    def _graph_default(self) -> "GraphDatabase":
        graph = GraphDatabase()
        graph.connect()
        return graph

    def __enter__(self) -> "Knowledge":
        """Allow using Knowledge with the with statement."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore
        """Clean up once the work is done."""
        self.prescriptions.clean()

    def iter_projects(self) -> Generator[str, None, None]:
        """Iterate over projects known to Thoth."""
        projects = set()

        for project_name in self.prescriptions.iter_projects():
            projects.add(project_name)
            _LOGGER.debug("Project %r from the prescriptions database", project_name)
            yield project_name

        for project_name in self.graph.get_python_package_version_names_all(distinct=True):
            if project_name not in projects:
                _LOGGER.debug("Project %r from the graph database", project_name)
                yield project_name
                # not necessary as distinct is set:
                #   projects.add(project_name)
