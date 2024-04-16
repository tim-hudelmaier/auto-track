import json

from auto_track.track import get_data_branch


def test_no_config(tmp_path):
    assert get_data_branch(None, tmp_path, "test_func") == "main"


def test_with_stored_config(tmp_path):
    at_config = {"some_param": "some_value", "at_branch": "test_branch"}

    base_path = tmp_path / ".auto-track"
    base_path.mkdir()

    db_key_config = {k: v for k, v in at_config.items() if not k.startswith("at_")}

    with open(base_path / "data_branches.json", "w") as f:
        json.dump({"test_func": {str(db_key_config): "test_branch"}}, f)

    assert get_data_branch(at_config, tmp_path, "test_func") == "test_branch"

    at_config["at_branch"] = "some_branch"
    assert get_data_branch(at_config, tmp_path, "test_func") == "test_branch"

    at_config["some_param"] = "another_value"
    assert get_data_branch(at_config, tmp_path, "test_func") == "some_branch"


def test_without_stored_config(tmp_path):
    at_config = {"some_param": "some_value", "at_branch": "test_branch"}

    assert get_data_branch(at_config, tmp_path, "test_func") == "test_branch"
    assert (tmp_path / ".auto-track" / "data_branches.json").exists()
    assert json.load(open(tmp_path / ".auto-track" / "data_branches.json", "r")) == {
        "test_func": {"{'some_param': 'some_value'}": "test_branch"}
    }

    at_config["at_branch"] = "some_branch"
    assert get_data_branch(at_config, tmp_path, "test_func") == "test_branch"
    assert json.load(open(tmp_path / ".auto-track" / "data_branches.json", "r")) == {
        "test_func": {"{'some_param': 'some_value'}": "test_branch"}
    }

    at_config["some_param"] = "another_value"
    assert get_data_branch(at_config, tmp_path, "test_func") == "some_branch"
    assert json.load(open(tmp_path / ".auto-track" / "data_branches.json", "r")) == {
        "test_func": {
            "{'some_param': 'some_value'}": "test_branch",
            "{'some_param': 'another_value'}": "some_branch",
        }
    }

    assert get_data_branch(None, tmp_path, "test_func") == "main"

    assert get_data_branch(at_config, tmp_path, "another_func") == "some_branch"
    assert json.load(open(tmp_path / ".auto-track" / "data_branches.json", "r")) == {
        "test_func": {
            "{'some_param': 'some_value'}": "test_branch",
            "{'some_param': 'another_value'}": "some_branch",
        },
        "another_func": {"{'some_param': 'another_value'}": "some_branch"},
    }
