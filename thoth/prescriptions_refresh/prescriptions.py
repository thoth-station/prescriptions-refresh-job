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

"""Base class for implementing handlers."""

import logging
import os
import random
import shutil
import tempfile
import yaml
from typing import Any
from typing import Dict
from typing import Generator
from typing import List
from typing import Optional
from typing import Tuple

import attr
from git import Repo
from ogr.services.github import GithubProject
from ogr.services.github import GithubService

from .exceptions import PrescriptionNotFound

_LOGGER = logging.getLogger(__name__)
_PR_BODY = """\
This change was automatically generated using \
[thoth-station/prescriptions-refresh-job](https://github.com/thoth-station/prescriptions-refresh-job). This periodic \
job makes sure the repository is up to date. Visit [thoth-station.ninja](https://thoth-station.ninja) for more info.
"""

_RANDOMIZE = bool(int(os.getenv("THOTH_PRESCRIPTIONS_REFRESH_RANDOMIZE", 0)))


@attr.s(slots=True)
class Prescriptions:
    """A base class implementing core prescriptions-refresh handler functionality."""

    DEFAULT_PRESCRIPTIONS_REPO = os.getenv(
        "THOTH_PRESCRIPTIONS_REFRESH_REPO",
        "git@github.com:thoth-station/prescriptions.git",
    )
    PRESCRIPTIONS_REPO: str = DEFAULT_PRESCRIPTIONS_REPO

    DEFAULT_LABELS: str = os.getenv("THOTH_PRESCRIPTIONS_REFRESH_GITHUB_LABELS", "bot")
    LABELS: List[str] = [i for i in DEFAULT_LABELS.split(",") if i]

    repo = attr.ib(type=Repo)
    github_tokens = attr.ib(type=List[str])
    project = attr.ib(type=GithubProject)

    @repo.default
    def _repo_default(self) -> Repo:
        """Clone repository on instantiation."""
        _LOGGER.debug("Cloning prescriptions repo %r", self.PRESCRIPTIONS_REPO)
        repo = Repo.clone_from(self.PRESCRIPTIONS_REPO, tempfile.mkdtemp(), depth=1)
        _LOGGER.debug("Cloned repository available at %r", repo.working_dir)
        return repo

    @project.default
    def _project_default(self) -> GithubService:
        """Initialize OGR for handling GitHub pull-requests."""
        _, parts = self.PRESCRIPTIONS_REPO.split(":", maxsplit=1)
        organization, repo = parts.split("/", maxsplit=1)

        if repo.endswith(".git"):
            repo = repo[: -len(".git")]

        return GithubService(
            token=self.get_github_token(),
            github_app_id=os.getenv("GITHUB_APP_ID"),
            github_app_private_key_path=os.getenv("GITHUB_PRIVATE_KEY_PATH"),
        ).get_project(namespace=organization, repo=repo)

    @github_tokens.default
    def _github_tokens_default(self) -> List[str]:
        """Initialize GitHub tokens passed."""
        tokens = os.getenv("THOTH_PRESCRIPTIONS_REFRESH_GITHUB_TOKEN")
        if not tokens:
            raise NotImplementedError("One or multiple GitHub tokens expected to run prescriptions-refresh-job")
        tokens = tokens.replace("\n", ",")  # Allow also new line delimiters.
        res = [t.strip() for t in tokens.split(",")]
        return res

    def get_github_token(self) -> Any:
        """Get a random GitHub token from pool."""
        return random.choice(self.github_tokens)

    def __enter__(self) -> "Prescriptions":
        """Allow using Prescriptions with the with statement."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore
        """Clean up once the work is done."""
        self.clean()

    def clean(self) -> None:
        """Clean the bits on destruction."""
        if self.repo and self.repo.working_dir:
            _LOGGER.debug("Cleaning up cloned repository in %r", self.repo.working_dir)
            shutil.rmtree(self.repo.working_dir)

    def iter_prescriptions_yaml(self) -> Generator[Tuple[str, Dict[str, Any]], None, None]:
        """Iterate over prescription YAML files available in the cloned repository."""
        all_files = list(os.walk(self.repo.working_dir))
        if _RANDOMIZE:
            _LOGGER.error("Randomizing prescriptions walk")
            random.shuffle(all_files)

        for root, _, files in all_files:
            for f in files:
                if not f.endswith((".yaml", ".yml")):
                    continue

                file_path = os.path.join(root, f)

                with open(file_path, "r") as f_file:
                    content = yaml.safe_load(f_file)

                root_path_len = len(self.repo.working_dir.split(os.sep))
                file_path = os.path.join(*file_path.split(os.sep)[root_path_len:])

                if "units" not in content:
                    _LOGGER.warning("No prescription units found in %r, skipping...", file_path)
                    continue

                yield file_path, content

    def iter_projects(self) -> Generator[str, None, None]:
        """Iterate over available projects.

        Note this method might be ineffective in cases when a handler does more things than just listing project
        names as the method requires loading all the prescriptions. To speed up this, similar logic can be
        implemented in the handler.
        """
        last_seen = None
        for file_path, _ in self.iter_prescriptions_yaml():
            project_name = self.project_name_from_prescription_path(file_path)
            if project_name != last_seen:
                _LOGGER.debug("Project %r from the prescriptions database", project_name)
                yield project_name
                last_seen = project_name

    @staticmethod
    def project_name_from_prescription_path(prescription_path: str) -> str:
        """Get project name out of prescription path."""
        return os.path.basename(os.path.dirname(prescription_path))

    def get_prescription_path(self, project_name: str, prescription_name: str) -> str:
        """Get path to a prescriptions directory for the given project."""
        path = os.path.join(self.repo.working_dir, "prescriptions")
        if len(project_name) > 2:
            path = os.path.join(path, f"{project_name[:2]}_")

        return os.path.join(path, project_name, prescription_name)

    @staticmethod
    def get_prescription_name_from_path(prescription_path: str) -> str:
        """Get prescription name from its path."""
        return os.path.basename(prescription_path)

    def get_prescription(self, project_name: str, prescription_name: str) -> Optional[Dict[str, Any]]:
        """Get a prescription for the given project."""
        prescription_path = os.path.join(
            self.repo.working_dir, self.get_prescription_path(project_name, prescription_name)
        )
        if not os.path.exists(prescription_path):
            return None

        with open(prescription_path, "r") as prescription_file:
            result: Optional[Dict[str, Any]] = yaml.safe_load(prescription_file)
            return result

    def delete_prescription(
        self,
        project_name: str,
        prescription_name: str,
        *,
        commit_message: Optional[str] = None,
        nonexisting_ok: bool = False,
    ) -> bool:
        """Delete the given prescription if exists."""
        prescription_path = self.get_prescription_path(project_name, prescription_name)

        if not os.path.exists(prescription_path):
            _LOGGER.debug("Not deleting prescription at %r as it does not exist", prescription_path)
            if not nonexisting_ok:
                raise PrescriptionNotFound(f"Prescription {prescription_name!r} for {project_name!r} does not exist")

            return False

        _LOGGER.debug("Creating a pull request to delete prescription at %r", prescription_path)

        branch_name = f"pres-rm-{project_name}-{prescription_name}"
        commit_message = "⚕️ " + (commit_message or f"Remove prescription {prescription_name!r} for {project_name!r}")
        self.repo.git.checkout("HEAD", b=branch_name)
        self.repo.index.remove([prescription_path], working_tree=True)
        self.repo.index.commit(commit_message)
        # If this PR already exists, this will fail.
        self.repo.remote().push(branch_name)
        self.repo.git.checkout("master")

        try:
            pr = self.project.create_pr(
                title=commit_message,
                body="This change was automatically generated",
                target_branch=self.project.default_branch,
                source_branch=branch_name,
            )
        except Exception as exc:
            github_errors = getattr(exc, "_GithubException__data", {}).get("errors")
            if github_errors and github_errors[0].get("message").startswith("A pull request already exists for"):
                _LOGGER.warning(github_errors[0]["message"])
                return False
            _LOGGER.exception("Failed to create a pull request")
            return False

        try:
            for label in self.LABELS:
                _LOGGER.debug("Adding label %r", label)
                pr.add_label(label)
        except Exception:
            _LOGGER.exception("Failed to add labels to the pull request")

        _LOGGER.info("Opened pull request #%s: %s", pr.id, commit_message)
        return True

    def create_prescription(
        self,
        project_name: str,
        prescription_name: str,
        content: str,
        *,
        commit_message: Optional[str] = None,
    ) -> bool:
        """Create the given prescription."""
        if not commit_message:
            commit_message = f"Add prescription {prescription_name!r} for {project_name!r}"

        prescription_content = yaml.safe_load(content)
        old_prescription = self.get_prescription(project_name, prescription_name)
        if old_prescription == prescription_content:
            _LOGGER.debug(
                "Prescription %r for %r is already present and its content is the same", prescription_name, project_name
            )
            return False

        prescription_path = self.get_prescription_path(project_name, prescription_name)
        with open(prescription_path, "w") as prescription_file:
            prescription_file.write(content)

        branch_name = f"pres-{project_name}-{prescription_name}"
        commit_message = "💊 " + (commit_message or f"Add prescription {prescription_name!r} for {project_name!r}")
        self.repo.git.checkout("HEAD", b=branch_name)
        self.repo.index.add([prescription_path])
        self.repo.index.commit(commit_message)
        # If this PR already exists, this will fail.
        self.repo.remote().push(branch_name)
        self.repo.git.checkout("master")

        try:
            pr = self.project.create_pr(
                title=commit_message,
                body=_PR_BODY,
                target_branch=self.project.default_branch,
                source_branch=branch_name,
            )
        except Exception as exc:
            github_errors = getattr(exc, "_GithubException__data", {}).get("errors")
            if github_errors and github_errors[0].get("message").startswith("A pull request already exists for"):
                _LOGGER.warning(github_errors[0]["message"])
                return False
            _LOGGER.exception("Failed to create a pull request")
            return False

        try:
            for label in self.LABELS:
                _LOGGER.debug("Adding label %r", label)
                pr.add_label(label)
        except Exception:
            _LOGGER.exception("Failed to add labels to the pull request")

        _LOGGER.info("Opened pull request #%s: %s", pr.id, commit_message)
        return True
