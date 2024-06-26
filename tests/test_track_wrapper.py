import os
from pathlib import Path

from auto_track.track import versioned_auto_save, get_output_path


def test_single_output(tmpdir):
    @versioned_auto_save(root=Path(tmpdir), output_names="output")
    def single_output_func():
        return ["single output"]

    assert single_output_func() == ["single output"]
    assert os.path.exists(
        tmpdir / "single_output_func" / "main" / "0.0.0" / "output.json"
    )


def test_multiple_outputs(tmpdir):
    @versioned_auto_save(root=Path(tmpdir), output_names=("output1", "output2"))
    def multiple_outputs_func():
        return ["output 1"], ["output 2"]

    assert multiple_outputs_func() == (["output 1"], ["output 2"])
    assert os.path.exists(
        tmpdir / "multiple_outputs_func" / "main" / "0.0.0" / "output1.json"
    )
    assert os.path.exists(
        tmpdir / "multiple_outputs_func" / "main" / "0.0.0" / "output2.json"
    )


def test_get_output_path(tmpdir):
    path = get_output_path("test_func", tmpdir)
    assert path == tmpdir / "test_func"
