import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import torch

from auto_track.auto_data import AutoData
from auto_track.helpers import save_object
from auto_track.track import track


def test_building_version_tree(tmp_path):
    root = tmp_path
    auto_data = AutoData(root)

    available_versions = [
        "0.0.1",
        "0.0.2",
        "0.1.0",
        "0.1.1",
        "0.1.2",
        "0.2.0",
        "0.2.1",
        "0.2.2",
    ]

    version_tree = auto_data._build_version_tree(available_versions)

    assert version_tree == {
        "0": {"0": ["1", "2"], "1": ["0", "1", "2"], "2": ["0", "1", "2"]}
    }


def test_resolving_versions(tmp_path):
    root = tmp_path
    auto_data = AutoData(root)

    available_versions = [
        "0.0.1",
        "0.0.2",
        "0.1.0",
        "0.1.1",
        "0.1.2",
        "0.2.0",
        "0.2.1",
        "0.2.2",
        "1.0.0",
    ]

    version = auto_data._resolve_version("latest", available_versions)
    assert version == "1.0.0"

    version = auto_data._resolve_version("0.*.*", available_versions)
    assert version == "0.2.2"

    version = auto_data._resolve_version("0.2.*", available_versions)
    assert version == "0.2.2"

    version = auto_data._resolve_version("0.2.2", available_versions)
    assert version == "0.2.2"

    with pytest.raises(FileNotFoundError):
        auto_data._resolve_version("0.3.0", available_versions)

    version = auto_data._resolve_version("*.0.0", available_versions)
    assert version == "1.0.0"

    with pytest.raises(FileNotFoundError):
        auto_data._resolve_version("*.0.1", available_versions)


def test_full_integration(tmp_path):
    root = tmp_path

    np_1 = np.array([1, 2, 3])
    np_2 = np.array([4, 5, 6])
    torch_1 = torch.tensor([7, 8, 9])
    torch_2 = torch.tensor([10, 11, 12])
    pd_1 = pd.DataFrame({"key": ["value"]})
    dict_1 = {"key": "value"}

    @track(root, dataset_name="test")
    def save_data():
        return {"array1": np_1, "array2": np_2}, [torch_1, torch_2], pd_1, dict_1

    save_data()

    auto_data = AutoData(root)
    data = auto_data.get_data_from_registry("test", "main", "latest")

    assert np.array_equal(data[0]["array1"], np_1)
    assert np.array_equal(data[0]["array2"], np_2)
    assert torch.equal(data[1][0], torch_1)
    assert torch.equal(data[1][1], torch_2)
    assert data[2].equals(pd_1)
    assert data[3] == dict_1


def test_full_integration_single_file(tmp_path):
    root = tmp_path

    np_1 = np.array([1, 2, 3])

    @track(root, dataset_name="test")
    def save_data():
        return np_1

    save_data()

    auto_data = AutoData(root)
    data = auto_data.get_data_from_registry("test", "main", "latest")

    assert np.array_equal(data, np_1)


def test_full_integration_single_iterable(tmp_path):
    root = tmp_path

    np_1 = np.array([1, 2, 3])
    np_2 = np.array([4, 5, 6])

    @track(root, dataset_name="test")
    def save_data():
        return [np_1, np_2]

    save_data()

    auto_data = AutoData(root)
    data = auto_data.get_data_from_registry("test", "main", "latest")

    assert np.array_equal(data[0], np_1)
    assert np.array_equal(data[1], np_2)


def test_full_integration_single_iterable_dict(tmp_path):
    root = tmp_path

    np_1 = np.array([1, 2, 3])
    np_2 = np.array([4, 5, 6])

    @track(root, dataset_name="test")
    def save_data():
        return {"first": np_1, "second": np_2}

    save_data()

    auto_data = AutoData(root)
    data = auto_data.get_data_from_registry("test", "main", "latest")

    assert np.array_equal(data["first"], np_1)
    assert np.array_equal(data["second"], np_2)
