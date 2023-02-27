from typing import Tuple


def split_absolute_ref(absolute_reference: str) -> Tuple[str, str, str]:
    protocol, reference = absolute_reference.split("://", 1)
    try:
        data_source, dotted_path = reference.split("/", 1)
    except ValueError:
        raise ValueError(f"Reference '{absolute_reference}' is not a valid absolute reference")
    attribute = ""
    path = dotted_path
    if "." in dotted_path:  # Dotted path has a attribute reference.
        path, attribute = dotted_path.split(".", 1)
    return data_source, path, attribute
