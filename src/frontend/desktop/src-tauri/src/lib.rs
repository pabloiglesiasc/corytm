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

/// The Desktop channel's port and per-launch secret, captured once
/// `spawn_desktop_sidecar` completes the handshake, so any later
/// command can open its own authenticated connection to it.
#[derive(Clone)]
struct DesktopChannel {
  port: u16,
  secret: String,
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

/// Send the one hardcoded `MoveClipCommand` this Feature triggers, and
/// return the resulting `ClipMovedEvent`'s fields.
///
/// Connects to the already-spawned sidecar's Desktop channel (ADR-010)
/// using the port/secret `spawn_desktop_sidecar` captured into managed
/// state, authenticates, sends one `Command`-enveloped `MoveClipCommand`
/// matching the Python core's own hardcoded fixture project exactly,
/// and decodes the enveloped `ClipMovedEvent` it returns. The Desktop
/// channel server accepts exactly one client connection per app
/// session (unchanged by FT-023, which only made that one connection
/// itself carry a sequence of commands), so this is expected to
/// succeed at most once.
#[tauri::command]
async fn move_clip(
  state: tauri::State<'_, Mutex<Option<DesktopChannel>>>,
) -> Result<MoveClipResult, String> {
  let channel = state
    .lock()
    .unwrap()
    .clone()
    .ok_or_else(|| "desktop channel is not ready yet".to_string())?;

  let mut stream = TcpStream::connect(("127.0.0.1", channel.port))
    .await
    .map_err(|error| format!("failed to connect to the desktop channel: {error}"))?;

  write_frame(&mut stream, channel.secret.as_bytes())
    .await
    .map_err(|error| format!("failed to authenticate with the desktop channel: {error}"))?;

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
  write_frame(&mut stream, &command.encode_to_vec())
    .await
    .map_err(|error| format!("failed to send the move-clip command: {error}"))?;

  let event_bytes = read_frame(&mut stream)
    .await
    .map_err(|error| format!("failed to read the clip-moved event: {error}"))?;
  let event = project_proto::Event::decode(event_bytes.as_slice())
    .map_err(|error| format!("failed to decode the clip-moved event: {error}"))?;
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
    .invoke_handler(tauri::generate_handler![move_clip])
    .setup(|app| {
      if cfg!(debug_assertions) {
        app.handle().plugin(
          tauri_plugin_log::Builder::default()
            .level(log::LevelFilter::Info)
            .build(),
        )?;
      }

      app.manage(Mutex::new(None::<CommandChild>));
      app.manage(Mutex::new(None::<DesktopChannel>));

      let app_handle = app.handle().clone();
      tauri::async_runtime::spawn(async move {
        match spawn_desktop_sidecar(&app_handle).await {
          Ok((_receiver, child, port, secret)) => {
            log::info!("desktop channel sidecar ready on port {port}");
            *app_handle.state::<Mutex<Option<CommandChild>>>().lock().unwrap() = Some(child);
            *app_handle.state::<Mutex<Option<DesktopChannel>>>().lock().unwrap() =
              Some(DesktopChannel { port, secret });
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
  use std::sync::Mutex;
  use std::time::Duration;

  use tauri::test::{mock_builder, mock_context, noop_assets};
  use tauri::Manager;
  use tauri_plugin_shell::process::{CommandChild, CommandEvent};

  use crate::{move_clip, spawn_desktop_sidecar, DesktopChannel};

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

    app.manage(Mutex::new(None::<DesktopChannel>));

    let (mut receiver, child, port, secret) = tokio::time::timeout(
      Duration::from_secs(10),
      spawn_desktop_sidecar(app.handle()),
    )
    .await
    .expect("timed out waiting for the desktop channel handshake")
    .expect("failed to spawn corytm serve and complete its handshake");
    let mut sidecar = SidecarGuard(Some(child));

    *app.state::<Mutex<Option<DesktopChannel>>>().lock().unwrap() =
      Some(DesktopChannel { port, secret });

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
