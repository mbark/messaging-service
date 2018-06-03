import logging
import colorlog

from msgr.app import create
from msgr.db import DbClient

app = create(DbClient())


def _configure_logging():
    log = logging.getLogger('msgr')

    handler = colorlog.StreamHandler()
    formatter = colorlog.ColoredFormatter(
        fmt=('%(log_color)s[%(asctime)s %(levelname)8s] --'
             ' %(message)s (%(filename)s:%(lineno)s)'),
        datefmt='%Y-%m-%d %H:%M:%S')
    handler.setFormatter(formatter)

    log.addHandler(handler)
    log.setLevel(logging.DEBUG)
