from io     import StringIO
from json   import JSONDecodeError, JSONDecoder
from pytest import raises, warns

from simplejsonseq import *

valid   = ('\x1E"spam"\n'
           '\x1Enull\n'
           '\x1E{"holy": "grenade", "pin": 1}\n')
invalid = ('\x1E"spam"\n'
           '\x1Ekiller: bunny\n'
           '\x1Etrue\n'
           '\x1E{"parrot":\n')

def test_empty_load():
	assert list(load(StringIO(""))) == []

def test_empty_dump():
	fp = StringIO()
	dump([], fp)
	assert fp.getvalue() == ""

def test_nonseq_load():
	with raises(ValueError, match="Text sequence does not start with "):
		list(load(StringIO('{"not-a": "jsonseq"}')))

def test_chunked_load():
	items = list(load(['\x1E"ex-', 'parrot"\n']))
	assert items == ["ex-parrot"]

def test_valid_load_dump(mocker):
	fp = StringIO()
	mocker.spy(fp, 'flush')
	dump(load(StringIO(valid)), fp)
	assert fp.flush.call_count == 1
	assert fp.getvalue() == valid

def test_valid_load_dump_unbuffered(mocker):
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

def test_invalid_load_default():
	with warns(InvalidJSONWarning) as warnings:
		items = list(load(StringIO(invalid)))
	assert len(warnings) == 2
	assert repr(items[1]).startswith("InvalidJSON('killer: bunny\\n', "
	                                 "JSONDecodeError")

def test_invalid_load_strict():
	with raises(JSONDecodeError):
		list(load(StringIO(invalid), strict=True))

def test_invalid_load_dump_default():
	with warns(InvalidJSONWarning) as warnings:
		items = list(load(StringIO(invalid)))
	assert len(warnings) == 2

	fp = StringIO()
	with raises(TypeError,
	            match="Object of type InvalidJSON is not JSON "
	                  "serializable"):
		dump(items, fp)

def test_invalid_load_dump_strict():
	with warns(InvalidJSONWarning) as warnings:
		items = list(load(StringIO(invalid), strict=False))
	assert len(warnings) == 2

	fp = StringIO()
	with raises(TypeError,
	            match="Object of type InvalidJSON is not JSON "
	                  "serializable"):
		dump(items, fp, strict=True)

def test_invalid_load_dump_lax():
	fp = StringIO()
	with warns(InvalidJSONWarning) as warnings:
		dump(load(StringIO(invalid), strict=False), fp, strict=False)
	assert len(warnings) == 4
	assert fp.getvalue() == invalid

def test_truncated_load():
	with warns(InvalidJSONWarning) as warnings:
		items = list(load(StringIO('\x1Etrue')))
	assert len(warnings) == 1
	assert (len(items) == 1 and
	        isinstance(items[0], InvalidJSON) and
	        items[0].item == 'true' and
	        items[0].exception.msg == "Truncated")

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

def test_write_jsonseq_jsonseqcls():
	with raises(ValueError,
	            match="Both jsonseq and construction arguments specified"):
		JSONSeqWriter(StringIO(),
		              jsonseq=JSONSeqDecoder(),
		              json=CustomJSONDecoder())
