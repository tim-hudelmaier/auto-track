import pytest
import numpy as np
import pandas as pd
import torch
from pathlib import Path
from auto_track.helpers import (
    save_object,
    save_iterable_types,
    _python_internal_types_only,
    _get_nested_obj_dir,
)


def test_save_object(tmp_path):
    d = {"a": 1, "b": 2}
    save_object(d, tmp_path / "dict.json")
    assert (tmp_path / "dict.json").exists()

    l = [1, 2, 3]
    save_object(l, tmp_path / "list.json")
    assert (tmp_path / "list.json").exists()

    arr = np.array([1, 2, 3])
    save_object(arr, tmp_path / "array.npy")
    assert (tmp_path / "array.npy").exists()

    df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
    save_object(df, tmp_path / "df.csv")
    assert (tmp_path / "df.csv").exists()

    s = pd.Series([1, 2, 3])
    save_object(s, tmp_path / "series.csv")
    assert (tmp_path / "series.csv").exists()

    tensor = torch.tensor([1, 2, 3])
    save_object(tensor, tmp_path / "tensor.pt")
    assert (tmp_path / "tensor.pt").exists()

    with pytest.raises(ValueError):
        save_object(set([1, 2, 3]), tmp_path / "set.json")


def test_save_obj_without_suffix(tmp_path):
    d = {"a": 1, "b": 2}
    save_object(d, tmp_path / "dict")
    assert (tmp_path / "dict.json").exists()

    l = [1, 2, 3]
    save_object(l, tmp_path / "list")
    assert (tmp_path / "list.json").exists()

    arr = np.array([1, 2, 3])
    save_object(arr, tmp_path / "array")
    assert (tmp_path / "array.npy").exists()

    df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
    save_object(df, tmp_path / "df")
    assert (tmp_path / "df.csv").exists()

    s = pd.Series([1, 2, 3])
    save_object(s, tmp_path / "series")
    assert (tmp_path / "series.csv").exists()

    tensor = torch.tensor([1, 2, 3])
    save_object(tensor, tmp_path / "tensor")
    assert (tmp_path / "tensor.pt").exists()


def test_save_iterable_types(tmp_path):
    d = {"a": np.array([1, 2, 3]), "b": np.array([4, 5, 6])}
    save_iterable_types(d, tmp_path / "dict")
    assert (tmp_path / "dict" / "a.npy").exists()
    assert (tmp_path / "dict" / "b.npy").exists()

    l = [np.array([1, 2, 3]), np.array([4, 5, 6])]
    save_iterable_types(l, tmp_path / "list")
    assert (tmp_path / "list" / "item_0.npy").exists()
    assert (tmp_path / "list" / "item_1.npy").exists()

    with pytest.raises(ValueError):
        d = {"a": np.array([1, 2, 3]), "b": [4, 5, 6]}
        save_iterable_types(d, tmp_path / "dict")


def test__python_internal_types_only():
    assert _python_internal_types_only({"a": 1, "b": 2})
    assert not _python_internal_types_only({"a": 1, "b": np.array([1, 2, 3])})


def test__get_nested_obj_dir(tmp_path):
    path = _get_nested_obj_dir(tmp_path / "dir", "a", "prefix_", ".suffix")
    assert path == tmp_path / "dir" / "prefix_a.suffix"
