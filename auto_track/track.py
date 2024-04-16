from dataclasses import dataclass
import functools
import json
from pathlib import Path
import uuid

from loguru import logger

from auto_track.helpers import save_object


def track(
    root, dataset_name: str | None = None, output_names: tuple[str] | str | None = None
):
    """
    Decorator to save the output of a function to a file.

    The output will be saved to a dicrectory with the same name as the function.
    """

    def inner(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            outputs = func(*args, **kwargs)

            if dataset_name is None:
                path = get_output_path(func.__name__, root)
            else:
                path = get_output_path(dataset_name, root)

            at_config = kwargs.get("at_config", None)
            branch_name = get_data_branch(at_config, root, func.__name__)
            version = get_function_version(func, root)

            path = path / branch_name / version

            if isinstance(outputs, tuple):
                if len(output_names) != len(outputs):
                    raise ValueError(
                        f"Number of output names ({len(output_names)}) must match number of outputs ({len(outputs)})."
                    )
                for i, output in enumerate(outputs):
                    if output_names is not None:
                        save_object(output, path / f"{output_names[i]}")
                    else:
                        save_object(output, path / f"output_{i}")
            else:
                if output_names is not None:
                    if isinstance(output_names, tuple):
                        raise ValueError(
                            "Output names must be a string for a function with a single return value."
                        )
                    save_object(outputs, path / output_names)
                else:
                    save_object(output, path / "output")

            return outputs

        return wrapper

    return inner


def get_output_path(dataset_name: str, root: Path):
    """
    Get the path to save the output of a function
    """
    return root / dataset_name


def get_data_branch(at_config: dict | None, root: Path, func_name: str) -> str:
    """
    Gets the branch name of the data given a configuration dictionary:
        - Looks up the data_branches.json file in the auto-track root/.auto-track folder
        - If the data is not found, it will return the default branch name 'main'

    Database format is "{"config": "as_string"}": "branch_name"
    """
    if at_config is None:
        return "main"

    db_path = root / ".auto-track" / "data_branches.json"

    # fallback if no data_branches.json file exists yet
    if not db_path.is_file():
        logger.warning(f"No data_branches.json file found at {db_path}. Creating file.")
        db_path.parent.mkdir(parents=True, exist_ok=True)
        with open(db_path, "w") as f:
            json.dump({}, f)

    lookup = json.load(open(db_path, "r"))
    func_db = lookup.get(func_name, None)
    query_branch_name = at_config.get("at_branch", None)
    query_config = clean_query_config(at_config)

    if func_db is None:
        # no branches have been stored yet for this function
        if query_branch_name is None:
            query_branch_name = str(uuid.uuid4())
            logger.warning(
                f"No branch name specified in config for {func_name}. Generated branch name: {query_branch_name}"
            )

        lookup[func_name] = {str(query_config): query_branch_name}
        with open(db_path, "w") as f:
            json.dump(lookup, f)
        return query_branch_name

    else:
        # branches have been stored for this function / func dict exists
        db_branch_name = func_db.get(str(query_config), None)

        if db_branch_name is None:
            # no branch has been stored yet for this config
            if query_branch_name is None:
                query_branch_name = str(uuid.uuid4())
                logger.warning(
                    f"No branch name specified in config for {func_name}. Generated branch name: {query_branch_name}"
                )

            lookup[func_name][str(query_config)] = query_branch_name
            with open(db_path, "w") as f:
                json.dump(lookup, f)
            return query_branch_name
        else:
            # query branch exists in database
            if db_branch_name == query_branch_name:
                return db_branch_name
            else:
                logger.warning(
                    f"You named your config: {query_branch_name}. \n"
                    f"The same config is already stored in the branch: "
                    f"{db_branch_name}.  \nUsing branch name already in"
                    f" database for consistency ({db_branch_name})."
                )
                return db_branch_name


def clean_query_config(config: dict) -> dict:
    """
    Cleans the query config by removing all keys that start with 'at_'
    """
    return {k: v for k, v in config.items() if not k.startswith("at_")}


def get_function_version(func: callable, root: Path) -> str:
    """
    Get the version of a function

    Args:
        func: Function to get the version of

    Returns:
        Version of the function
    """
    signature = func.__annotations__
    if signature is {}:
        logger.warning(
            "Use type hints to annotate the function signature. "
            "API changes cannot be detected and used for versioning"
            " of your functions generated data!"
        )

    func_code = str(func.__code__.co_code)
    func_constants = str(func.__code__.co_consts)
    func_defaults_str = str(func.__defaults__)
    func_patch = func_constants + func_defaults_str

    with FunctionDatabase(root) as fn_lookup:
        if fn_lookup.get(func.__name__, None) is None:
            logger.info("Function is not yet in database. Starting with version 0.0.0")

            fn_lookup[func.__name__] = {
                "__last_versions": [str(signature)],
                str(signature): {
                    "__last_versions": [func_code],
                    func_code: {
                        "__last_versions": [func_patch],
                        func_patch: {
                            "version": "0.0.0",
                            "docs": func.__doc__,
                            "change_msg": "Initial version",
                        },
                    },
                },
            }
            return "0.0.0"

        same_major = [
            _signature
            for _signature in fn_lookup[func.__name__].keys()
            if _signature != "__last_versions" and _signature == str(signature)
        ]

        if len(same_major) > 1:
            raise ValueError(
                "Multiple functions with the same signature found in the database."
            )
        elif len(same_major) == 0:
            last_version_signature = fn_lookup[func.__name__]["__last_versions"][-1]
            last_version_major = len(fn_lookup[func.__name__]["__last_versions"]) - 1
            new_version = f"{last_version_major + 1}.0.0"

            logger.info(
                f"The signature of your function has changed! \n"
                f"Old signature: {last_version_signature} \n"
                f"New signature: {signature} \n"
                f"New version: {new_version}"
            )

            change_msg = input(
                "Describe the changes made for automatic documentation: "
            )

            fn_lookup[func.__name__][str(signature)] = {
                "__last_versions": [func_code],
                func_code: {
                    "__last_versions": [func_patch],
                    func_patch: {
                        "version": new_version,
                        "docs": func.__doc__,
                        "change_msg": change_msg,
                    },
                },
            }

            if fn_lookup[func.__name__].get("__last_versions", None) is None:
                fn_lookup[func.__name__]["__last_versions"] = [str(signature)]
            else:
                fn_lookup[func.__name__]["__last_versions"].append(str(signature))

            return new_version
        else:
            last_fn_signature = same_major[0]

        same_minor = [
            code
            for code in fn_lookup[func.__name__][last_fn_signature].keys()
            if code == func_code and code != "__last_versions"
        ]

        if len(same_minor) > 1:
            raise ValueError(
                "Multiple function entries with the same code found in the database."
            )
        elif len(same_minor) == 0:
            last_version_code = fn_lookup[func.__name__][last_fn_signature][
                "__last_versions"
            ][-1]
            last_version_minor = (
                len(fn_lookup[func.__name__][last_fn_signature]["__last_versions"]) - 1
            )
            last_version_major = fn_lookup[func.__name__]["__last_versions"].index(
                last_fn_signature
            )
            last_version_patch = (
                len(
                    fn_lookup[func.__name__][last_fn_signature][last_version_code][
                        "__last_versions"
                    ]
                )
                - 1
            )

            logger.info("The inner logic of your function has changed!")
            logger.info(
                f"Updating version from {last_version_major}.{last_version_minor}.{last_version_patch} to {last_version_major}.{last_version_minor + 1}.0"
            )

            change_msg = input(
                "Describe the changes made for automatic documentation: "
            )

            fn_lookup[func.__name__][last_fn_signature][func_code] = {
                "__last_versions": [func_patch],
                func_patch: {
                    "version": f"{last_version_major}.{last_version_minor + 1}.0",
                    "docs": func.__doc__,
                    "change_msg": change_msg,
                },
            }

            fn_lookup[func.__name__][last_fn_signature]["__last_versions"].append(
                func_code
            )

            return f"{last_version_major}.{last_version_minor + 1}.0"
        else:
            last_fn_code = same_minor[0]

        same_patch = [
            _patch
            for _patch in fn_lookup[func.__name__][last_fn_signature][
                last_fn_code
            ].keys()
            if _patch == func_patch and _patch != "__last_versions"
        ]

        if len(same_patch) > 1:
            raise ValueError(
                "Multiple function entries with the same constants and defaults found in the database."
            )
        elif len(same_patch) == 0:
            last_version_const_defaults = fn_lookup[func.__name__][last_fn_signature][
                last_fn_code
            ]["__last_versions"][-1]
            last_version_minor = fn_lookup[func.__name__][last_fn_signature][
                "__last_versions"
            ].index(last_fn_code)
            last_version_major = fn_lookup[func.__name__]["__last_versions"].index(
                last_fn_signature
            )
            last_version_patch = fn_lookup[func.__name__][last_fn_signature][
                last_fn_code
            ][last_version_const_defaults]["version"][-1]
            last_version_patch = int(last_version_patch)

            logger.info(
                "The constants of your function have changed! \n"
                f"Old constants: {last_version_const_defaults} \n"
                f"New constants: {func_patch}"
            )
            logger.info(
                f"Updating version from {last_version_major}.{last_version_minor}.{last_version_patch} to {last_version_major}.{last_version_minor}.{last_version_patch + 1}"
            )

            change_msg = input(
                "Describe the changes made for automatic documentation: "
            )

            fn_lookup[func.__name__][last_fn_signature][last_fn_code][func_patch] = {
                "version": f"{last_version_major}.{last_version_minor}.{last_version_patch + 1}",
                "docs": func.__doc__,
                "change_msg": change_msg,
            }

            fn_lookup[func.__name__][last_fn_signature][last_fn_code][
                "__last_versions"
            ].append(func_patch)

            return f"{last_version_major}.{last_version_minor}.{last_version_patch + 1}"
        else:
            logger.info("No version change detected")
            return same_patch[0]["version"]


class FunctionDatabase(object):
    def __init__(self, root) -> None:
        path = root / ".auto-track" / "function_versions.json"

        if not path.is_file():
            logger.warning(
                f"No function_versions.json file found at {path}. Creating file."
            )
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w") as f:
                json.dump({}, f)

        self.path = path
        self.lookup = None

    def __enter__(self):
        with open(self.path, "r") as f:
            self.lookup = json.load(f)

        return self.lookup

    def __exit__(self, *args):
        with open(self.path, "w") as f:
            json.dump(self.lookup, f)
        self.lookup = None
