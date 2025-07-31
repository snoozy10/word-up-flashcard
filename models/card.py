"""
fsrs.models.card
---------

This module defines the Card and State classes.

Classes:
    Card: Represents a flashcard in the FSRS system.
    State: Enum representing the learning state of a Card object.
"""

from __future__ import annotations
from enum import IntEnum
from dataclasses import dataclass
from datetime import datetime, timezone
import time

from utils import DEFAULT_DECK_ID  # (Nuzy)


class State(IntEnum):
    """
    Enum representing the learning state of a Card object.
    """
    New = 0  # (Nuzy)
    Learning = 1
    Review = 2
    Relearning = 3


@dataclass
class Card:
    """
    Represents a flashcard in the FSRS system.

    Attributes:
        card_id: The id of the card. Defaults to the epoch milliseconds of when the card was created.
        (Nuzy) deck_id: The id of the deck the card belongs to.
        (Nuzy) content_id: The id of the content the card was created from.
        state: The card's current learning state.
        step: The card's current learning or relearning step or None if the card is in the Review state
             (Nuzy) or New state.
        stability: Core mathematical parameter used for future scheduling.
        difficulty: Core mathematical parameter used for future scheduling.
        due: For states Learning|Review|Relearning -- The date and time when the card is due next in epochmillis.
             For state New -- The date and time of card creation in epochmillis i.e. card_id essentially
        last_review: The date and time of the card's last review in epochmillis.
    """
    # card_id, deck_id, content_id, state, step, stability, difficulty, due, last_review
    id: int
    deck_id: int  # (Nuzy)
    content_id: int  # (Nuzy)
    state: State
    step: int | None
    stability: float | None
    difficulty: float | None
    due: int
    last_review: int | None

    def __init__(
        self,
        id: int | None,
        deck_id: int = DEFAULT_DECK_ID,  # (Nuzy)
        content_id: int | None = None,
        # state: State = State.Learning,  # (Nuzy)
        state: State = State.New,  # (Nuzy)
        step: int | None = None,
        stability: float | None = None,
        difficulty: float | None = None,
        due: int | None = None,
        last_review: int | None = None,
    ) -> None:
        if id is None:
            # epoch milliseconds of when the card was created
            id = int(datetime.now(timezone.utc).timestamp() * 1000)
            # wait 1ms to prevent potential card_id collision on next Card creation
            time.sleep(0.001)
        self.id = id

        self.content_id = content_id

        self.deck_id = deck_id  # (Nuzy)

        self.state = state

        if self.state == State.Learning or self.state == State.New and step is None:  # (Nuzy) or self.state== State.New
            step = 0
        self.step = step

        self.stability = stability
        self.difficulty = difficulty

        if due is None:
            due = id
        self.due = due

        self.last_review = last_review

    def to_dict(self) -> dict[str, float | None | int]:
        """
        Returns a JSON-serializable dictionary representation of the Card object.

        This method is specifically useful for storing Card objects in a database.

        Returns:
            A dictionary representation of the Card object.
        """

        return_dict = {
            "id": self.id,
            "deck_id": self.deck_id,  # (Nuzy)
            "content_id": self.content_id,  # (Nuzy)
            "state": self.state,
            "step": self.step,
            "stability": self.stability,
            "difficulty": self.difficulty,
            "due": self.due,
            "last_review": self.last_review if self.last_review else None,
        }

        return return_dict

    @staticmethod
    def from_dict(source_dict: dict[str, int | float | str | None]) -> Card:
        """
        Creates a Card object from an existing dictionary.

        Args:
            source_dict: A dictionary representing an existing Card object.

        Returns:
            A Card object created from the provided dictionary.
        """

        card_id = int(source_dict["card_id"])
        deck_id = int(source_dict["deck_id"])  # (Nuzy)
        content_id = int(source_dict["content_id"])  # (Nuzy)
        state = State(int(source_dict["state"]))
        step = (
            int(source_dict["step"]) if source_dict["step"] else None
        )
        stability = (
            float(source_dict["stability"]) if source_dict["stability"] else None
        )
        difficulty = (
            float(source_dict["difficulty"]) if source_dict["difficulty"] else None
        )
        due = source_dict["due"]
        last_review = (
            source_dict["last_review"] if source_dict["last_review"] else None
        )

        return Card(
            card_id=card_id,
            deck_id=deck_id,  # (Nuzy)
            content_id=content_id,  # (Nuzy)
            state=state,
            step=step,
            stability=stability,
            difficulty=difficulty,
            due=due,
            last_review=last_review,
        )


__all__ = ["Card", "State"]
