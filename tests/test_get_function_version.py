import json
from pathlib import Path

from auto_track.track import get_function_version


def test_get_function_version(tmp_path, monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: "Some Message")

    def func(a: int, b: int) -> int:
        return a + b

    assert get_function_version(func=func, root=tmp_path) == "0.0.0"

    db_path = tmp_path / ".auto-track" / "function_versions.json"
    assert db_path.exists()

    with open(db_path, "r") as f:
        lookup = json.load(f)
        assert lookup.get("func", None) is not None
        assert lookup["func"].get("__last_versions", None) is not None

    def func(a: int, b: int, c: int) -> int:
        return a * b * c

    assert get_function_version(func=func, root=tmp_path) == "1.0.0"

    def func(a: int, b: int, c: int = 42) -> int:
        return a * b * c

    assert get_function_version(func=func, root=tmp_path) == "1.0.1"

    def func(a: int, b: int = 16, c: int = 42) -> int:
        return a * b * c

    assert get_function_version(func=func, root=tmp_path) == "1.0.2"

    def func(a: int, b: int, c: int) -> int:
        d = 42
        return a + b + c + d

    assert get_function_version(func=func, root=tmp_path) == "1.1.0"

    def func(a: int, b: int, c: int) -> int:
        d = 16
        return a + b + c + d

    assert get_function_version(func=func, root=tmp_path) == "1.1.1"

    def func2(a: int, b: int, c: int) -> int:
        d = 16
        return a + b + c + d

    assert get_function_version(func=func2, root=tmp_path) == "0.0.0"
