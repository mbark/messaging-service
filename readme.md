# msgr
Messaging via REST.

## Structure
- `main.py` create the app;
- `msgr`
  - `app.py` manages the REST-server;
  - `db.py` communicates with the database.
- `tests`
  - `test_integration.py` starts a real redis instance to test integration;
  - `test_app.py` tests with a mocked database.
- `docker-compose.yml` configuration for `redis` via `Docker`;
- `restclient.http` can be used in `Emacs` with
  [`restclient.el`](https://github.com/pashky/restclient.el) for testing.

## Quick start
Dependencies are managed with `pipenv`, if you don't have it installed see
[their installation instructions](https://github.com/pypa/pipenv#installation).

Start redis:
``` shell
$ docker-compose up
```

And in another window start the application:
``` shell
$ pipenv install --dev  # install all dependencies (including dev)
$ pipenv shell          # activate a shell in the virtualenv
$ gunicorn main:app     # start the application for local development
# curl the service to verify it works
$ curl http://localhost:8000/messages/some@queue.com
[]
```

## Testing via a simple CLI
There is a very simple CLI program called `cli_msgr` in the project that allows
testing the app. Below is a short example of how the programs can be used. For
more information on the API, [see below](#api).

*NOTE:* since the `uuid`:s are generated randomly when doing a `DELETE` you need
to copy your own output of the `POST`.

### GET range
Call `get_range` with two parameters: `start` and `end` to read a range of
messages idenfitied by their indexes.
``` shell
$ ./cli_msgr get_range 0 1
HTTP/1.1 200 OK
Server: gunicorn/19.8.1
Date: Sun, 03 Jun 2018 13:22:22 GMT
Connection: close
content-type: application/json; charset=UTF-8
content-length: 2

[]
```

### GET unread
Call `get_unread` without any parameters to get all messages since you last
called `get_unread`.
``` shell
$ ./cli_msgr get_unread
HTTP/1.1 200 OK
Server: gunicorn/19.8.1
Date: Sun, 03 Jun 2018 13:22:50 GMT
Connection: close
content-type: application/json; charset=UTF-8
content-length: 2

[]
```

### POST
Call `post` with one parameter, which should be a valid `JSON` object.
``` shell
$ ./cli_msgr post '{"foo":"bar"}'
HTTP/1.1 201 Created
Server: gunicorn/19.8.1
Date: Sun, 03 Jun 2018 13:23:37 GMT
Connection: close
content-type: application/json; charset=UTF-8
content-length: 72

{"uuid": "6835d064-f8ae-414b-9caa-7e63b826d7ca", "data": {"foo": "bar"}}
```

### DELETE
Call `delete` with one parameter which should be a list of previously saved
messages. To create such a list: `POST`, copy the returned `json`, wrap it in an
array (`[]`) and single quotes.
``` shell
$ ./cli_msgr delete '[{"uuid": "6835d064-f8ae-414b-9caa-7e63b826d7ca", "data": {"foo": "bar"}}]'
HTTP/1.1 200 OK
Server: gunicorn/19.8.1
Date: Sun, 03 Jun 2018 13:27:14 GMT
Connection: close
content-type: application/json; charset=UTF-8
content-length: 14

{"removed": 1}
```

## API
All messages are assumed to be valid `json` and all responses will be `json`.
Messages are stored in the format: `{ "uuid": "UUID", "data": {} }` where `uuid`
is generated for each new message and `data` contains the actual message.

There is one endpoint: `/message/{id}`, which can be managed via `GET`, `POST`
and `DELETE`:
- `GET`: can be used in three ways:
    - with the query parameter `start` which indicates the index from where to
    return all messages till the end;
    - with both `start` and `end` which return the messages from `start` to
      `end` (inclusively);
    - with no query parameters which returns all new messages since last time.
- `POST`: posts the message given in the body and returns what was created;
- `DELETE`: deletes the given messages by value (i.e. you must give the entire
  stored message with `uuid` and all).

## Testing
`pytest` is used to run tests. All tests can be found in the `tests` directory.

- `python -m pytest` run all tests;
- `python -m pytest --cov=msgr` run all tests and show coverage;
- `python -m pytest -m "not integration" --cov` run all non-integration tests;

*NOTE:* when running integration tests be sure to stop `redis` with
`docker-compose down` as it is controlled by `pytest` as a fixture.

## Design choices
A brief overview of some design choices and motivation.

### Database
Redis is used as the database to store messages. This allows high performance in
terms of pushing new messages and reading messages that are fairly recent. It
is also if necessary capable of clustering.

### Storing messages
Messages are converted to `msgpack` internally to provide more efficient
storage, especially so since all messages are `json` themselves.

New messages are stored in two lists: `full` and `unread`, where `full` contains
all message over time and `unread` is just the messages since we last read. When
performing a `remove` this means the value is removed from both lists.

Storing the messages in two lists means that data is stored twice, which should
however not be a problem given that messages are stored in a compact fashion
thanks to `msgpack` and the `unread` list should be cleared fairly often.
