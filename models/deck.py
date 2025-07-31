from typing import Optional


class Deck:
    def __init__(self, id: int, name: str, parent_id: Optional[int] = None):
        """
        Initialize the Deck object.

        :param id: The unique identifier for the deck.
        :param name: The name of the deck.
        :param parent_id: The ID of the parent deck, or None for root decks.
        """
        self.id = id
        self.name = name
        self.parent_id = parent_id

    def __repr__(self):
        """
        Return a string representation of the Deck object.
        """
        return f"Deck(id={self.id}, name={self.name}, parent_id={self.parent_id})"

    def to_dict(self):
        """
        Convert the Deck object to a dictionary.
        :return: A dictionary representation of the Deck.
        """
        return {
            'id': self.id,
            'name': self.name,
            'parent_id': self.parent_id
        }

    @classmethod
    def from_dict(cls, data: dict):
        """
        Create a Deck object from a dictionary.
        :param data: A dictionary containing deck data.
        :return: A Deck object.
        """
        return cls(
            id=data['id'],
            name=data['name'],
            parent_id=data.get('parent_id')  # This is optional
        )


__all__ = ["Deck"]
