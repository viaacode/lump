from lump.humanreadable import format_metric, format_binary
import pytest


@pytest.mark.parametrize('num,expected_output', [
    (0, '0.00B'),
    (0.5, '0.50B'),
    (-34.5, '-34.50B'),
    (1000, '1.00kB'),
])
def test_metric_basic(num, expected_output):
    assert format_metric(num) == expected_output


@pytest.mark.parametrize('num,expected_output', [
    (0, '0.00B'),
    (0.5, '0.50B'),
    (-34.5, '-34.50B'),
    (1024, '1.00KiB'),
])
def test_binary_basic(num, expected_output):
    assert format_binary(num) == expected_output
