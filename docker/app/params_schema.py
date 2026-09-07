"""
Elenco curato dei parametri di Polymer esposti nell'interfaccia grafica.

I significati derivano dalla docstring di ``run_atm_corr`` (polymer/main.py) e da
``polymer/params.py``.  Tutto cio' che non e' qui resta comunque impostabile dalla
sezione "Parametri avanzati" dell'interfaccia (passati come **kwargs).
"""

# Sensori riconosciuti dall'interfaccia. "auto" = rilevamento dal nome file.
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

# Sensori la cui autodetezione dal nome file NON e' supportata da polymer.level1.Level1
NEEDS_EXPLICIT_SENSOR = {"PRISMA", "HICO"}

OUTPUT_FORMATS = ["netcdf4", "hdf4"]

WATER_MODELS = {
    "PR05": "Park & Ruddick 2005 (predefinito, consigliato)",
    "MM01": "Morel & Maritorena 2001",
    "MM01_FOQ": "Morel & Maritorena 2001 con f/Q direzionale",
}

NORMALIZE = {
    0: "Nessuna normalizzazione",
    1: "Normalizza la riflettanza dell'acqua al nadir",
    2: "Normalizzazione in lunghezza d'onda (MERIS/OLCI)",
    3: "Entrambe (nadir + lunghezza d'onda)",
}

ANCILLARY_SOURCES = {
    "auto": "Automatico (usa NASA se disponibili le credenziali)",
    "NASA": "NASA Earthdata (ozono, vento, pressione)",
    "ERA5": "Copernicus ERA5 / CDS",
    "none": "Nessuno (usa le climatologie interne)",
}

# Campi "comuni" mostrati sempre nel modulo di elaborazione.
# tipo: text | int | float | bool | choice
COMMON_PARAMS = [
    {
        "name": "multiprocessing",
        "label": "Numero di core CPU",
        "type": "int",
        "default": -1,
        "help": "0 = un solo core.  -1 = tutti i core disponibili.  N = N core.",
    },
    {
        "name": "sline",
        "label": "Riga iniziale (ritaglio)",
        "type": "int",
        "default": 0,
        "help": "Ritaglia il prodotto: prima riga da elaborare (0 = dall'inizio).",
    },
    {
        "name": "eline",
        "label": "Riga finale (ritaglio)",
        "type": "int",
        "default": -1,
        "help": "Ultima riga da elaborare (-1 = fino alla fine).",
    },
    {
        "name": "scol",
        "label": "Colonna iniziale (ritaglio)",
        "type": "int",
        "default": 0,
        "help": "Prima colonna da elaborare (0 = dall'inizio). Ignorato da alcuni sensori.",
    },
    {
        "name": "ecol",
        "label": "Colonna finale (ritaglio)",
        "type": "int",
        "default": -1,
        "help": "Ultima colonna da elaborare (-1 = fino alla fine).",
    },
]

# Etichette leggibili per i flag di qualita' di Polymer (polymer/common.py).
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
