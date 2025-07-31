class Content:
    # Column mapping for database access
    COLUMNS = [
        "id",
        "de",
        "en",
    ]
    COL = {key: i for i, key in enumerate(COLUMNS)}

    def __init__(self, id, de, en):
        """
        Initialize a content-instance with the given properties.

        Args:
            id (int): Epoch milliseconds when the content was created
            de: The word in German
            en: The word in English
        """
        self.id = id
        self.de = de
        self.en = en

    @classmethod
    def from_db_row(cls, row):
        """
        Create a content object from a database row.

        Args:
            row: A database row containing content data

        Returns:
            Card: A new Content object
        """
        return cls(
            id=row[cls.COL["id"]],
            de=row[cls.COL["de"]],
            en=row[cls.COL["en"]],
        )

    def to_db_values(self):
        """
        Convert the Content object to a tuple suitable for database insertion.

        Returns:
            tuple: A tuple of values matching the database schema
        """
        return (
            self.id,
            self.de,
            self.en,
        )

    def __str__(self):
        """Return a string representation of the content instance."""
        return (f"Content(id={self.id}, "
                f"de={self.de}, "
                f"en={self.en})")


__all__ = ["Content"]