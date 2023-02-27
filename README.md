## Mongo Doc
This is a simple and straight forward wrapper around pymongo that will help you with simpe storage of documents in a MongoDB.

#### How it works
Before you can use the database you will need to connect to it.

#### Connecting to the database
This can be done in one of two ways.

##### Using init_db
You can use the provided init_db function to make the connection.

```python
from mongo_doc import init_db

init_db('mongodb://localhost:27017', 'test')
```
The first argument is the connections string. It can contain username and password, and is a normal mongodb connection string.

The second argument is the database to use.

##### Using environement variables
You can instead use the two environment variables MONGO_DB_CONNECTION_STRING and MONGO_DB_NAME

The first one should be set to the same connection string as for the init_db call, and the second one with the dabase name.

### Creating a document class
As we will be storing the data in MongoDB we will be working with documents. We represent the documents with one class per collection.

When using Mongo Doc you have two options for how to use these classes.

#### Schema-less documents
Your collection class can be schema-less. What this mean, is that you can actually store anything you want in the document. With this aproach there is no gurantee that two documents in the same collection will have the same fields.

Creating such a class is very simple and straight forward. You create the class using a factory function called create_collection_class.

```python
from mongo_doc import create_collection_class

User = create_collection_class('User', 'users')
```

Here we get a class called User. The first argument to create_collection_class is the name the class should have (that is in the meta data for this class). The second argument is optinal. If given this is the name of the collection that the documents for this class will be stored in. If not give, the class name will be used as the collection name.


