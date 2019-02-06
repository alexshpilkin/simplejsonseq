Encoder and decoder for JSON text sequences
===========================================

``simplejsonseq`` is a simple encoder and decoder for `RFC 7464`_ JSON
text sequences with an API mirroring that of json and simplejson.  A
JSON text sequence is a collection of JSON items in a text file, with
each item preceded by an ASCII record separator (^^, U+1E) and usually
followed by a line feed (^J, U+0A).

To convert a file to an iterable or to write out an iterable into a file,
use the ``dump()`` and ``load()`` functions, similar to the json module:

>>> import io, simplejsonseq
>>> s = io.StringIO()
>>> simplejsonseq.dump(['hello', 'world'], s)
>>> s.getvalue()
'\x1e"hello"\n\x1e"world"\n'
>>> for e in simplejsonseq.load(io.StringIO('\x1e"hello"\n\x1e"world"\n')):
...     print(e)
...
hello
world

For more sophisticated processing, use ``JSONSeqReader`` and
``JSONSeqWriter``.  These can also function as context managers to close
the underlying file, if necessary:

>>> from simplejsonseq import JSONSeqReader, JSONSeqWriter
>>> test = ['hello', 'world']
>>> with JSONSeqWriter(open("/tmp/test.jsonseq", 'w')) as w:
...     w.write(test[0])
...     w.write(test[1])
... 
>>> with JSONSeqReader(open("/tmp/test.jsonseq", 'r')) as r:
...     print(list(r) == test)
... 
True

By default, the reader accepts unparseable items and wraps them into
``InvalidJSON`` objects, but the writer refuses to write these.  Use the
``strict`` argument of either ``load`` and ``dump`` or ``JSONSeqReader``
and ``JSONSeqWriter`` to tune this behaviour, but bear in mind that the
RFC recommends recovering from invalid input items:

>>> import io, simplejsonseq
>>> value = '\x1e{"parrot":\n'
>>> items = list(simplejsonseq.load(value))
__main__:1: InvalidJSONWarning: Read invalid JSON: '{"parrot":\n'
>>> items
[InvalidJSON('{"parrot":\n', JSONDecodeError('Expecting value: line 2 column 1 (char 11)'))]
>>> list(simplejsonseq.load(value, strict=True))
Traceback (most recent call last):
  ...
json.decoder.JSONDecodeError: Expecting value: line 2 column 1 (char 11)
>>> s = io.StringIO(); simplejsonseq.dump(items, s)
Traceback (most recent call last):
  ...
TypeError: Object of type InvalidJSON is not JSON serializable
>>> s = io.StringIO(); simplejsonseq.dump(items, s, strict=False)
  ...
>>> s.getvalue() == value
True

Detailed documentation is available in the docstrings.

.. _RFC 7464: https://tools.ietf.org/html/rfc7464
