from typing import Callable
from .explore_structure import explore_structure
from .read_file import read_file
from .write_review import write_review
from .write_todos import write_todos
from .update_todo import update_todo
from .remove_todo import remove_todo

_callables: list[Callable] = [
    explore_structure,
    read_file,
    write_review,
    write_todos,
    update_todo,
    remove_todo,
]
TOOLS = {func.__name__: func for func in _callables}
