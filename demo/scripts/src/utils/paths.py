import os


def get_path(relative_path):
    """
    Returns the path of the required file relative to the root directory of the project.
    """

    # Get the directory of the current file (`paths.py`)
    current_dir = os.path.dirname(os.path.realpath(__file__))

    # Traverse up to the project's root directory (repository folder)
    project_root = os.path.abspath(os.path.join(current_dir, "../../../.."))

    # Join the project root with the provided relative path
    return os.path.join(project_root, relative_path)
