import os
import sys
import pytest


@pytest.fixture(scope="function")
def tf():
    sys.path.insert(
        0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "metaform")
    )
    from compose import MetaFormer

    return MetaFormer()
