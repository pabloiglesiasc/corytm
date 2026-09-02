import asyncio
import sys
from pathlib import Path

import pytest

from corytm.engine.clip import AudioClip
from corytm.engine.persistence import load_project, save_project
from corytm.engine.project import Project
from corytm.engine.track import AudioTrack
from corytm.generated.project_pb2 import (
    Command,
    CreateProjectCommand,
    Event,
    MoveClipCommand,
    OpenProjectCommand,
    SaveProjectCommand,
)
from corytm.runtime.desktop import serve_desktop_channel
from corytm.runtime.transport import read_frame, write_frame

_SAMPLE_RATE = 44100.0


class _CapturingStdout:
    def __init__(self) -> None:
        self.lines: list[str] = []
        self._buffer = ""

    def write(self, data: str) -> int:
        self._buffer += data
        while "\n" in self._buffer:
            line, self._buffer = self._buffer.split("\n", 1)
            self.lines.append(line)
        return len(data)

    def flush(self) -> None:
        pass


class _FakeStdin:
    """Yields one `SHUTDOWN` line, standing in for the real sidecar stdin.

    Lets a Python-only test drive `serve_desktop_channel()` through its
    full lifecycle — including the post-session stdin wait — without
    touching the real process stdin, which pytest's own capture
    replaces with an object that raises on read.
    """

    def __iter__(self) -> _FakeStdin:
        return self

    def __next__(self) -> str:
        if self._yielded:
            raise StopIteration
        self._yielded = True
        return "SHUTDOWN\n"

    _yielded = False


async def _read_handshake(stdout: _CapturingStdout) -> tuple[int, str]:
    while True:
        for line in stdout.lines:
            if line.startswith("DESKTOP "):
                _, port_text, secret = line.split(" ")
                return int(port_text), secret
        await asyncio.sleep(0.01)


async def _exchange(
    writer: asyncio.StreamWriter, reader: asyncio.StreamReader, command: Command
) -> Event:
    write_frame(writer, command.SerializeToString())
    await writer.drain()

    event = Event()
    event.ParseFromString(await asyncio.wait_for(read_frame(reader), timeout=15))
    return event


def _build_fixture_project(project_id: str) -> Project:
    clip = AudioClip(id="clip-1", start_seconds=0.0, duration_seconds=2.0)
    track = AudioTrack(id="track-1", clips=(clip,))
    return Project(id=project_id, tracks=(track,))


def test_create_and_save_project_over_one_connection(tmp_path: Path) -> None:
    async def _scenario() -> None:
        stdout = _CapturingStdout()
        original_stdout = sys.stdout
        original_stdin = sys.stdin
        sys.stdout = stdout
        sys.stdin = _FakeStdin()
        try:
            server_task = asyncio.create_task(serve_desktop_channel())

            port, secret = await asyncio.wait_for(_read_handshake(stdout), timeout=5)

            reader, writer = await asyncio.open_connection("127.0.0.1", port)
            write_frame(writer, secret.encode("utf-8"))
            await writer.drain()

            created = await _exchange(
                writer,
                reader,
                Command(create_project=CreateProjectCommand(schema_version=1)),
            )
            assert created.WhichOneof("event") == "project_created"
            assert created.project_created.project_id

            save_path = tmp_path / "saved.corytm.json"
            saved = await _exchange(
                writer,
                reader,
                Command(
                    save_project=SaveProjectCommand(
                        schema_version=1, file_path=str(save_path)
                    )
                ),
            )
            assert saved.WhichOneof("event") == "project_saved"
            assert saved.project_saved.project_id == created.project_created.project_id
            assert saved.project_saved.file_path == str(save_path)

            reloaded = load_project(save_path)
            assert reloaded.id == created.project_created.project_id
            assert reloaded.tracks == ()

            writer.close()
            await writer.wait_closed()

            await asyncio.wait_for(server_task, timeout=5)
        finally:
            sys.stdout = original_stdout
            sys.stdin = original_stdin

    asyncio.run(asyncio.wait_for(_scenario(), timeout=20))


@pytest.mark.transport
def test_open_project_re_materializes_it_and_move_clip_still_applies(
    tmp_path: Path,
) -> None:
    fixture_project = _build_fixture_project("open-project-test")
    fixture_path = tmp_path / "fixture.corytm.json"
    save_project(fixture_project, fixture_path)

    async def _scenario() -> None:
        stdout = _CapturingStdout()
        original_stdout = sys.stdout
        original_stdin = sys.stdin
        sys.stdout = stdout
        sys.stdin = _FakeStdin()
        try:
            server_task = asyncio.create_task(serve_desktop_channel())

            port, secret = await asyncio.wait_for(_read_handshake(stdout), timeout=5)

            reader, writer = await asyncio.open_connection("127.0.0.1", port)
            write_frame(writer, secret.encode("utf-8"))
            await writer.drain()

            opened = await _exchange(
                writer,
                reader,
                Command(
                    open_project=OpenProjectCommand(
                        schema_version=1, file_path=str(fixture_path)
                    )
                ),
            )
            assert opened.WhichOneof("event") == "project_opened"
            assert opened.project_opened.project_id == "open-project-test"
            assert opened.project_opened.track_count == 1
            assert opened.project_opened.rendered_sample_count == pytest.approx(
                2.0 * _SAMPLE_RATE, abs=1
            )
            assert opened.project_opened.peak_amplitude > 0.5

            moved = await _exchange(
                writer,
                reader,
                Command(
                    move_clip=MoveClipCommand(
                        schema_version=1,
                        project_id="open-project-test",
                        track_id="track-1",
                        clip_id="clip-1",
                        new_start_seconds=1.0,
                    )
                ),
            )
            assert moved.WhichOneof("event") == "clip_moved"
            assert moved.clip_moved.moved is True
            assert moved.clip_moved.start_seconds == 1.0

            writer.close()
            await writer.wait_closed()

            await asyncio.wait_for(server_task, timeout=5)
        finally:
            sys.stdout = original_stdout
            sys.stdin = original_stdin

    asyncio.run(asyncio.wait_for(_scenario(), timeout=30))


@pytest.mark.transport
def test_move_clip_still_works_without_any_prior_command() -> None:
    async def _scenario() -> None:
        stdout = _CapturingStdout()
        original_stdout = sys.stdout
        original_stdin = sys.stdin
        sys.stdout = stdout
        sys.stdin = _FakeStdin()
        try:
            server_task = asyncio.create_task(serve_desktop_channel())

            port, secret = await asyncio.wait_for(_read_handshake(stdout), timeout=5)

            reader, writer = await asyncio.open_connection("127.0.0.1", port)
            write_frame(writer, secret.encode("utf-8"))
            await writer.drain()

            moved = await _exchange(
                writer,
                reader,
                Command(
                    move_clip=MoveClipCommand(
                        schema_version=1,
                        project_id="desktop-fixture",
                        track_id="track-1",
                        clip_id="clip-1",
                        new_start_seconds=1.0,
                    )
                ),
            )
            assert moved.WhichOneof("event") == "clip_moved"
            assert moved.clip_moved.moved is True
            assert moved.clip_moved.start_seconds == 1.0
            assert moved.clip_moved.rendered_sample_count > 0
            assert moved.clip_moved.peak_amplitude > 0.0

            writer.close()
            await writer.wait_closed()

            await asyncio.wait_for(server_task, timeout=5)
        finally:
            sys.stdout = original_stdout
            sys.stdin = original_stdin

    asyncio.run(asyncio.wait_for(_scenario(), timeout=30))
