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


class MessageResource(object):
    def __init__(self):
        self.redis = DbClient()

    def on_get(self, req, resp, id):
        """Get all messages for the given id"""
        resp.status = falcon.HTTP_200
        start = req.get_param_as_int('start')
        stop = req.get_param_as_int('stop')

        messages = []
        if start != None:
            if stop == None:
                log.debug("start without stop, assuming stop=-1")
                stop = -1

            log.debug('fetching message range [id: %s, start: %s, stop: %s]' % (
                id, start, stop))
            messages = self.redis.get(id, start, stop)
        else:
            log.debug('fetching messages since last read [id: %s]' % id)
            messages = self.redis.since_last(id)

        messages = [msgpack.unpackb(msg, raw=False) for msg in messages]
        log.info("messages: %s", messages)
        resp.body = json.dumps(messages)

    def on_post(self, req, resp, id):
        """Push a new message to the given id"""
        body = req.stream.read(req.content_length or 0).decode('utf-8')
        data = json.loads(body)
        msg = msgpack.packb({'uuid': str(uuid.uuid4()), 'data': data}, use_bin_type=True)
        success = self.redis.add(id, msg)

        if success:
            log.debug('added to list [id: %s, message: %s]' % (id, data))
            resp.status = falcon.HTTP_201
        else:
            log.debug('failed to add [id: %s, message: %s]' % (id, data))
            resp.status = falcon.HTTP_500

    def on_delete(self, req, resp, id):
        """Delete a number of messages for the given id and index(es)"""
        body = req.stream.read(req.content_length or 0).decode('utf-8')
        data = json.loads(body)
        messages = [msgpack.packb(msg, use_bin_type=True) for msg in data]

        log.debug('removing messages: %s [id: %s]' % (messages, id))
        removed = self.redis.remove(id, messages)
        log.info("removed %s messages [id: %s]" % (removed, id))


app = falcon.API()
messages = MessageResource()
app.add_route('/messages/{id}', messages)
