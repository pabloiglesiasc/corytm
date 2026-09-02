use std::io::Read;
use std::path::PathBuf;

use sha2::{Digest, Sha256};

fn main() {
  tauri_build::try_build(
    tauri_build::Attributes::new()
      .windows_attributes(tauri_build::WindowsAttributes::new_without_app_manifest())
      .app_manifest(tauri_build::AppManifest::new().commands(&[
        "move_clip",
        "create_project",
        "save_project",
        "open_project",
        "add_track",
        "add_clip",
        "desktop_channel_ready",
      ])),
  )
  .expect("failed to run tauri-build");

  #[cfg(windows)]
  embed_manifest_if_msvc();

  compile_protos();
}

struct ProtocRelease {
  url: &'static str,
  sha256: &'static str,
}

fn protoc_release() -> ProtocRelease {
  if cfg!(target_os = "macos") {
    ProtocRelease {
      url: "https://github.com/protocolbuffers/protobuf/releases/download/v36.1/protoc-36.1-osx-aarch_64.zip",
      sha256: "de56d57afe30c5d191b11d24ff93dd4025728d7fb43b773886b2d3613e0bdbb2",
    }
  } else if cfg!(target_os = "windows") {
    ProtocRelease {
      url: "https://github.com/protocolbuffers/protobuf/releases/download/v36.1/protoc-36.1-win64.zip",
      sha256: "390e515cb456e6a978553bdb57baf087b054885077fd6da7f7ff0160279c07d6",
    }
  } else {
    panic!("no prebuilt protoc binary pinned for this platform in build.rs")
  }
}

fn fetch_protoc() -> PathBuf {
  let out_dir = PathBuf::from(std::env::var("OUT_DIR").expect("OUT_DIR not set"));
  let exe_name = if cfg!(target_os = "windows") {
    "protoc.exe"
  } else {
    "protoc"
  };
  let protoc_path = out_dir.join(exe_name);

  if protoc_path.exists() {
    return protoc_path;
  }

  let release = protoc_release();

  let mut archive_bytes = Vec::new();
  ureq::get(release.url)
    .call()
    .expect("failed to download protoc release")
    .body_mut()
    .as_reader()
    .read_to_end(&mut archive_bytes)
    .expect("failed to read protoc release body");

  let mut hasher = Sha256::new();
  hasher.update(&archive_bytes);
  let digest = hasher
    .finalize()
    .iter()
    .map(|byte| format!("{byte:02x}"))
    .collect::<String>();
  assert_eq!(
    digest, release.sha256,
    "protoc release hash mismatch for {}",
    release.url
  );

  let mut archive =
    zip::ZipArchive::new(std::io::Cursor::new(archive_bytes)).expect("failed to open protoc release zip");
  let mut entry = archive
    .by_name(&format!("bin/{exe_name}"))
    .expect("protoc binary missing from release archive");
  let mut out_file = std::fs::File::create(&protoc_path).expect("failed to create protoc output file");
  std::io::copy(&mut entry, &mut out_file).expect("failed to extract protoc binary");
  drop(out_file);

  #[cfg(unix)]
  {
    use std::os::unix::fs::PermissionsExt;
    std::fs::set_permissions(&protoc_path, std::fs::Permissions::from_mode(0o755))
      .expect("failed to make protoc executable");
  }

  protoc_path
}

fn compile_protos() {
  let schema_dir = PathBuf::from("../../../schemas");
  let desktop_path = schema_dir.join("desktop.proto");
  let project_path = schema_dir.join("project.proto");

  println!("cargo:rerun-if-changed={}", desktop_path.display());
  println!("cargo:rerun-if-changed={}", project_path.display());

  prost_build::Config::new()
    .protoc_executable(fetch_protoc())
    .compile_protos(&[desktop_path, project_path], &[schema_dir])
    .expect("failed to compile desktop.proto/project.proto");
}

#[cfg(windows)]
fn embed_manifest_if_msvc() {
  let target_env = std::env::var("CARGO_CFG_TARGET_ENV");

  if Ok("msvc") != target_env.as_deref() {
    return;
  }

  let manifest = std::env::current_dir()
    .unwrap()
    .join("windows-app-manifest.xml");

  println!("cargo:rerun-if-changed={}", manifest.display());
  println!("cargo:rustc-link-arg=/MANIFEST:EMBED");
  println!(
    "cargo:rustc-link-arg=/MANIFESTINPUT:{}",
    manifest.to_str().unwrap()
  );
  println!("cargo:rustc-link-arg=/WX");
}
