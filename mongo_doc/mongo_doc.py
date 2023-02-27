"""
Mongo Doc Library
~~~~~~~~~~~~~~~~~~
A simple and easy to use library to access a MongoDB database.

Basic usage:
from mongo_doc import init_db, create_collection_class


# First initialize the database connection
init_db('mongodb://username:password@host:port')


# Create a collection class
User = create_collection_class('User', 'users')

# Create a user object using a dict
user = User(
    {
        'first_name': 'Alice',
        'last_name': 'Smith',
        'email': 'alice@email.com'
    })

# Create a user object using keyword arguments
user = User(
    first_name='Alice',
    last_name='Smith',
    email='alice@email.com'
)

# Save the object to the database
user.save()

# Search for all users with this first name and return the first hit
# or None if no documents are found
user = User.find(first_name='Alice').first_or_none()
if user:
    # Change the first name
    user.first_name = 'Bob'
    # and save it
    user.save()

:copyright: (c) 2023 by Joakim Wassberg.
:license: MIT License, see LICENSE for more details.
:version: 0.03
"""
import time
from copy import copy, deepcopy
import unicodedata
from typing import Any, Callable, Union
import os
from functools import wraps
import bson
from .mongo_doc_exceptions import MongoDBCollectionError, MongoFieldError, MongoDBConnectionError
from .base_dict import BaseDict
from .database import DataBase
from .resultlist import ResultList
import pymongo
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError


class Document(BaseDict, DataBase):
    """
    This class acts as the base class for collection classes. Each instance of the subclasses
    will represent a single document
    """
    collection = None
    schema = None

    def __init__(self, *args, **kwargs):
        super().__init__()
        # If _id is not present we add the _id attribute
        if '_id' not in kwargs:
            self._id = None

        # Handle dict argument
        if len(args) > 0 and isinstance(args[0], dict):
            as_dict = copy(args[0])
        else:
            as_dict = copy(kwargs)

        # We need to check if there is an embedded document in this document.
        # If so, we will convert it into a dict
        for key, value in as_dict.items():
            if isinstance(value, Document):
                as_dict[key] = value.__dict__

        # Update the object
        self.__dict__.update(as_dict)
    
    def _has_changed(self) -> dict:
        """
        Checks if any of the fields in this document has changed
        :return: dict, a dict with the changed fields, empty if no fields have changed
        """
        changed_fields = {}
        for key, value in self.__dict__.items():
            if key != '_id':
                # compare with the value in the database
                result = self.collection.find_one({'_id': self._id}, {key: 1})
                if result and key in result and result[key] != value:
                    changed_fields[key] = value
        return changed_fields

    def is_saved(self) -> bool:
        """
        Checks if this document has been saved to the database
        :return: bool, True if the document has been saved, False otherwise
        """
        return not bool(self._has_changed())
    
    def save(self):
        """
        Saves the current object to the database
        :return: The saved object
        """
        if self.collection is None:
            raise MongoDBCollectionError('The collection does not exist')

        if self.schema is not None:
            self.validate()
        # If _id is None, this is a new document
        if self._id is None:
            del self._id
            res = self.collection.insert_one(self.__dict__)
            self._id = res.inserted_id
            return self

        # if no fields have changed, return the document unchanged
        if not (changed_fields := self._has_changed()):
            return self

        # update the document
        update_result = self.collection.update_one({'_id': self._id}, {'$set': changed_fields})
        if update_result.matched_count == 0:
            raise ValueError('Document with _id {} does not exist'.format(self._id))
        else:
            return self

    def delete_field(self, field: str):
        """
        Removes a field from this document
        :param field: str, the field to remove
        :return: None
        """
        self.collection.update_one({'_id': self._id}, {"$unset": {field: ""}})

    @classmethod
    def create_index(cls, keys: list[str], index_type:int=pymongo.ASCENDING, unique:bool=False, name:Union[str,None]=None) -> None:
        """
        Creates an index on the specified keys
        :param keys: The keys to index on
        :param index_type: The index type, e.g. ASCENDING or DESCENDING
        :param unique: Whether the index should be unique
        :param name: The name of the index
        :return: None
        """
        index_name = name or '_'.join(keys) + '_' + index_type.lower()
        cls.collection.create_index([(key, index_type) for key in keys], name=index_name, unique=unique)

    @classmethod
    def get_by_id(cls, _id:str) -> Union['Document', None]:
        """
        Get a document by its _id
        :param _id: str, the id of the document
        :return: The retrieved document or None
        """
        try:
            return cls(cls.collection.find_one({'_id': bson.ObjectId(_id)}))
        except bson.errors.InvalidId:
            return None

    @classmethod
    def insert_many(cls, items: list[dict]) -> None:
        """
        Inserts a list of dictionaries into the databse
        :param items: list of dict, items to insert
        :return: None
        """
        for item in items:
            cls(item).save()

    @classmethod
    def all(cls) -> ResultList:
        """
        Retrieve all documents from the collection
        :return: ResultList of documents
        """
        return ResultList([cls(**item) for item in cls.collection.find({})])

    @classmethod
    def find(cls, **kwargs):
        """
        Find a document that matches the keywords
        :param kwargs: keyword arguments or dict to match
        :return: ResultList
        """
        if len(kwargs) == 1 and isinstance(kwargs.get(list(kwargs.keys())[0]), dict):
            d = copy(kwargs.get(list(kwargs.keys())[0]))
        else:
            d = copy(kwargs)
        return ResultList(cls(item) for item in cls.collection.find(d))

    @classmethod
    def find_in(cls, field:str, values:list) -> ResultList:
        """
        Find a document that matches the keywords
        :param field: str, the field to search in
        :param values: list, the values to search for
        :return: ResultList
        """
        return ResultList(cls(item) for item in cls.collection.find({field: {"$in": values}}))

    @classmethod
    def delete(cls, **kwargs) -> None:
        """
        Delete the document that matches the keywords
        :param kwargs: keyword arguments or dict to match
        :return: None
        """
        if len(kwargs) == 1 and isinstance(kwargs.get(list(kwargs.keys())[0]), dict):
            d = copy(kwargs.get(list(kwargs.keys())[0]))
        else:
            d = copy(kwargs)
        cls.collection.delete_many(kwargs)

    @classmethod
    def document_count(cls) -> int:
        """
        Returns the total number of documents in the collection
        :return: int
        """
        return cls.collection.count_documents({})


# *******************
# Helper functions
# *******************
def mongo_check_and_connect(func: Callable) -> Callable:
    """
    Decorator to check if the database is connected and connect if not
    :param func: The function to decorate
    :return: Callable
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        """
        Wrapper function to check if the database is connected and connect if not
        If the database is not connected, 
        the MONGO_DB_CONNECTION_STRING and MONGO_DB_NAME environment variables must be set
        """
        if DataBase.db is None:
            if os.environ.get('MONGO_DB_CONNECTION_STRING') and os.environ.get('MONGO_DB_NAME'):
                init_db(os.environ.get('MONGO_DB_CONNECTION_STRING'), os.environ.get('MONGO_DB_NAME'))
            else:
                msg = 'init_db function must be called before creation of collection classes.\n' 
                msg += 'Another option is to set the MONGO_DB_CONNECTION_STRING and MONGO_DB_NAME environment variables'
                raise MongoDBConnectionError(msg)
        return func(*args, **kwargs)
    return wrapper

def _validate(self):
    """
    Method to validate the document against the schema.
    Only injected in the class if a schema is provided
    """
    for field_name, field_schema in self.schema.items():
        field_value = self.__dict__.get(field_name)
        field_type = field_schema.get('type')
        field_required = field_schema.get('required', False)
        # If we have a custom validator, use it
        if 'validator' in field_schema and not field_schema['validator'](field_value):
            raise ValueError(f"Field '{field_name}' is invalid")

        # Check that required fields are present
        if field_required and field_value is None:
            raise ValueError(f"Required field '{field_name}' is missing")

        # Check that the field has the correct type
        if field_value is not None and not isinstance(field_value, field_type):
            raise TypeError(f"Field '{field_name}' has invalid type. Expected {field_type}, got {type(field_value)}")

    # Check that all fields in the document are present in the schema
    for field_name in self.__dict__.keys():
        if field_name != '_id' and field_name not in self.schema:
            raise MongoFieldError(f"Field '{field_name}' is not in the schema")

@mongo_check_and_connect
def create_collection_class(class_name: str, collection_name: Union[str, None] = None, schema: dict[str, Any] = None):
    """
    Factory function for creating collection classes
    :param class_name: str, name of collection class
    :param collection_name: str or None, name of collection in database. If None, the class name will be used
    :param schema: dict or None, document schema. If None, no schema validation will be performed.
    :return: The newly created collection class
    """
    if collection_name is None:
        collection_name = class_name


    # Define the collection class
    collection_class = type(class_name, (Document,), {'collection': DataBase.db[collection_name]})
    # Add the class to the instances dict
    DataBase.instances[class_name] = collection_class
    # Define the validate method if a schema is provided
    if schema is not None:
        # Add the validate method to the collection class
        collection_class.validate = _validate
        collection_class.schema = schema

    return collection_class


def add_base_class(cls, base_class: type) -> None:
    """
    Helper function to add a base class to a collection class
    :param cls: The collection class
    :param base_class: The base class to add
    :return: None
    """
    cls.__bases__ = (base_class,) + cls.__bases__

def add_collection_method(cls, method: Callable) -> None:
    """
    Helper function to add methods to a collection class.
    Usage:
    def method(self):
        print(self.name)

    user = create_collection_class('User')
    add_collection_method(User, method)
    user.method()
    :param cls: The collection class
    :param method: The method to add to the class
    :return: None
    """
    setattr(cls, method.__name__, method)


def init_db(connection_str: str, database: str, retries: int = 3, retry_delay: int = 2) -> None:
    """
    Function to initialize database connection. Must be called before any use of the library
    :param connection_str: str, the database connection string
    :param database: str, the name of the database to use
    :param retries: int, the number of times to retry connection, defaults to 3
    :param retry_delay: int, the delay between retries, defeults to 2 seconds
    :return: None
    """
    for i in range(retries):
        try:
            client = MongoClient(connection_str)
            client.server_info()
            break
        except ServerSelectionTimeoutError as e:
            if i == retries - 1:
                raise MongoDBConnectionError("Could not connect to database") from e
            else:
                time.sleep(retry_delay ** i)
    DataBase.db = client[database]

