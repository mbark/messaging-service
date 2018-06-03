import json

import pytest
import msgpack
from falcon import testing

from conftest import MockDb
from msgr.app import create


def test_post_adds_message_with_uuid(mocker):
    mockdb = MockDb()
    spy = mocker.spy(mockdb, 'add')
    client = testing.TestClient(create(mockdb))

    client.simulate_post('/messages/1', body=json.dumps({'foo': 'bar'}))
    (id, data) = spy.call_args[0]

    assert spy.call_count == 1
    assert id == '1'
    assert msgpack.unpackb(data)[b'uuid']


def test_post_fails_if_add_fails(mocker):
    mockdb = MockDb()
    patch = mocker.patch.object(mockdb, 'add')
    patch.return_value = False
    client = testing.TestClient(create(mockdb))

    result = client.simulate_post(
        '/messages/1', body=json.dumps({'foo': 'bar'}))

    assert result.status_code == 500
    assert result.text == ''


def mock_get(mocker, mockdb, method):
    patch = mocker.patch.object(mockdb, method)
    messages = [{'uuid': '1', 'data': {}}, {
        'uuid': '2', 'data': [{'foo': 'bar'}]}]
    patch.return_value = [msgpack.packb(msg) for msg in messages]

    return messages


def test_get_with_no_messages(mocker):
    mockdb = MockDb()
    mocker.patch.object(mockdb, 'get_unread')
    client = testing.TestClient(create(mockdb))

    result = client.simulate_get('/messages/1')

    assert result.status_code == 200
    print('text', result.text)
    assert json.loads(result.text) == []


def test_get_unread_returns_stored_messages(mocker):
    mockdb = MockDb()
    messages = mock_get(mocker, mockdb, 'get_unread')
    client = testing.TestClient(create(mockdb))

    result = client.simulate_get('/messages/1')

    assert result.status_code == 200
    assert json.loads(result.text) == messages


def test_get_returns_stored_messages(mocker):
    mockdb = MockDb()
    messages = mock_get(mocker, mockdb, 'get_range')
    client = testing.TestClient(create(mockdb))

    result = client.simulate_get(
        '/messages/1', params={'start': '0', 'end': 2})

    assert result.status_code == 200
    assert json.loads(result.text) == messages


def test_get_defaults_with_no_end(mocker):
    mockdb = MockDb()
    spy = mocker.spy(mockdb, 'get_range')
    client = testing.TestClient(create(mockdb))

    client.simulate_get('/messages/1', params={'start': '0'})
    (id, start, end) = spy.call_args[0]

    assert spy.call_count == 1
    assert id == '1'
    assert start == 0
    assert end == -1


def test_delete_returns_max_removed(mocker):
    mockdb = MockDb()
    patch = mocker.patch.object(mockdb, 'remove')
    patch.return_value = [1, 2]
    client = testing.TestClient(create(mockdb))

    result = client.simulate_delete('/messages/1', body=json.dumps([]))

    assert result.status_code == 200
    assert json.loads(result.text) == {'removed': 2}


def test_delete_packs_messages(mocker):
    mockdb = MockDb()
    spy = mocker.spy(mockdb, 'remove')
    client = testing.TestClient(create(mockdb))
    messages = [{'uuid': '0', 'data': 'foo'}, {'uuid': '3', 'data': {}}]

    client.simulate_delete('/messages/1', body=json.dumps(messages))
    (id, elements) = spy.call_args[0]

    assert spy.call_count == 1
    assert id == '1'
    assert elements == [msgpack.packb(
        msg, use_bin_type=True) for msg in messages]

def test_delete_no_messages(mocker):
    mockdb = MockDb()
    patch = mocker.patch.object(mockdb, 'remove')
    patch.return_value = []
    client = testing.TestClient(create(mockdb))

    result = client.simulate_delete('/messages/1', body=json.dumps([]))

    assert result.status_code == 200
    assert json.loads(result.text) == {'removed': 0}
