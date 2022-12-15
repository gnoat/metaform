import os
import sys
import pytest


def enter_module(file_from_root="metaform"):
    return sys.path.insert(
        0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "metaform")
    )


@pytest.fixture(scope="function")
def tf():
    enter_module("metaform")
    from metaform.compose import MetaFormer

    return MetaFormer()


@pytest.fixture(scope="function")
def compose():
    enter_module("metaform")
    from metaform import compose

    return compose
