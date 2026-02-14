"""Tests for agentlog._describe — value descriptor engine."""

from agentlog._describe import describe


def test_none():
    d = describe(None)
    assert d == {"t": "NoneType", "v": None}


def test_bool():
    assert describe(True) == {"t": "bool", "v": True}
    assert describe(False) == {"t": "bool", "v": False}


def test_int():
    assert describe(42) == {"t": "int", "v": 42}


def test_float():
    assert describe(3.14) == {"t": "float", "v": 3.14}


def test_short_string():
    d = describe("hello")
    assert d == {"t": "str", "v": "hello"}


def test_long_string():
    s = "x" * 500
    d = describe(s)
    assert d["t"] == "str"
    assert len(d["v"]) == 200
    assert d["truncated"] == 500


def test_bytes():
    d = describe(b"hello world")
    assert d["t"] == "bytes"
    assert d["n"] == 11


def test_small_list():
    d = describe([1, 2, 3])
    assert d["t"] == "list"
    assert d["n"] == 3
    assert d["it"] == "int"
    assert d["v"] == [1, 2, 3]


def test_large_list():
    d = describe(list(range(100)))
    assert d["t"] == "list"
    assert d["n"] == 100
    assert "preview" in d
    assert len(d["preview"]) == 3


def test_empty_list():
    d = describe([])
    assert d["t"] == "list"
    assert d["n"] == 0
    assert "it" not in d


def test_tuple():
    d = describe((1, "a"))
    assert d["t"] == "tuple"
    assert d["n"] == 2


def test_small_dict():
    d = describe({"a": 1, "b": 2})
    assert d["t"] == "dict"
    assert d["n"] == 2
    assert d["k"] == ["a", "b"]
    assert d["v"] == {"a": 1, "b": 2}


def test_large_dict():
    big = {f"key_{i}": i for i in range(50)}
    d = describe(big)
    assert d["t"] == "dict"
    assert d["n"] == 50
    assert len(d["k"]) == 20  # capped at _MAX_DICT_KEYS
    assert "v" not in d  # too large for inline value


def test_set():
    d = describe({1, 2, 3})
    assert d["t"] == "set"
    assert d["n"] == 3


def test_object_with_dict():
    class Foo:
        def __init__(self):
            self.name = "test"
            self.value = 42
            self._private = "hidden"

    d = describe(Foo())
    assert d["t"] == "Foo"
    assert "name" in d["k"]
    assert "value" in d["k"]
    assert "_private" not in d["k"]
    assert d["n"] == 2


def test_fallback_with_len():
    # A custom object with __len__ — note it also has __dict__ so
    # the object branch catches it first with k/n for attrs
    class Custom:
        def __len__(self):
            return 5

    d = describe(Custom())
    assert d["t"] == "Custom"
    # Has __dict__ (empty), so goes through object branch
    assert d["n"] == 0


def test_fallback_repr():
    # Test the repr fallback for a type that has __dict__ (class object)
    import types
    d = describe(types.SimpleNamespace)
    assert d["t"] == "type"
    # Classes have __dict__, so they go through the object branch
    assert "k" in d or "v" in d
