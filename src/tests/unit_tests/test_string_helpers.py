import unittest

from utils.string_helpers import split_address


class TestStringHelpers(unittest.TestCase):
    def test_split_address_1(self):
        data_source = "DataSource"
        id = "$4483c9b0-d505"
        attribute = "jobs.result"
        example_address = f"{data_source}/{id}.{attribute}"
        protocol, data_source_result, id_result, attribute_result = split_address(example_address)
        assert protocol == ""
        assert data_source == data_source_result
        assert id == id_result
        assert attribute == attribute_result

    def test_split_address_2(self):
        data_source = "DataSource"
        path = "root/sub/entity"
        attribute = "jobs.0"
        example_address = f"{data_source}/{path}.{attribute}"
        protocol, data_source_result, path_result, attribute_result = split_address(example_address)
        assert protocol == ""
        assert data_source == data_source_result
        assert path == path_result
        assert attribute == attribute_result

    def test_split_address_3(self):
        data_source = "DataSource"
        path = "root_package/sub_package"
        example_address = f"{data_source}/{path}"
        protocol, data_source_result, path_result, attribute_result = split_address(example_address)
        assert protocol == ""
        assert data_source == data_source_result
        assert path == path_result
        assert attribute_result == ""

    def test_split_address_4(self):
        protocol = "dmss"
        data_source = "DataSource"
        id = "$4483c9b0-d505-x"
        attribute = "jobs.0.content[0]"
        example_address = f"{protocol}://{data_source}/{id}.{attribute}"
        protocol_result, data_source_result, id_result, attribute_result = split_address(example_address)
        assert protocol == protocol_result
        assert data_source == data_source_result
        assert id == id_result
        assert attribute == attribute_result

    def test_split_address_5(self):
        protocol = "dmss"
        data_source = "DataSource"
        example_address = f"{protocol}://{data_source}"
        protocol_result, data_source_result, id_result, attribute_result = split_address(example_address)
        assert protocol == protocol_result
        assert data_source == data_source_result
        assert id_result == ""
        assert attribute_result == ""

    def test_split_address_6(self):
        data_source = "DataSource"
        id = "$4483c9b0-d505-x"
        example_address = f"/{data_source}/{id}"
        protocol_result, data_source_result, id_result, attribute_result = split_address(example_address)
        assert protocol_result == ""
        assert data_source == data_source_result
        assert id == id_result
        assert attribute_result == ""
