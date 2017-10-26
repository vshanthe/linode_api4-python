import json
from unittest import TestCase
from unittest.mock import patch
import requests
import json
import sys

from linode import LinodeClient

class MockResponse:
    def __init__(self, status_code, json):
        self.status_code = status_code
        self._json = json

    def json(self):
        return self._json


def load_json(url):
    """
    Returns a dict from a .json file living in /test/response/GET/{url}.json

    :param url: The URL being accessed whose JSON is to be returned

    :returns: A dict containing the loaded JSON from that file
    """
    formatted_url = url

    while formatted_url.startswith('/'):
        formatted_url = formatted_url[1:]

    formatted_url = formatted_url.replace('/', '_')

    file_path = sys.path[0] + '/responses/GET/' + formatted_url + '.json'

    with open(file_path) as f:
        response = f.read()

    return json.loads(response)


def mock_get(url, headers=None, data=None):
    """
    Loads the response from a JSON file
    """
    response = load_json(url)

    return MockResponse(200, response)


class MethodMock:
    """
    This class is used to mock methods on requests and store the parameters
    and headers it was called with.
    """
    def __init__(self, method, return_dct):
        """
        Creates and initiates a new MethodMock with the given details

        :param method: The HTTP method we are mocking
        :param return_dct: The python dct to returned, or the URL for a JSON
            file to return
        """
        self.method = method
        if isinstance(return_dct, dict):
            self.return_dct = return_dct
        elif isinstance(return_dct, str):
            self.return_dct = load_json(return_dct)
        else:
            raise TypeError('return_dct must be a dict or a URL from which the '
                            'JSON could be loaded')

    def __enter__(self):
        """
        Begins the method mocking
        """
        self.mock = patch(
            'linode.linode_client.requests.'+self.method,
            return_value=MockResponse(200, self.return_dct)
        )
        self.mock.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Removed the mocked method
        """
        self.mock.stop()

    @property
    def call_args(self):
        # TODO - these don't work :(
        """
        A shortcut to accessing the underlying mock object's call args
        """
        return self.mock.call_args

    @property
    def call_data(self):
        """
        A shortcut to getting the data param this was called with
        """
        return self.mock.call_args[1]['data']

    @property
    def call_headers(self):
        """
        A shortcut to getting the headers param this was called with
        """
        return self.mock.call_args[1]['headers']


class ClientBaseCase(TestCase):
    def setUp(self):
        self.client = LinodeClient('testing', base_url='/')

        self.get_patch = patch('linode.linode_client.requests.get',
                side_effect=mock_get)
        self.get_patch.start()

    def tearDown(self):
        self.get_patch.stop()

    def mock_post(self, return_dct):
        """
        Returns a MethodMock mocking a POST.  This should be used in a with
        statement.

        :param return_dct: The JSON that should be returned from this POST

        :returns
        """
        return MethodMock('post', return_dct)
