from pathlib import Path
from ansiblelint.file_utils import kind_from_path


def test_kind_from_path_python_basic():
    """Ensure Python files are not treated as YAML."""
    p = Path("example.py")

    assert kind_from_path(p, base=True) == "text/x-python"
    assert kind_from_path(p, base=False) == "python"


def test_kind_from_path_mock_module():
    """Ensure mock module paths are not treated as YAML."""
    p = Path(
        ".ansible/collections/ansible_collections/x/y/plugins/modules/test.py"
    )

    assert kind_from_path(p, base=True) == "text/x-python"
    assert kind_from_path(p, base=False) == "python"
