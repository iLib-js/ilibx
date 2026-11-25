# data

Locale data input for ilibx (not added yet).

- Source: flutter_ilib `assets/locale` (assembled iLib data), pinned to a
  flutter_ilib tag. Copied here as-is; never edited by hand.
- The source version will be recorded in `data/SOURCE` (repository, tag, commit).
- The webOS build is not stored here. The Yocto recipe passes the webOS
  assembled data directory to `datagen` at build time.
- `datagen` turns this directory into `locale.bin` (one file per device,
  installed as `/usr/share/ilibx/locale.bin`).
