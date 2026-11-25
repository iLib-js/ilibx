// Give the shared library a versioned soname so apps record
// `NEEDED libilibx.so.1`. Bump the major number only when an existing
// C function is changed or removed.
const SONAME_MAJOR: u32 = 1;

fn main() {
    let os = std::env::var("CARGO_CFG_TARGET_OS").unwrap_or_default();
    if os == "linux" {
        println!("cargo:rustc-cdylib-link-arg=-Wl,-soname,libilibx.so.{SONAME_MAJOR}");
    }
    println!("cargo:rerun-if-changed=build.rs");
}
