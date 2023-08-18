from typing import Tuple


def split_address(address: str) -> Tuple[str | None, str, str, str]:
    """Split an address into protocol, data_source, path and attribute.

    a reference is on the format {data_source_id}/{id}.{attribute}.

    Examples:
        "DataSource/$4483c9b0-d505.jobs.result" -> None, DataSource, $4483c9b0-d505, .jobs.result
        "dmss://DataSource/rootPackage/subPackage/entity.jobs.result" -> dmss, DataSource, rootPackage/subPackage/entity, .jobs.result
    """
    protocol = None
    if "://" in address:
        protocol = address.split("://")[0]
        address = address.split("://")[1]
    try:
        data_source, dotted_path = address.split("/", 1)
    except ValueError:
        raise ValueError(f"Reference '{address}' is not a valid absolute reference")
    attribute = ""
    path_or_id: str = dotted_path
    if "." in dotted_path:  # Dotted path has an attribute reference.
        path_or_id, attribute = dotted_path.split(".", 1)
    return protocol, data_source, path_or_id, attribute
