//! datagen: converts flutter_ilib `assets/locale` (open source or webOS build)
//! into `locale.bin`. Runs on the build machine only.
//!
//! Planned steps:
//! 1. read every `<locale>.json` in the input directory
//! 2. keep only the sections ilibx uses (drop localematch, ctype_*, ...)
//! 3. deduplicate keys and strings
//! 4. group by section, sort keys for direct lookup, write locale.bin
//!    (with a header recording the data source/version)
//!
//! Usage (planned): datagen <assets/locale dir> <output locale.bin>

fn main() {}
