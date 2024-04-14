"""DEV TODOs:
- [] add support for AnnData
"""

from pathlib import Path
import json
import numpy as np
import pandas as pd
import torch


def save_object(obj, path: Path):
    """
    Saves python objects to a predefined path

    Args:
        obj: Python object to save can be any of the following types:
            - dict
            - list
            - np.ndarray
            - pd.DataFrame
            - pd.Series
            - torch.Tensor
        path: Path to save the object
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    if not path.suffix:
        if isinstance(obj, (list, tuple, dict)):
            path = path.with_suffix(".json")
        elif isinstance(obj, np.ndarray):
            path = path.with_suffix(".npy")
        elif isinstance(obj, (pd.DataFrame, pd.Series)):
            path = path.with_suffix(".csv")
        elif isinstance(obj, torch.Tensor):
            path = path.with_suffix(".pt")

    if isinstance(obj, (list, tuple, dict)):
        save_iterable_types(obj, path)
    elif isinstance(obj, np.ndarray):
        np.save(path, obj)
    elif isinstance(obj, (pd.DataFrame, pd.Series)):
        obj.to_csv(path, index=False)
    elif isinstance(obj, torch.Tensor):
        torch.save(obj, path)
    else:
        raise ValueError(f"Unsupported object type: {type(obj)}")


def save_iterable_types(obj: list | dict | tuple, path: Path):
    """
    Saves a iterable to a predefined path and checks for types contained in the dictionary.

    Iterables only consisting of internal python types (str, int, float, bool, list, dict, tuple)
        are stored as json files.
    
    If the object contains external types (np.ndarray, pd.DataFrame, torch.Tensor) and only one type,
        the objects is stored in the corresponding format in a subdirectory. With each file named after
        the key or index of the object.

    Any other combination of types will raise a ValueError.

    Args:
        obj: Dictionary to save
        path: Path to save the dictionary
    """
    iterable_types = (list, dict, tuple)
    if not isinstance(obj, iterable_types):
        raise ValueError(f"Unsupported object type: {type(obj)}")

    if _python_internal_types_only(obj):
        with open(path, "w") as f:
            json.dump(obj, f)
    elif isinstance(obj, dict):
        value_types = {type(value) for value in obj.values()}
        contains_external_types = any(value_type in [np.ndarray, pd.DataFrame, pd.Series, torch.Tensor] for value_type in value_types)
        if len(value_types) != 1 and contains_external_types:
            raise ValueError(f"Values in the dictionary are not of the same type: {value_types}")
        value_type = value_types.pop()
        if value_type == np.ndarray:
            for key, value in obj.items():
                p = _get_nested_obj_dir(path, key, "", ".npy")
                np.save(p, value)
        elif value_type == pd.DataFrame or value_type == pd.Series:
            for key, value in obj.items():
                p = _get_nested_obj_dir(path, key, "", ".csv")
                value.to_csv(p, index=False)
        elif value_type == torch.Tensor:
            for key, value in obj.items():
                p = _get_nested_obj_dir(path, key, "", ".pt")
                torch.save(value, p)
    elif isinstance(obj, (list, tuple)):
        value_types = {type(value) for value in obj}
        contains_external_types = any(value_type in [np.ndarray, pd.DataFrame, pd.Series, torch.Tensor] for value_type in value_types)
        if len(value_types) != 1 and contains_external_types:
            raise ValueError(f"Values in the dictionary are not of the same type: {value_types}")
        value_type = value_types.pop()
        if value_type == np.ndarray:
            for idx, value in enumerate(obj):
                p = _get_nested_obj_dir(path, idx, "item_", ".npy")
                np.save(p, value)
        elif value_type == pd.DataFrame or value_type == pd.Series:
            for idx, value in enumerate(obj):
                p = _get_nested_obj_dir(path, idx, "item_", ".csv")
                value.to_csv(p, index=False)
        elif value_type == torch.Tensor:
            for idx, value in enumerate(obj):
                p = _get_nested_obj_dir(path, idx, "item_", ".pt")
                torch.save(value, p)
    else:
        raise ValueError(f"Object type {type(obj)} is currently not supported for automatic saving.")


def _python_internal_types_only(d: list | dict | tuple) -> bool:
    """
    Checks if all values in a dictionary are of internal Python types

    Args:
        d: Dictionary to check

    Returns:
        True if all values are of internal Python types, False otherwise
    """
    iterable_types = (list, dict, tuple)
    internal_types = (str, int, float, bool)

    if isinstance(d, (list, tuple)):
        for value in d:
            if isinstance(value, iterable_types):
                _ = _python_internal_types_only(value)
            elif not isinstance(value, internal_types):
                return False
    elif isinstance(d, dict):
        for value in d.values():
            if isinstance(value, iterable_types):
                _ = _python_internal_types_only(value)
            elif not isinstance(value, internal_types):
                return False
    
    return True


def _get_nested_obj_dir(path: Path, idx: str, prefix: str, suffix: str) -> Path:
    """
    Generates a directory for nested objects

    Args:
        path: Path to the object

    Returns:
        Path to the directory
    """
    dir = path.parent / path.stem
    dir.mkdir(exist_ok=True)
    return dir / f"{prefix}{idx}{suffix}"