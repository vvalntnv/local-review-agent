import os
import re
from tools.schemas import Directory, File


def explore_structure(
    root_dir_path: str,
    depth: int = 1,
    ignore_names: list[str] | None = None,
) -> Directory:
    if not os.path.isdir(root_dir_path):
        raise Exception(f"Path is not a directory: {root_dir_path}")

    # Initialize ignore patterns
    ignore_patterns = []
    if ignore_names:
        ignore_patterns = [re.compile(pattern) for pattern in ignore_names]

    def should_ignore(name: str) -> bool:
        return any(pattern.search(name) for pattern in ignore_patterns)

    directory = Directory(root_file_path=root_dir_path, files=[], children=[])

    try:
        # Sort entries to ensure deterministic output
        entries = sorted(os.scandir(root_dir_path), key=lambda e: e.name)

        for entry in entries:
            # Skip entries that match ignore patterns
            if should_ignore(entry.name):
                continue
            if entry.is_file():
                try:
                    stat = entry.stat()
                    file_obj = File(
                        file_path=entry.path,
                        extension=os.path.splitext(entry.name)[1],
                        file_name=entry.name,
                        file_size_bytes=stat.st_size,
                    )
                    directory.files.append(file_obj)
                except OSError:
                    # Skip files we cannot access
                    continue
            elif entry.is_dir():
                if depth > 0:
                    child_dir = explore_structure(entry.path, depth - 1, ignore_names)
                    directory.children.append(child_dir)

    except OSError:
        # If we can't access the directory, just return the empty structure for it
        pass

    return directory
