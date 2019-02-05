from __future__ import unicode_literals

"""Simple codec for JSON text sequences.

A JSON text sequence as specified in RFC 7464 to be a sequence of valid JSON
items with each item introduced by a single ASCII RS (^^, U+1E).  This module
provides a decoder and an encoder with incremental APIs in JSONSeqDecoder and
JSONSeqEncoder.  Common functionality is encapsulated in JSONSeqBase.
Convenience functions load and dump to read and write JSON text sequences to
and from file-like objects, similar to those in the json module in the standard
library, are also provided.
"""

from json     import JSONDecodeError, JSONDecoder, JSONEncoder
from warnings import warn

class JSONSeqBase(object):
	"""Base class for JSON text sequence decoders and encoders.

	Defines the common constructor interface that initializes json as well
	as the item introducer INTR.
	"""

	INTR = '\x1E'
	"""Item introducer.

	In encoders, this attribute should only contain optional whitespace and
	a single ASCII RS (^^, U+1E) in order to generate a standard JSON text
	sequence, and must in any case contain a string that will not be
	produced by the JSON encoder.

	In decoders, this attribute should contain a single ASCII RS in order
	to decode all standard JSON text sequences, and must in any case
	contain a string that will not occur inside the JSON-encoded items.
	"""

	def __init__(self, *, json=None, jsoncls=None, **named):
		"""Initialize a JSON text sequence decoder or encoder.

		If json is passed, it is stored in self.json, and no additional
		arguments are permitted.  Otherwise, jsoncls is called to
		initialize self.json.  Any remaining keyword arguments are then
		passed on to jsoncls.
		"""
		if json is not None and named:
			raise ValueError("Both json and construction "
			                 "arguments specified")
		if json is None:
			json = jsoncls(**named)
		self.json = json
		"""Underlying JSON decoder or encoder."""

class InvalidJSONWarning(UserWarning):
	"""Warning issued when attempting to decode or encode invalid JSON."""
	pass

class InvalidJSON(object):
	"""Placeholder for items that are not valid JSON.

	The decoder uses instances of this class to represent invalid items.
	The encoder can recognize these and pass them through to the output as
	is if full roundtripping is desired.  Both situations cause an
	InvalidJSONWarning to be issued.  JSON decoders should not produce
	instances of this class, and JSON encoders must not attempt to encode
	them.

	The item and the JSON decoder exception are stored as attributes item
	and exception, respectively.  When the object is encoded as an item of
	a JSON text sequence, the value of item is written instead.
	"""

	__slots__ = ['item', 'exception']

	def __init__(self, item, exception):
		self.item = item
		"""Item that failed to parse as JSON, as a string."""
		assert isinstance(exception, JSONDecodeError)
		self.exception = exception
		"""Instance of JSONDecodeError describing the problem."""

	def __repr__(self):
		return "{}({!r}, {!r})".format(type(self).__name__,
		                               self.item,
		                               self.exception)

class JSONSeqDecoder(JSONSeqBase):
	"""Decoder for JSON text sequences.

	Decodes JSON text sequences, i.e. sequences of JSON items with each
	item introduced by an ASCII RS character (^^, U+1E).  Individual items
	are decoded one at a time using a json.JSONDecoder-compatible decoder
	stored in json, as initialized by the constructor.

	Only an incremental interface is provided: decodeiter() decodes the
	JSON text sequence passed as a collection of chunks.  There is no
	explicit support for trailing undecodable data.  Subclasses can
	override items() to change how the splitting works, or INTR (inherited
	from JSONSeqBase) to use a non-standard item introducer.
	"""

	def __init__(self, *, strict=False, jsoncls=JSONDecoder, **named):
		"""Initialize a JSON text sequence decoder.

		If strict is false (the default), self.strict will be set to
		False, allowing any invalid items to be passed through to the
		output encapsulated in InvalidJSON values and cause an
		InvalidJSONWarning to be issued.

		If no JSON decoder is passed in json, the decoder constructor
		specified in jsoncls (or a json.JSONDecoder by default) is
		called to create one.  Any remaining keyword arguments are then
		passed on to jsoncls.  Note, however, that control characters
		in strings can disrupt parsing of JSON text sequences, so the
		strict argument is not passed on to jsoncls.
		"""
		super(JSONSeqDecoder, self).__init__(jsoncls=jsoncls, **named)
		self.strict = bool(strict)
		"""Whether to fail on invalid items.

		If false, any invalid items are passed through to the output
		encapsulated in InvalidJSON values and cause an
		InvalidJSONWarning to be issued.  This allows recovering from
		invalid items as conforming decoders should.
		"""

	def items(self, chunks):
		"""Iterate over the text sequence in chunks.

		Returns an iterable over the text sequence in chunks, where
		each item is a string preceded by the introducer self.INTR, by
		default ASCII RS (^^, U+1E).  If input is not empty and does
		not start with the introducer, raises ValueError.

		Even if the iterator is stopped midway into the sequence, there
		is no way to recover the remainder of the chunk that contains
		the last item.  Any following chunks will be available, however.
		"""
		INTR = self.INTR
		chunks = iter(chunks)
		try:
			first = next(chunks)
		except StopIteration:
			return # Empty file
		if not first.startswith(INTR):
			raise ValueError("Text sequence does not start with "
			                 "INTR")
		buf = [first[len(INTR):]]

		for chunk in chunks:
			buf.append(chunk)
			if INTR not in chunk:
				continue
			items = ''.join(buf).split(INTR)
			buf   = [items.pop()]
			for item in items:
				yield item

		yield ''.join(buf)

	def decodeiter(self, chunks):
		"""Iterate over the JSON text sequence in chunks.

		Returns an iterable over the JSON text sequence items in chunks,
		where each item is a JSON-encoded value preceded by the
		introducer self.INTR and followed by at least one whitespace
		character if it is undelimited (i.e. not an object, a list, or
		a string).  The standard specifies a value of ASCII RS (^^,
		U+1E) for the introducer and recommends that every item be
		terminated by an ASCII LF (^J, U+0A).

		Even if the iterator is stopped midway into the sequence, there
		is no way to recover the remainder of the chunk that contains
		the last item.  Any following chunks will be available, however.

		If self.strict is false, any invalid items will be passed
		through to the output encapsulated in InvalidJSON values and
		will cause an InvalidJSONWarning to be issued.

		The decoder in self.json, the flag in self.strict, and the
		introducer in self.INTR must not change while this method is
		active.
		"""
		json, strict = self.json, self.strict
		for item in self.items(chunks):
			try:
				jsonitem = json.decode(item)
				# Valid JSON, so len(.lstrip()) > 0 and all
				# whitespace is ASCII
				if (item.lstrip()[0] not in '{["' and
				    not item[-1].isspace()):
					raise JSONDecodeError("Truncated",
					                      item,
					                      len(item))
			except JSONDecodeError as e:
				if strict:
					raise
				warn("Read invalid JSON: {!r}".format(item),
				     InvalidJSONWarning,
				     stacklevel=2)
				yield InvalidJSON(item, e)
			else:
				yield jsonitem

def load(fp, *, cls=JSONSeqDecoder, **named):
	"""Load a JSON text sequence from the text file fp.

	Returns an iterable over the items in fp.  It can only be iterated over
	once and consumes the file completely.

	The decoder constructor specified by cls (or JSONSeqDecoder by default)
	is called to create a decoder.  Any remaining keyword arguments are
	passed on to cls.
	"""
	# Chunking by line breaks seems like a good default
	return cls(**named).decodeiter(fp)

class JSONSeqEncoder(JSONSeqBase):
	"""Encoder for JSON text sequences.

	Encodes JSON text sequences, i.e. sequences of JSON items with each
	item introduced by an ASCII RS character (^^, U+1E).  By convention,
	each item is also followed by an ASCII LF (^J, U+0A).  JSON items are
	encoded in order using a json.JSONEncoder-compatible encoder stored in
	json, as initialized by the constructor.

	Only an incremental interface is provided: iterencode() returns an
	iterable of chunks that encode the elements of an iterable.  Subclasses
	can override TERM to use a non-recommended item terminator, or INTR
	(inherited from JSONSeqBase) to use a non-standard item introducer.

	Encoding a JSON text sequence distributes over concatenation, so it is
	valid to call iterencode() several times and write the results in order.
	"""

	TERM = '\n'
	"""Item terminator.

	The standard recommends that an ASCII LF (^J, U+0D) be used here.  This
	value must in any case only consist of ASCII whitespace and be at least
	one character long.

	Note that a line feed is prone to newline translation on output.  If it
	is translated to a CRLF pair as used by Windows and mandated by many
	Internet protocols, the resulting file will still fully conform to the
	standard.
	"""

	def __init__(self, *, strict=True, jsoncls=JSONEncoder, **named):
		"""Initialize a JSON text sequence encoder.

		If strict is false, self.strict is set to False, allowing any
		invalid items encapsulated in InvalidJSON values to be passed
		through to the output and to cause InvalidJSONWarning to be
		issued.

		If no JSON encoder is passed in json, the encoder constructor
		specified in jsoncls (or a json.JSONDecoder by default) is
		called to create one.  Any remaining keyword arguments are then
		passed on to jsoncls.
		"""
		super(JSONSeqEncoder, self).__init__(jsoncls=jsoncls, **named)
		self.strict = bool(strict)
		"""Whether to fail on invalid items.

		If false, any invalid items encapsulated in InvalidJSON values
		are allowed to pass through to the output and cause an
		InvalidJSONWarning to be issued.  This allows roundtripping
		such items found in preexisting text sequences.  Such sequences
		are invalid, but conforming readers should recover.
		"""

	def iterencode(self, iterable):
		"""Iterate over chunks in the encoding of iterable.

		Returns the encoding, in chunks, of iterable as a JSON text
		sequence, meaning the JSON encoding of each element of the
		iterable preceded by the introducer self.INTR and followed by
		the terminator self.TERM.  The standard specifies INTR to be
		ASCII RS (^^, U+1E) and TERM to be at least one whitespace
		character, with a recommended value of ASCII LF (^J, U+0A).

		Encoding a JSON text sequence distributes over concatenation.
		Therefore, if this method is called several times and the
		results written in order, the result is a valid JSON text
		sequence representing the concatenation of the arguments.

		If self.strict is false, any invalid items encapsulated in
		InvalidJSON values will be passed through to the output and
		will cause an InvalidJSONWarning to be issued.

		The encoder in self.json, the flag in self.strict, the
		introducer in self.INTR, and the terminator in self.TERM must
		not change while this method is active.
		"""
		INTR, TERM, json, lax = \
			self.INTR, self.TERM, self.json, not self.strict
		for o in iterable:
			yield INTR
			if lax and isinstance(o, InvalidJSON):
				warn("Wrote invalid JSON: {!r}".format(o.item),
				     InvalidJSONWarning,
				     stacklevel=2)
				assert INTR not in o.item
				yield o.item
			else:
				for chunk in json.iterencode(o):
					yield chunk
				yield TERM

def dump(iterable, fp, *, flush=False, cls=JSONSeqEncoder, **named):
	"""Dump elements of iterable to fp as a JSON text sequence.

	If flush is set to True, fp is flushed after each item is written.

	The decoder constructor specified by cls (or JSONSeqDecoder by default)
	is called to create an encoder.  Any remaining keyword arguments are
	passed on to cls.
	"""
	encoder = cls(**named)
	INTR = encoder.INTR
	for chunk in encoder.iterencode(iterable):
		if flush and chunk.startswith(INTR):
			fp.flush()
		assert chunk.startswith(INTR) or INTR not in chunk
		fp.write(chunk)
	if flush:
		fp.flush()
