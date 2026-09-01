`cargo test` for a Tauri app's `src-tauri` crate fails to even start on real Windows CI with `STATUS_ENTRYPOINT_NOT_FOUND` (0xc0000139) — confirmed on this repository (TK-011, run `33501836929`): `npm run tauri build` succeeds fully (including MSI/NSIS bundles) immediately beforehand, `cargo test` finishes compiling, then the produced `app_lib-<hash>.exe` test harness fails at the OS loader level before any test code runs. This is a known, reproducible **upstream Tauri limitation**, not specific to any one project's code — see `tauri-apps/tauri` issues #11028, #13419, #13948, #13954.

Root cause, confirmed by fetching Tauri's own real, currently-shipping `examples/api/src-tauri/build.rs` and `crates/tauri-build/src/windows-app-manifest.xml` directly from the repo (not paraphrased from an issue thread): `tauri-build` automatically embeds a Windows application manifest (declaring a dependency on `Microsoft.Windows.Common-Controls` version `6.0.0.0`) into the built binary, but only for the declared `[[bin]]` target. Cargo's auto-generated unit-test harness for the `[lib]` target (`app_lib`, not `app`) is not a `[[bin]]`, so it never receives that manifest. Without it, Windows' SxS activation context resolves the legacy COMCTL32 v5 instead of v6; some Windows-UI code path Tauri still links in even under `tauri::test::mock_builder()` (no real window is ever created) references a v6-only export, and the loader rejects the whole executable — hence the release binary being fine while only the debug test harness fails, and the harness failing before any test runs (a load-time, not run-time, failure).

Fix, matching Tauri's own real pattern rather than inventing a new one — `build.rs`:
```rust
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
  if Ok("msvc") != std::env::var("CARGO_CFG_TARGET_ENV").as_deref() {
    return;
  }
  let manifest = std::env::current_dir().unwrap().join("windows-app-manifest.xml");
  println!("cargo:rerun-if-changed={}", manifest.display());
  println!("cargo:rustc-link-arg=/MANIFEST:EMBED");
  println!("cargo:rustc-link-arg=/MANIFESTINPUT:{}", manifest.to_str().unwrap());
  println!("cargo:rustc-link-arg=/WX");
}
```
`WindowsAttributes::new_without_app_manifest()` opts out of `tauri-build`'s own bin-scoped embedding entirely; the manual embed then uses a *bare* (unscoped) `cargo:rustc-link-arg`, which applies uniformly to every linked artifact from the crate — release binary and test harness alike — deliberately avoiding the combination of one bin-scoped embed plus one bare embed, which a separate real Tauri issue (#10154) reports as a genuine "duplicate resource" linker failure. `windows-app-manifest.xml` is copied verbatim from Tauri's own shipped file (a standard Microsoft manifest snippet, not project-specific).

Verification note specific to this pattern: `#[cfg(windows)]` inside `build.rs` reflects the *host* compiling the build script, not any `--target` being cross-checked for — `cargo check --target x86_64-pc-windows-msvc` from macOS silently compiles the whole `embed_manifest_if_msvc` function out, giving false confidence. To actually typecheck that function's body from a non-Windows host, temporarily strip the `#[cfg(windows)]` gate and run a native `cargo check`, then restore it — this catches Rust-level errors (wrong API, wrong types) but still can't verify the real Windows linker/loader behavior; only a real Windows CI run can do that. `tauri-build`'s icon-resource embedding already requires a Windows resource compiler (`llvm-rc`, installable via `brew install llvm` on macOS — not symlinked into `PATH` by Homebrew by default, needs `/opt/homebrew/opt/llvm/bin` added explicitly) even before this fix — a pre-existing requirement for cross-checking this crate for Windows at all, not something this fix introduces.
