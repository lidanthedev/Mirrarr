import pytest
from app.providers.rivestream_provider import RiveSolver


@pytest.fixture
def python_solver():
    return RiveSolver()


@pytest.mark.parametrize(
    "input_val, expected",
    [
        (1418, "NGFmNjhjZDg="),
        ("1418", "NGFmNjhjZDg="),
        (12345, "LWJhNTQzZTI="),
        ("test", "NTEzMGQ3OWM="),
        ("rive", "LTYxYmNlNWU4"),
        ("0", "LTcwYjQ4OWI0"),
        ("", "NTRhYWRmNTg="),
    ],
)
def test_compare_against_known_values(python_solver, input_val, expected):
    """
    Test Python implementation against known expected values
    (derived from Deno runs).
    """
    assert python_solver.solve(input_val) == expected
