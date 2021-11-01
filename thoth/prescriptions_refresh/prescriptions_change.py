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

"""Context kept to create multiple prescriptions in a single commit and pull-request."""

import logging
import os
from typing import Dict
from typing import Tuple
from typing import Optional
from types import TracebackType


import attr

from .prescriptions import Prescriptions

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class PrescriptionsChange:
    """Create multiple prescriptions in a single commit and pull-request."""

    prescriptions = attr.ib(type=Prescriptions, kw_only=True)
    commit_message = attr.ib(type=str, kw_only=True)
    branch_name = attr.ib(type=str, kw_only=True)
    body = attr.ib(type=Optional[str], kw_only=True, default=None)

    _prescription_changes = attr.ib(type=Dict[Tuple[str, str], str], init=False, factory=dict)

    def __enter__(self) -> "PrescriptionsChange":
        """Start context for creating prescriptions."""
        self.prescriptions.repo.git.checkout("HEAD", b=self.branch_name)
        return self

    def __exit__(
        self, exc_type: Optional[Exception], exc_value: Optional[BaseException], traceback: Optional[TracebackType]
    ) -> None:
        """Leave context for creating prescriptions."""
        try:
            if exc_type is not None:
                return

            self.commit()
        finally:
            # Discard changes on any exception.
            self.prescriptions.repo.git.checkout("--", ".")
            self.prescriptions.repo.heads.master.checkout()
            self._prescription_changes.clear()

    def commit(self) -> None:
        """Commit changes done to prescriptions."""
        for key, prescription in self._prescription_changes.items():
            project_name, prescription_name = key
            prescription_path = self.prescriptions.get_prescription_path(project_name, prescription_name)
            os.makedirs(os.path.dirname(prescription_path), exist_ok=True)

            with open(prescription_path, "w") as prescription_file:
                prescription_file.write(prescription)

            self.prescriptions.repo.index.add(prescription_path)

        self.prescriptions.repo.index.commit(self.commit_message)
        # If this PR already exists, this will fail.
        self.prescriptions.repo.remote().push(self.branch_name)

        try:
            pr = self.prescriptions.project.create_pr(
                title=self.commit_message,
                body=self.body or self.prescriptions.PR_BODY,
                target_branch=self.prescriptions.project.default_branch,
                source_branch=self.branch_name,
            )
        except Exception as exc:
            github_errors = getattr(exc, "_GithubException__data", {}).get("errors")
            if github_errors and github_errors[0].get("message").startswith("A pull request already exists for"):
                _LOGGER.warning(github_errors[0]["message"])
                raise

            _LOGGER.exception("Failed to create a pull request")
            raise

        try:
            for label in self.prescriptions.LABELS:
                _LOGGER.debug("Adding label %r", label)
                pr.add_label(label)
        except Exception:
            _LOGGER.exception("Failed to add labels to the pull request")

        _LOGGER.info("Opened pull request #%s: %s", pr.id, self.commit_message)
        self._prescription_changes.clear()

    def rollback(self) -> None:
        """Rollback any changes done to prescriptions."""
        self._prescription_changes.clear()

    def add_prescription(
        self, project_name: str, prescription_name: str, content: str, *, overwrite_cached: bool = False
    ) -> bool:
        """Add the given prescription to cache, scheduled for a change."""
        if not content:
            _LOGGER.warning(
                "No prescription content generated for %r (prescription %r), no changes done",
                project_name,
                prescription_name,
            )
            return False

        if not overwrite_cached and project_name in self._prescription_changes:
            _LOGGER.warning(
                "Prescription for %r has already cached change, not making changes to cached prescription", project_name
            )
            return False

        self._prescription_changes[(project_name, prescription_name)] = content
        return True
