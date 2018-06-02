import json
import pytest

pytestmark = pytest.mark.integration


def post_msg(client, msg={'foo': 'bar'}):
    endpoint = '/messages/1'
    result = client.simulate_post(endpoint, body=json.dumps(msg))
    return endpoint, json.loads(result.text)


def test_get_with_no_messages(client):
    result = client.simulate_get('/messages/1')
    assert result.json == []


def test_post_creates_message(client):
    result = client.simulate_post('/messages/1', body=json.dumps({}))
    assert result.status_code == 201


def test_post_and_get(client):
    msg = {'foo': 'bar'}

    endpoint, _ = post_msg(client, msg)
    result = client.simulate_get(endpoint)

    assert result.status_code == 200
    response = json.loads(result.text)
    assert len(response) == 1
    assert response[0]['uuid']
    assert response[0]['data'] == msg


def test_post_and_delete(client):
    endpoint, msg = post_msg(client)
    result = client.simulate_delete(endpoint, body=json.dumps([msg]))

    assert result.status_code == 200
    assert json.loads(result.text)['removed'] == 1


def test_post_delete_get(client):
    endpoint, msg = post_msg(client)
    client.simulate_delete(endpoint, body=json.dumps([msg]))
    result = client.simulate_get(endpoint)

    assert result.status_code == 200
    response = json.loads(result.text)
    assert len(response) == 0


def test_get_since_last(client):
    endpoint, _ = post_msg(client)

    result1 = client.simulate_get(endpoint)
    result2 = client.simulate_get(endpoint)

    assert result1.status_code == 200
    assert len(json.loads(result1.text)) == 1
    assert result2.status_code == 200
    assert len(json.loads(result2.text)) == 0


def test_get_range(client):
    endpoint, _ = post_msg(client)
    post_msg(client)
    post_msg(client)

    result = client.simulate_get(endpoint, params={'start': 0, 'end': 1})

    assert result.status_code == 200
    assert len(json.loads(result.text)) == 2


def test_get_range_without_end(client):
    endpoint, _ = post_msg(client)
    post_msg(client)

    result = client.simulate_get(endpoint, params={'start': 0})

    assert result.status_code == 200
    assert len(json.loads(result.text)) == 2


def test_get_range_with_too_large_start(client):
    endpoint, _ = post_msg(client)

    result = client.simulate_get(endpoint, params={'start': 4})

    assert result.status_code == 200
    assert len(json.loads(result.text)) == 0


def test_remove_unread_message(client):
    endpoint, msg1 = post_msg(client)
    endpoint, msg2 = post_msg(client, msg={'bar': 'foo'})

    client.simulate_delete(endpoint, body=json.dumps([msg1]))
    result = client.simulate_get(endpoint)
    response = json.loads(result.text)

    assert result.status_code == 200
    assert len(response) == 1
    assert response[0] == msg2