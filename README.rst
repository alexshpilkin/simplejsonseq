Simple codec for JSON text sequences
====================================

simplejsonseq is a simple encoder and decoder for JSON text sequences
(`RFC 7464`_) with API mirroring that of json and simplejson. Currently
it only provides two functions, ``dump()`` and ``load()``, that convert
between a file-like object containing a JSON text sequence and an
iterable. Detailed documentation is available in the docstrings.

.. _RFC 7464: https://tools.ietf.org/html/rfc7464
