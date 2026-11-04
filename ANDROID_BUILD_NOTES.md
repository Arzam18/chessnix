# Chessnix Android ARM64 Build

This fork-ready build adds a GitHub Actions workflow for the existing Chessnix UCI engine. It does not change the engine's chess logic or evaluation.

## Source-archive repair

The supplied upstream source ZIP has an unconditional import of `src/local/searchtuner.zig` in `src/main.zig`, but does not contain that file or the `src/local/` directory. The standard UCI build sets `lib.program = .uci`; the search-tuner branch is not used. To allow Zig to resolve the import, this package adds `src/local/searchtuner.zig` as a small placeholder that returns `error.SearchTunerSourceNotIncluded` if the optional, missing search-tuning command is ever selected. The UCI engine path is unchanged.

## Outputs

- `chessnix-android-arm64-neon`
- `chessnix-android-arm64-dotprod`

Both are AArch64, `ReleaseFast`, statically linked Linux/musl executables intended to run on Android ARM64. Static musl is used because the upstream source pins Zig 0.15.2 and that compiler release does not provide a straightforward Android/Bionic cross-link configuration. The static build avoids a dependency on Android shared libraries or `libc++_shared.so`.

## Build details

- Zig compiler: exactly `0.15.2` (required by `src/lib.zig` compile-time check)
- Engine: UCI executable from the upstream `build.zig` target
- NEON target: `aarch64-linux-musl`, `generic+neon`
- Dotprod-capable target: `aarch64-linux-musl`, `generic+neon+dotprod`
- Optimization: `ReleaseFast`
- Build trigger: GitHub Actions `workflow_dispatch`
- No NNUE file is required. Chessnix uses handcrafted evaluation (HCE).

The Dotprod build enables the Arm dot-product CPU feature in the compiler target. The current Chessnix source does not contain an explicit SDOT/UDOT evaluation kernel, so the flag makes Dotprod instructions available to compiler optimization but does not guarantee that SDOT/UDOT instructions appear in this engine's final machine code. Do not interpret the variant name as proof of a hand-written Dotprod kernel.

## Verification in Actions

The workflow checks the AArch64 ELF machine type, rejects a dynamic interpreter and shared-library dependencies, and runs a UCI handshake plus a depth-2 search under `qemu-aarch64`. The final Actions artifact contains both engine files, `BUILD-INFO.txt`, and `SHA256SUMS`.

The QEMU test is a CI smoke test, not a replacement for testing the executable on the target Android phone and in the intended chess GUI. Confirm that the engine reports `uciok`, `readyok`, and a valid `bestmove` on-device before using it in rating matches.
