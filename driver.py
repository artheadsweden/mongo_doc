from mongo_doc import create_collection_class
import os

os.environ['MONGO_DB_CONNECTION_STRING'] = 'mongodb://localhost:27017'
os.environ['MONGO_DB_NAME'] = 'test'

schema = {
    'first_name': {'type': str, 'required': True},
    'last_name': {'type': str, 'required': True},
    'email_address': {
        'type': list,
        'validator': lambda v: all(isinstance(email, str) for email in v),
        'required': True
    },
    'street_addresses': {
        'type': list,
        'validator': lambda v: all(isinstance(address, dict) and 'street' in address and 'zip_code' in address for address in v),
        'required': True,
        'schema': {
            'street': {'type': str, 'required': True},
            'zip_code': {'type': str, 'required': True}
        }
    }
}

User = create_collection_class('User', 'users', schema=schema)


data = {
    'first_name': 'Evan',
    'last_name': 'Svensson',
    'email_address': ['nisse@email.com', 'nils.svensson@email.com'],
    'street_addresses': [
        {'street': 'Storgatan 1', 'zip_code': '12345'},
        {'street': 'Storgatan 2', 'zip_code': '12345'},
    ]
}
user = User(data)
user.save()
print(user)
user2 = User.find(first_name='Evan').first_or_none()
user2.street_addresses[0]['street'] = 'Storgatan 3'
user2.save()
print(user2)