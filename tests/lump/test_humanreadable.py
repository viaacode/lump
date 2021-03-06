from lump.humanreadable import format_metric, format_binary
import pytest


@pytest.mark.parametrize('num,expected_output', [
    (0, '0.00B'),
    (0.5, '0.50B'),
    (-34.5, '-34.50B'),
    (1000, '1.00kB'),
    (1.56e10, '15.60GB'),
    (43.328453e20, '4.33ZB'),
    (-2.12345e24, '-2.12YB'),
    (1e18, '1.00EB'),
])
def test_metric_basic(num, expected_output):
    assert format_metric(num) == expected_output


@pytest.mark.parametrize('num,expected_output', [
    (0, '0.00B'),
    (0.5, '0.50B'),
    (-34.5, '-34.50B'),
    (1024, '1.00KiB'),
    (1.56e10, '14.53GiB'),
    (2**40, '1.00TiB'),
    (2**80, '1.00YiB'),
    (1073741824, '1.00GiB'),
    (140737488355328, '128.00TiB'),
    (1099511627776, '1.00TiB'),
])
def test_binary_basic(num, expected_output):
    assert format_binary(num) == expected_output
