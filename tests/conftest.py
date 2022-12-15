import pytest


@pytest.fixture(scope="function")
def tf():
    from metaform.compose import MetaFormer

    return MetaFormer()


@pytest.fixture(scope="function")
def compose():
    from metaform import compose

    return compose
