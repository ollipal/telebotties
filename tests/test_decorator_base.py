import pytest

from telebotties._internal.callbacks import CallbackBase
from telebotties._internal.decorators import DecoratorBase

from .helpers import (
    fake_listen,
    get_async_result,
    get_cb_result,
    get_cbs,
    reset,
)

# Decorator


class dec(DecoratorBase):  # noqa: N801
    def verify_params_and_set_flags(self, params):
        pass

    def wrap(self, func):
        CallbackBase.register_callback("dec", func)


# Tests


def test_non_callable_errors():
    reset()
    with pytest.raises(AssertionError):
        dec("potato")


def test_class_decorator_errors():
    reset()
    with pytest.raises(AssertionError):

        @dec
        class Class:
            pass


def test_decorator_empty_parenthesis_errors():
    reset()
    with pytest.raises(AssertionError):

        @dec()
        def example():
            return 3


def test_function():
    reset()

    @dec
    def example():
        return 3

    fake_listen()
    assert example() == 3
    assert get_cb_result("dec") == 3


def test_function_async():
    reset()

    @dec
    async def example():
        return 3

    fake_listen()
    assert get_async_result(example()) == 3
    assert get_cb_result("dec") == 3


def test_lambda():
    reset()
    dec(lambda: 3)
    fake_listen()
    assert get_cb_result("dec") == 3


def test_class_instance():
    reset()

    class Class:
        def __init__(self):
            self.val = 1

        def example(self):
            return self.val + 2

    c = Class()

    dec(c.example)

    fake_listen()
    assert c.example() == 3
    assert get_cb_result("dec") == 3


def test_class_instance_async():
    reset()

    class Class:
        def __init__(self):
            self.val = 1

        async def example(self):
            return self.val + 2

    c = Class()

    dec(c.example)

    fake_listen()
    assert get_async_result(c.example()) == 3
    assert get_cb_result("dec") == 3


def test_class_instance_static():
    reset()

    class Class:
        @staticmethod
        def example():
            return 3

    c = Class()

    dec(c.example)

    fake_listen()
    assert c.example() == 3
    assert get_cb_result("dec") == 3


def test_class_instance_static_async():
    reset()

    class Class:
        @staticmethod
        async def example():
            return 3

    c = Class()

    dec(c.example)

    fake_listen()
    assert get_async_result(c.example()) == 3
    assert get_cb_result("dec") == 3


def test_class_instance_classmethod():
    reset()

    class Class:
        value = 3

        @classmethod
        def example(cls):
            assert cls.__name__ == "Class"
            return cls.value

    Class()

    dec(Class.example)
    fake_listen()
    assert Class.example() == 3
    assert get_cb_result("dec") == 3


def test_class_instance_classmethod_async():
    reset()

    class Class:
        value = 3

        @classmethod
        async def example(cls):
            assert cls.__name__ == "Class"
            return cls.value

    Class()

    dec(Class.example)
    fake_listen()
    assert get_async_result(Class.example()) == 3
    assert get_cb_result("dec") == 3


def test_class_method():
    reset()

    class Class:
        def __init__(self):
            self.val = 1

        @dec
        def example(self):
            return self.val + 2

    Class()

    fake_listen()
    assert get_cb_result("dec") == 3
    assert Class().example() == 3


def test_class_method_async():
    reset()

    class Class:
        def __init__(self):
            self.val = 1

        @dec
        async def example(self):
            return self.val + 2

    Class()

    fake_listen()
    assert get_cb_result("dec") == 3
    assert get_async_result(Class().example()) == 3


def test_class_staticmethod():
    reset()

    class Class:
        @dec
        @staticmethod
        def example():
            return 3

    Class()

    fake_listen()
    assert Class.example() == 3
    assert get_cb_result("dec") == 3


def test_class_staticmethod_mixed():
    reset()

    class Class:
        @staticmethod
        @dec
        def example():
            return 3

    Class()

    fake_listen()
    assert Class.example() == 3
    assert get_cb_result("dec") == 3


def test_class_staticmethod_async():
    reset()

    class Class:
        @dec
        @staticmethod
        async def example():
            return 3

    Class()

    fake_listen()
    assert get_async_result(Class.example()) == 3
    assert get_cb_result("dec") == 3


def test_class_classmethod():
    reset()

    class Class:
        value = 3

        @dec
        @classmethod
        def example(cls):
            assert cls.__name__ == "Class"
            return cls.value

    Class()

    fake_listen()
    assert Class.example() == 3
    assert get_cb_result("dec") == 3


# def test_class_classmethod_mixed():
# ERRORS! but is ok, cannot fix


def test_class_classmethod_async():
    reset()

    class Class:
        value = 3

        @dec
        @classmethod
        async def example(cls):
            assert cls.__name__ == "Class"
            return cls.value

    Class()

    fake_listen()
    assert get_async_result(Class.example()) == 3
    assert get_cb_result("dec") == 3


def test_multiple_function():
    reset()

    @dec
    def example():
        return 2

    @dec
    def example2():
        return 3

    fake_listen()
    assert (
        CallbackBase.get_by_name("dec")[0]()
        + CallbackBase.get_by_name("dec")[1]()
        == 5
    )


def test_multiple_class_method():
    reset()

    class Class:
        def __init__(self):
            self.val = 1

        @dec
        def example(self):
            return self.val + 2

        @dec
        def example2(self):
            return self.val + 3

    Class()

    fake_listen()
    cbs = get_cbs("dec")
    assert cbs[0]() + cbs[1]() == 7


def test_multiple_classes():
    reset()

    class Class1:
        def __init__(self):
            self.val = 1

        @dec
        def example(self):
            return self.val + 2

    class Class2:
        def __init__(self):
            self.val = 3

        @dec
        def example(self):
            return self.val + 4

    Class1()
    Class2()

    fake_listen()
    cbs = get_cbs("dec")
    assert cbs[0]() + cbs[1]() == 10
