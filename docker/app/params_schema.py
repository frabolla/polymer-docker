"""
Structural description of the Polymer parameters exposed in the interface.

Only names, types and defaults live here. All user-facing labels and help texts
are translated in i18n.py (keys "param.<name>.label" / "param.<name>.help",
"watermodel.*", "normalize.*", "ancillary.*").

Meanings come from the ``run_atm_corr`` docstring (polymer/main.py) and
``polymer/params.py``. Anything not listed here is still reachable through the
"Advanced parameters" section of the interface (passed as **kwargs).
"""

# Sensors known to the interface. "auto" = detect from the file name.
SENSORS = [
    "auto",
    "OLCI",       # Sentinel-3
    "MSI",        # Sentinel-2
    "MERIS",      # Envisat
    "MODIS",      # Aqua
    "VIIRS",
    "SeaWiFS",
    "PRISMA",
    "LANDSAT8",
    "HICO",
]

# Sensors whose file-name auto-detection is NOT supported by polymer.level1.Level1
NEEDS_EXPLICIT_SENSOR = {"PRISMA", "HICO"}

OUTPUT_FORMATS = ["netcdf4", "hdf4"]

# Codes only; descriptions come from i18n ("watermodel.<code>").
WATER_MODELS = ["PR05", "MM01", "MM01_FOQ"]

# Codes only; descriptions come from i18n ("normalize.<code>").
NORMALIZE = [0, 1, 2, 3]

# Codes only; descriptions come from i18n ("ancillary.<code>").
ANCILLARY_SOURCES = ["auto", "NASA", "ERA5", "none"]

# Common fields, always shown in the processing form.
# type: int (only int is used for now)
COMMON_PARAMS = [
    {"name": "multiprocessing", "type": "int", "default": -1},
    {"name": "sline", "type": "int", "default": 0},
    {"name": "eline", "type": "int", "default": -1},
    {"name": "scol", "type": "int", "default": 0},
    {"name": "ecol", "type": "int", "default": -1},
]

# Human-readable names for Polymer's quality flags (polymer/common.py).
L2_FLAGS = {
    "LAND": 1,
    "CLOUD_BASE": 2,
    "L1_INVALID": 4,
    "NEGATIVE_BB": 8,
    "OUT_OF_BOUNDS": 16,
    "EXCEPTION": 32,
    "THICK_AEROSOL": 64,
    "HIGH_AIR_MASS": 128,
    "EXTERNAL_MASK": 512,
    "CASE2": 1024,
    "INCONSISTENCY": 2048,
    "ANOMALY_RWMOD_BLUE": 4096,
}
