# `data/` — your files

Everything Polymer reads and writes lives in this folder, next to the launcher.
It is mounted into the container, so what you put here appears inside Polymer and
what Polymer produces appears here. **Nothing in this folder is uploaded to
GitHub** (only these empty folders and this note are tracked).

| Folder | What goes in it |
|---|---|
| `input/` | Your **Level-1** satellite products — the files/folders to correct (`.SEN3`, `.SAFE`, `.he5`, `.N1`, `.L1C` …). Put them here (or use the *Upload a product* panel). |
| `output/` | The **corrected Level-2** images Polymer writes (`.hdf` by default). |
| `auxdata/` | Polymer's static reference tables (~200 MB, `LUT.hdf` …). Downloaded once from the **Setup** page — do not edit by hand. |
| `ancillary/` | Weather data (ozone / wind / pressure) downloaded automatically during processing. |
| `config/` | Saved credentials (`.netrc`, `.cdsapirc`), language, licence acceptance, and the optional `dirs.env`. Treat as private. |

You can point `input/` and `output/` somewhere else (e.g. an external drive) from
the interface: **Working folders → Change the input / output folders**, then
restart with the launcher.
