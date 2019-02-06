Changes
=======

0.2.0 (2019-02-06)
------------------

Format changes
~~~~~~~~~~~~~~
* Detect truncated items on reading as required by the RFC.

Interface changes
~~~~~~~~~~~~~~~~~
* Make single-item reading errors non-fatal and roundtrip invalid items
  using the ``InvalidJSON`` wrapper.  Writing disallows invalid items by
  default, but reading allows them, as recommended by the RFC.
* Move reading and writing into ``JSONSeqReader`` and ``JSONSeqWriter``,
  which also become context managers.  Make it invalid to call ``dump()``
  several times (a ``JSONSeqWrter`` should be created instead, or a
  ``JSONSeqEncoder`` should be used directly).
* Move decoding and encoding into ``JSONSeqDecoder`` and
  ``JSONSeqEncoder``.
* Support passing either a constructed JSON codec or a codec constructor
  and arguments.

Code changes
~~~~~~~~~~~~
* Add comprehensive tests.

0.1.0 (2018-09-23)
------------------

* Initial release.
