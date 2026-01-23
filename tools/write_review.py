def write_review(review: str, file_to_write: str) -> None:
    with open(file_to_write, "w") as f:
        f.write(review)
