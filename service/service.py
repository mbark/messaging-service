import falcon
import logging
import colorlog

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

    def on_get(self, req, resp):
        """Get all messages for the given id"""
        resp.status = falcon.HTTP_200
        id = req.get_param('id')
        start = req.get_param_as_int('start')
        stop = req.get_param_as_int('stop')
        
        if start != None and stop != None:
            log.debug('fetching message range [id: %s, start: %s, stop: %s]' % (
                id, start, stop))
            resp.body = '%s' % self.redis.get(id, start, stop)
        else:
            log.debug('fetching messages since last read [id: %s]' % id)
            resp.body = '%s' % self.redis.since_last(id)

    def on_post(self, req, resp):
        """Push a new message to the given id"""
        id = req.get_param('id')
        message = req.get_param('message')
        success = self.redis.add(id, message)

        if success:
            log.debug('added to list [id: %s, message: %s]' % (id, message))
            resp.status = falcon.HTTP_201
        else:
            log.debug('failed to add [id: %s, message: %s]' % (id, message))
            resp.status = falcon.HTTP_500

    def on_delete(self, req, resp):
        """Delete a number of messages for the given id and index(es)"""
        id = req.get_param('id')
        index = req.get_param_as_list('index')

        for idx in index:
            log.debug('removing message [id: %s, index: %s]' % (id, idx))
            self.redis.remove(id, idx)


app = falcon.API()
messages = MessageResource()
app.add_route('/messages', messages)
