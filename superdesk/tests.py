
import os
import unittest
from app import get_app
from pyelasticsearch import ElasticSearch
from base64 import b64encode
from flask import json

test_user = {'username': 'test_user', 'password': 'test_password'}


def get_test_settings():
    test_settings = {}
    test_settings['ELASTICSEARCH_URL'] = 'http://localhost:9200'
    test_settings['ELASTICSEARCH_INDEX'] = 'sptests'
    test_settings['MONGO_DBNAME'] = 'sptests'
    return test_settings


def drop_elastic(settings):
    try:
        es = ElasticSearch(settings['ELASTICSEARCH_URL'])
        es.delete_index(settings['ELASTICSEARCH_INDEX'])
    except:
        pass


def drop_mongo(app):
    with app.test_request_context():
        try:
            app.data.mongo.driver.cx.drop_database(app.config['MONGO_DBNAME'])
        except AttributeError:
            pass


def setup(context=None, config=None):
    if config:
        config.update(get_test_settings())
    else:
        config = get_test_settings()

    drop_elastic(config)
    app = get_app(config)
    drop_mongo(app)
    if context:
        context.app = app
        context.client = app.test_client()


def setup_auth_user(context):
    with context.app.test_request_context():
        context.app.data.insert('users', [test_user])
    auth_data = json.dumps({'username': test_user['username'], 'password': test_user['password']})
    auth_response = context.client.post('/auth', data=auth_data, headers=context.headers)
    token = json.loads(auth_response.get_data()).get('token').encode('ascii')
    context.headers.append(('Authorization', b'basic ' + b64encode(token + b':')))
    context.user = test_user


def setup_amazon(context):
    if ('AMAZON_CONTAINER_NAME' in os.environ and
            'AMAZON_ACCESS_KEY_ID' in os.environ and
            'AMAZON_SECRET_ACCESS_KEY' in os.environ):
        context.app.config['AMAZON_CONTAINER_NAME'] = os.environ.get('AMAZON_CONTAINER_NAME')
        context.app.config['AMAZON_ACCESS_KEY_ID'] = os.environ.get('AMAZON_ACCESS_KEY_ID')
        context.app.config['AMAZON_SECRET_ACCESS_KEY'] = os.environ.get('AMAZON_SECRET_ACCESS_KEY')
        context.app.config['AMAZON_REGION'] = os.environ.get('AMAZON_REGION')
    else:
        setup_auth_user(context)


class TestCase(unittest.TestCase):

    def setUp(self):
        setup(self)

    def get_fixture_path(self, filename):
        rootpath = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        return os.path.join(rootpath, 'features', 'steps', 'fixtures', filename)
