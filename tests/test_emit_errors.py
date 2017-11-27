import sys

def broken_sink(m):
    raise Exception

def test_no_sys_stderr(logger, capsys, monkeypatch):
    monkeypatch.setattr(sys, 'stderr', None)
    logger.start(broken_sink)
    logger.debug('a')

    out, err = capsys.readouterr()
    assert out == err == ""

def test_broken_sys_stderr(logger, capsys, monkeypatch):
    def broken_write(*args, **kwargs):
        raise OSError

    monkeypatch.setattr(sys.stderr, 'write', broken_write)
    logger.start(broken_sink)
    logger.debug('a')

    out, err = capsys.readouterr()
    assert out == err == ""

def test_encoding_error(logger, capsys):
    def sink(m):
        raise UnicodeEncodeError('utf8', "", 10, 11, 'too bad')

    logger.start(sink)
    logger.debug("test")

    out, err = capsys.readouterr()
    lines = err.strip().splitlines()

    assert out == ""
    assert lines[0] == "--- Logging error in Loguru ---"
    assert lines[1].startswith("Record was: {")
    assert lines[1].endswith("}")
    assert lines[-2] == "UnicodeEncodeError: 'utf8' codec can't encode characters in position 10-10: too bad"
    assert lines[-1] == "--- End of logging error ---"

def test_unprintable_record(logger, writer, capsys):
    class Unprintable:
        def __repr__(self):
            raise ValueError("Failed")

    logger.start(writer, format='{message} {extra[unprintable]}')
    logger.bind(unprintable=1).debug('a')
    logger.bind(unprintable=Unprintable()).debug('b')
    logger.bind(unprintable=2).debug('c')

    out, err = capsys.readouterr()
    lines = err.strip().splitlines()

    assert out == ""
    assert lines[0] == "--- Logging error in Loguru ---"
    assert lines[1] == "Record was: /!\\ Unprintable record /!\\"
    assert lines[-2] == "ValueError: Failed"
    assert lines[-1] == "--- End of logging error ---"
    assert writer.read() == "a 1\nc 2\n"