pub mod desktop_proto {
  include!(concat!(env!("OUT_DIR"), "/corytm.schemas.desktop.rs"));
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
  tauri::Builder::default()
    .setup(|app| {
      if cfg!(debug_assertions) {
        app.handle().plugin(
          tauri_plugin_log::Builder::default()
            .level(log::LevelFilter::Info)
            .build(),
        )?;
      }
      Ok(())
    })
    .run(tauri::generate_context!())
    .expect("error while running tauri application");
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
