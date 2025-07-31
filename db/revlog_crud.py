# To-do
from typing import List, Tuple, Optional
from db import DatabaseBaseClass


class RevlogCRUD(DatabaseBaseClass):
    # Common column selection for revlogs
    # REVLOG_COLUMNS = "card_id, rating, review_datetime, review_duration"
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def insert_review(self, review_log: Tuple) -> None:
        query = """
            INSERT INTO revlogs (card_id, rating, review_datetime, review_duration)
            VALUES (?, ?, ?, ?)
        """
        self.execute_insert(query, (review_log,))
        print(f"revlogs: 1 row inserted successfully")

    def insert_many_reviews(self, review_logs: List[Tuple]) -> None:
        query = """
            INSERT INTO revlogs (card_id, rating, review_datetime, review_duration)
            VALUES (?, ?, ?, ?)
        """
        count = self.execute_many(query, review_logs)
        print(f"revlogs: {count} rows inserted successfully")

