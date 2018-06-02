from service.service import create
from service.db import DbClient

app = create(DbClient())
