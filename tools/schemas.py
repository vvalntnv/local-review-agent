from pydantic import BaseModel


class File(BaseModel):
    file_path: str
    extension: str
    file_name: str
    file_size_bytes: int


class Directory(BaseModel):
    root_file_path: str
    files: list[File] = []
    children: list[Directory] = []
