"""
Mondo Doc Exceptions
"""
class MongoException(Exception):
    """
    Base exception class
    """


class MongoDBConnectionError(MongoException):
    """
    Database initialization exceptions
    """


class MongoDBCollectionError(MongoException):
    """
    Collection exceptions
    """


class MongoFieldError(MongoException):
    """
    Field exceptions
    """