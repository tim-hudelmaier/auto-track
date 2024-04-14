import functools
from pathlib import Path
from typing import Tuple

from auto_track.helpers import save_object


def track(root: Path = None, output_names: Tuple[str] | str = None):
    """
    Decorator to save the output of a function to a file.

    The function must have a return type annotation. The output will be saved to a dicrectory with the same name as the function.
    """
    def inner(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            outputs = func(*args, **kwargs)

            if root is None:
                # todo: need to change this default to something more sensible
                path = get_output_path(func.__name__, "./outputs")
            path = get_output_path(func.__name__, root)

            if isinstance(outputs, tuple):
                if len(output_names) != len(outputs):
                        raise ValueError(f"Number of output names ({len(output_names)}) must match number of outputs ({len(outputs)}).")
                for i, output in enumerate(outputs):
                    if output_names is not None:
                        save_object(output, path / f"{output_names[i]}")
                    else:
                        save_object(output, path / f"output_{i}")
            else:
                if output_names is not None:
                    if isinstance(output_names, tuple):
                        raise ValueError("Output names must be a string for a function with a single return value.")
                    save_object(outputs, path / output_names)
                else:
                    save_object(output, path / "output")

            return outputs
        return wrapper
    return inner


def get_output_path(func_name: str, root: Path):
    """
    Get the path to save the output of a function
    """
    return root / func_name