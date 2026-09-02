"""Local JSON file persistence for a canonical `Project` (ADR-011).

`corytm.engine` is the sole reader and writer of a Corytm project file's
content: a versioned envelope wrapping a JSON payload that currently
mirrors `Project`'s own shape. The envelope's `schema_version` is
Corytm's own persistence-format version, independent of
`src/schemas/project.proto`'s wire-protocol versioning, and carries no
migration or backward-compatibility guarantee during Alpha.
"""

import json
from pathlib import Path
from typing import cast

from .project import Project

SCHEMA_VERSION = 1


class ProjectFileError(ValueError):
    """A project file's envelope is missing, malformed, or unsupported."""


def save_project(project: Project, path: Path) -> None:
    """Write `project` to `path` as ADR-011's versioned JSON envelope.

    Args:
        project: The canonical project to persist.
        path: Destination file path; overwritten if it already exists.
    """
    envelope = {
        "schema_version": SCHEMA_VERSION,
        "project": project.model_dump(mode="json"),
    }
    path.write_text(json.dumps(envelope, indent=2))


def load_project(path: Path) -> Project:
    """Read `path` as ADR-011's versioned JSON envelope and rebuild a `Project`.

    Args:
        path: File path to load.

    Returns:
        The `Project` reconstructed from the envelope's `project` payload.

    Raises:
        ProjectFileError: `path`'s content isn't valid JSON, isn't an
            envelope carrying both `schema_version` and `project`, or
            names a `schema_version` other than this module's own
            `SCHEMA_VERSION`.
        pydantic.ValidationError: The envelope's `project` payload
            doesn't match `Project`'s own shape.
    """
    try:
        raw: object = json.loads(path.read_text())
    except json.JSONDecodeError as error:
        raise ProjectFileError(f"{path} does not contain valid JSON") from error

    if not isinstance(raw, dict) or "schema_version" not in raw or "project" not in raw:
        raise ProjectFileError(
            f"{path} is missing a valid schema_version/project envelope"
        )

    envelope = cast(dict[str, object], raw)
    schema_version: object = envelope["schema_version"]
    if schema_version != SCHEMA_VERSION:
        raise ProjectFileError(
            f"{path} has schema_version {schema_version!r}, expected {SCHEMA_VERSION!r}"
        )

    return Project.model_validate(envelope["project"])
