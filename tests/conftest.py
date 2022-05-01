import os
import pathlib
import shutil
from typing import Optional

import pytest
from devtools import debug


class Helpers:
    """Contains (possibly) useful random utilities

    Combined with the fixture that returns this class it is easy to share
    common functions across multiple tests. Simply use `helpers` as a parameter
    for the respective test function.

    Helpers should be static methods generally.
    """

    separator = "-" * 80
    should_debug = True

    @staticmethod
    def wrapped_debug(element, description: Optional[str] = None) -> None:
        """Calls devtools `debug` and adds horizontal lines and description.

        Args:
            element: Whatever that should be printed by devtools `debug`.
            description (Optional[str], optional): Description. Defaults to None.
        """

        if Helpers.should_debug:
            print(f"\n{Helpers.separator}\n")
            if description:
                print(f"{description}\n")
            debug(element)
            print(f"\n{Helpers.separator}\n")


@pytest.fixture
def helpers():
    """Fixture that returns `Helpers` class.

    Returns:
        Helpers: Helpers class.
    """

    return Helpers


FILE = __file__


@pytest.fixture
def data_path(tmp_path: pathlib.Path):
    """Fixture that returns a temporary path with data.

    If the directory `data` exists, its content will be copied to a temporary
    location.

    Args:
        tmp_path (pathlib.Path): Path to temporary location.

    Returns:
        pathlib.Path: Path to temporary location.
    """

    source = pathlib.Path(FILE).parent.joinpath("data")
    destination = tmp_path

    if source.is_dir():
        for item in os.listdir(source):
            s = os.path.join(source, item)
            print(s)
            d = os.path.join(destination, item)
            print(d)
            if os.path.isdir(s):
                shutil.copytree(s, d, symlinks=False, ignore=None)
            else:
                shutil.copy2(s, d)

    return tmp_path
