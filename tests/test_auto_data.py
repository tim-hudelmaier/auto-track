from pathlib import Path

import pytest

from auto_track.auto_data import AutoData


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
