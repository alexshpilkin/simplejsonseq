from __future__ import unicode_literals

from json import JSONDecoder, JSONEncoder

class JSONSeqBase(object):
	RS = '\x1E'

	def __init__(self, *, json=None, jsoncls=None, **named):
		if json is not None:
			if named:
				raise ValueError("Both json and construction "
				                 "arguments specified")
			self.json = json
		else:
			self.json = jsoncls(**named)

class JSONSeqDecoder(JSONSeqBase):
	def __init__(self, *, jsoncls=JSONDecoder, **named):
		"""Decoder for JSON text sequences (RFC 7464).

		Individual objects are parsed from strings using the JSON
		decoder specified in the json argument.  If no decoder is
		passed, the decoder constructor specified in jsoncls (or a
		json.JSONDecoder by default) is instantiated.  Any remaining
		keyword arguments are then passed to jsoncls.
		"""
		super(JSONSeqDecoder, self).__init__(jsoncls=jsoncls, **named)

	def records(self, chunks):
		"""Iterate over the records in chunks."""

		RS = self.RS
		chunks = iter(chunks)
		try:
			first = next(chunks)
		except StopIteration:
			return # Empty file
		if first[0] != RS:
			raise IOError("JSON text sequence does not start "
			              "with RS")
		buf = [first[1:]]

		for chunk in chunks:
			buf.append(chunk)
			if RS not in chunk:
				continue
			recs = ''.join(buf).split(RS)
			buf  = [recs.pop()]
			for rec in recs:
				yield rec

		yield ''.join(buf)

	def decodeiter(self, chunks):
		"""Iterate over the JSON text sequence in chunks."""

		json = self.json
		for rec in self.records(chunks):
			yield json.decode(rec)

def load(fp, *, cls=JSONSeqDecoder, **named):
	"""Load a JSON text sequence from the text file fp.

	Returns an iterable of the objects in fp.  It can only be iterated over
	once and consumes the file completely.

	The decoder constructor specified by cls (or a JSONSeqDecoder by
	default) is invoked to parse the file.  All remaining keyword arguments
	are passed to cls.
	"""
	# Chunking by line breaks seems like a good default
	return cls(**named).decodeiter(fp)

class JSONSeqEncoder(JSONSeqBase):
	def __init__(self, *, jsoncls=JSONEncoder, **named):
		"""Encoder for JSON text sequences (RFC 7464).

		Individual objects are encoded using the JSON encoder specified
		in the json argument.  If no decoder is passed, the decoder
		constructor specified in jsoncls (or a json.JSONEncoder by 
		default) is instantiated.  Any remaining keyword arguments are 
		then passed to jsoncls.
		"""
		super(JSONSeqEncoder, self).__init__(jsoncls=jsoncls, **named)

	def iterencode(self, iterable):
		"""Iterate over chunks in the encoding of iterable."""

		RS, json = self.RS, self.json
		for o in iterable:
			yield RS
			for chunk in json.iterencode(o):
				yield chunk
			yield '\n'

def dump(iterable, fp, *, flush=False, cls=JSONSeqEncoder, **named):
	"""Dump objects in iterable to fp as a JSON text sequence.

	If flush is set to True, the file is flushed after every object.
	Any remaining keyword arguments are passed to json.dumps.
	"""
	encoder = cls(**named)
	RS = encoder.RS
	for chunk in encoder.iterencode(iterable):
		if flush and chunk.startswith(RS):
			fp.flush()
		assert chunk.startswith(RS) or RS not in chunk
		fp.write(chunk)
	if flush:
		fp.flush()
