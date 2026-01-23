from typing import Callable
from .explore_structure import explore_structure
from .read_file import read_file
from .write_review import write_review

_callables: list[Callable] = [explore_structure, read_file, write_review]
TOOLS = {func.__name__: func for func in _callables}
