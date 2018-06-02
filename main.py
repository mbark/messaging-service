from msgr.app import create
from msgr.db import DbClient

app = create(DbClient())
