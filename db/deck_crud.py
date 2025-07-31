import sqlite3
from typing import Optional, List
from db import DatabaseBaseClass


class DeckCRUD(DatabaseBaseClass):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def create_deck(self, id: int, name: str, parent_id: Optional[int] = None) -> None:
        """
        Create a new deck in the database.
        :param id: The id of the deck. Default deck has id=1 (saved in utils). Others have id in epoch milliseconds.
        :param name: The name of the deck. Default deck (id=1) is Main. Set in fill_con....table.py in scripts folder.
        :param parent_id: The parent deck id. If None, this deck is a root deck.
        """
        query = "INSERT INTO decks (id, name, parent_id) VALUES (?, ?, ?)"
        params = (id, name, parent_id)
        self.execute_insert(query, params)
        print("decks: 1 row inserted successfully")

    def get_deck_by_id(self, deck_id: int) -> sqlite3.Row:
        """
        Retrieve a deck by its ID.
        :param deck_id: The ID of the deck to retrieve.
        :return: A tuple containing the deck's details (id, name, parent_id), or None if not found.
        """
        query = "SELECT id, name, parent_id FROM decks WHERE id = ?"
        params = deck_id
        return self.execute_select_one(query, params)

    def get_deck_name_by_id(self, deck_id: int) -> sqlite3.Row:
        """
        Retrieve a deck by its ID.
        :param deck_id: The ID of the deck to retrieve.
        :return: A tuple containing the deck's details (id, name, parent_id), or None if not found.
        """
        query = "SELECT name FROM decks WHERE id = ?"
        params = deck_id
        return self.execute_select_one(query, params)

    def get_all_decks(self) -> List[sqlite3.Row]:
        """
        Retrieve all decks from the database.
        :return: A list of tuples containing all decks' details (id, name, parent_id).
        """
        query = "SELECT id, name, parent_id FROM decks"
        return self.execute_select_all(query)

    def update_deck_name(self, deck_id: int, new_name: str) -> int:
        """
        Update the name of an existing deck.
        :param deck_id: The ID of the deck to update.
        :param new_name: The new name for the deck.
        """
        query, params = "UPDATE decks SET name = ? WHERE id = ?", (new_name, deck_id)
        count = self.execute_update_delete(query, params)
        print(f"decks: {count} rows updated successfully")
        return count

    def delete_deck(self, deck_id: int) -> None:
        """
        Delete a deck from the database by its ID.
        :param deck_id: The ID of the deck to delete.
        """
        query, params = "DELETE FROM decks WHERE id = ?", (deck_id,)
        self.execute_update_delete(query, params)
        print("decks: 1 row deleted successfully")

    def delete_all_decks(self) -> None:
        query = """DELETE FROM decks;"""
        count = self.execute_update_delete(query, None)
        print(f"decks: {count} rows deleted successfully")

