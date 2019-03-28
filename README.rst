[![FOSSA Status](https://app.fossa.io/api/projects/git%2Bgithub.com%2Falexshpilkin%2Fsimplejsonseq.svg?type=shield)](https://app.fossa.io/projects/git%2Bgithub.com%2Falexshpilkin%2Fsimplejsonseq?ref=badge_shield)

Encoder and decoder for JSON text sequences
===========================================

``simplejsonseq`` is a simple encoder and decoder for `RFC 7464`_ JSON
text sequences with an API mirroring that of json and simplejson.  A
JSON text sequence is a collection of JSON items in a text file, with
each item preceded by an ASCII record separator (^^, U+1E) and usually
followed by a line feed (^J, U+0A).

.. The following examples will not pass doctest in Python < 3.5 (wrong
   StringIO in < 3, no JSONDecodeError in < 3.5).

To convert a file to an iterable or to write out an iterable into a file,
use the ``dump()`` and ``load()`` functions, similar to the json module:

>>> import io, simplejsonseq  # In Python < 3, use cStringIO not io
>>> s = io.StringIO()
>>> simplejsonseq.dump(['hello', 'world'], s, buffered=False)
>>> s.getvalue()
'\x1e"hello"\n\x1e"world"\n'
>>> for e in simplejsonseq.load(io.StringIO('\x1e"hello"\n\x1e"world"\n')):
...     print(e)
...
hello
world

The ``buffered=False`` setting flushes every item to storage as soon as
it is written instead of doing it only once at the end of ``dump()``.

By default, the reader accepts unparseable items and wraps them into
``InvalidJSON`` objects, but the writer refuses to write these.  Use the
``strict`` argument of either ``load`` and ``dump`` or ``JSONSeqReader``
and ``JSONSeqWriter`` to tune this behaviour, but bear in mind that the
RFC recommends recovering from invalid input items:

>>> import sys; sys.stderr = sys.stdout  # placate doctest
>>> import io, simplejsonseq  # In Python < 3, use cStringIO not io
>>> value = '\x1e{"parrot":\n'
>>> items = list(simplejsonseq.load(value))  # doctest: +ELLIPSIS
/...: InvalidJSONWarning: Read invalid JSON: '{"parrot":\n'
  ...
>>> items
[InvalidJSON('{"parrot":\n', JSONDecodeError('Expecting value: line 2 column 1 (char 11)'))]
>>> list(simplejsonseq.load(value, strict=True))
Traceback (most recent call last):
  ...
json.decoder.JSONDecodeError: Expecting value: line 2 column 1 (char 11)
>>> s = io.StringIO()
>>> simplejsonseq.dump(items, s)
Traceback (most recent call last):
  ...
TypeError: Object of type InvalidJSON is not JSON serializable
>>> s = io.StringIO()
>>> simplejsonseq.dump(items, s, strict=False)  # doctest:+ELLIPSIS
/...: InvalidJSONWarning: Wrote invalid JSON: '{"parrot":\n'
  ...
>>> s.getvalue() == value
True

For more sophisticated processing, use ``JSONSeqReader`` and
``JSONSeqWriter``.  These can also function as context managers to close
the underlying file, if necessary:

>>> from simplejsonseq import JSONSeqReader, JSONSeqWriter
>>> test = ['hello', 'world']
>>> with JSONSeqWriter(open("/tmp/test.jsonseq", 'w'),
...                    buffered=False) as w:
...     w.write(test[0])
...     w.write(test[1])
...
>>> with JSONSeqReader(open("/tmp/test.jsonseq", 'r')) as r:
...     print(list(r) == test)
...
True

In addition to passing ``buffered=False`` to the constructor of
``JSONSeqWriter``, it is also possible to flush unwritten data
explicitly using the ``flush()`` method, or to pass ``flush=True`` to an
individual ``write()`` call to flush all data at the end of the call.
It's pointless to do either with a writer constructed with
``buffered=False``, of course, as it flushes after every entry anyway.

Both the functions and the class constructors pass all extra keyword
arguments to the underlying ``JSONDecoder`` or ``JSONEncoder``.  This
can be used, for example, to dump the entries in a more readable (but
still valid!) format:

>>> import io, simplejsonseq  # In Python < 3, use cStringIO not io
>>> value = [True, {'holy': 'grenade', 'killer': 'bunny'}]
>>> s = io.StringIO()
>>> simplejsonseq.dump(value, s, indent=2)
>>> print(s.getvalue().replace('\x1e', '!'), end='')
!true
!{
  "holy": "grenade",
  "killer": "bunny"
}
>>> list(simplejsonseq.load(s.getvalue())) == value
True

Detailed documentation is available in the docstrings.

.. _RFC 7464: https://tools.ietf.org/html/rfc7464


## License
[![FOSSA Status](https://app.fossa.io/api/projects/git%2Bgithub.com%2Falexshpilkin%2Fsimplejsonseq.svg?type=large)](https://app.fossa.io/projects/git%2Bgithub.com%2Falexshpilkin%2Fsimplejsonseq?ref=badge_large)