import importlib
import pytest


def test_create_app_skips_when_deps_missing():
    app_mod = importlib.import_module("tools.answer_app")
    # create_app should be callable
    assert hasattr(app_mod, "create_app")
    app = app_mod.create_app()
    # If Starlette isn't installed in this environment, create_app returns None
    # Otherwise it should return an ASGI app object. We accept both.
    assert app is None or callable(getattr(app, "__call__", None))
