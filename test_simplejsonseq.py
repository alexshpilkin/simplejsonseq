from io     import StringIO
from json   import JSONDecodeError, JSONDecoder
from pytest import raises, warns

from simplejsonseq import InvalidJSONWarning, dump, load

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
	with raises(IOError, match="Text sequence does not start with "):
		list(load(StringIO('{"not-a": "jsonseq"}')))

def test_chunked_load():
	items = list(load(['\x1E"ex-', 'parrot"\n']))
	assert items == ["ex-parrot"]

def test_valid_load_dump():
	fp = StringIO()
	dump(load(StringIO(valid)), fp)
	assert fp.getvalue() == valid

def test_valid_load_dump_flush(mocker):
	fp = StringIO()
	mocker.spy(fp, 'flush')
	dump(load(StringIO(valid)), fp, flush=True)
	# There is a spurious flush before the first element
	assert fp.flush.call_count == 4
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
