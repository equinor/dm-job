from typing import Tuple


def split_address(address: str) -> Tuple[str, str, str, str]:
    """Split an address into protocol, data_source, path and attribute.

    address: Can be on one of the formats:
        - {protocol}://{data_source_id}/{id}.{attribute} (protocol is optional)
        - {data_source_id}/{root_package}/{sub_package}/{entity}.{attribute}
        - /{data_source_id}/{root_package}/{sub_package}/{entity}
        - {protocol}://{data_source_id}

    Examples:
        - "DataSource/$4483c9b0-d505.jobs.result" -> None, DataSource, $4483c9b0-d505, .jobs.result
        - "dmss://DataSource/rootPackage/subPackage/entity.jobs.result" -> dmss, DataSource, rootPackage/subPackage/entity, .jobs.result
    """
    protocol = ""
    if "://" in address:
        protocol = address.split("://")[0]
        address = address.split("://")[1]
    elif address[0] == "/":
        address = address.replace("/", "", 1)

    if "/" not in address:
        data_source, dotted_path = address, ""
    else:
        data_source, dotted_path = address.split("/", 1)
    attribute = ""
    path_or_id: str = dotted_path
    if "." in dotted_path:  # Dotted path has an attribute reference.
        path_or_id, attribute = dotted_path.split(".", 1)
    return protocol, data_source, path_or_id, attribute
