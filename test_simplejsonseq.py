# On Python < 3, mind the single spurious PytestWarning:
# <https://github.com/pytest-dev/pytest/issues/4014>

from json   import JSONDecoder, JSONEncoder
from pytest import raises, warns

try:
	# For Python < 3; need the pure-Python version in order to subclass it
	from StringIO import StringIO as _StringIO
except ImportError:
	from io import StringIO
else:
	class StringIO(_StringIO):
		def __enter__(self):
			return self
		def __exit__(self, exc_val, exc_type, exc_tb):
			self.close()

try:
	from json import JSONDecodeError as _JSONDecodeError
except ImportError:
	# For Python < 3.5
	_JSONDecodeError = ValueError

from simplejsonseq import *

valid   = ('\x1E"spam"\n'
           '\x1Enull\n'
           '\x1E["holy", "grenade"]\n')
invalid = ('\x1E"spam"\n'
           '\x1Ekiller: bunny\n'
           '\x1Etrue\n'
           '\x1E{"parrot":\n')

def test_load_empty():
	assert list(load(StringIO(""))) == []

def test_dump_empty():
	fp = StringIO()
	dump([], fp)
	assert fp.getvalue() == ""

def test_load_nonseq():
	with raises(ValueError, match="Text sequence does not start with "):
		list(load(StringIO('{"not-a": "jsonseq"}')))

def test_load_chunked():
	items = list(load(['\x1E"ex-', 'parrot"\n']))
	assert items == ["ex-parrot"]

def test_load_close(mocker):
	fp = StringIO(valid)
	mocker.spy(fp, 'close')
	reader = JSONSeqReader(fp)
	assert len(list(reader)) == 3
	assert fp.close.call_count == 0
	reader.close()
	assert fp.close.call_count == 1

def test_load_with(mocker):
	fp = StringIO(valid)
	mocker.spy(fp, 'close')
	with JSONSeqReader(fp) as reader:
		assert len(list(reader)) == 3
		assert fp.close.call_count == 0
	assert fp.close.call_count == 1

def test_load_with_raise(mocker):
	fp = StringIO(valid)
	mocker.spy(fp, 'close')
	with raises(RuntimeError, match="Success"):
		with JSONSeqReader(fp) as reader:
			assert len(list(reader)) == 3
			assert fp.close.call_count == 0
			raise RuntimeError("Success")
	assert fp.close.call_count == 1

def test_load_dump(mocker):
	fp = StringIO()
	mocker.spy(fp, 'flush')
	dump(load(StringIO(valid)), fp)
	assert fp.flush.call_count == 1
	assert fp.getvalue() == valid

def test_load_dump_unbuffered(mocker):
	fp = StringIO()
	mocker.spy(fp, 'flush')
	dump(load(StringIO(valid)), fp, buffered=False)
	assert fp.flush.call_count == 3
	assert fp.getvalue() == valid

def test_load_write(mocker):
	fp = StringIO()
	mocker.spy(fp, 'flush')
	items  = load(StringIO(valid))
	writer = JSONSeqWriter(fp)
	writer.write(*items)
	assert fp.flush.call_count == 0
	writer.flush()
	assert fp.flush.call_count == 1
	assert fp.getvalue() == valid

def test_load_dump_close(mocker):
	fp = StringIO()
	mocker.spy(fp, 'close')
	writer = JSONSeqWriter(fp)
	writer.dump(load(StringIO(valid)))
	assert fp.close.call_count == 0
	assert fp.getvalue() == valid
	writer.close()
	assert fp.close.call_count == 1

def test_load_dump_with(mocker):
	fp = StringIO()
	mocker.spy(fp, 'close')
	with JSONSeqWriter(fp) as writer:
		writer.dump(load(StringIO(valid)))
		assert fp.close.call_count == 0
		assert fp.getvalue() == valid
	assert fp.close.call_count == 1

def test_load_dump_with_raise(mocker):
	fp = StringIO()
	mocker.spy(fp, 'close')
	with raises(RuntimeError, match="Success"):
		with JSONSeqWriter(fp) as writer:
			writer.dump(load(StringIO(valid)))
			assert fp.close.call_count == 0
			assert fp.getvalue() == valid
			raise RuntimeError("Success")
	assert fp.close.call_count == 1

def test_load_invalid_default():
	with warns(InvalidJSONWarning) as warnings:
		items = list(load(StringIO(invalid)))
	assert len(warnings) == 2
	assert repr(items[1]).startswith("InvalidJSON")

def test_load_invalid_strict():
	with raises(_JSONDecodeError):
		list(load(StringIO(invalid), strict=True))

def test_load_dump_invalid_default():
	with warns(InvalidJSONWarning) as warnings:
		items = list(load(StringIO(invalid)))
	assert len(warnings) == 2

	fp = StringIO()
	with raises(TypeError,
	            match=".*InvalidJSON.* is not JSON serializable"):
		dump(items, fp)

def test_load_dump_invalid_strict():
	with warns(InvalidJSONWarning) as warnings:
		items = list(load(StringIO(invalid), strict=False))
	assert len(warnings) == 2

	fp = StringIO()
	with raises(TypeError,
	            match=".*InvalidJSON.* is not JSON serializable"):
		dump(items, fp, strict=True)

def test_load_dump_invalid_lax():
	fp = StringIO()
	with warns(InvalidJSONWarning) as warnings:
		dump(load(StringIO(invalid), strict=False), fp, strict=False)
	assert len(warnings) == 4
	assert fp.getvalue() == invalid

def test_load_truncated():
	with warns(InvalidJSONWarning) as warnings:
		items = list(load(StringIO('\x1Etrue')))
	assert len(warnings) == 1
	assert (len(items) == 1 and
	        isinstance(items[0], InvalidJSON) and
	        items[0].item == 'true' and
	        "Truncated" in repr(items[0].exception))

class CustomError(RuntimeError):
	pass

class CustomJSONDecoder(JSONDecoder):
	def decode(self, *args, **named):
		raise CustomError("Success")

def test_load_named():
	items = list(load(StringIO('\x1E{"spam": 1}\n'), parse_float=float))
	assert len(items) == 1 and items[0] == {"spam": 1.0}

def test_load_json():
	with raises(CustomError, match="Success"):
		list(load(StringIO(valid), json=CustomJSONDecoder()))

def test_load_jsoncls():
	with raises(CustomError, match="Success"):
		list(load(StringIO(valid), jsoncls=CustomJSONDecoder))

def test_load_json_jsoncls():
	with raises(ValueError,
	            match="Both json and construction arguments specified"):
		list(load(StringIO(valid),
		          json=CustomJSONDecoder(),
		          parse_int=None))

def test_load_jsonseq_jsonseqcls():
	with raises(ValueError,
	            match="Both jsonseq and construction arguments specified"):
		list(load(StringIO(valid),
		          jsonseq=JSONSeqDecoder(),
		          json=JSONDecoder()))

def test_dump_jsonseq_jsonseqcls():
	with raises(ValueError,
	            match="Both jsonseq and construction arguments specified"):
		JSONSeqWriter(StringIO(),
		              jsonseq=JSONSeqEncoder(),
		              json=JSONEncoder())
