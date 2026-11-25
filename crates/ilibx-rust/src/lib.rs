//! Rust API of ilibx for Rust apps.
//!
//! This crate only converts values and calls libilibx.so through the C ABI
//! (C function list + safe wrappers that copy strings and free handles).
//! It holds no i18n logic (no defaults, locale resolution or pattern
//! handling), so every app gets the result of the one shared library on the
//! device.
//!
//! When the first C function is added, a build.rs will link `libilibx.so`
//! (`cargo:rustc-link-lib=dylib=ilibx`, search path from `ILIBX_LIB_DIR`
//! for local development).
