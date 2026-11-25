//! ilibx core: the iLib-compatible i18n logic (ported from flutter_ilib).
//!
//! Rules for this crate:
//! - `#![no_std]`: no files, mmap, clock, threads or env. Anything that needs
//!   the OS lives in an entry crate (`ilibx-ffi`, later `ilibx-mcu`).
//! - `alloc` is allowed (String, Vec) for intermediate work.
//! - Locale data comes in as borrowed bytes/views; the core never opens files.
//! - Must not panic across the C ABI; return errors instead.
#![no_std]
#![forbid(unsafe_code)]

extern crate alloc;
