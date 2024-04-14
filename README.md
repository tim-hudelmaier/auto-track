Automaticaly generated file structure.

At the beginning of each experiment a tracker has to be instanciated and named.

Then the substructure is as follows:

auto-tracker-root-dir (set in config) / experiment-dir (by name of tracker instance) / run-dir (using date and count & maybe an alias like in wandb) / function-name / file-name (or file-name/child-file-name)
