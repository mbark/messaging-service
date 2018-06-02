import falcon
import logging
import colorlog
import uuid
import json
import msgpack

from .db import DbClient

log = logging.getLogger('msgr')

handler = colorlog.StreamHandler()
formatter = colorlog.ColoredFormatter(
    fmt=('%(log_color)s[%(asctime)s %(levelname)8s] --'
         ' %(message)s (%(filename)s:%(lineno)s)'),
    datefmt='%Y-%m-%d %H:%M:%S')
handler.setFormatter(formatter)

log.addHandler(handler)
log.setLevel(logging.DEBUG)


"""A resource representing a message queue"""
class MessageResource(object):
    def __init__(self, redis_client):
        self.redis = redis_client

    def on_get(self, req, resp, id):
        """Get all messages for the given id"""
        start = req.get_param_as_int('start')
        end = req.get_param_as_int('end')

        messages = []
        if start != None:
            if end == None:
                log.debug("start without end, assuming end=-1")
                end = -1

            log.debug('fetching message range [id: %s, start: %s, end: %s]' % (
                id, start, end))
            messages = self.redis.get(id, start, end)
        else:
            log.debug('fetching messages since last read [id: %s]' % id)
            messages = self.redis.since_last(id)

        messages = [msgpack.unpackb(msg, raw=False) for msg in messages]
        log.info("messages: %s", messages)
        resp.status = falcon.HTTP_200
        resp.body = json.dumps(messages)

    def on_post(self, req, resp, id):
        """Push a new message to the given id"""
        body = req.stream.read(req.content_length or 0).decode('utf-8')
        data = json.loads(body)
        msg = {'uuid': str(uuid.uuid4()), 'data': data}
        success = self.redis.add(id, msgpack.packb(msg, use_bin_type=True))

        if success:
            log.debug('added to list [id: %s, message: %s]' % (id, data))
            resp.status = falcon.HTTP_201
            resp.body = json.dumps(msg)
        else:
            log.debug('failed to add [id: %s, message: %s]' % (id, data))
            resp.status = falcon.HTTP_500

    def on_delete(self, req, resp, id):
        """Delete the given messages from the queue identified by the id"""
        body = req.stream.read(req.content_length or 0).decode('utf-8')
        data = json.loads(body)
        messages = [msgpack.packb(msg, use_bin_type=True) for msg in data]

        log.debug('removing messages: %s [id: %s]' % (data, id))
        removed = self.redis.remove(id, messages)
        log.info("removed %s messages [id: %s]" % (removed, id))

        resp.status = falcon.HTTP_200
        resp.body = json.dumps({ 'removed': max(removed) })


def create(redis_client): 
    """Create a falcon app using the given redis_client"""
    app = falcon.API()
    messages = MessageResource(redis_client)
    app.add_route('/messages/{id}', messages)

    return app
