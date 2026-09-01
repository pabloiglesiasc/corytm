fn main() {
  tauri_build::try_build(
    tauri_build::Attributes::new()
      .windows_attributes(tauri_build::WindowsAttributes::new_without_app_manifest()),
  )
  .expect("failed to run tauri-build");

  #[cfg(windows)]
  embed_manifest_if_msvc();
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
