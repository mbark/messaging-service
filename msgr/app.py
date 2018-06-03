import logging
import uuid
import msgpack
import falcon

from .db import DbClient

log = logging.getLogger('msgr')


class MessageResource(object):
    """A resource representing message queues that are identified by a given key."""

    def __init__(self, redis_client):
        self.redis = redis_client

    def on_get(self, req, resp, key):
        """Get either a range of messages or the last unread messages."""
        start = req.get_param_as_int('start')
        end = req.get_param_as_int('end')

        messages = self._get_messages(key, start, end) 
        resp.status = falcon.HTTP_200
        resp.media = self._unpack_all(messages)

    def on_post(self, req, resp, key):
        """Push a new message to the queue."""
        msg = {'uuid': str(uuid.uuid4()), 'data': req.media}
        success = self.redis.add(key, self._pack(msg))

        if success:
            log.debug('added: %s [key: %s]' % (msg, key))
            resp.status = falcon.HTTP_201
            resp.media = msg
        else:
            log.debug('failed to add: %s [key: %s]' % (msg, key))
            resp.status = falcon.HTTP_500

    def on_delete(self, req, resp, key):
        """Delete the given messages from the queue."""
        messages = req.media

        log.debug('removing messages: %s [key: %s]' % (messages, key))
        removed = self.redis.remove(key, self._pack_all(messages))
        log.debug("removed %s messages [key: %s]" % (removed, key))

        remove_count = 0 if len(removed) == 0 else max(removed)

        resp.status = falcon.HTTP_200
        resp.media = {'removed': remove_count}

    def _get_messages(self, key, start, end):
        messages = []
        if start != None:
            if end == None:
                log.debug("start without end, assuming end=-1")
                end = -1

            log.debug('fetching messages in range [%d, %d] [key: %s]' % (
                start, end, key))
            messages = self.redis.get_range(key, start, end)
        else:
            log.debug('fetching unread [key: %s]' % key)
            messages = self.redis.get_unread(key)

        return messages

    def _pack(self, message):
        return msgpack.packb(message, use_bin_type=True)

    def _pack_all(self, messages):
        return [self._pack(msg) for msg in messages] 

    def _unpack_all(self, messages):
        return [msgpack.unpackb(msg, raw=False) for msg in messages]


def create(redis_client):
    """Create a falcon app using the given redis_client""" 
    app = falcon.API()

    messages = MessageResource(redis_client)
    app.add_route('/messages/{key}', messages)

    return app
