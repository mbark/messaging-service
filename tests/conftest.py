import os

import pytest
import redis
from falcon import testing

from msgr.app import create
from msgr.db import DbClient


def is_responsive(client):
    try:
        return client.ping()
    except redis.ConnectionError:
        return False


@pytest.fixture(scope='session')
def redis_client(docker_ip, docker_services):
    """A fixture that starts a real redis instance via docker-compose."""
    client = redis.StrictRedis(host='localhost', port=6379, db=0)
    docker_services.wait_until_responsive(
        timeout=30.0, pause=0.1,
        check=lambda: is_responsive(client)
    )
    return client


@pytest.fixture(scope='session')
def docker_compose_file(pytestconfig):
    return os.path.join(
        str(pytestconfig.rootdir),
        'docker-compose.yml'
    )


@pytest.fixture(scope='function')
def client(redis_client, request):
    def cleanup():
        """Remove everything from redis to ensure a clean slate between tests."""
        redis_client.flushall()

    request.addfinalizer(cleanup)
    return testing.TestClient(create(DbClient(client=redis_client)))


class MockDb():
    def __init__(self):
        pass

    def add(self, key, value):
        return True

    def get_range(self, key, start, stop):
        return []

    def get_unread(self, key):
        return []

    def remove(self, key, elements):
        return [0, 0]
