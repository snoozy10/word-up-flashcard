import sqlite3
from typing import List

from db import DatabaseBaseClass


class MetadataCRUD(DatabaseBaseClass):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    # Common column selection for revlogs
    METADATA_COLUMNS = "last_session_cutoff, remaining_new_cards"

    def insert_or_replace_metadata(self, last_session_cutoff, new_cards_reviewed) -> None:
        query = """
            INSERT OR REPLACE INTO metadata (id, last_session_cutoff, new_cards_reviewed)
            VALUES (?, ?, ?)
        """
        params = (1, last_session_cutoff, new_cards_reviewed)
        count = self.execute_insert(query, params)
        print(f"metadata: {count} rows inserted or updated successfully")

    def get_metadata(self) -> List[sqlite3.Row]:
        query = """
            SELECT id, last_session_cutoff, new_cards_reviewed FROM metadata
        """
        return self.execute_select_all(query)

