from utils.string_helpers import split_absolute_ref


def test_split_absolute_ref():
    data_source = "AnalysisPlatformDS"
    path = "4483c9b0-d505-46c9-a157-94c79f4d7a6a"
    attribute = "jobs.0"
    example_reference = f"dmss://{data_source}/{path}.{attribute}"
    data_source_result, path_result, attribute_result = split_absolute_ref(example_reference)
    assert data_source == data_source_result
    assert path == path_result
    assert attribute == attribute_result

    data_source = "AnalysisPlatformDS"
    path = "4483c9b0-d505-46c9-a157-94c79f4d7a6a"
    example_reference_2 = f"dmss://{data_source}/{path}"
    data_source_result, path_result, attribute_result = split_absolute_ref(example_reference_2)
    assert data_source == data_source_result
    assert path == path_result
    assert attribute_result == ""
