---
paths:
  - ".github/**"
  - "packaging/**"
  - "build.sh"
  - "run.sh"
  - "msys2-env.sh"
  - "shell.nix"
---

# CI, build and packaging rules

## Workflows

- `windows-zip.yml` and `linux-appimage.yml` run only by hand (`workflow_dispatch`) on the branch to build. No tag: build and test, keep the artifact. Existing release tag: replace the attached package. New tag: publish a test pre-release. Changing what a tag input does changes how releases are published: the maintainer decides that.
- `discord-notify.yml` runs on `pull_request_target` and `issues` events and has access to secrets, including for PRs from forks. It must never check out or execute PR code, and its `permissions` stay empty. Treat any edit to it as security-sensitive and take the PR title, body and branch name as untrusted text (no direct `${{ }}` interpolation into a shell `run:` line; pass through `env:`).
- The Windows job sets `core.autocrlf false` before checkout, because CRLF breaks the FSR-Vulkan patches. Keep that, and keep LF in `*.patch` and shell scripts.
- The Windows package is built with MSYS2 CLANG64 and a python.org-style Python, then opened on a clean runner without MSYS2 (the `smoke` job). Any new runtime DLL must be bundled; a smoke failure means a missing dependency.
- The AppImage is built on Ubuntu 24.04 so it needs glibc 2.39 or newer. A build step that raises that floor (for example a toolchain that links a newer glibc) breaks SteamOS and Debian 13 users: the "GLIBC_2.44 not found" regression was this.
- Pin actions to major versions already in use and Python packages to exact versions. No secrets in workflow files; use repository secrets.

## Build scripts

- `build.sh` has a Windows (MSYS2) branch that exits early and a Linux branch. A change to one must be checked against the other, or reported as unchecked.
- The submodule patch loop (reverse-check, then apply) must stay idempotent: running `build.sh` twice must not fail.
- `SPARTAN_LTO`, `SPARTAN_PGO` and `SPARTAN_*` env variables are interface; do not rename them.
- Shell scripts: `set -euo pipefail`, quote every expansion, no bashisms in anything run by `sh`.

## Release

Version bumps and tags are the maintainer's job. Do not bump the version or push tags from a feature branch.
