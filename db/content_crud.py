import sqlite3
from typing import List, Tuple, Optional, Any

from db import DatabaseBaseClass


class ContentCRUD(DatabaseBaseClass):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def create_content(self, id: int, de: str, en: str) -> None:
        query = "INSERT INTO contents (id, de, en) VALUES (?, ?, ?)"
        params = (id, de, en)
        self.execute_insert(query, params)
        print("contents: 1 row inserted successfully")

    def create_many_contents(self, contents: List[Tuple[int, str, str]]) -> None:
        """
        Insert multiple entries into the contents table.

        :param contents: A list of tuples, where each tuple contains (id, de, en).
        """
        if not contents:
            print("contents: No rows to insert.")
            return
        query = """
            INSERT INTO contents (id, de, en) VALUES (?, ?, ?)
        """

        count = self.execute_many(query, contents)
        print(f"contents: {count} rows inserted successfully")

    def get_all_contents(self) -> Optional[List[sqlite3.Row]]:
        """Retrieve all contents."""
        query = "SELECT id, de, en FROM contents"
        return self.execute_select_all(query)

    def get_many_contents_by_ids(self, ids: List[Any]) -> Optional[List[sqlite3.Row]]:
        placeholders = ",".join("?" for _ in ids)
        query = "SELECT id, de, en FROM contents WHERE id IN (" + placeholders + ")"
        
        return self.execute_select_many(query, ids)

    def get_content_by_id(self, content_id) -> Optional[sqlite3.Row]:
        """Retrieve content with content_id (id = epoch milliseconds)."""
        query = "SELECT id, de, en FROM contents WHERE id = ?"
        row = self.execute_select_one(query, content_id)
        return row

    def delete_all_contents(self):
        query = """DELETE FROM contents;"""
        count = self.execute_update_delete(query, ())
        print(f"contents: {count} rows deleted successfully")


