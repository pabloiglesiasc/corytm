"""Serves ADR-010's second, Desktop-facing loopback transport.

Implements the Python-core half of the Desktop↔Python command channel:
a second `asyncio` listener, independent of whatever port/secret this
process later uses to spawn and authenticate the Native Audio Runtime
(ADR-007), whose port and per-launch secret are handed to Rust over the
existing sidecar stdout lifecycle channel. Accepts one authenticated
client connection and dispatches a sequence of `project.proto`
`Command`-enveloped commands against one in-memory "current project"
slot — `CreateProjectCommand`/`SaveProjectCommand`/`OpenProjectCommand`
(backed by ADR-011's `corytm.engine.persistence` module),
`AddAudioTrackCommand`/`AddAudioClipCommand` (EP-012's track/clip
authoring operations), and the pre-existing `MoveClipCommand` —
mirroring the multi-command session loop `native_runtime.cpp` already
implements (FT-017/TK-018), reusing `project.proto`'s message types by
reference per ADR-010 rather than a new Desktop-owned envelope.
"""

import asyncio
import contextlib
import secrets
import sys
import tempfile
import uuid
from pathlib import Path

from corytm.engine.clip import AudioClip
from corytm.engine.persistence import load_project, save_project
from corytm.engine.project import Project
from corytm.engine.track import AudioTrack
from corytm.generated.project_pb2 import (
    AudioClipAddedEvent,
    AudioTrackAddedEvent,
    Command,
    Event,
    ProjectCreatedEvent,
    ProjectOpenedEvent,
    ProjectSavedEvent,
)

from .session import (
    PlaybackSession,
    add_clip_in_session,
    materialize_project,
    move_clip_in_session,
)
from .transport import read_frame, write_frame

_AUTHENTICATION_TIMEOUT_SECONDS = 5
_SCHEMA_VERSION = 1


def _build_desktop_fixture_project() -> Project:
    clip = AudioClip(id="clip-1", start_seconds=0.0, duration_seconds=2.0)
    track = AudioTrack(id="track-1", clips=(clip,))
    return Project(id="desktop-fixture", tracks=(track,))


async def _dispatch_command(
    command: Command,
    current_project: Project,
    playback_session: PlaybackSession,
    device_warm_up_task: asyncio.Task[bool],
    output_directory: Path,
) -> tuple[Event, Project]:
    """Apply one `Command` against `current_project` and return its `Event`.

    Args:
        command: The received, already-decoded command.
        current_project: The session's project so far — `_run_session`
            always seeds this with the hardcoded fixture, so a
            connection that only ever sends `MoveClipCommand` behaves
            exactly as before this dispatcher existed.
        playback_session: The session's single, connection-lifetime
            playback process, spawned eagerly by `_run_session`.
        device_warm_up_task: The playback session's own backgrounded
            device-open call — every playback command awaits this
            first (a no-op once it has already completed, which real
            usage gives plenty of time to do before Play is first
            clicked) since it reads/writes the same connection
            `playback_session`'s own commands do, and only one read
            can be in flight on it at a time.
        output_directory: Directory the native process should write
            its rendered output into, for any command that renders.

    Returns:
        The resulting `Event`, and the project to carry forward as
        `current_project` for the next command in this session.

    Raises:
        ValueError: `command` names an unknown track/clip, or carries
            no recognized command.
        FileNotFoundError, RuntimeError, TimeoutError: propagated
            unchanged from the Runtime/native calls a command makes.
    """
    which = command.WhichOneof("command")

    if which == "create_project":
        new_project = Project(id=str(uuid.uuid4()), tracks=())
        return (
            Event(
                project_created=ProjectCreatedEvent(
                    schema_version=_SCHEMA_VERSION, project_id=new_project.id
                )
            ),
            new_project,
        )

    if which == "save_project":
        file_path = command.save_project.file_path
        save_project(current_project, Path(file_path))
        return (
            Event(
                project_saved=ProjectSavedEvent(
                    schema_version=_SCHEMA_VERSION,
                    project_id=current_project.id,
                    file_path=file_path,
                )
            ),
            current_project,
        )

    if which == "open_project":
        file_path = command.open_project.file_path
        loaded_project = load_project(Path(file_path))
        rendered_event = await materialize_project(loaded_project, output_directory)
        return (
            Event(
                project_opened=ProjectOpenedEvent(
                    schema_version=_SCHEMA_VERSION,
                    project_id=loaded_project.id,
                    file_path=file_path,
                    track_count=len(loaded_project.tracks),
                    rendered_sample_count=rendered_event.rendered_sample_count,
                    peak_amplitude=rendered_event.peak_amplitude,
                )
            ),
            loaded_project,
        )

    if which == "add_track":
        track_id = str(uuid.uuid4())
        new_project = current_project.with_track_added(track_id=track_id)
        return (
            Event(
                track_added=AudioTrackAddedEvent(
                    schema_version=_SCHEMA_VERSION,
                    project_id=new_project.id,
                    track_id=track_id,
                    track_count=len(new_project.tracks),
                )
            ),
            new_project,
        )

    if which == "add_clip":
        add_clip_command = command.add_clip
        clip_id = str(uuid.uuid4())
        new_project, new_clip, rendered_event = await add_clip_in_session(
            current_project,
            track_id=add_clip_command.track_id,
            clip_id=clip_id,
            duration_seconds=add_clip_command.duration_seconds,
            output_directory=output_directory,
        )
        return (
            Event(
                clip_added=AudioClipAddedEvent(
                    schema_version=_SCHEMA_VERSION,
                    project_id=new_project.id,
                    track_id=add_clip_command.track_id,
                    clip_id=clip_id,
                    start_seconds=new_clip.start_seconds,
                    duration_seconds=new_clip.duration_seconds,
                    rendered_file_path=rendered_event.rendered_file_path,
                    rendered_sample_count=rendered_event.rendered_sample_count,
                    peak_amplitude=rendered_event.peak_amplitude,
                )
            ),
            new_project,
        )

    if which == "move_clip":
        move = command.move_clip
        new_project, clip_moved_event = await move_clip_in_session(
            current_project,
            track_id=move.track_id,
            clip_id=move.clip_id,
            new_start_seconds=move.new_start_seconds,
            output_directory=output_directory,
        )
        return Event(clip_moved=clip_moved_event), new_project

    if which == "play":
        await device_warm_up_task
        started_event = await playback_session.play(current_project)
        return Event(playback_started=started_event), current_project

    if which == "get_playback_position":
        await device_warm_up_task
        position_event = await playback_session.get_position()
        return Event(playback_position=position_event), current_project

    if which == "stop":
        await device_warm_up_task
        stopped_event = await playback_session.stop()
        return Event(playback_stopped=stopped_event), current_project

    raise ValueError(f"unsupported Desktop channel command: {which!r}")


async def _run_session(
    reader: asyncio.StreamReader, writer: asyncio.StreamWriter
) -> None:
    """Dispatch `Command` frames from `reader` until the client disconnects.

    Holds one in-memory "current project" slot, and one connection-
    lifetime `PlaybackSession`, across the whole connection — the
    project slot seeded with the existing hardcoded fixture so a
    connection that only ever sends `MoveClipCommand` behaves exactly
    as before this session loop existed. The playback session is
    spawned here, before the first command is even read, and its own
    device-open is kicked off as a backgrounded task right away: real
    usage (creating/opening a project, adding a track and clip) gives
    its real several-second cost plenty of time to finish before the
    user ever clicks Play; a Play arriving before it finishes simply
    awaits it rather than erroring. Spawning the process itself is
    deliberately not backgrounded (`PlaybackSession.spawn` is fast) so
    a real process handle is always available immediately to kill on
    disconnect, without ever having to wait out the slow device-open —
    only the backgrounded warm-up task itself needs cancelling first.

    The read below deliberately has no timeout: this channel is
    genuinely persistent for the app's whole session (ADR-010), so an
    arbitrarily long gap between human-triggered commands is normal,
    not a failure — only the client actually closing the connection
    (`IncompleteReadError`, on EOF) ends the session, at which point the
    playback session is killed rather than left to leak.

    Args:
        reader: The authenticated client connection to read commands
            from.
        writer: The same connection, to write each command's `Event`
            back to.
    """
    current_project: Project = _build_desktop_fixture_project()

    with tempfile.TemporaryDirectory() as playback_output_directory:
        playback_session = await PlaybackSession.spawn(Path(playback_output_directory))
        device_warm_up_task: asyncio.Task[bool] = asyncio.create_task(
            playback_session.prepare_device()
        )

        while True:
            try:
                command_bytes = await read_frame(reader)
            except asyncio.IncompleteReadError:
                device_warm_up_task.cancel()
                with contextlib.suppress(asyncio.CancelledError, Exception):
                    await device_warm_up_task
                await playback_session.kill()
                return

            command = Command()
            command.ParseFromString(command_bytes)

            with tempfile.TemporaryDirectory() as output_directory:
                event, current_project = await _dispatch_command(
                    command,
                    current_project,
                    playback_session,
                    device_warm_up_task,
                    Path(output_directory),
                )

            write_frame(writer, event.SerializeToString())
            await writer.drain()


async def serve_desktop_channel() -> None:
    """Run the Desktop channel server until shutdown.

    Prints `READY` followed by a `DESKTOP <port> <secret>` line over
    stdout, accepts exactly one authenticated client connection, then
    dispatches its sequence of `Command`-enveloped commands (see
    `_run_session`) until that connection closes, then blocks reading
    stdin lines until `SHUTDOWN` before returning — mirroring
    `sidecar_proof.py`'s existing lifecycle protocol with one
    additional handshake line.

    Raises:
        RuntimeError: The connecting client's first frame didn't match
            the printed secret.
    """
    secret = secrets.token_hex(16)
    loop = asyncio.get_running_loop()
    connection_future: asyncio.Future[
        tuple[asyncio.StreamReader, asyncio.StreamWriter]
    ] = loop.create_future()

    async def handle_client(
        reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        connection_future.set_result((reader, writer))

    server = await asyncio.start_server(handle_client, "127.0.0.1", 0)
    assert server.sockets is not None
    port = server.sockets[0].getsockname()[1]

    print("READY", flush=True)
    print(f"DESKTOP {port} {secret}", flush=True)

    writer: asyncio.StreamWriter | None = None
    try:
        reader, writer = await asyncio.wait_for(
            connection_future, timeout=_AUTHENTICATION_TIMEOUT_SECONDS
        )

        received_secret = await asyncio.wait_for(
            read_frame(reader), timeout=_AUTHENTICATION_TIMEOUT_SECONDS
        )
        if received_secret.decode("utf-8") != secret:
            raise RuntimeError("desktop channel client failed to authenticate")

        await _run_session(reader, writer)

        writer.close()
        await writer.wait_closed()
        writer = None
    finally:
        # `Server.wait_closed()` (Python 3.12.1+) waits for the listening
        # socket to close *and* for the one accepted connection to drop.
        # Closing our own end here first, on every exit path, is what
        # actually lets that second condition become true — without it,
        # a command-handler failure between accepting the connection and
        # the success path's own `writer.close()` leaves this writer
        # open, and `wait_closed()` blocks forever on a connection the
        # client is itself only ever waiting to read a response from.
        if writer is not None:
            writer.close()
            await writer.wait_closed()

        server.close()
        await server.wait_closed()

    for line in sys.stdin:
        if line.strip() == "SHUTDOWN":
            break
