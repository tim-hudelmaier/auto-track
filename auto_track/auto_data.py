from pathlib import Path

import pandas as pd
import numpy as np
import torch
import json


class AutoData:
    def __init__(self, root: Path):
        self.root = root

    def get_data_from_registry(
        self, dataset: str, branch: str = "main", version: str = "latest"
    ):
        """
        Searches for outputs of a tracked function in the data registry and returns the data.

        Args:
            dataset: Name of the dataset
            branch: Branch of the dataset
            version: Version of the dataset
        """
        if not self.root.exists():
            raise FileNotFoundError(f"Root not found at {self.root}")

        if not (self.root / dataset).exists():
            raise FileNotFoundError(f"Dataset not found at {self.root / dataset}")

        if not (self.root / dataset / branch).exists():
            raise FileNotFoundError(
                f"Branch not found at {self.root / dataset / branch}. Consider using one of {[(self.root / dataset).iterdir()]} as branch."
            )

        available_versions = list((self.root / dataset / branch).iterdir())

        if not available_versions:
            raise FileNotFoundError(
                f"No versions found for dataset {dataset} on branch {branch}"
            )

        version = self._resolve_version(version, available_versions)

        data_path = self.root / dataset / branch / version

        if not data_path.exists():
            raise FileNotFoundError(
                f"Data not found at {data_path}, make sure your root and branch are correct."
            )

        outputs = self._load_from_tuple(data_path)

        if len(outputs) == 1:
            # retruning single files
            return outputs[0]
        else:
            return outputs

    def _resolve_version(self, version: str, available_versions: list[str]) -> str:
        if version == "latest":
            return sorted(available_versions)[-1]

        if "*" in version:
            major, minor, patch = version.split(".")
            version_tree = self._build_version_tree(available_versions)

            if major == "*":
                major = sorted(version_tree.keys())[-1]

            if minor == "*":
                minor = sorted(version_tree[major].keys())[-1]

            if patch == "*":
                patch = sorted(version_tree[major][minor])[-1]

            if minor not in version_tree[major]:
                raise FileNotFoundError(
                    f"No minor version found for major version '{major}', check if your branch is correct."
                )

            if patch not in version_tree[major][minor]:
                raise FileNotFoundError(
                    f"No version found for {major}.{minor}.{patch}, check if your branch is correct."
                )

            return f"{major}.{minor}.{patch}"
        else:
            if version not in available_versions:
                raise FileNotFoundError(
                    f"No version found for {version}, check if your branch is correct."
                )
            return version

    def _build_version_tree(self, versions: list[str]):
        tree = {}
        for version in versions:
            major, minor, patch = version.split(".")
            if major not in tree:
                tree[major] = {}
            if minor not in tree[major]:
                tree[major][minor] = []
            tree[major][minor].append(patch)

        return tree

    def _load_from_tuple(self, data_path: Path):
        """
        Loads data from a tuple of files with type inference.

        Args:
            data_path: Path to the data files
        """
        output = []
        for p in data_path.iterdir():
            if p.is_dir():
                output.append(self._load_iterable_types(p))
            else:
                output.append(self._load_object(p))
        return tuple(output)

    def _load_object(self, path: Path):
        """
        Loads python objects from a predefined path

        Args:
            path: Path to load the object from
        """
        suffix = path.suffix
        if suffix == ".json":
            with open(path, "r") as f:
                json_obj = json.load(f)
            return json_obj
        elif suffix == ".npy":
            return np.load(path)
        elif suffix == ".csv":
            return pd.read_csv(path)
        elif suffix == ".pt":
            return torch.load(path)
        else:
            raise ValueError(f"Unsupported file type: {suffix}")

    def _load_iterable_types(self, path: Path):
        """
        Loads a iterable from a predefined path and checks for types contained in the dictionary.

        Args:
            path: Path to load the dictionary from
        """
        files = list(path.iterdir())

        if files[0].name.startswith("item_"):
            outputs = []
            for p in files:
                outputs.append(self._load_object(p))
            named_outputs = zip(outputs, [p.stem.split("_")[1] for p in files])
            sorted_outputs = sorted(named_outputs, key=lambda x: int(x[1]))
            return [x[0] for x in sorted_outputs]
        else:
            outputs = {}
            for p in files:
                key = p.stem.split("_")[0]
                outputs[key] = self._load_object(p)
            return outputs
