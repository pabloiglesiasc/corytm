use std::sync::Mutex;

use tauri::async_runtime::Receiver;
use tauri::{Manager, RunEvent};
use tauri_plugin_shell::{
  process::{CommandChild, CommandEvent},
  ShellExt,
};

pub mod desktop_proto {
  include!(concat!(env!("OUT_DIR"), "/corytm.schemas.desktop.rs"));
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
    .setup(|app| {
      if cfg!(debug_assertions) {
        app.handle().plugin(
          tauri_plugin_log::Builder::default()
            .level(log::LevelFilter::Info)
            .build(),
        )?;
      }

      app.manage(Mutex::new(None::<CommandChild>));

      let app_handle = app.handle().clone();
      tauri::async_runtime::spawn(async move {
        match spawn_desktop_sidecar(&app_handle).await {
          Ok((_receiver, child, port, _secret)) => {
            log::info!("desktop channel sidecar ready on port {port}");
            *app_handle.state::<Mutex<Option<CommandChild>>>().lock().unwrap() = Some(child);
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
  use std::time::Duration;

  use prost::Message;
  use tauri::test::{mock_builder, mock_context, noop_assets};
  use tauri_plugin_shell::process::CommandEvent;
  use tokio::io::{AsyncReadExt, AsyncWriteExt};
  use tokio::net::TcpStream;

  use crate::desktop_proto::DesktopProofMessage;
  use crate::spawn_desktop_sidecar;

  const TRANSPORT_MAGIC: u32 = 0x636F_7274;

  async fn write_frame(stream: &mut TcpStream, payload: &[u8]) {
    stream
      .write_all(&TRANSPORT_MAGIC.to_le_bytes())
      .await
      .expect("failed to write frame magic");
    stream
      .write_all(&(payload.len() as u32).to_le_bytes())
      .await
      .expect("failed to write frame length");
    stream
      .write_all(payload)
      .await
      .expect("failed to write frame payload");
  }

  async fn read_frame(stream: &mut TcpStream) -> Vec<u8> {
    let mut header = [0u8; 8];
    stream
      .read_exact(&mut header)
      .await
      .expect("failed to read frame header");

    let magic = u32::from_le_bytes(header[0..4].try_into().unwrap());
    assert_eq!(magic, TRANSPORT_MAGIC, "unexpected frame magic");
    let length = u32::from_le_bytes(header[4..8].try_into().unwrap()) as usize;

    let mut payload = vec![0u8; length];
    stream
      .read_exact(&mut payload)
      .await
      .expect("failed to read frame payload");
    payload
  }

  #[tokio::test]
  async fn desktop_channel_round_trips_over_the_second_transport() {
    let app = mock_builder()
      .plugin(tauri_plugin_shell::init())
      .build(mock_context(noop_assets()))
      .expect("failed to build mock app");

    let (mut receiver, mut child, port, secret) = tokio::time::timeout(
      Duration::from_secs(10),
      spawn_desktop_sidecar(app.handle()),
    )
    .await
    .expect("timed out waiting for the desktop channel handshake")
    .expect("failed to spawn corytm serve and complete its handshake");

    let mut stream = TcpStream::connect(("127.0.0.1", port))
      .await
      .expect("failed to connect to the desktop channel");

    write_frame(&mut stream, secret.as_bytes()).await;

    let command = DesktopProofMessage {
      schema_version: 1,
      payload: "corytm-desktop-transport-proof-command".to_string(),
    };
    write_frame(&mut stream, &command.encode_to_vec()).await;

    let event_bytes = read_frame(&mut stream).await;
    let event = DesktopProofMessage::decode(event_bytes.as_slice()).expect("failed to decode");

    assert_eq!(event.schema_version, command.schema_version);
    assert_eq!(event.payload, "corytm-desktop-transport-proof-event");

    drop(stream);

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
