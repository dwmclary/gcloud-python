# Copyright 2015 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest


class TestClient(unittest.TestCase):

    def _getTargetClass(self):
        from google.cloud.storage.client import Client
        return Client

    def _makeOne(self, *args, **kw):
        return self._getTargetClass()(*args, **kw)

    def test_ctor_connection_type(self):
        from google.cloud.storage.connection import Connection

        PROJECT = 'PROJECT'
        CREDENTIALS = _Credentials()

        client = self._makeOne(project=PROJECT, credentials=CREDENTIALS)
        self.assertEqual(client.project, PROJECT)
        self.assertIsInstance(client.connection, Connection)
        self.assertIs(client.connection.credentials, CREDENTIALS)
        self.assertIsNone(client.current_batch)
        self.assertEqual(list(client._batch_stack), [])

    def test__push_batch_and__pop_batch(self):
        from google.cloud.storage.batch import Batch

        PROJECT = 'PROJECT'
        CREDENTIALS = _Credentials()

        client = self._makeOne(project=PROJECT, credentials=CREDENTIALS)
        batch1 = Batch(client)
        batch2 = Batch(client)
        client._push_batch(batch1)
        self.assertEqual(list(client._batch_stack), [batch1])
        self.assertIs(client.current_batch, batch1)
        client._push_batch(batch2)
        self.assertIs(client.current_batch, batch2)
        # list(_LocalStack) returns in reverse order.
        self.assertEqual(list(client._batch_stack), [batch2, batch1])
        self.assertIs(client._pop_batch(), batch2)
        self.assertEqual(list(client._batch_stack), [batch1])
        self.assertIs(client._pop_batch(), batch1)
        self.assertEqual(list(client._batch_stack), [])

    def test_connection_setter(self):
        PROJECT = 'PROJECT'
        CREDENTIALS = _Credentials()
        client = self._makeOne(project=PROJECT, credentials=CREDENTIALS)
        client._connection = None  # Unset the value from the constructor
        client.connection = connection = object()
        self.assertIs(client._connection, connection)

    def test_connection_setter_when_set(self):
        PROJECT = 'PROJECT'
        CREDENTIALS = _Credentials()
        client = self._makeOne(project=PROJECT, credentials=CREDENTIALS)
        self.assertRaises(ValueError, setattr, client, 'connection', None)

    def test_connection_getter_no_batch(self):
        PROJECT = 'PROJECT'
        CREDENTIALS = _Credentials()
        client = self._makeOne(project=PROJECT, credentials=CREDENTIALS)
        self.assertIs(client.connection, client._connection)
        self.assertIsNone(client.current_batch)

    def test_connection_getter_with_batch(self):
        from google.cloud.storage.batch import Batch
        PROJECT = 'PROJECT'
        CREDENTIALS = _Credentials()
        client = self._makeOne(project=PROJECT, credentials=CREDENTIALS)
        batch = Batch(client)
        client._push_batch(batch)
        self.assertIsNot(client.connection, client._connection)
        self.assertIs(client.connection, batch)
        self.assertIs(client.current_batch, batch)

    def test_bucket(self):
        from google.cloud.storage.bucket import Bucket

        PROJECT = 'PROJECT'
        CREDENTIALS = _Credentials()
        BUCKET_NAME = 'BUCKET_NAME'

        client = self._makeOne(project=PROJECT, credentials=CREDENTIALS)
        bucket = client.bucket(BUCKET_NAME)
        self.assertIsInstance(bucket, Bucket)
        self.assertIs(bucket.client, client)
        self.assertEqual(bucket.name, BUCKET_NAME)

    def test_batch(self):
        from google.cloud.storage.batch import Batch

        PROJECT = 'PROJECT'
        CREDENTIALS = _Credentials()

        client = self._makeOne(project=PROJECT, credentials=CREDENTIALS)
        batch = client.batch()
        self.assertIsInstance(batch, Batch)
        self.assertIs(batch._client, client)

    def test_get_bucket_miss(self):
        from google.cloud.exceptions import NotFound

        PROJECT = 'PROJECT'
        CREDENTIALS = _Credentials()
        client = self._makeOne(project=PROJECT, credentials=CREDENTIALS)

        NONESUCH = 'nonesuch'
        URI = '/'.join([
            client.connection.API_BASE_URL,
            'storage',
            client.connection.API_VERSION,
            'b',
            'nonesuch?projection=noAcl',
        ])
        http = client.connection._http = _Http(
            {'status': '404', 'content-type': 'application/json'},
            b'{}',
        )
        self.assertRaises(NotFound, client.get_bucket, NONESUCH)
        self.assertEqual(http._called_with['method'], 'GET')
        self.assertEqual(http._called_with['uri'], URI)

    def test_get_bucket_hit(self):
        from google.cloud.storage.bucket import Bucket

        PROJECT = 'PROJECT'
        CREDENTIALS = _Credentials()
        client = self._makeOne(project=PROJECT, credentials=CREDENTIALS)

        BLOB_NAME = 'blob-name'
        URI = '/'.join([
            client.connection.API_BASE_URL,
            'storage',
            client.connection.API_VERSION,
            'b',
            '%s?projection=noAcl' % (BLOB_NAME,),
        ])
        http = client.connection._http = _Http(
            {'status': '200', 'content-type': 'application/json'},
            '{{"name": "{0}"}}'.format(BLOB_NAME).encode('utf-8'),
        )

        bucket = client.get_bucket(BLOB_NAME)
        self.assertIsInstance(bucket, Bucket)
        self.assertEqual(bucket.name, BLOB_NAME)
        self.assertEqual(http._called_with['method'], 'GET')
        self.assertEqual(http._called_with['uri'], URI)

    def test_lookup_bucket_miss(self):
        PROJECT = 'PROJECT'
        CREDENTIALS = _Credentials()
        client = self._makeOne(project=PROJECT, credentials=CREDENTIALS)

        NONESUCH = 'nonesuch'
        URI = '/'.join([
            client.connection.API_BASE_URL,
            'storage',
            client.connection.API_VERSION,
            'b',
            'nonesuch?projection=noAcl',
        ])
        http = client.connection._http = _Http(
            {'status': '404', 'content-type': 'application/json'},
            b'{}',
        )
        bucket = client.lookup_bucket(NONESUCH)
        self.assertIsNone(bucket)
        self.assertEqual(http._called_with['method'], 'GET')
        self.assertEqual(http._called_with['uri'], URI)

    def test_lookup_bucket_hit(self):
        from google.cloud.storage.bucket import Bucket

        PROJECT = 'PROJECT'
        CREDENTIALS = _Credentials()
        client = self._makeOne(project=PROJECT, credentials=CREDENTIALS)

        BLOB_NAME = 'blob-name'
        URI = '/'.join([
            client.connection.API_BASE_URL,
            'storage',
            client.connection.API_VERSION,
            'b',
            '%s?projection=noAcl' % (BLOB_NAME,),
        ])
        http = client.connection._http = _Http(
            {'status': '200', 'content-type': 'application/json'},
            '{{"name": "{0}"}}'.format(BLOB_NAME).encode('utf-8'),
        )

        bucket = client.lookup_bucket(BLOB_NAME)
        self.assertIsInstance(bucket, Bucket)
        self.assertEqual(bucket.name, BLOB_NAME)
        self.assertEqual(http._called_with['method'], 'GET')
        self.assertEqual(http._called_with['uri'], URI)

    def test_create_bucket_conflict(self):
        from google.cloud.exceptions import Conflict

        PROJECT = 'PROJECT'
        CREDENTIALS = _Credentials()
        client = self._makeOne(project=PROJECT, credentials=CREDENTIALS)

        BLOB_NAME = 'blob-name'
        URI = '/'.join([
            client.connection.API_BASE_URL,
            'storage',
            client.connection.API_VERSION,
            'b?project=%s' % (PROJECT,),
        ])
        http = client.connection._http = _Http(
            {'status': '409', 'content-type': 'application/json'},
            '{"error": {"message": "Conflict"}}',
        )

        self.assertRaises(Conflict, client.create_bucket, BLOB_NAME)
        self.assertEqual(http._called_with['method'], 'POST')
        self.assertEqual(http._called_with['uri'], URI)

    def test_create_bucket_success(self):
        from google.cloud.storage.bucket import Bucket

        PROJECT = 'PROJECT'
        CREDENTIALS = _Credentials()
        client = self._makeOne(project=PROJECT, credentials=CREDENTIALS)

        BLOB_NAME = 'blob-name'
        URI = '/'.join([
            client.connection.API_BASE_URL,
            'storage',
            client.connection.API_VERSION,
            'b?project=%s' % (PROJECT,),
        ])
        http = client.connection._http = _Http(
            {'status': '200', 'content-type': 'application/json'},
            '{{"name": "{0}"}}'.format(BLOB_NAME).encode('utf-8'),
        )

        bucket = client.create_bucket(BLOB_NAME)
        self.assertIsInstance(bucket, Bucket)
        self.assertEqual(bucket.name, BLOB_NAME)
        self.assertEqual(http._called_with['method'], 'POST')
        self.assertEqual(http._called_with['uri'], URI)

    def test_list_buckets_empty(self):
        from six.moves.urllib.parse import parse_qs
        from six.moves.urllib.parse import urlparse

        PROJECT = 'PROJECT'
        CREDENTIALS = _Credentials()
        client = self._makeOne(project=PROJECT, credentials=CREDENTIALS)

        EXPECTED_QUERY = {
            'project': [PROJECT],
            'projection': ['noAcl'],
        }
        http = client.connection._http = _Http(
            {'status': '200', 'content-type': 'application/json'},
            b'{}',
        )
        buckets = list(client.list_buckets())
        self.assertEqual(len(buckets), 0)
        self.assertEqual(http._called_with['method'], 'GET')
        self.assertIsNone(http._called_with['body'])

        BASE_URI = '/'.join([
            client.connection.API_BASE_URL,
            'storage',
            client.connection.API_VERSION,
            'b',
        ])
        URI = http._called_with['uri']
        self.assertTrue(URI.startswith(BASE_URI))
        uri_parts = urlparse(URI)
        self.assertEqual(parse_qs(uri_parts.query), EXPECTED_QUERY)

    def test_list_buckets_non_empty(self):
        from six.moves.urllib.parse import parse_qs
        from six.moves.urllib.parse import urlencode
        from six.moves.urllib.parse import urlparse
        PROJECT = 'PROJECT'
        CREDENTIALS = _Credentials()
        client = self._makeOne(project=PROJECT, credentials=CREDENTIALS)

        BUCKET_NAME = 'bucket-name'
        query_params = urlencode({'project': PROJECT, 'projection': 'noAcl'})
        BASE_URI = '/'.join([
            client.connection.API_BASE_URL,
            'storage',
            client.connection.API_VERSION,
        ])
        URI = '/'.join([BASE_URI, 'b?%s' % (query_params,)])
        http = client.connection._http = _Http(
            {'status': '200', 'content-type': 'application/json'},
            '{{"items": [{{"name": "{0}"}}]}}'.format(BUCKET_NAME)
            .encode('utf-8'),
        )
        buckets = list(client.list_buckets())
        self.assertEqual(len(buckets), 1)
        self.assertEqual(buckets[0].name, BUCKET_NAME)
        self.assertEqual(http._called_with['method'], 'GET')
        self.assertTrue(http._called_with['uri'].startswith(BASE_URI))
        self.assertEqual(parse_qs(urlparse(http._called_with['uri']).query),
                         parse_qs(urlparse(URI).query))

    def test_list_buckets_all_arguments(self):
        from six.moves.urllib.parse import parse_qs
        from six.moves.urllib.parse import urlparse

        PROJECT = 'foo-bar'
        CREDENTIALS = _Credentials()
        client = self._makeOne(project=PROJECT, credentials=CREDENTIALS)

        MAX_RESULTS = 10
        PAGE_TOKEN = 'ABCD'
        PREFIX = 'subfolder'
        PROJECTION = 'full'
        FIELDS = 'items/id,nextPageToken'
        EXPECTED_QUERY = {
            'project': [PROJECT],
            'maxResults': [str(MAX_RESULTS)],
            'pageToken': [PAGE_TOKEN],
            'prefix': [PREFIX],
            'projection': [PROJECTION],
            'fields': [FIELDS],
        }

        http = client.connection._http = _Http(
            {'status': '200', 'content-type': 'application/json'},
            '{"items": []}',
        )
        iterator = client.list_buckets(
            max_results=MAX_RESULTS,
            page_token=PAGE_TOKEN,
            prefix=PREFIX,
            projection=PROJECTION,
            fields=FIELDS,
        )
        buckets = list(iterator)
        self.assertEqual(buckets, [])
        self.assertEqual(http._called_with['method'], 'GET')
        self.assertIsNone(http._called_with['body'])

        BASE_URI = '/'.join([
            client.connection.API_BASE_URL,
            'storage',
            client.connection.API_VERSION,
            'b'
        ])
        URI = http._called_with['uri']
        self.assertTrue(URI.startswith(BASE_URI))
        uri_parts = urlparse(URI)
        self.assertEqual(parse_qs(uri_parts.query), EXPECTED_QUERY)


class Test__BucketPage(unittest.TestCase):

    def _getTargetClass(self):
        from google.cloud.storage.client import _BucketPage
        return _BucketPage

    def _makeOne(self, *args, **kw):
        return self._getTargetClass()(*args, **kw)

    def test_empty_response(self):
        from google.cloud.storage.client import _BucketIterator

        connection = object()
        client = _Client(connection)
        iterator = _BucketIterator(client)
        page = self._makeOne(iterator, {})
        self.assertEqual(list(page), [])

    def test_non_empty_response(self):
        from google.cloud.storage.bucket import Bucket
        from google.cloud.storage.client import _BucketIterator

        BLOB_NAME = 'blob-name'
        response = {'items': [{'name': BLOB_NAME}]}
        connection = object()
        client = _Client(connection)
        iterator = _BucketIterator(client)
        page = self._makeOne(iterator, response)
        self.assertEqual(page.num_items, 1)
        bucket = page.next()
        self.assertEqual(page.remaining, 0)
        self.assertIsInstance(bucket, Bucket)
        self.assertEqual(bucket.name, BLOB_NAME)


class Test__BucketIterator(unittest.TestCase):

    def _getTargetClass(self):
        from google.cloud.storage.client import _BucketIterator
        return _BucketIterator

    def _makeOne(self, *args, **kw):
        return self._getTargetClass()(*args, **kw)

    def test_ctor(self):
        connection = object()
        client = _Client(connection)
        iterator = self._makeOne(client)
        self.assertEqual(iterator.path, '/b')
        self.assertEqual(iterator.page_number, 0)
        self.assertIsNone(iterator.next_page_token)
        self.assertIs(iterator.client, client)


class _Credentials(object):

    _scopes = None

    @staticmethod
    def create_scoped_required():
        return True

    def create_scoped(self, scope):
        self._scopes = scope
        return self


class _Http(object):

    _called_with = None

    def __init__(self, headers, content):
        from httplib2 import Response
        self._response = Response(headers)
        self._content = content

    def request(self, **kw):
        self._called_with = kw
        return self._response, self._content


class _Client(object):

    def __init__(self, connection):
        self.connection = connection
