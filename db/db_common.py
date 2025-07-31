import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import List, Tuple, Optional, Any
import os
import csv
import time
from datetime import datetime, timezone

from ttkbootstrap.dialogs import Messagebox

from utils import DB_PATH, SCHEMA_PATH, CSV_PATH, DEFAULT_DECK_ID, DEFAULT_DECK_NAME


class DatabaseInitializer:
    def __init__(self):
        self.db_path = DB_PATH
        self.schema_path = SCHEMA_PATH
        self.csv_path = CSV_PATH

    def database_exists(self):
        if os.path.exists(self.db_path):
            return True
        return False

    def delete_existing_database(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
            return
        print("No database to delete!")

    def initialize_database(self):
        """Create database and tables if they don't exist"""
        if not os.path.exists(self.db_path):
            self._create_database()
            self._populate_tables_in_order()
        # else:
        #     answer = Messagebox.yesno(
        #         parent=self.window,
        #         title="Database Exists",
        #         message=f"A database already exists with the name {self.db_path}\nDo you want to delete and reinitialize it?",
        #         alert=True
        #     )
        #     if answer == "Yes":
        #         os.remove(self.db_path)
        #         self.initialize_database()

    def _create_database(self):
        """Create all required tables"""
        with sqlite3.connect(self.db_path) as conn:
            # Enable foreign key support
            conn.execute("PRAGMA foreign_keys = ON;")
            try:
                # Create your tables from pre-written script
                schema_sql = Path(self.schema_path).read_text()
                conn.executescript(schema_sql)
                conn.commit()
                print("✅ Database initialized.")
            except sqlite3.Error as e:
                conn.rollback()
                raise RuntimeError(f"Database initialization failed: {e}")

    def _populate_tables_in_order(self):
        try:
            self._create_default_deck()
            self._populate_contents_table_from_csv()
            self._populate_cards_table_from_contents_table()
        except sqlite3.Error as e:
            raise RuntimeError(f"Database seeding failed: {e}")

    def _create_default_deck(self):
        from db import DeckCRUD
        deck_crud = DeckCRUD()
        deck_crud.delete_all_decks()  # Make sure the decks table is empty

        default_did = DEFAULT_DECK_ID  # usually epoch_millis
        default_dname = DEFAULT_DECK_NAME
        default_parent_id = None
        deck_crud.create_deck(default_did, default_dname, default_parent_id)

    def _populate_contents_table_from_csv(self):
        from db import ContentCRUD
        content_crud = ContentCRUD()
        content_crud.delete_all_contents()

        with open(self.csv_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)  # Expects headers: de, en
            contents = []

            for row in reader:
                deutsch = row["de"]
                english = row["en"]
                epoch_millis = int(datetime.now(timezone.utc).timestamp() * 1000)
                content = (epoch_millis, deutsch, english)
                contents.append(content)

                time.sleep(0.001)
        content_crud.create_many_contents(contents=contents)

    def _populate_cards_table_from_contents_table(self):
        from db import ContentCRUD, CardCRUD
        content_crud = ContentCRUD()
        card_crud = CardCRUD()
        contents = content_crud.get_all_contents()
        cards = []

        card_crud.delete_all_cards()

        # card_id, deck_id, content_id, state, step, stability, difficulty, due, last_review
        for (content_id, _, _) in contents:
            epoch_millis = int(datetime.now(timezone.utc).timestamp() * 1000)
            card = (epoch_millis, DEFAULT_DECK_ID, content_id, 0, None, None, None, epoch_millis, None)
            cards.append(card)
            time.sleep(0.001)

        card_crud.insert_many_cards(cards=cards)


class DatabaseBaseClass:
    """Base class for CRUD inheritance"""
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.connection_timeout = 30
        self.enable_foreign_keys = True
        self._setup_database()

    def _setup_database(self):
        """Initialize database settings"""
        with self._get_connection() as conn:
            if self.enable_foreign_keys:
                conn.execute("PRAGMA foreign_keys = ON")
            conn.execute(f"PRAGMA busy_timeout = {self.connection_timeout * 1000}")

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            # Don't automatically commit here - let the caller decide
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def execute_select_all(self, query: str) -> List[sqlite3.Row]:
        """Execute a SELECT query and return all results."""
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute(query)
            return cur.fetchall()

    def execute_select_many(self, query: str, params: Tuple | List[Tuple]) -> List[sqlite3.Row]:
        """Execute a SELECT query and return all results."""
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute(query, params)
            return cur.fetchall()

    def execute_select_one(self, query: str, param) -> Optional[sqlite3.Row]:
        """Execute a SELECT query and return first result."""
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute(query, (param,))
            return cur.fetchone()

    def execute_insert(self, query: str, params: Tuple) -> int:
        """Execute an INSERT query and return the last row ID."""
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute(query, params)
            conn.commit()
            return cur.lastrowid

    def execute_update_delete(self, query: str, params: Optional[Tuple]) -> int:
        """Execute an UPDATE/DELETE query and return number of affected rows."""
        with self._get_connection() as conn:
            cur = conn.cursor()
            if not params: cur.execute(query)
            else: cur.execute(query, params)
            conn.commit()
            return cur.rowcount

    def execute_many(self, query: str, params_list: List[Tuple] | Tuple) -> int:
        """Execute a query with multiple parameter sets."""
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.executemany(query, params_list)
            conn.commit()
            return cur.rowcount


if __name__ == "__main__":
    db_init = DatabaseInitializer()
    db_base = DatabaseBaseClass()

