from pathlib import Path
import json
import numpy as np
import pandas as pd
import torch

def save_object(obj, path: str | Path):
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
    match obj:
        case isinstance(obj, dict):
            with open(path, "w") as f:
                json.dump(obj, f)
        case isinstance(obj, list):
            with open(path, "w") as f:
                json.dump(obj, f)
        case isinstance(obj, np.ndarray):
            np.save(path, obj)
        case isinstance(obj, pd.DataFrame):
            obj.to_csv(path, index=False)
        case isinstance(obj, pd.Series):
            obj.to_csv(path)
        case isinstance(obj, torch.Tensor):
            torch.save(obj, path)
        case _:
            raise ValueError(f"Unsupported object type: {type(obj)}")
