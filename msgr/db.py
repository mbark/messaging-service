import redis
import logging
import hashlib


log = logging.getLogger('msgr')


class DbClient():
    def __init__(self, client=None):
        if client == None:
            self.redis = redis.StrictRedis(host='localhost', port=6379, db=0)
        else:
            self.redis = client

    def add(self, key, value):
        (unread, full) = self._keys(key)
        pipe = self.redis.pipeline()
        pipe.rpush(unread, value)
        pipe.rpush(full, value)

        return pipe.execute()

    def get(self, key, start, stop):
        (_, full) = self._keys(key)
        return self.redis.lrange(full, start, stop)

    def remove(self, key, elements):
        (unread, full) = self._keys(key)
        pipe = self.redis.pipeline()
        for el in elements:
            log.debug("removing %s", el)
            pipe.lrem(unread, 0, el)
            pipe.lrem(full, 0, el)

        return pipe.execute()

    def since_last(self, key):
        (unread, _) = self._keys(key)

        pipe = self.redis.pipeline()
        pipe.lrange(unread, 0, -1)
        pipe.delete(unread)

        output = pipe.execute()
        return output[0]

    def _keys(self, key):
        return (self._key(key, 'unread'), self._key(key, 'full'))

    def _key(self, key, temperature):
        name = '%s:%s' % (key, temperature)
        return hashlib.sha512(name.encode('utf-8')).digest()
