import functools
import json
from pathlib import Path
from typing import Tuple
import uuid

from loguru import logger

from auto_track.helpers import save_object


def track(
    root, dataset_name: str | None = None, output_names: Tuple[str] | str | None = None
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
            print(branch_name)

            path = path / branch_name
            print(path)

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
