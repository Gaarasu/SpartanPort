---
paths:
  - "gpu/**"
---

# GPU library rules

`gpu/` is a CMake project (C++23, Ninja) that builds the shadPS4 video core, shader recompiler and Gnm/VideoOut drivers into `libspartanportgpu` (Linux) or links them statically into `spartanport-probe.exe` (Windows). Read `gpu/VENDOR.txt` first.

## Vendored code

- `gpu/shadps4/` is vendored from shadPS4 at a recorded commit plus a short list of backported recompiler fixes. Local changes carry a `spartanport:` comment. Keep every change minimal and marked. Never reformat, rename or reorder vendored files: it makes the next upstream sync unreadable.
- Prefer putting new behavior in `gpu/shim/` (this port's glue, overlay, settings, graphics options) and a small hook in vendored code, over a large edit inside vendored code.
- Syncing upstream or backporting a fix: update `gpu/VENDOR.txt` in the same commit with the upstream commit hash and PR number, and state the correctness reason. Only correctness fixes are backported.
- Submodules (`.gitmodules`: fsr-vulkan, imgui, magic_enum, miniz, xbyak, LibAtrac9) are never edited in place. Changes go in `gpu/patches/<name>/*.patch`, applied by `build.sh` (LF endings, applied once, reverse-checked first).
- `gpu/third_party/gcn`, `sirit`, `fonts` and similar are tracked files, not submodules. Treat them as vendored too.

## Behavior

- GPU bugs are often vendor-specific. State which GPUs and drivers a change was checked on (AMD RDNA2, NVIDIA, Intel, Steam Deck RADV) and which not. A fix for one vendor must not change the path of the others unless that is the point.
- Rendering fixes that replace guest GPU state (blend rewrite, depth/stencil, aliasing, MSAA) need a unit test target next to the existing ones (`blend-rewrite-test`, `depth-stencil-state-test`, `no-msaa-test`, and so on).
- Frame pacing, swapchain and fence changes: describe the thread and fence ordering in the commit message. These bugs only show up under load.
- Shader cache and pipeline cache formats are user data. A format change needs a version bump that discards the old cache cleanly, never a crash on load.
- New test targets: `add_executable(<name>-test EXCLUDE_FROM_ALL ../tests/test_<name>.cpp ...)` in `gpu/CMakeLists.txt`, and add it to the README test list only if it is meant for contributors.
