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

"""Check scorecards computed by Open Source Security Foundation."""

import logging
from typing import Any
from typing import Dict

from typing import TYPE_CHECKING

from google.cloud import bigquery

from .gh_link import iter_gh_info

if TYPE_CHECKING:
    from thoth.prescriptions_refresh.prescriptions import Prescriptions


_LOGGER = logging.getLogger(__name__)

_SCORECARDS_WRAP_GENERIC_UNIT = """\
units:
  wraps:
  - name: {prescription_name}
    type: wrap
    should_include:
      adviser_pipeline: true
    match:
      state:
        resolved_dependencies:
        - name: {package_name}
    run:
      justification:
      - type: {type}
        message: {message}
        link: https://github.com/ossf/scorecard/blob/main/docs/checks.md
        package_name: {package_name}
"""


def _handle_code_review(
    prescriptions: "Prescriptions",
    project_name: str,
    scorecards_entry: Dict[str, Any],
) -> None:
    """Handle Code-Review scorecards."""
    if int(scorecards_entry["Confidence"]) == 0:
        prescriptions.delete_prescription(
            project_name,
            prescription_name="scorecards_code_review.yaml",
            commit_message=f"Code-Review Security Scorecards for {project_name!r} have low confidence",
            nonexisting_ok=True,
        )
        return

    prescription_name = "CodeReview"
    prescription_name += prescriptions.get_prescription_name("ScoreCardsWrap", project_name)

    if scorecards_entry["Pass"]:
        justification_type = "INFO"
        message = "Project requires code review before the code is merged based on Security Scorecards"
    else:
        justification_type = "WARNING"
        message = "Project does NOT require code review before the code is merged based on Security Scorecards"

    prescriptions.create_prescription(
        project_name,
        "scorecards_code_review.yaml",
        content=_SCORECARDS_WRAP_GENERIC_UNIT.format(
            prescription_name=prescription_name,
            package_name=project_name,
            type=justification_type,
            message=message,
        ),
        commit_message=f"Code-Review Security Scorecards update for {project_name!r}",
    )


def _handle_active(
    prescriptions: "Prescriptions",
    project_name: str,
    scorecards_entry: Dict[str, Any],
) -> None:
    """Handle Active scorecards."""
    if int(scorecards_entry["Confidence"]) == 0:
        prescriptions.delete_prescription(
            project_name,
            prescription_name="scorecards_active.yaml",
            commit_message=f"Active Security Scorecards for {project_name!r} have low confidence",
            nonexisting_ok=True,
        )
        return

    prescription_name = "Active"
    prescription_name += prescriptions.get_prescription_name("ScoreCardsWrap", project_name)

    if scorecards_entry["Pass"]:
        justification_type = "INFO"
        message = "Project is actively maintained based on Security Scorecards"
    else:
        justification_type = "WARNING"
        message = "Project is NOT actively maintained based on Security Scorecards"

    prescriptions.create_prescription(
        project_name,
        "scorecards_active.yaml",
        content=_SCORECARDS_WRAP_GENERIC_UNIT.format(
            prescription_name=prescription_name,
            package_name=project_name,
            type=justification_type,
            message=message,
        ),
        commit_message=f"Active Security Scorecards update for {project_name!r}",
    )


def _handle_automatic_dependency_update(
    prescriptions: "Prescriptions",
    project_name: str,
    scorecards_entry: Dict[str, Any],
) -> None:
    """Handle Automatic-Dependency-Update scorecards."""
    if int(scorecards_entry["Confidence"]) == 0:
        prescriptions.delete_prescription(
            project_name,
            prescription_name="scorecards_automatic_dependency_update.yaml",
            commit_message=f"Automatic-Dependency-Update Security Scorecards for {project_name!r} have low confidence",
            nonexisting_ok=True,
        )
        return

    prescription_name = "AutomaticDependencyUpdate"
    prescription_name += prescriptions.get_prescription_name("ScoreCardsWrap", project_name)

    if scorecards_entry["Pass"]:
        justification_type = "INFO"
        message = "Project uses tools for automatic dependency updates based on Security Scorecards"
    else:
        justification_type = "WARNING"
        message = "Project does NOT use tools for automatic dependency updates based on Security Scorecards"

    prescriptions.create_prescription(
        project_name,
        "scorecards_automatic_dependency_update.yaml",
        content=_SCORECARDS_WRAP_GENERIC_UNIT.format(
            prescription_name=prescription_name,
            package_name=project_name,
            type=justification_type,
            message=message,
        ),
        commit_message=f"Automatic-Dependency-Update Security Scorecards update for {project_name!r}",
    )


def _handle_branch_protection(
    prescriptions: "Prescriptions",
    project_name: str,
    scorecards_entry: Dict[str, Any],
) -> None:
    """Handle Branch-Protection scorecards."""
    if int(scorecards_entry["Confidence"]) == 0:
        prescriptions.delete_prescription(
            project_name,
            prescription_name="scorecards_branch_protection.yaml",
            commit_message=f"Branch-Protection Security Scorecards for {project_name!r} have low confidence",
            nonexisting_ok=True,
        )
        return

    prescription_name = "BranchProtection"
    prescription_name += prescriptions.get_prescription_name("ScoreCardsWrap", project_name)

    if scorecards_entry["Pass"]:
        justification_type = "INFO"
        message = "Project has branch protection setup based on Security Scorecards"
    else:
        justification_type = "WARNING"
        message = "Project does NOT have branch protection setup based on Security Scorecards"

    prescriptions.create_prescription(
        project_name,
        "scorecards_branch_protection.yaml",
        content=_SCORECARDS_WRAP_GENERIC_UNIT.format(
            prescription_name=prescription_name,
            package_name=project_name,
            type=justification_type,
            message=message,
        ),
        commit_message=f"Branch-Protection Security Scorecards update for {project_name!r}",
    )


def _handle_token_permissions(
    prescriptions: "Prescriptions",
    project_name: str,
    scorecards_entry: Dict[str, Any],
) -> None:
    """Handle Token-Permissions scorecards."""
    if int(scorecards_entry["Confidence"]) == 0:
        prescriptions.delete_prescription(
            project_name,
            prescription_name="scorecards_token_permissions.yaml",
            commit_message=f"Token-Permissions Security Scorecards for {project_name!r} have low confidence",
            nonexisting_ok=True,
        )
        return

    prescription_name = "TokenPermissions"
    prescription_name += prescriptions.get_prescription_name("ScoreCardsWrap", project_name)

    if scorecards_entry["Pass"]:
        justification_type = "INFO"
        message = "Project follows the principle of least privileged in GitHub workflows based on Security Scorecards"
    else:
        justification_type = "WARNING"
        message = (
            "Project does NOT follow the principle of least privileged in GitHub workflows "
            "based on Security Scorecards"
        )

    prescriptions.create_prescription(
        project_name,
        "scorecards_token_permissions.yaml",
        content=_SCORECARDS_WRAP_GENERIC_UNIT.format(
            prescription_name=prescription_name,
            package_name=project_name,
            type=justification_type,
            message=message,
        ),
        commit_message=f"Token-Permissions Security Scorecards update for {project_name!r}",
    )


def _handle_security_policy(
    prescriptions: "Prescriptions",
    project_name: str,
    scorecards_entry: Dict[str, Any],
) -> None:
    """Handle Security-Policy scorecards."""
    if int(scorecards_entry["Confidence"]) == 0:
        prescriptions.delete_prescription(
            project_name,
            prescription_name="scorecards_security_policy.yaml",
            commit_message=f"Security-Policy Security Scorecards for {project_name!r} have low confidence",
            nonexisting_ok=True,
        )
        return

    prescription_name = "SecurityPolicy"
    prescription_name += prescriptions.get_prescription_name("ScoreCardsWrap", project_name)

    if scorecards_entry["Pass"]:
        justification_type = "INFO"
        message = "Project has a security policy published based on Security Scorecards"
    else:
        justification_type = "WARNING"
        message = "Project does not have any security policy published based on Security Scorecards"

    prescriptions.create_prescription(
        project_name,
        "scorecards_security_policy.yaml",
        content=_SCORECARDS_WRAP_GENERIC_UNIT.format(
            prescription_name=prescription_name,
            package_name=project_name,
            type=justification_type,
            message=message,
        ),
        commit_message=f"Security-Policy Security Scorecards update for {project_name!r}",
    )


def _handle_signed_releases(
    prescriptions: "Prescriptions",
    project_name: str,
    scorecards_entry: Dict[str, Any],
) -> None:
    """Handle Signed-Releases scorecards."""
    if int(scorecards_entry["Confidence"]) == 0:
        prescriptions.delete_prescription(
            project_name,
            prescription_name="scorecards_signed_releases.yaml",
            commit_message=f"Signed-Releases Security Scorecards for {project_name!r} have low confidence",
            nonexisting_ok=True,
        )
        return

    prescription_name = "SignedReleases"
    prescription_name += prescriptions.get_prescription_name("ScoreCardsWrap", project_name)

    if scorecards_entry["Pass"]:
        justification_type = "INFO"
        message = "Project cryptographically signs released artifacts based on Security Scorecards"
    else:
        justification_type = "WARNING"
        message = "Project does NOT cryptographically sign released artifacts based on Security Scorecards"

    prescriptions.create_prescription(
        project_name,
        "scorecards_signed_releases.yaml",
        content=_SCORECARDS_WRAP_GENERIC_UNIT.format(
            prescription_name=prescription_name,
            package_name=project_name,
            type=justification_type,
            message=message,
        ),
        commit_message=f"Signed-Releases Security Scorecards update for {project_name!r}",
    )


def _handle_signed_tags(
    prescriptions: "Prescriptions",
    project_name: str,
    scorecards_entry: Dict[str, Any],
) -> None:
    """Handle Signed-Tags scorecards."""
    if int(scorecards_entry["Confidence"]) == 0:
        prescriptions.delete_prescription(
            project_name,
            prescription_name="scorecards_signed_tags.yaml",
            commit_message=f"Signed-Tags Security Scorecards for {project_name!r} have low confidence",
            nonexisting_ok=True,
        )
        return

    prescription_name = "SignedTags"
    prescription_name += prescriptions.get_prescription_name("ScoreCardsWrap", project_name)

    if scorecards_entry["Pass"]:
        justification_type = "INFO"
        message = "Project cryptographically signs tags based on Security Scorecards"
    else:
        justification_type = "WARNING"
        message = "Project does NOT cryptographically sign tags based on Security Scorecards"

    prescriptions.create_prescription(
        project_name,
        "scorecards_signed_tags.yaml",
        content=_SCORECARDS_WRAP_GENERIC_UNIT.format(
            prescription_name=prescription_name,
            package_name=project_name,
            type=justification_type,
            message=message,
        ),
        commit_message=f"Signed-Tags Security Scorecards update for {project_name!r}",
    )


def _handle_fuzzing(
    prescriptions: "Prescriptions",
    project_name: str,
    scorecards_entry: Dict[str, Any],
) -> None:
    """Handle Fuzzing scorecards."""
    if int(scorecards_entry["Confidence"]) == 0:
        prescriptions.delete_prescription(
            project_name,
            prescription_name="scorecards_fuzzing.yaml",
            commit_message=f"Fuzzing Security Scorecards for {project_name!r} have low confidence",
            nonexisting_ok=True,
        )
        return

    prescription_name = "Fuzzing"
    prescription_name += prescriptions.get_prescription_name("ScoreCardsWrap", project_name)

    if scorecards_entry["Pass"]:
        justification_type = "INFO"
        message = "Project uses fuzzing based on Security Scorecards"
    else:
        justification_type = "WARNING"
        message = "Project does not use fuzzing based on Security Scorecards"

    prescriptions.create_prescription(
        project_name,
        "scorecards_fuzzing.yaml",
        content=_SCORECARDS_WRAP_GENERIC_UNIT.format(
            prescription_name=prescription_name,
            package_name=project_name,
            type=justification_type,
            message=message,
        ),
        commit_message=f"Fuzzing Security Scorecards update for {project_name!r}",
    )


def _handle_vulnerabilities(
    prescriptions: "Prescriptions",
    project_name: str,
    scorecards_entry: Dict[str, Any],
) -> None:
    """Handle Vulnerabilities scorecards."""
    if int(scorecards_entry["Confidence"]) == 0:
        prescriptions.delete_prescription(
            project_name,
            prescription_name="scorecards_vulnerabilities.yaml",
            commit_message=f"Vulnerabilities Security Scorecards for {project_name!r} have low confidence",
            nonexisting_ok=True,
        )
        return

    prescription_name = "Vulnerabilities"
    prescription_name += prescriptions.get_prescription_name("ScoreCardsWrap", project_name)

    if scorecards_entry["Pass"]:
        justification_type = "INFO"
        message = (
            "Project does not have open or unfixed vulnerabilities on the OSV service " "based on Security Scorecards"
        )
    else:
        justification_type = "WARNING"
        message = (
            "Project has open or unfixed vulnerabilities on the Open Source Vulnerabilities "
            "based on Security Scorecards"
        )

    prescriptions.create_prescription(
        project_name,
        "scorecards_vulnerabilities.yaml",
        content=_SCORECARDS_WRAP_GENERIC_UNIT.format(
            prescription_name=prescription_name,
            package_name=project_name,
            type=justification_type,
            message=message,
        ),
        commit_message=f"Vulnerabilities Security Scorecards update for {project_name!r}",
    )


def _handle_packaging(
    prescriptions: "Prescriptions",
    project_name: str,
    scorecards_entry: Dict[str, Any],
) -> None:
    """Handle Packaging scorecards."""
    if int(scorecards_entry["Confidence"]) == 0:
        prescriptions.delete_prescription(
            project_name,
            prescription_name="scorecards_packaging.yaml",
            commit_message=f"Packaging Security Scorecards for {project_name!r} have low confidence",
            nonexisting_ok=True,
        )
        return

    prescription_name = "Packaging"
    prescription_name += prescriptions.get_prescription_name("ScoreCardsWrap", project_name)

    if scorecards_entry["Pass"]:
        justification_type = "INFO"
        message = "Project is published as a package based on Security Scorecards"
    else:
        justification_type = "WARNING"
        message = "Project is NOT published as a package based on Security Scorecards"

    prescriptions.create_prescription(
        project_name,
        "scorecards_packaging.yaml",
        content=_SCORECARDS_WRAP_GENERIC_UNIT.format(
            prescription_name=prescription_name,
            package_name=project_name,
            type=justification_type,
            message=message,
        ),
        commit_message=f"Packaging Security Scorecards update for {project_name!r}",
    )


def _handle_binary_artifacts(
    prescriptions: "Prescriptions",
    project_name: str,
    scorecards_entry: Dict[str, Any],
) -> None:
    """Handle Binary-Artifacts scorecards."""
    if int(scorecards_entry["Confidence"]) == 0:
        prescriptions.delete_prescription(
            project_name,
            prescription_name="scorecards_binary_artifacts.yaml",
            commit_message=f"Binary-Artifacts Security Scorecards for {project_name!r} have low confidence",
            nonexisting_ok=True,
        )
        return

    prescription_name = "BinaryArtifacts"
    prescription_name += prescriptions.get_prescription_name("ScoreCardsWrap", project_name)

    if scorecards_entry["Pass"]:
        justification_type = "INFO"
        message = "Project does not have binary artifacts in the source repository"
    else:
        justification_type = "WARNING"
        message = "Project has binary artifacts in the source repository"

    prescriptions.create_prescription(
        project_name,
        "scorecards_binary_artifacts.yaml",
        content=_SCORECARDS_WRAP_GENERIC_UNIT.format(
            prescription_name=prescription_name,
            package_name=project_name,
            type=justification_type,
            message=message,
        ),
        commit_message=f"Binary-Artifacts Security Scorecards update for {project_name!r}",
    )


def _handle_cii_best_practices(
    prescriptions: "Prescriptions",
    project_name: str,
    scorecards_entry: Dict[str, Any],
) -> None:
    """Handle CII-Best-Practices scorecards."""
    if int(scorecards_entry["Confidence"]) == 0:
        prescriptions.delete_prescription(
            project_name,
            prescription_name="scorecards_cii_best_practices.yaml",
            commit_message=f"CII-Best-Practices Security Scorecards for {project_name!r} have low confidence",
            nonexisting_ok=True,
        )
        return

    prescription_name = "CIIBestPractices"
    prescription_name += prescriptions.get_prescription_name("ScoreCardsWrap", project_name)

    if scorecards_entry["Pass"]:
        justification_type = "INFO"
        message = "Project honours CII Best Practices based on Security Scorecards"
    else:
        justification_type = "WARNING"
        message = "Project does NOT honour CII Best Practices based on Security Scorecards"

    prescriptions.create_prescription(
        project_name,
        "scorecards_cii_best_practices.yaml",
        content=_SCORECARDS_WRAP_GENERIC_UNIT.format(
            prescription_name=prescription_name,
            package_name=project_name,
            type=justification_type,
            message=message,
        ),
        commit_message=f"CII-Best-Practices Security Scorecards update for {project_name!r}",
    )


def _handle_pinned_dependencies(
    prescriptions: "Prescriptions",
    project_name: str,
    scorecards_entry: Dict[str, Any],
) -> None:
    """Handle Pinned-Dependencies scorecards."""
    if int(scorecards_entry["Confidence"]) == 0:
        prescriptions.delete_prescription(
            project_name,
            prescription_name="scorecards_pinned_dependencies.yaml",
            commit_message=f"Pinned-Dependencies Security Scorecards for {project_name!r} have low confidence",
            nonexisting_ok=True,
        )
        return

    prescription_name = "PinnedDependencies"
    prescription_name += prescriptions.get_prescription_name("ScoreCardsWrap", project_name)

    if scorecards_entry["Pass"]:
        justification_type = "INFO"
        message = "Project uses pinned dependencies based on Security Scorecards"
    else:
        justification_type = "WARNING"
        message = "Project does NOT use pinned dependencies based on Security Scorecards"

    prescriptions.create_prescription(
        project_name,
        "scorecards_pinned_dependencies.yaml",
        content=_SCORECARDS_WRAP_GENERIC_UNIT.format(
            prescription_name=prescription_name,
            package_name=project_name,
            type=justification_type,
            message=message,
        ),
        commit_message=f"Pinned-Dependencies Security Scorecards update for {project_name!r}",
    )


def _handle_contributors(
    prescriptions: "Prescriptions",
    project_name: str,
    scorecards_entry: Dict[str, Any],
) -> None:
    """Handle Contributors scorecards."""
    if int(scorecards_entry["Confidence"]) == 0:
        prescriptions.delete_prescription(
            project_name,
            prescription_name="scorecards_contributors.yaml",
            commit_message=f"Contributors Security Scorecards for {project_name!r} have low confidence",
            nonexisting_ok=True,
        )
        return

    prescription_name = "Contributors"
    prescription_name += prescriptions.get_prescription_name("ScoreCardsWrap", project_name)

    if scorecards_entry["Pass"]:
        justification_type = "INFO"
        message = "Project has a set of contributors from multiple companies based on Security Scorecards"
    else:
        justification_type = "WARNING"
        message = "Project does NOT have a set of contributors from multiple companies based on Security Scorecards"

    prescriptions.create_prescription(
        project_name,
        "scorecards_contributors.yaml",
        content=_SCORECARDS_WRAP_GENERIC_UNIT.format(
            prescription_name=prescription_name,
            package_name=project_name,
            type=justification_type,
            message=message,
        ),
        commit_message=f"Contributors Security Scorecards update for {project_name!r}",
    )


def _handle_ci_tests(
    prescriptions: "Prescriptions",
    project_name: str,
    scorecards_entry: Dict[str, Any],
) -> None:
    """Handle CI-Tests scorecards."""
    if int(scorecards_entry["Confidence"]) == 0:
        prescriptions.delete_prescription(
            project_name,
            prescription_name="scorecards_ci_tests.yaml",
            commit_message=f"CI-Tests Security Scorecards for {project_name!r} have low confidence",
            nonexisting_ok=True,
        )
        return

    prescription_name = "CITests"
    prescription_name += prescriptions.get_prescription_name("ScoreCardsWrap", project_name)

    if scorecards_entry["Pass"]:
        justification_type = "INFO"
        message = "Project runs CI tests before pull requests are merged based on Security Scorecards"
    else:
        justification_type = "WARNING"
        message = "Project does NOT run CI tests before pull requests are merged based on Security Scorecards"

    prescriptions.create_prescription(
        project_name,
        "scorecards_ci_tests.yaml",
        content=_SCORECARDS_WRAP_GENERIC_UNIT.format(
            prescription_name=prescription_name,
            package_name=project_name,
            type=justification_type,
            message=message,
        ),
        commit_message=f"CI-Tests Security Scorecards update for {project_name!r}",
    )


def _handle_sast(
    prescriptions: "Prescriptions",
    project_name: str,
    scorecards_entry: Dict[str, Any],
) -> None:
    """Handle SAST scorecards."""
    if int(scorecards_entry["Confidence"]) == 0:
        prescriptions.delete_prescription(
            project_name,
            prescription_name="scorecards_sast.yaml",
            commit_message=f"SAST Security Scorecards for {project_name!r} have low confidence",
            nonexisting_ok=True,
        )
        return

    prescription_name = "SAST"
    prescription_name += prescriptions.get_prescription_name("ScoreCardsWrap", project_name)

    if scorecards_entry["Pass"]:
        justification_type = "INFO"
        message = "Project uses static source code analysis based on Security Scorecards"
    else:
        justification_type = "WARNING"
        message = "Project does NOT use static source code analysis based on Security Scorecards"

    prescriptions.create_prescription(
        project_name,
        "scorecards_sast.yaml",
        content=_SCORECARDS_WRAP_GENERIC_UNIT.format(
            prescription_name=prescription_name,
            package_name=project_name,
            type=justification_type,
            message=message,
        ),
        commit_message=f"SAST Security Scorecards update for {project_name!r}",
    )


_SCORECARDS_HANDLERS = {
    "Code-Review": _handle_code_review,
    "Active": _handle_active,
    "Maintained": _handle_active,
    "Automatic-Dependency-Update": _handle_automatic_dependency_update,
    "Dependency-Update-Tool": _handle_automatic_dependency_update,
    "Branch-Protection": _handle_branch_protection,
    "Token-Permissions": _handle_token_permissions,
    "Security-Policy": _handle_security_policy,
    "Signed-Releases": _handle_signed_releases,
    "Signed-Tags": _handle_signed_tags,
    "Fuzzing": _handle_fuzzing,
    "Vulnerabilities": _handle_vulnerabilities,
    "Packaging": _handle_packaging,
    "Binary-Artifacts": _handle_binary_artifacts,
    "CII-Best-Practices": _handle_cii_best_practices,
    "Pinned-Dependencies": _handle_pinned_dependencies,
    "Frozen-Dependencies": _handle_pinned_dependencies,
    "Frozen-Deps": _handle_pinned_dependencies,
    "Contributors": _handle_contributors,
    "CI-Tests": _handle_ci_tests,
    "SAST": _handle_sast,
}


def scorecards(prescriptions: "Prescriptions") -> None:
    """Check scorecards computed by OSSF and create corresponding prescriptions."""
    # Parse and prepare scorecards in advance.
    _LOGGER.info("Querying scorecards available in BigQuery")
    client = bigquery.Client()
    query_job = client.query('SELECT * FROM openssf.scorecardcron.scorecard WHERE starts_with(Repo, "github.com")')

    scorecards_dict = {}
    for row in query_job:
        repo = row["Repo"].rstrip("/")

        parts = repo.split("/")
        if len(parts) != 2:
            _LOGGER.debug(
                "Skipping scorecard for repo %r from %r: cannot parse organization and repository",
                parts,
                row["Repo"],
            )
            continue

        scorecards_dict[tuple(parts)] = dict(row)

    _LOGGER.info("Mapping available scorecards to prescriptions")
    for project_name, organization, repository in iter_gh_info(prescriptions):
        scorecards_entry = scorecards_dict.get((organization, repository))

        if not scorecards_entry:
            _LOGGER.debug(
                "No scorecard found for project %r hosted on GitHub slug %s/%s",
                project_name,
                organization,
                repository,
            )
            continue

        for check in scorecards_entry.get("Checks") or []:
            handler = _SCORECARDS_HANDLERS.get(check.get("Name"))

            if not handler:
                _LOGGER.error(
                    "No scorecards handler registered for scorecard %r found for project %r (GItHub slug: %s/%s)",
                    check.get("Name"),
                    project_name,
                    organization,
                    repository,
                )
                continue

            handler(prescriptions, project_name, check)
