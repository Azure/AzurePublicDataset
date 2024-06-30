import ruamel.yaml
from typing import Any
import os
from pathlib import Path

yaml = ruamel.yaml.YAML()

def read_yaml(yaml_file: str) -> dict:
    """Read a YAML file and return the contents as a dictionary.

    Args:
        yaml_file: The YAML file to read.

    Returns:
        A dictionary containing the YAML file's contents.
    """
    with open(yaml_file, 'r') as f:
        return yaml.load(f)
    
def write_yaml(yaml_file: str, yaml_data: Any) -> None:
    """Write a dictionary to a YAML file.

    Args:
        yaml_file: The YAML file to write to.
        yaml_dict: The dictionary to write to the YAML file.
    """
    with open(yaml_file, 'w') as f:
        yaml.dump(yaml_data, f)


def join_path(*paths: str) -> str:
    """Join paths together.

    Args:
        paths: The paths to join.

    Returns:
        The joined path.
    """
    paths = [path for path in paths if path != '']
    # normalize paths
    paths = [os.path.normpath(path) for path in paths]
    return os.path.join(*paths)

# open last level directory
def open_path_dir(path, file=True):
    path_obj = Path(path)
    if file:
        path_obj = path_obj.parent
    path_obj.mkdir(parents=True, exist_ok=True)