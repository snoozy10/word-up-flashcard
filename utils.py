from pathlib import Path

# Filenames
_VOCAB_CSV_NAME = "B1-Glossary.csv"
_DB_NAME = "fsrs.db"
_SCHEMA_NAME = "schema.sql"

# Paths
_curr_dir = Path(__file__).resolve().parent

ROOT_DIR = _curr_dir
MODEL_DIR = ROOT_DIR / "models"
CSV_PATH = ROOT_DIR / "db" / _VOCAB_CSV_NAME
DB_PATH = ROOT_DIR / "db" / _DB_NAME
SCHEMA_PATH = ROOT_DIR / "db" / _SCHEMA_NAME

DEFAULT_DECK_ID = 1
DEFAULT_DECK_NAME = "Main_Deck"

__all__ = ["ROOT_DIR", "MODEL_DIR", "CSV_PATH", "DB_PATH", "SCHEMA_PATH", "DEFAULT_DECK_ID", "DEFAULT_DECK_NAME"]