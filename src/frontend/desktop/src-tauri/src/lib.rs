use std::sync::Mutex;

use prost::Message;
use tauri::async_runtime::Receiver;
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

  write_frame(stream, &command.encode_to_vec())
    .await
    .map_err(|error| format!("failed to send command: {error}"))?;

  let event_bytes = read_frame(stream)
    .await
    .map_err(|error| format!("failed to read event: {error}"))?;

  project_proto::Event::decode(event_bytes.as_slice())
    .map_err(|error| format!("failed to decode event: {error}"))
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

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
  tauri::Builder::default()
    .plugin(tauri_plugin_shell::init())
    .plugin(tauri_plugin_dialog::init())
    .invoke_handler(tauri::generate_handler![
      move_clip,
      create_project,
      save_project,
      open_project
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

  use crate::{
    connect_desktop_channel, create_project, move_clip, open_project, save_project,
    spawn_desktop_sidecar, DesktopConnection,
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
}
