"""
Implements the database connection
Acts as a base class for the Document class
"""
from typing import Union
import pymongo


class DataBase:
    """
    Class that contains the database connection
    Acts as a base class for the Document class
    """
    db = None
    instances = {}

    @classmethod
    def get_instances(cls) -> dict:
        """
        Return a dict with all instances of the class
        """
        return cls.instances

    @classmethod
    def get_db(cls) -> Union[pymongo.database.Database, None]:
        """
        Return the database connection
        :return: Database connection
        """
        return cls.db