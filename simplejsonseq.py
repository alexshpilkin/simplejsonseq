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

from json import JSONDecoder, JSONEncoder

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

	In decoders, this attribute should contain a single ASCII RS in order to
	parse all standard JSON text sequences, and must in any case contain a
	string that will not occur inside the JSON-encoded items.
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

class JSONSeqDecoder(JSONSeqBase):
	"""Decoder for JSON text sequences.

	Decodes JSON text sequences, i.e. sequences of JSON items with each
	item introduced by an ASCII RS character (^^, U+1E).  Individual items
	are decoded one at a time using a json.JSONDecoder-compatible decoder
	stored in json, as initialized by the constructor.

	Only an incremental parsing interface is provided: decodeiter() parses
	the JSON text sequence passed as a collection of chunks.  There is no
	explicit support for trailing unparseable data.  Subclasses can override
	items() to change how the splitting works, or INTR (inherited from
	JSONSeqBase) to use a non-standard item introducer.
	"""

	def __init__(self, *, jsoncls=JSONDecoder, **named):
		"""Initialize a JSON text sequence decoder.

		If no JSON decoder is passed in json, the decoder constructor
		specified in jsoncls (or a json.JSONDecoder by default) is
		called to create one.  Any remaining keyword arguments are then
		passed on to jsoncls.
		"""
		super(JSONSeqDecoder, self).__init__(jsoncls=jsoncls, **named)

	def items(self, chunks):
		"""Iterate over the text sequence in chunks."""
		INTR = self.INTR
		chunks = iter(chunks)
		try:
			first = next(chunks)
		except StopIteration:
			return # Empty file
		if not first.startswith(INTR):
			raise IOError("Text sequence does not start with INTR")
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

		Even if the iterator is stopped midway into the sequence, there
		is no way to recover the remaining input.  FIXME

		The decoder in self.json must not be changed while this method
		is being executed.
		"""
		json = self.json
		for item in self.items(chunks):
			yield json.decode(item)

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
	each item is also followed by an ASCII LF (^J, U+0A).  Objects are
	encoded in order using a json.JSONEncoder-compatible encoder stored in
	json, as initialized by the constructor.

	Only an incremental interface is provided: iterencode() returns an
	iterable of chunks that encode a sequence of objects.  Subclasses can
	override TERM to use a non-recommended item terminator, or INTR
	(inherited from JSONSeqBase) to use a non-standard item introducer.

	Encoding a JSON text sequence distributes over concatenation, so it is
	valid to call iterencode() several times and write the results in order.
	"""

	TERM = '\n'
	"""Item terminator.

	The standard recommends that an ASCII LF (^J, U+0D) be used here.  This
	value must in any case only consist of ASCII whitespace.

	Note that a line feed is prone to newline translation on output.  If it
	is translated to a CRLF pair as used by Windows and mandated by many
	Internet protocols, the resulting file will still fully conform to the
	standard.
	"""

	def __init__(self, *, jsoncls=JSONEncoder, **named):
		"""Initialize a JSON text sequence encoder.

		If no JSON encoder is passed in json, the encoder constructor
		specified in jsoncls (or a json.JSONDecoder by default) is
		called to create one.  Any remaining keyword arguments are then
		passed on to jsoncls.
		"""
		super(JSONSeqEncoder, self).__init__(jsoncls=jsoncls, **named)

	def iterencode(self, iterable):
		"""Iterate over chunks in the encoding of iterable.

		Encoding a JSON text sequence distributes over concatenation.
		Therefore, if this method is called several times and the
		results written in order, the result is a valid JSON text
		sequence representing the concatenation of the arguments.
		"""
		INTR, TERM, json = self.INTR, self.TERM, self.json
		for o in iterable:
			yield INTR
			for chunk in json.iterencode(o):
				yield chunk
			yield TERM

def dump(iterable, fp, *, flush=False, cls=JSONSeqEncoder, **named):
	"""Dump objects in iterable to fp as a JSON text sequence.

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
