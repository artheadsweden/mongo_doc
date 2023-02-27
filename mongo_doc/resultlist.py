"""
This module contains the ResultList class, 
which extends the list class with methods to retrieve the 
first or last value, or None if the list is empty
"""

class ResultList(list):
    """
    Extends the list class with methods to retrieve the first or last value,
    or None if the list is empty
    This class is used as a return value for returned documents
    """
    def first_or_none(self):
        """
        Return the first value or None if list is empty
        :return: First list element or None
        """
        return self[0] if len(self) > 0 else None

    def last_or_none(self):
        """
       Return the last value or None if list is empty
       :return: Last list element or None
       """
        return self[-1] if len(self) > 0 else None