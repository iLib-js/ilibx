# CLAUDE.md

## Project

ilibx is an i18n library for native apps (Rust, C/LVGL). It ports the logic of flutter_ilib v2.0 (Dart) to Rust so that native apps get the same locale-specific results (dates, numbers, time zones, …) as iLib and flutter_ilib. The design is in `docs/LLD_ilibx.ko.md` (source) / `docs/LLD_ilibx.md` (English). If this file and the LLD disagree, the LLD wins; IDs below refer to it.

Packages: `ilibx-core` (logic), `ilibx-ffi` (C ABI, built as the shared `libilibx.so`), `ilibx-rust` (safe wrapper for Rust apps), plus build tools `datagen` (locale JSON → `locale.bin`) and `ilibx-dump`.

### Rules that apply to every code change

- **Match flutter_ilib, not "correctness"** (BC02). The baseline is the flutter_ilib test expectations. When ported behavior looks wrong but matches flutter_ilib, keep it.
- **No ICU in any form** (TC01): no ICU4C, no ICU4X-family crates (including zerovec, yoke), no ICU bindings. `deny.toml` and `scripts/check-no-icu.sh` enforce this.
- **`ilibx-core` is `no_std` + `alloc`** (TC05). No files, mmap, time or threads there; it takes data only as `&[u8]`. OS work belongs in `ilibx-ffi`.
- **`ilibx-rust` must not depend on `ilibx-core` or `ilibx-ffi`** (TC04). It declares the C functions and links to `libilibx.so` dynamically, so apps never contain the core logic.
- **The C ABI is the only public interface** (TC02, FR14): create/use/free functions, UTF-8 into caller-supplied buffers, numeric error codes, no callbacks, no panic across the boundary. Do not change or remove existing C functions; add new ones.
- **Minimum Rust 1.75, edition 2021** (TC06). Do not use features stabilized after 1.75 (e.g. `LazyLock`, `core::error::Error`, `c"..."` literals). New dependencies must support this version and `no_std` where needed (TC08); keep `Cargo.lock` pinned.
- **No JSON parsing on the device** (TC09). Only `datagen` reads JSON.
- Keep `unsafe` to the C ABI boundary and the mmap loader (QA05).

Undecided items are listed in LLD §6 (open issues). Do not settle one silently in code; point it out and ask.

## Design documents (LLD)

`docs/LLD_ilibx.ko.md` (Korean) is the source; `docs/LLD_ilibx.md` (English) is translated from it. Never edit the English one alone: apply any change, including English review feedback, to the Korean source first. The English file's first line records the source version: `<!-- translated-from: docs/LLD_ilibx.ko.md blob <id> -->`.

### Whenever you edit `docs/LLD_ilibx.ko.md`

Update the English edition in the same turn, unasked (also if it is already behind):

1. Translate only what changed since the recorded blob (`git diff <blob> $(git hash-object docs/LLD_ilibx.ko.md)`), keeping headings, anchors, table IDs, code and links identical.
2. Set the marker to the new blob id (first 12 characters).
3. Run `python3 tools/check_doc_sync.py docs/LLD_ilibx.md docs/LLD_ilibx.ko.md`; check numbers in prose by eye.
4. Summarize the English changes in Korean.
