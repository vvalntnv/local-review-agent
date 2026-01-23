def read_file(file_path: str) -> str:
    """
    Reads the file data and outputs the content of the file
    The file path passed should be the relative file path to the project
    """

    with open(file_path, "r") as f:
        return f.read()
