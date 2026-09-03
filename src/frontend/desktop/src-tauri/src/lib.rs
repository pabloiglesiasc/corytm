#[cfg(not(test))]
use std::sync::Mutex;

use prost::Message;
use tauri::async_runtime::Receiver;
#[cfg(not(test))]
use tauri::{Manager, RunEvent};
use tauri_plugin_shell::{
  process::{CommandChild, CommandEvent},
  ShellExt,
};
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::net::TcpStream;
use tokio::sync::Mutex as AsyncMutex;

pub mod desktop_proto {
  include!(concat!(env!("OUT_DIR"), "/corytm.schemas.desktop.rs"));
}

pub mod project_proto {
  include!(concat!(env!("OUT_DIR"), "/corytm.schemas.project.rs"));
}

const TRANSPORT_MAGIC: u32 = 0x636F_7274;

async fn write_frame(stream: &mut TcpStream, payload: &[u8]) -> std::io::Result<()> {
  stream.write_all(&TRANSPORT_MAGIC.to_le_bytes()).await?;
  stream
    .write_all(&(payload.len() as u32).to_le_bytes())
    .await?;
  stream.write_all(payload).await
}

async fn read_frame(stream: &mut TcpStream) -> std::io::Result<Vec<u8>> {
  let mut header = [0u8; 8];
  stream.read_exact(&mut header).await?;

  let magic = u32::from_le_bytes(header[0..4].try_into().unwrap());
  assert_eq!(magic, TRANSPORT_MAGIC, "unexpected frame magic");
  let length = u32::from_le_bytes(header[4..8].try_into().unwrap()) as usize;

  let mut payload = vec![0u8; length];
  stream.read_exact(&mut payload).await?;
  Ok(payload)
}

/// The Desktop channel's single, held connection for the life of the
/// app session.
///
/// `serve_desktop_channel` (Python core) accepts exactly one client
/// TCP connection for the life of the sidecar process, then dispatches
/// a sequence of `Command`-enveloped commands over it until the client
/// disconnects (ADR-010, extended by FT-023). Every command this
/// Feature adds shares this one connection instead of each opening its
/// own — reused connect-per-call, as the original `move_clip` did,
/// only ever worked because it was the sole command ever invoked; a
/// second command reopening a new connection would find the server no
/// longer accepting one. `run()`'s setup opens and authenticates this
/// connection once, right after `spawn_desktop_sidecar`'s handshake.
type DesktopConnection = AsyncMutex<Option<TcpStream>>;

/// Connect to the Desktop channel at `port` and authenticate with
/// `secret`, per ADR-010's handshake.
async fn connect_desktop_channel(port: u16, secret: &str) -> Result<TcpStream, String> {
  let mut stream = TcpStream::connect(("127.0.0.1", port))
    .await
    .map_err(|error| format!("failed to connect to the desktop channel: {error}"))?;

  write_frame(&mut stream, secret.as_bytes())
    .await
    .map_err(|error| format!("failed to authenticate with the desktop channel: {error}"))?;

  Ok(stream)
}

/// Send one `Command` over the held Desktop channel connection and
/// return the resulting `Event`.
///
/// Shared by every command this Feature (and `move_clip`, migrated
/// onto it) sends, so the connection is genuinely reused rather than
/// reopened per call — see [`DesktopConnection`].
async fn send_command(
  state: &tauri::State<'_, DesktopConnection>,
  command: project_proto::Command,
) -> Result<project_proto::Event, String> {
  let mut guard = state.lock().await;
  let stream = guard
    .as_mut()
    .ok_or_else(|| "desktop channel is not connected yet".to_string())?;

  if let Err(error) = write_frame(stream, &command.encode_to_vec()).await {
    // The connection is dead (e.g. the peer process exited) — clear
    // it rather than leaving a stale stream in place, so
    // `desktop_channel_ready` immediately reflects reality and the
    // frontend disables every control again instead of continuing to
    // offer actions that are now guaranteed to fail. This channel is
    // genuinely persistent for the app's session (ADR-010), not
    // reconnecting — once cleared, it stays `None` until relaunch.
    *guard = None;
    return Err(format!("failed to send command: {error}"));
  }

  let event_bytes = match read_frame(stream).await {
    Ok(bytes) => bytes,
    Err(error) => {
      *guard = None;
      return Err(format!("failed to read event: {error}"));
    }
  };

  project_proto::Event::decode(event_bytes.as_slice())
    .map_err(|error| format!("failed to decode event: {error}"))
}

/// Report whether the Desktop channel's persistent connection is
/// genuinely established yet.
///
/// The frontend must call this (and disable Desktop-channel-dependent
/// controls until it reports `true`) rather than assume the channel
/// is ready as soon as the window is interactive: `run()`'s `.setup()`
/// spawns the sidecar and connects asynchronously, so a user could
/// otherwise click a control before that work completes.
#[tauri::command]
async fn desktop_channel_ready(state: tauri::State<'_, DesktopConnection>) -> Result<bool, ()> {
  Ok(state.lock().await.is_some())
}

/// A `ClipMovedEvent`'s fields, reshaped for JSON serialization back
/// to the frontend.
#[derive(serde::Serialize)]
struct MoveClipResult {
  moved: bool,
  start_seconds: f64,
  rendered_file_path: String,
  rendered_sample_count: u64,
  peak_amplitude: f64,
}

/// Send the one hardcoded `MoveClipCommand` this project's fixture
/// project supports, and return the resulting `ClipMovedEvent`'s
/// fields.
#[tauri::command]
async fn move_clip(state: tauri::State<'_, DesktopConnection>) -> Result<MoveClipResult, String> {
  let command = project_proto::Command {
    command: Some(project_proto::command::Command::MoveClip(
      project_proto::MoveClipCommand {
        schema_version: 1,
        project_id: "desktop-fixture".to_string(),
        track_id: "track-1".to_string(),
        clip_id: "clip-1".to_string(),
        new_start_seconds: 1.0,
      },
    )),
  };
  let event = send_command(&state, command).await?;
  let Some(project_proto::event::Event::ClipMoved(event)) = event.event else {
    return Err("expected a clip-moved event".to_string());
  };

  Ok(MoveClipResult {
    moved: event.moved,
    start_seconds: event.start_seconds,
    rendered_file_path: event.rendered_file_path,
    rendered_sample_count: event.rendered_sample_count,
    peak_amplitude: event.peak_amplitude,
  })
}

/// A `ProjectCreatedEvent`'s fields, reshaped for JSON serialization
/// back to the frontend.
#[derive(serde::Serialize)]
struct ProjectCreatedResult {
  project_id: String,
}

/// Create a fresh, empty project in the session's current-project slot.
#[tauri::command]
async fn create_project(
  state: tauri::State<'_, DesktopConnection>,
) -> Result<ProjectCreatedResult, String> {
  let command = project_proto::Command {
    command: Some(project_proto::command::Command::CreateProject(
      project_proto::CreateProjectCommand { schema_version: 1 },
    )),
  };
  let event = send_command(&state, command).await?;
  let Some(project_proto::event::Event::ProjectCreated(event)) = event.event else {
    return Err("expected a project-created event".to_string());
  };

  Ok(ProjectCreatedResult {
    project_id: event.project_id,
  })
}

/// A `ProjectSavedEvent`'s fields, reshaped for JSON serialization
/// back to the frontend.
#[derive(serde::Serialize)]
struct ProjectSavedResult {
  project_id: String,
  file_path: String,
}

/// Save the session's current project to `file_path` via ADR-011's
/// JSON envelope.
#[tauri::command]
async fn save_project(
  state: tauri::State<'_, DesktopConnection>,
  file_path: String,
) -> Result<ProjectSavedResult, String> {
  let command = project_proto::Command {
    command: Some(project_proto::command::Command::SaveProject(
      project_proto::SaveProjectCommand {
        schema_version: 1,
        file_path,
      },
    )),
  };
  let event = send_command(&state, command).await?;
  let Some(project_proto::event::Event::ProjectSaved(event)) = event.event else {
    return Err("expected a project-saved event".to_string());
  };

  Ok(ProjectSavedResult {
    project_id: event.project_id,
    file_path: event.file_path,
  })
}

/// A `ProjectOpenedEvent`'s fields, reshaped for JSON serialization
/// back to the frontend.
#[derive(serde::Serialize)]
struct ProjectOpenedResult {
  project_id: String,
  file_path: String,
  track_count: u32,
  rendered_sample_count: u64,
  peak_amplitude: f64,
}

/// Load `file_path` via ADR-011's JSON envelope, replace the session's
/// current project with it, and re-materialize it through the Native
/// Audio Runtime.
#[tauri::command]
async fn open_project(
  state: tauri::State<'_, DesktopConnection>,
  file_path: String,
) -> Result<ProjectOpenedResult, String> {
  let command = project_proto::Command {
    command: Some(project_proto::command::Command::OpenProject(
      project_proto::OpenProjectCommand {
        schema_version: 1,
        file_path,
      },
    )),
  };
  let event = send_command(&state, command).await?;
  let Some(project_proto::event::Event::ProjectOpened(event)) = event.event else {
    return Err("expected a project-opened event".to_string());
  };

  Ok(ProjectOpenedResult {
    project_id: event.project_id,
    file_path: event.file_path,
    track_count: event.track_count,
    rendered_sample_count: event.rendered_sample_count,
    peak_amplitude: event.peak_amplitude,
  })
}

/// An `AudioTrackAddedEvent`'s fields, reshaped for JSON serialization
/// back to the frontend.
#[derive(serde::Serialize)]
struct AudioTrackAddedResult {
  track_id: String,
  track_count: u32,
}

/// Add an empty track to the session's current project.
#[tauri::command]
async fn add_track(
  state: tauri::State<'_, DesktopConnection>,
) -> Result<AudioTrackAddedResult, String> {
  let command = project_proto::Command {
    command: Some(project_proto::command::Command::AddTrack(
      project_proto::AddAudioTrackCommand { schema_version: 1 },
    )),
  };
  let event = send_command(&state, command).await?;
  let Some(project_proto::event::Event::TrackAdded(event)) = event.event else {
    return Err("expected a track-added event".to_string());
  };

  Ok(AudioTrackAddedResult {
    track_id: event.track_id,
    track_count: event.track_count,
  })
}

/// An `AudioClipAddedEvent`'s fields, reshaped for JSON serialization
/// back to the frontend.
#[derive(serde::Serialize)]
struct AudioClipAddedResult {
  clip_id: String,
  start_seconds: f64,
  duration_seconds: f64,
  rendered_file_path: String,
  rendered_sample_count: u64,
  peak_amplitude: f64,
}

/// Append a new clip of `duration_seconds` to `track_id`, and
/// re-render the resulting project.
#[tauri::command]
async fn add_clip(
  state: tauri::State<'_, DesktopConnection>,
  track_id: String,
  duration_seconds: f64,
) -> Result<AudioClipAddedResult, String> {
  let command = project_proto::Command {
    command: Some(project_proto::command::Command::AddClip(
      project_proto::AddAudioClipCommand {
        schema_version: 1,
        track_id,
        duration_seconds,
      },
    )),
  };
  let event = send_command(&state, command).await?;
  let Some(project_proto::event::Event::ClipAdded(event)) = event.event else {
    return Err("expected a clip-added event".to_string());
  };

  Ok(AudioClipAddedResult {
    clip_id: event.clip_id,
    start_seconds: event.start_seconds,
    duration_seconds: event.duration_seconds,
    rendered_file_path: event.rendered_file_path,
    rendered_sample_count: event.rendered_sample_count,
    peak_amplitude: event.peak_amplitude,
  })
}

/// A `PlaybackStartedEvent`'s fields, reshaped for JSON serialization
/// back to the frontend.
#[derive(serde::Serialize)]
struct PlaybackStartedResult {
  device_opened: bool,
}

/// Start real-time playback of the session's current project.
#[tauri::command]
async fn play(
  state: tauri::State<'_, DesktopConnection>,
) -> Result<PlaybackStartedResult, String> {
  let command = project_proto::Command {
    command: Some(project_proto::command::Command::Play(
      project_proto::PlayCommand {
        schema_version: 1,
        project: None,
      },
    )),
  };
  let event = send_command(&state, command).await?;
  let Some(project_proto::event::Event::PlaybackStarted(event)) = event.event else {
    return Err("expected a playback-started event".to_string());
  };

  Ok(PlaybackStartedResult {
    device_opened: event.device_opened,
  })
}

/// A `PlaybackPositionEvent`'s fields, reshaped for JSON serialization
/// back to the frontend.
#[derive(serde::Serialize)]
struct PlaybackPositionResult {
  is_playing: bool,
  position_seconds: f64,
}

/// Query the current live playback position.
#[tauri::command]
async fn get_playback_position(
  state: tauri::State<'_, DesktopConnection>,
) -> Result<PlaybackPositionResult, String> {
  let command = project_proto::Command {
    command: Some(project_proto::command::Command::GetPlaybackPosition(
      project_proto::GetPlaybackPositionCommand { schema_version: 1 },
    )),
  };
  let event = send_command(&state, command).await?;
  let Some(project_proto::event::Event::PlaybackPosition(event)) = event.event else {
    return Err("expected a playback-position event".to_string());
  };

  Ok(PlaybackPositionResult {
    is_playing: event.is_playing,
    position_seconds: event.position_seconds,
  })
}

/// A `PlaybackStoppedEvent`'s fields, reshaped for JSON serialization
/// back to the frontend.
#[derive(serde::Serialize)]
struct PlaybackStoppedResult {
  final_position_seconds: f64,
}

/// Stop real-time playback of the session's current project.
#[tauri::command]
async fn stop(
  state: tauri::State<'_, DesktopConnection>,
) -> Result<PlaybackStoppedResult, String> {
  let command = project_proto::Command {
    command: Some(project_proto::command::Command::Stop(
      project_proto::StopCommand { schema_version: 1 },
    )),
  };
  let event = send_command(&state, command).await?;
  let Some(project_proto::event::Event::PlaybackStopped(event)) = event.event else {
    return Err("expected a playback-stopped event".to_string());
  };

  Ok(PlaybackStoppedResult {
    final_position_seconds: event.final_position_seconds,
  })
}

async fn spawn_desktop_sidecar<R: tauri::Runtime>(
  app: &tauri::AppHandle<R>,
) -> Result<(Receiver<CommandEvent>, CommandChild, u16, String), String> {
  let (mut receiver, child) = app
    .shell()
    .command("uv")
    .args([
      "run",
      "--project",
      "../../../backend/core",
      "corytm",
      "serve",
    ])
    .spawn()
    .map_err(|error| format!("failed to spawn corytm serve: {error}"))?;

  let mut port: Option<u16> = None;
  let mut secret: Option<String> = None;

  while port.is_none() || secret.is_none() {
    let event = receiver
      .recv()
      .await
      .ok_or_else(|| "corytm serve exited before completing the handshake".to_string())?;

    match event {
      CommandEvent::Stdout(line) => {
        let line = String::from_utf8_lossy(&line);
        if let Some(rest) = line.trim().strip_prefix("DESKTOP ") {
          let mut parts = rest.split(' ');
          port = parts.next().and_then(|p| p.parse().ok());
          secret = parts.next().map(str::to_string);
        }
      }
      CommandEvent::Terminated(payload) => {
        return Err(format!(
          "corytm serve exited before completing the handshake: {payload:?}"
        ));
      }
      _ => continue,
    }
  }

  Ok((
    receiver,
    child,
    port.expect("loop only exits once port is set"),
    secret.expect("loop only exits once secret is set"),
  ))
}

// `tauri::generate_context!()` embeds a process-wide `_EMBED_INFO_PLIST`
// symbol that can only be defined once per compiled binary — this
// crate's own tests need a second, independent expansion (against the
// same real `tauri.conf.json`/`capabilities/`) to exercise the real
// ACL/capability pipeline, which `mock_context`'s empty ACL cannot.
// `run()` itself is never called from a test (only `main.rs` calls
// it), so its real body is compiled out under `cfg(test)` instead of
// colliding with that second expansion.
#[cfg(test)]
pub fn run() {
  unreachable!("run() must not be called from unit tests — see the cfg(not(test)) copy below")
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
#[cfg(not(test))]
pub fn run() {
  tauri::Builder::default()
    .plugin(tauri_plugin_shell::init())
    .plugin(tauri_plugin_dialog::init())
    .invoke_handler(tauri::generate_handler![
      move_clip,
      create_project,
      save_project,
      open_project,
      add_track,
      add_clip,
      play,
      stop,
      get_playback_position,
      desktop_channel_ready
    ])
    .setup(|app| {
      if cfg!(debug_assertions) {
        app.handle().plugin(
          tauri_plugin_log::Builder::default()
            .level(log::LevelFilter::Info)
            .build(),
        )?;
      }

      app.manage(Mutex::new(None::<CommandChild>));
      app.manage(DesktopConnection::new(None));

      let app_handle = app.handle().clone();
      tauri::async_runtime::spawn(async move {
        match spawn_desktop_sidecar(&app_handle).await {
          Ok((_receiver, child, port, secret)) => {
            log::info!("desktop channel sidecar ready on port {port}");
            *app_handle.state::<Mutex<Option<CommandChild>>>().lock().unwrap() = Some(child);

            match connect_desktop_channel(port, &secret).await {
              Ok(stream) => {
                *app_handle.state::<DesktopConnection>().lock().await = Some(stream);
              }
              Err(error) => {
                log::error!("failed to connect to desktop channel: {error}");
              }
            }
          }
          Err(error) => {
            log::error!("failed to start desktop channel sidecar: {error}");
          }
        }
      });

      Ok(())
    })
    .build(tauri::generate_context!())
    .expect("error while building tauri application")
    .run(|app_handle, event| {
      if matches!(event, RunEvent::ExitRequested { .. } | RunEvent::Exit) {
        // The Python session loop only starts reading stdin for
        // `SHUTDOWN` once its Desktop channel connection closes (it
        // stays blocked reading the next command otherwise) — drop
        // our held connection first so it can reach that point.
        app_handle.state::<DesktopConnection>().blocking_lock().take();

        if let Some(mut child) = app_handle
          .state::<Mutex<Option<CommandChild>>>()
          .lock()
          .unwrap()
          .take()
        {
          if let Err(error) = child.write(b"SHUTDOWN\n") {
            log::error!("failed to shut down desktop channel sidecar: {error}");
          }
        }
      }
    });
}

#[cfg(test)]
mod tests {
  use std::time::Duration;

  use tauri::test::{mock_builder, mock_context, noop_assets};
  use tauri_plugin_shell::{process::CommandEvent, ShellExt};

  #[tokio::test]
  async fn sidecar_shuts_down_via_explicit_protocol() {
    let app = mock_builder()
      .plugin(tauri_plugin_shell::init())
      .build(mock_context(noop_assets()))
      .expect("failed to build mock app");

    let (mut receiver, mut child) = app
      .shell()
      .command("uv")
      .args([
        "run",
        "--directory",
        "../../../backend/core",
        "python",
        "sidecar_proof.py",
      ])
      .spawn()
      .expect("failed to spawn sidecar_proof.py");

    loop {
      let event = tokio::time::timeout(Duration::from_secs(10), receiver.recv())
        .await
        .expect("timed out waiting for READY")
        .expect("sidecar process ended before signalling READY");

      match event {
        CommandEvent::Stdout(line) if String::from_utf8_lossy(&line).trim() == "READY" => break,
        CommandEvent::Terminated(payload) => {
          panic!("sidecar exited before signalling READY: {payload:?}")
        }
        _ => continue,
      }
    }

    child.write(b"SHUTDOWN\n").expect("failed to write SHUTDOWN");

    loop {
      let event = tokio::time::timeout(Duration::from_secs(10), receiver.recv())
        .await
        .expect("timed out waiting for the sidecar to terminate")
        .expect("sidecar event channel closed before terminating");

      if let CommandEvent::Terminated(payload) = event {
        assert_eq!(payload.code, Some(0));
        break;
      }
    }
  }
}

#[cfg(test)]
mod desktop_proto_tests {
  use prost::Message;

  use crate::desktop_proto::DesktopProofMessage;

  #[test]
  fn desktop_proof_message_round_trips() {
    let original = DesktopProofMessage {
      schema_version: 1,
      payload: "corytm-desktop-protobuf-toolchain-proof".to_string(),
    };

    let encoded = original.encode_to_vec();
    let decoded = DesktopProofMessage::decode(encoded.as_slice()).expect("failed to decode");

    assert_eq!(decoded, original);
  }
}

#[cfg(test)]
mod desktop_channel_tests {
  use std::time::Duration;

  use tauri::test::{mock_builder, mock_context, noop_assets};
  use tauri::Manager;
  use tauri_plugin_shell::process::{CommandChild, CommandEvent};

  use serde_json::json;
  use tauri::ipc::CallbackFn;
  use tauri::test::get_ipc_response;
  use tauri::webview::InvokeRequest;
  use tauri::WebviewWindowBuilder;

  use crate::{
    add_clip, add_track, connect_desktop_channel, create_project, desktop_channel_ready,
    get_playback_position, move_clip, open_project, play, save_project, spawn_desktop_sidecar,
    stop, DesktopConnection,
  };

  /// Kills the wrapped sidecar on drop unless [`Self::disarm`] already
  /// took it.
  ///
  /// `CommandChild` has no `Drop`-based cleanup of its own (confirmed
  /// against `tauri_plugin_shell`'s source), so a bare local variable
  /// leaks the real `uv`/`corytm serve`/`native_runtime` process tree
  /// on any early return — a panicking assertion, a timed-out await —
  /// between spawn and the test's own explicit `SHUTDOWN` handshake.
  /// A leaked `corytm serve` blocks forever reading stdin for a
  /// `SHUTDOWN` line that will now never arrive, which can in turn
  /// keep the whole CI job from ever observing EOF on that process
  /// tree's inherited output pipe.
  struct SidecarGuard(Option<CommandChild>);

  impl SidecarGuard {
    fn write(&mut self, data: &[u8]) -> Result<(), tauri_plugin_shell::Error> {
      self
        .0
        .as_mut()
        .expect("sidecar already disarmed")
        .write(data)
    }

    /// Give up kill-on-drop once the sidecar's own clean exit is confirmed.
    fn disarm(&mut self) {
      self.0.take();
    }
  }

  impl Drop for SidecarGuard {
    fn drop(&mut self) {
      if let Some(child) = self.0.take() {
        let _ = child.kill();
      }
    }
  }

  #[tokio::test]
  async fn move_clip_command_moves_the_fixture_clip_and_renders_the_effect() {
    let app = mock_builder()
      .plugin(tauri_plugin_shell::init())
      .build(mock_context(noop_assets()))
      .expect("failed to build mock app");

    app.manage(DesktopConnection::new(None));

    let (mut receiver, child, port, secret) = tokio::time::timeout(
      Duration::from_secs(10),
      spawn_desktop_sidecar(app.handle()),
    )
    .await
    .expect("timed out waiting for the desktop channel handshake")
    .expect("failed to spawn corytm serve and complete its handshake");
    let mut sidecar = SidecarGuard(Some(child));

    let stream = connect_desktop_channel(port, &secret)
      .await
      .expect("failed to connect to the desktop channel");
    *app.state::<DesktopConnection>().lock().await = Some(stream);

    let result = tokio::time::timeout(Duration::from_secs(60), move_clip(app.state()))
      .await
      .expect("timed out waiting for the move_clip command to complete")
      .expect("move_clip command failed");

    assert!(result.moved, "expected the fixture clip to genuinely move");
    assert_eq!(result.start_seconds, 1.0);
    assert!(
      result.rendered_sample_count > 0,
      "expected a real render sample count"
    );
    assert!(
      result.peak_amplitude > 0.0,
      "expected a real non-silent render"
    );

    app.state::<DesktopConnection>().lock().await.take();
    sidecar
      .write(b"SHUTDOWN\n")
      .expect("failed to write SHUTDOWN");

    loop {
      let event = tokio::time::timeout(Duration::from_secs(10), receiver.recv())
        .await
        .expect("timed out waiting for the sidecar to terminate")
        .expect("sidecar event channel closed before terminating");

      if let CommandEvent::Terminated(payload) = event {
        assert_eq!(payload.code, Some(0));
        break;
      }
    }

    sidecar.disarm();
  }

  /// Confirms `path` genuinely round-trips through the real,
  /// authoritative `corytm.engine.persistence.load_project` — an
  /// independent check of the ADR-011 envelope this Rust test's own
  /// `save_project` call wrote, not merely that some JSON was written.
  fn assert_round_trips_via_persistence(path: &std::path::Path) {
    let script_path = std::env::temp_dir().join(format!(
      "corytm-desktop-test-roundtrip-{}.py",
      std::process::id()
    ));
    std::fs::write(
      &script_path,
      "import sys\nfrom pathlib import Path\nfrom corytm.engine.persistence import load_project\nload_project(Path(sys.argv[1]))\n",
    )
    .expect("failed to write the round-trip check script");

    let output = std::process::Command::new("uv")
      .args(["run", "--project", "../../../backend/core", "python"])
      .arg(&script_path)
      .arg(path)
      .output()
      .expect("failed to run the persistence round-trip check");

    let _ = std::fs::remove_file(&script_path);

    assert!(
      output.status.success(),
      "saved file failed to round-trip via persistence.load_project: {}",
      String::from_utf8_lossy(&output.stderr)
    );
  }

  fn temp_json_path(label: &str) -> std::path::PathBuf {
    let unique = std::time::SystemTime::now()
      .duration_since(std::time::UNIX_EPOCH)
      .expect("system clock before UNIX_EPOCH")
      .as_nanos();
    std::env::temp_dir().join(format!("corytm-desktop-test-{label}-{unique}.json"))
  }

  #[tokio::test]
  async fn create_save_open_move_all_succeed_over_one_held_connection() {
    let app = mock_builder()
      .plugin(tauri_plugin_shell::init())
      .build(mock_context(noop_assets()))
      .expect("failed to build mock app");

    app.manage(DesktopConnection::new(None));

    let (mut receiver, child, port, secret) = tokio::time::timeout(
      Duration::from_secs(10),
      spawn_desktop_sidecar(app.handle()),
    )
    .await
    .expect("timed out waiting for the desktop channel handshake")
    .expect("failed to spawn corytm serve and complete its handshake");
    let mut sidecar = SidecarGuard(Some(child));

    let stream = connect_desktop_channel(port, &secret)
      .await
      .expect("failed to connect to the desktop channel");
    *app.state::<DesktopConnection>().lock().await = Some(stream);

    let created = tokio::time::timeout(Duration::from_secs(30), create_project(app.state()))
      .await
      .expect("timed out waiting for create_project")
      .expect("create_project failed");
    assert!(!created.project_id.is_empty(), "expected a real project id");

    let save_path = temp_json_path("save");
    let saved = tokio::time::timeout(
      Duration::from_secs(30),
      save_project(app.state(), save_path.to_string_lossy().into_owned()),
    )
    .await
    .expect("timed out waiting for save_project")
    .expect("save_project failed");
    assert_eq!(saved.project_id, created.project_id);
    assert_eq!(saved.file_path, save_path.to_string_lossy());

    assert_round_trips_via_persistence(&save_path);
    let _ = std::fs::remove_file(&save_path);

    let fixture_path = temp_json_path("fixture");
    std::fs::write(
      &fixture_path,
      r#"{"schema_version":1,"project":{"schema_version":1,"id":"fixture-project","tracks":[{"schema_version":1,"id":"track-1","clips":[{"schema_version":1,"id":"clip-1","start_seconds":0.0,"duration_seconds":2.0}]}]}}"#,
    )
    .expect("failed to write the fixture project file");

    let opened = tokio::time::timeout(
      Duration::from_secs(60),
      open_project(app.state(), fixture_path.to_string_lossy().into_owned()),
    )
    .await
    .expect("timed out waiting for open_project")
    .expect("open_project failed");
    assert_eq!(opened.track_count, 1);
    assert!(
      opened.rendered_sample_count > 0,
      "expected a real render sample count from the opened project"
    );
    assert!(
      opened.peak_amplitude > 0.0,
      "expected a real non-silent render from the opened project"
    );
    let _ = std::fs::remove_file(&fixture_path);

    let moved = tokio::time::timeout(Duration::from_secs(60), move_clip(app.state()))
      .await
      .expect("timed out waiting for move_clip")
      .expect("move_clip failed");
    assert!(
      moved.moved,
      "expected the opened fixture's clip to genuinely move over the same held connection"
    );
    assert_eq!(moved.start_seconds, 1.0);

    app.state::<DesktopConnection>().lock().await.take();

    sidecar
      .write(b"SHUTDOWN\n")
      .expect("failed to write SHUTDOWN");

    loop {
      let event = tokio::time::timeout(Duration::from_secs(10), receiver.recv())
        .await
        .expect("timed out waiting for the sidecar to terminate")
        .expect("sidecar event channel closed before terminating");

      if let CommandEvent::Terminated(payload) = event {
        assert_eq!(payload.code, Some(0));
        break;
      }
    }

    sidecar.disarm();
  }

  #[tokio::test]
  async fn create_add_track_add_clip_all_succeed_over_one_held_connection() {
    let app = mock_builder()
      .plugin(tauri_plugin_shell::init())
      .build(mock_context(noop_assets()))
      .expect("failed to build mock app");

    app.manage(DesktopConnection::new(None));

    let (mut receiver, child, port, secret) = tokio::time::timeout(
      Duration::from_secs(10),
      spawn_desktop_sidecar(app.handle()),
    )
    .await
    .expect("timed out waiting for the desktop channel handshake")
    .expect("failed to spawn corytm serve and complete its handshake");
    let mut sidecar = SidecarGuard(Some(child));

    let stream = connect_desktop_channel(port, &secret)
      .await
      .expect("failed to connect to the desktop channel");
    *app.state::<DesktopConnection>().lock().await = Some(stream);

    let created = tokio::time::timeout(Duration::from_secs(30), create_project(app.state()))
      .await
      .expect("timed out waiting for create_project")
      .expect("create_project failed");
    assert!(!created.project_id.is_empty(), "expected a real project id");

    let track_added = tokio::time::timeout(Duration::from_secs(30), add_track(app.state()))
      .await
      .expect("timed out waiting for add_track")
      .expect("add_track failed");
    assert_eq!(track_added.track_count, 1);
    assert!(!track_added.track_id.is_empty(), "expected a real track id");

    let first_clip = tokio::time::timeout(
      Duration::from_secs(60),
      add_clip(app.state(), track_added.track_id.clone(), 2.0),
    )
    .await
    .expect("timed out waiting for add_clip")
    .expect("add_clip failed");
    assert_eq!(first_clip.start_seconds, 0.0);
    assert!(
      first_clip.rendered_sample_count > 0,
      "expected a real render sample count"
    );
    assert!(
      first_clip.peak_amplitude > 0.0,
      "expected a real non-silent render"
    );

    let second_clip = tokio::time::timeout(
      Duration::from_secs(60),
      add_clip(app.state(), track_added.track_id, 1.0),
    )
    .await
    .expect("timed out waiting for the second add_clip")
    .expect("second add_clip failed");
    assert_eq!(
      second_clip.start_seconds,
      first_clip.start_seconds + first_clip.duration_seconds,
      "expected the second clip appended right after the first"
    );

    app.state::<DesktopConnection>().lock().await.take();

    sidecar
      .write(b"SHUTDOWN\n")
      .expect("failed to write SHUTDOWN");

    loop {
      let event = tokio::time::timeout(Duration::from_secs(10), receiver.recv())
        .await
        .expect("timed out waiting for the sidecar to terminate")
        .expect("sidecar event channel closed before terminating");

      if let CommandEvent::Terminated(payload) = event {
        assert_eq!(payload.code, Some(0));
        break;
      }
    }

    sidecar.disarm();
  }

  /// Drives Play -> GetPlaybackPosition -> Stop over one held
  /// connection. Tolerates a test environment with no real audio
  /// output device (`device_opened == false`) rather than failing on
  /// it — mirroring the Python integration test's own precedent
  /// (`test_play_reports_advancing_position_and_stop_halts_it`) and
  /// `playback_proof`'s original soft-skip design.
  #[tokio::test]
  async fn play_reports_advancing_position_and_stop_halts_it() {
    let app = mock_builder()
      .plugin(tauri_plugin_shell::init())
      .build(mock_context(noop_assets()))
      .expect("failed to build mock app");

    app.manage(DesktopConnection::new(None));

    let (mut receiver, child, port, secret) = tokio::time::timeout(
      Duration::from_secs(10),
      spawn_desktop_sidecar(app.handle()),
    )
    .await
    .expect("timed out waiting for the desktop channel handshake")
    .expect("failed to spawn corytm serve and complete its handshake");
    let mut sidecar = SidecarGuard(Some(child));

    let stream = connect_desktop_channel(port, &secret)
      .await
      .expect("failed to connect to the desktop channel");
    *app.state::<DesktopConnection>().lock().await = Some(stream);

    tokio::time::timeout(Duration::from_secs(30), create_project(app.state()))
      .await
      .expect("timed out waiting for create_project")
      .expect("create_project failed");

    let track_added = tokio::time::timeout(Duration::from_secs(30), add_track(app.state()))
      .await
      .expect("timed out waiting for add_track")
      .expect("add_track failed");

    tokio::time::timeout(
      Duration::from_secs(60),
      add_clip(app.state(), track_added.track_id, 3.0),
    )
    .await
    .expect("timed out waiting for add_clip")
    .expect("add_clip failed");

    let started = tokio::time::timeout(Duration::from_secs(30), play(app.state()))
      .await
      .expect("timed out waiting for play")
      .expect("play failed");

    if started.device_opened {
      let first_position = tokio::time::timeout(
        Duration::from_secs(30),
        get_playback_position(app.state()),
      )
      .await
      .expect("timed out waiting for get_playback_position")
      .expect("get_playback_position failed");
      assert!(first_position.is_playing);

      tokio::time::sleep(Duration::from_millis(300)).await;

      let second_position = tokio::time::timeout(
        Duration::from_secs(30),
        get_playback_position(app.state()),
      )
      .await
      .expect("timed out waiting for the second get_playback_position")
      .expect("second get_playback_position failed");
      assert!(second_position.is_playing);
      assert!(
        second_position.position_seconds > first_position.position_seconds,
        "expected playback position to genuinely advance"
      );
    }

    tokio::time::timeout(Duration::from_secs(30), stop(app.state()))
      .await
      .expect("timed out waiting for stop")
      .expect("stop failed");

    app.state::<DesktopConnection>().lock().await.take();

    sidecar
      .write(b"SHUTDOWN\n")
      .expect("failed to write SHUTDOWN");

    loop {
      let event = tokio::time::timeout(Duration::from_secs(10), receiver.recv())
        .await
        .expect("timed out waiting for the sidecar to terminate")
        .expect("sidecar event channel closed before terminating");

      if let CommandEvent::Terminated(payload) = event {
        assert_eq!(payload.code, Some(0));
        break;
      }
    }

    sidecar.disarm();
  }

  /// Drives the real `play` command over the real Desktop channel after
  /// a real idle gap past the persistent playback process's own command
  /// timeout, through the same vertical path (Desktop -> Rust ->
  /// Desktop channel -> `corytm serve` sidecar) FT-030's own human
  /// validation exercised. Mirrors the Python-level regression test of
  /// the same name.
  #[tokio::test]
  async fn play_survives_a_real_human_idle_gap_before_it() {
    let app = mock_builder()
      .plugin(tauri_plugin_shell::init())
      .build(mock_context(noop_assets()))
      .expect("failed to build mock app");

    app.manage(DesktopConnection::new(None));

    let (mut receiver, child, port, secret) = tokio::time::timeout(
      Duration::from_secs(10),
      spawn_desktop_sidecar(app.handle()),
    )
    .await
    .expect("timed out waiting for the desktop channel handshake")
    .expect("failed to spawn corytm serve and complete its handshake");
    let mut sidecar = SidecarGuard(Some(child));

    let stream = connect_desktop_channel(port, &secret)
      .await
      .expect("failed to connect to the desktop channel");
    *app.state::<DesktopConnection>().lock().await = Some(stream);

    tokio::time::timeout(Duration::from_secs(30), create_project(app.state()))
      .await
      .expect("timed out waiting for create_project")
      .expect("create_project failed");

    let track_added = tokio::time::timeout(Duration::from_secs(30), add_track(app.state()))
      .await
      .expect("timed out waiting for add_track")
      .expect("add_track failed");

    tokio::time::timeout(
      Duration::from_secs(60),
      add_clip(app.state(), track_added.track_id, 2.0),
    )
    .await
    .expect("timed out waiting for add_clip")
    .expect("add_clip failed");

    tokio::time::sleep(Duration::from_secs(13)).await;

    tokio::time::timeout(Duration::from_secs(30), play(app.state()))
      .await
      .expect("timed out waiting for play")
      .expect(
        "play failed after a real idle gap -- the persistent playback \
         process likely gave up and exited on its own, crashing the \
         whole corytm serve process",
      );

    tokio::time::timeout(Duration::from_secs(30), stop(app.state()))
      .await
      .expect("timed out waiting for stop")
      .expect("stop failed");

    app.state::<DesktopConnection>().lock().await.take();

    sidecar
      .write(b"SHUTDOWN\n")
      .expect("failed to write SHUTDOWN");

    loop {
      let event = tokio::time::timeout(Duration::from_secs(10), receiver.recv())
        .await
        .expect("timed out waiting for the sidecar to terminate")
        .expect("sidecar event channel closed before terminating");

      if let CommandEvent::Terminated(payload) = event {
        assert_eq!(payload.code, Some(0));
        break;
      }
    }

    sidecar.disarm();
  }

  /// A minimal, real IPC invoke request for `cmd`, matching the shape
  /// the frontend's own `invoke()` sends over the actual `postMessage`
  /// pipeline this test drives through — not a direct Rust function
  /// call, which bypasses ACL/capability resolution entirely (the
  /// gap that let `add_track`/`add_clip` ship without one).
  ///
  /// The request's `url` must match whatever Tauri's own ACL
  /// evaluation (`Webview::is_local_url`) considers this platform's
  /// local origin, confirmed against `tauri`'s own source
  /// (`manager::tauri_protocol_url`): `tauri://localhost` on
  /// macOS/Linux, but `https://tauri.localhost` on Windows, since
  /// WebView2 cannot serve a bare custom URI scheme as an origin. A
  /// hardcoded `tauri://localhost` here previously passed locally on
  /// macOS by coincidence while failing every real IPC command as
  /// "not allowed" under this app's own compiled-in capability on
  /// Windows.
  fn invoke_request(cmd: &str, args: serde_json::Value) -> InvokeRequest {
    let local_origin = if cfg!(windows) {
      "https://tauri.localhost"
    } else {
      "tauri://localhost"
    };

    InvokeRequest {
      cmd: cmd.into(),
      callback: CallbackFn(0),
      error: CallbackFn(1),
      url: local_origin.parse().unwrap(),
      body: tauri::ipc::InvokeBody::Json(args),
      headers: Default::default(),
      invoke_key: tauri::test::INVOKE_KEY.to_string(),
    }
  }

  /// Every real app command must be reachable through the actual IPC
  /// invoke pipeline this app ships — not merely callable as a plain
  /// Rust function (every other test in this module does that, which
  /// never exercises ACL/capability resolution at all), and the
  /// `desktop_channel_ready` readiness query must genuinely reflect
  /// connection state before and after the real handshake. Both are
  /// proven in one test: `tauri::generate_context!()` (needed for the
  /// app's own real, compiled-in `tauri.conf.json`/`capabilities/`,
  /// not `mock_context`'s empty, unresolved ACL) can only expand once
  /// per compiled test binary — a second expansion anywhere else in
  /// this module fails to link (`_EMBED_INFO_PLIST` already defined).
  // `get_ipc_response` blocks its calling thread on a synchronous
  // channel receive while the invoked async command runs — on a
  // single-threaded runtime that would starve the very task it's
  // waiting on, deadlocking. `flavor = "multi_thread"` gives the
  // command a separate worker thread to actually run on.
  #[tokio::test(flavor = "multi_thread", worker_threads = 2)]
  async fn real_app_commands_are_permitted_and_readiness_is_observable() {
    let app = mock_builder()
      .plugin(tauri_plugin_shell::init())
      .plugin(tauri_plugin_dialog::init())
      .invoke_handler(tauri::generate_handler![
        move_clip,
        create_project,
        save_project,
        open_project,
        add_track,
        add_clip,
        play,
        stop,
        get_playback_position,
        desktop_channel_ready
      ])
      .build(tauri::generate_context!())
      .expect("failed to build the app with its real generated context");

    app.manage(DesktopConnection::new(None));

    let webview = WebviewWindowBuilder::new(&app, "main", Default::default())
      .build()
      .expect("failed to build a mock webview window");

    // Before any spawn/connect happens at all — exactly a user
    // clicking the instant the window appears. The readiness query
    // must report `false`, and a Desktop-channel command must fail
    // cleanly (a clear, specific error) rather than hang or produce a
    // confusing low-level failure.
    let ready_before = get_ipc_response(&webview, invoke_request("desktop_channel_ready", json!({})))
      .expect("desktop_channel_ready should always be permitted")
      .deserialize::<bool>()
      .expect("failed to decode desktop_channel_ready's response");
    assert!(!ready_before, "expected not ready before the channel connects");

    let premature_response =
      get_ipc_response(&webview, invoke_request("create_project", json!({})));
    let Err(premature_error) = premature_response else {
      panic!("expected create_project to fail before the channel is connected");
    };
    let premature_message = premature_error.as_str().unwrap_or_default();
    assert!(
      premature_message.contains("not connected yet"),
      "expected a clear not-connected error, got {premature_message:?}"
    );

    let (mut receiver, child, port, secret) = tokio::time::timeout(
      Duration::from_secs(10),
      spawn_desktop_sidecar(app.handle()),
    )
    .await
    .expect("timed out waiting for the desktop channel handshake")
    .expect("failed to spawn corytm serve and complete its handshake");
    let mut sidecar = SidecarGuard(Some(child));

    let stream = connect_desktop_channel(port, &secret)
      .await
      .expect("failed to connect to the desktop channel");
    *app.state::<DesktopConnection>().lock().await = Some(stream);

    let ready_after = get_ipc_response(&webview, invoke_request("desktop_channel_ready", json!({})))
      .expect("desktop_channel_ready should always be permitted")
      .deserialize::<bool>()
      .expect("failed to decode desktop_channel_ready's response");
    assert!(ready_after, "expected ready once the channel is connected");

    // `move_clip` first, against the still-intact fixture project — a
    // known-already-working control proving this test's own method
    // (a real IPC invoke, not a direct Rust call) correctly reports
    // "permitted" and isn't itself silently vacuous.
    let move_response = get_ipc_response(&webview, invoke_request("move_clip", json!({})));
    assert!(
      move_response.is_ok(),
      "expected move_clip to be permitted by capabilities/default.json, got {move_response:?}"
    );

    // `create_project` resets the session before `add_track`/`add_clip`
    // — the two commands this test exists to catch a regression on.
    let create_response =
      get_ipc_response(&webview, invoke_request("create_project", json!({})));
    assert!(
      create_response.is_ok(),
      "expected create_project to be permitted, got {create_response:?}"
    );

    let track_response = get_ipc_response(&webview, invoke_request("add_track", json!({})));
    assert!(
      track_response.is_ok(),
      "expected add_track to be permitted by capabilities/default.json, got {track_response:?}"
    );
    let track_id = track_response
      .expect("checked above")
      .deserialize::<serde_json::Value>()
      .expect("failed to decode add_track's response")["track_id"]
      .as_str()
      .expect("expected a string track_id")
      .to_string();

    let clip_response = get_ipc_response(
      &webview,
      invoke_request(
        "add_clip",
        json!({ "trackId": track_id, "durationSeconds": 1.0 }),
      ),
    );
    assert!(
      clip_response.is_ok(),
      "expected add_clip to be permitted by capabilities/default.json, got {clip_response:?}"
    );

    let play_response = get_ipc_response(&webview, invoke_request("play", json!({})));
    assert!(
      play_response.is_ok(),
      "expected play to be permitted by capabilities/default.json, got {play_response:?}"
    );

    let stop_response = get_ipc_response(&webview, invoke_request("stop", json!({})));
    assert!(
      stop_response.is_ok(),
      "expected stop to be permitted by capabilities/default.json, got {stop_response:?}"
    );

    app.state::<DesktopConnection>().lock().await.take();

    sidecar
      .write(b"SHUTDOWN\n")
      .expect("failed to write SHUTDOWN");

    loop {
      let event = tokio::time::timeout(Duration::from_secs(10), receiver.recv())
        .await
        .expect("timed out waiting for the sidecar to terminate")
        .expect("sidecar event channel closed before terminating");

      if let CommandEvent::Terminated(payload) = event {
        assert_eq!(payload.code, Some(0));
        break;
      }
    }

    sidecar.disarm();
  }

  /// Reproduces the "leave the app open, then Broken pipe" bug's
  /// Rust-side half: once the peer is gone, `send_command` must not
  /// leave a stale stream behind for `desktop_channel_ready` to keep
  /// reporting `true` against — a user must never see live-looking
  /// controls that are now guaranteed to fail. This channel is
  /// genuinely persistent (ADR-010), so the fix is not to reconnect —
  /// only to make the app's own readiness state honest once dead.
  ///
  /// A throwaway TCP listener stands in for the real sidecar: this is
  /// purely about `send_command`'s own error handling, not about
  /// `corytm serve`'s process lifecycle, and a real peer process is
  /// both slower and, on this platform, not reliably killable by PID
  /// at all — `CommandChild::kill()` only terminates the `uv` process
  /// it directly spawned, not `corytm serve` running as *its* child
  /// (confirmed directly: both remained alive, independently, after
  /// `kill()` during this test's own development).
  #[tokio::test]
  async fn a_dead_connection_is_cleared_so_readiness_reflects_it() {
    let app = mock_builder()
      .plugin(tauri_plugin_shell::init())
      .build(mock_context(noop_assets()))
      .expect("failed to build mock app");

    app.manage(DesktopConnection::new(None));

    let listener = tokio::net::TcpListener::bind("127.0.0.1:0")
      .await
      .expect("failed to bind a throwaway listener");
    let addr = listener.local_addr().expect("failed to read listener addr");

    let client = tokio::net::TcpStream::connect(addr)
      .await
      .expect("failed to connect to the throwaway listener");
    let (peer, _) = listener
      .accept()
      .await
      .expect("failed to accept the throwaway connection");

    *app.state::<DesktopConnection>().lock().await = Some(client);

    assert!(
      desktop_channel_ready(app.state()).await.expect("checked"),
      "expected the channel to report ready once connected"
    );

    // Simulate the peer disappearing mid-session: close its end.
    drop(peer);
    drop(listener);

    let result = create_project(app.state()).await;
    assert!(
      result.is_err(),
      "expected create_project to fail against a dead connection"
    );

    assert!(
      !desktop_channel_ready(app.state()).await.expect("checked"),
      "expected the connection to be cleared after the failed command"
    );
  }
}
