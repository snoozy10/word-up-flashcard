import sqlite3
from typing import List, Tuple, Optional
from db import DatabaseBaseClass


class CardCRUD(DatabaseBaseClass):
    # Common column selection for cards
    # CARD_COLUMNS = "id, deck_id, content_id, state, step, stability, difficulty, due, last_review"
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def insert_card(self, card: Tuple) -> None:
        """Create a single card."""
        if not card:
            return
        query = """
            INSERT INTO cards (id, deck_id, content_id, state, step, stability, difficulty, due, last_review)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        try:
            self.execute_insert(query, (card,))
            print("cards: 1 row inserted successfully")
        except RuntimeError as e:
            print(f"Error occurred while inserting card: {e}")

    def insert_many_cards(self, cards: List[Tuple]) -> None:
        """Insert multiple entries into the cards table."""
        if not cards:
            print(f"cards: No rows to insert.")
            return

        query = """
            INSERT INTO cards (id, deck_id, content_id, state, step, stability, difficulty, due, last_review)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        count = self.execute_many(query, cards)
        print(f"cards: {count} rows inserted successfully")

    def get_cards_by_deck_id(self, deck_id: int) -> Optional[List[sqlite3.Row]]:
        """Retrieve all cards from a specific deck."""
        query = "SELECT * FROM cards WHERE deck_id = ?"
        return self.execute_select_many(
            query, (deck_id,)
        )

    def get_limited_new_cards(self, deck_id: int, new_state_int: int, limit: int) -> Optional[List[sqlite3.Row]]:
        """Retrieve the first {limit} rows of new cards."""
        query = """
            SELECT * FROM cards 
            WHERE deck_id = ? AND state = ? 
            ORDER BY due 
            LIMIT ?
        """
        # print("card_crud -> get_limited_new_cards")
        # print(deck_id, new_state_int, limit)
        return self.execute_select_many(
            query, (deck_id, new_state_int, limit)
        )

    def get_due_review_cards(self, deck_id: int, review_state_int: int, session_cutoff_epoch_millis: int) \
            -> Optional[List[sqlite3.Row]]:
        """Retrieve review cards that are due."""
        query = """
            SELECT * FROM cards 
            WHERE deck_id = ? AND state = ? AND due < ? 
            ORDER BY due ASC
        """
        return self.execute_select_many(
            query, (deck_id, review_state_int, session_cutoff_epoch_millis)
        )

    def get_due_learning_cards(self, deck_id: int, learning_state_int: int, relearning_state_int: int,
                               session_cutoff_epoch_millis: int) -> Optional[List[sqlite3.Row]]:
        """Retrieve learning cards that are due."""
        query = """
            SELECT * FROM cards 
            WHERE deck_id = ? AND state IN (?, ?) AND due < ? 
            ORDER BY due ASC
        """
        return self.execute_select_many(
            query, (deck_id, learning_state_int, relearning_state_int, session_cutoff_epoch_millis)
        )

    def get_all_due_cards(self, deck_id: int, new_state_int: int, session_cutoff_epoch_millis: int) \
            -> Optional[List[sqlite3.Row]]:
        """Retrieve all due cards."""
        query = """
            SELECT * FROM cards 
            WHERE deck_id = ? AND state != ? AND due < ?
            ORDER BY due ASC
        """
        return self.execute_select_many(
            query, (deck_id, new_state_int, session_cutoff_epoch_millis)
        )

    def get_all_cards(self) -> Optional[List[sqlite3.Row]]:
        """Retrieve all cards."""
        query = "SELECT * FROM cards"
        return self.execute_select_all(query)

    def delete_all_cards(self) -> None:
        """Delete all cards from the table."""
        try:
            count = self.execute_update_delete("DELETE FROM cards", None)
            print(f"cards: {count} rows deleted successfully")
        except RuntimeError as e:
            raise RuntimeError(f"Failed to clear cards table: {e}")

    # CARD_UPDATE_COLUMNS = "state, step, stability, difficulty, due, last_review"
    def update_many_cards(self, updated_cards_dict: List[dict]) -> None:
        if not updated_cards_dict:
            return
        query = ("UPDATE cards"
                 " SET state = ?, step = ?, stability = ?, difficulty = ?, due = ?, last_review = ?"
                 " WHERE id = ?")
        params: List[Tuple] = [(card["state"], card["step"], card["stability"],
                                card["difficulty"], card["due"], card["last_review"],
                                card["id"]) for card in updated_cards_dict]
        try:
            count = self.execute_many(query, params)
            print(f"cards: {count} rows updated successfully")
        except RuntimeError as e:
            print(f"Error occurred while updating cards: {e}")
