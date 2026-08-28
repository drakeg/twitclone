"""Regression coverage for application import boundaries."""

import subprocess
import sys


def test_application_imports_cleanly_in_fresh_python_process():
    result = subprocess.run(
        [sys.executable, "-c", "import application; assert application.application is not None"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr


def test_resource_endpoints_are_blueprint_namespaced_in_fresh_process():
    code = (
        "import application; app = application.application; "
        "assert 'index' in app.view_functions; "
        "assert 'resources.index' in app.view_functions; "
        "assert app.view_functions['index'] is not app.view_functions['resources.index']; "
        "assert any(rule.endpoint == 'resources.index' and rule.rule == '/resources/' "
        "for rule in app.url_map.iter_rules())"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
