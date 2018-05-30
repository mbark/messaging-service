import redis


class DbClient():
    def __init__(self):
        self.redis = redis.StrictRedis(host='localhost', port=6379, db=0)

    def add(self, key, value):
        return self.redis.rpush(key, value)

    def get(self, key, start, stop):
        return self.redis.lrange(key, start, stop)

    def remove(self, key, index):
        with self.redis.pipeline() as pipe:
            pipe.lset(key, index, "DELETED").lrem(key, 1, "DELETED").execute()

    def since_last(self, key):
        pos_key = '%s-pos' % key
        messages = []

        with self.redis.pipeline() as pipe:
            while 1:
                try:
                    pipe.watch(pos_key)

                    position = pipe.get(pos_key)
                    if position == None:
                        position = 0

                    messages = pipe.lrange(key, position, -1)
                    new_position = pipe.llen(key)

                    pipe.multi()
                    pipe.set(pos_key, new_position)
                    pipe.execute()
                    break
                except redis.WatchError:
                    # another client must have changed 'OUR-SEQUENCE-KEY' between
                    # the time we started WATCHing it and the pipeline's execution.
                    # our best bet is to just retry.
                    continue

        return messages
