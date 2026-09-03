import json
from pathlib import Path

import pytest

from corytm.engine.clip import AudioClip
from corytm.engine.persistence import (
    SCHEMA_VERSION,
    ProjectFileError,
    load_project,
    save_project,
)
from corytm.engine.project import Project
from corytm.engine.track import AudioTrack


def _build_project() -> Project:
    clip_a = AudioClip(id="clip-1", start_seconds=0.0, duration_seconds=1.0)
    clip_b = AudioClip(id="clip-2", start_seconds=2.0, duration_seconds=1.5)
    track_a = AudioTrack(id="track-1", clips=(clip_a, clip_b))
    track_b = AudioTrack(id="track-2", clips=())
    return Project(id="persistence-test", tracks=(track_a, track_b))


def test_save_then_load_round_trips_the_project_unchanged(tmp_path: Path) -> None:
    project = _build_project()
    path = tmp_path / "project.corytm.json"

    save_project(project, path)
    loaded = load_project(path)

    assert loaded == project


def test_save_writes_the_documented_envelope_shape(tmp_path: Path) -> None:
    project = _build_project()
    path = tmp_path / "project.corytm.json"

    save_project(project, path)

    envelope = json.loads(path.read_text())

    assert envelope["schema_version"] == SCHEMA_VERSION
    assert envelope["project"]["id"] == "persistence-test"
    assert len(envelope["project"]["tracks"]) == 2


def test_load_rejects_invalid_json(tmp_path: Path) -> None:
    path = tmp_path / "project.corytm.json"
    path.write_text("not json")

    with pytest.raises(ProjectFileError):
        load_project(path)


def test_load_rejects_a_missing_schema_version(tmp_path: Path) -> None:
    path = tmp_path / "project.corytm.json"
    path.write_text(json.dumps({"project": {"id": "x", "tracks": []}}))

    with pytest.raises(ProjectFileError):
        load_project(path)


def test_load_rejects_a_missing_project_payload(tmp_path: Path) -> None:
    path = tmp_path / "project.corytm.json"
    path.write_text(json.dumps({"schema_version": SCHEMA_VERSION}))

    with pytest.raises(ProjectFileError):
        load_project(path)


def test_load_rejects_an_unsupported_schema_version(tmp_path: Path) -> None:
    path = tmp_path / "project.corytm.json"
    path.write_text(
        json.dumps(
            {"schema_version": SCHEMA_VERSION + 1, "project": {"id": "x", "tracks": []}}
        )
    )

    with pytest.raises(ProjectFileError, match="schema_version"):
        load_project(path)


def test_load_rejects_a_non_object_envelope(tmp_path: Path) -> None:
    path = tmp_path / "project.corytm.json"
    path.write_text(json.dumps([1, 2, 3]))

    with pytest.raises(ProjectFileError):
        load_project(path)
