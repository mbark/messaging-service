import redis
import hashlib


class DbClient():
    """A client to connect and talk to the database."""
    def __init__(self, client=None):
        if client == None:
            self.redis = redis.StrictRedis(host='localhost', port=6379, db=0)
        else:
            self.redis = client

    def add(self, key, value):
        """Add the given value to the list identified by the key."""
        (unread, full) = self._keys(key)
        pipe = self.redis.pipeline()
        pipe.rpush(unread, value)
        pipe.rpush(full, value)

        return pipe.execute()

    def get_range(self, key, start, stop):
        """Get the range of values from the list identified by the key."""
        (_, full) = self._keys(key)
        return self.redis.lrange(full, start, stop)

    def get_unread(self, key):
        """Get all unread messages from the list identified by the key."""
        (unread, _) = self._keys(key)

        pipe = self.redis.pipeline()
        pipe.lrange(unread, 0, -1)
        pipe.delete(unread)

        output = pipe.execute()
        return output[0]

    def remove(self, key, elements):
        """Remove the specified elements from the list identified by the key."""
        (unread, full) = self._keys(key)
        pipe = self.redis.pipeline()
        for el in elements:
            pipe.lrem(unread, 0, el)
            pipe.lrem(full, 0, el)

        return pipe.execute()

    def _keys(self, key):
        return (self._key(key, 'unread'), self._key(key, 'full'))

    def _key(self, key, temperature):
        name = '%s:%s' % (key, temperature)
        # we use sha512 to be sure to avoid collisions for keys
        return hashlib.sha512(name.encode('utf-8')).digest()
