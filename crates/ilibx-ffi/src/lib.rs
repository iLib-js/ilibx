//! C ABI of ilibx (`libilibx.so`, header `include/ilibx.h`).
//!
//! Conventions every exported function will follow:
//! - Names start with `ilibx_`; types with `Ilibx`.
//! - Strings in and out are UTF-8.
//! - Results are written into a buffer supplied by the caller. The return
//!   value is the full length the result needs (without the trailing NUL),
//!   or a negative error code.
//! - Objects are handled with `*_new` / use / `*_free`.
//! - No callbacks into the caller.
//! - No panic may cross the boundary.
//! - Existing functions never change; only additions within soname 1.
//!
//! This crate also owns everything that needs the OS: opening/mmapping
//! `locale.bin` and reading the system time zone.
//!
//! The header is generated with:
//! `cbindgen --config cbindgen.toml --crate ilibx-ffi --output include/ilibx.h`
