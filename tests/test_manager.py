from phaistos import Manager


def test_manager_as_singleton():
    assert id(
        Manager.start(discover=False)  # First instantiation
    ) == id(
        Manager.start(discover=False)  # Second instantiation - should return the same instance
    )
    assert id(
        Manager()
    ) == id(
        Manager()
    )
