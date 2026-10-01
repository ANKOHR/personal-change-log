import pytest
from personal_change_log.fixtures import generate
from personal_change_log.cli import load_input


@pytest.fixture
def fixture_dir(tmp_path):
    path = tmp_path / "inputs"
    generate(path)
    return path


@pytest.fixture
def result(fixture_dir):
    return load_input(fixture_dir)[0]
