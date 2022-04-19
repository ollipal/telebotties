from abc import ABC, abstractmethod

from ..callback_executor import CallbackExecutor
from ..constants import KEYS
from ..function_utils import get_params, takes_parameter

SENDER_REPR = {
    "any": "",
    "host": ", host_only=True",
}


class ControlBase(ABC):
    _event_callbacks = {}
    _controls = []

    def __init__(
        self,
        type,
        keys,
        host_only,
        start_event,
        alternatives,
        amount,
    ):
        # TODO makey assertions key makes sense, others type boolean
        # Make sure makes sense

        self._keys = keys
        self._sender = "host" if host_only else "any"
        self._state = start_event.name
        self._latest_event = start_event
        self._alternative_map = {}
        self._state_callbacks = {}
        self._callbacks_added = False

        for key in self._keys:
            # Checks all keys are allowed before the assertion next
            self._register_key(key)
        assert len(keys) == len(
            set(keys)
        ), "Control cannot have multiple same keys"

        self._data = {
            "type": type,
            "keys": {key: [key] for key in keys},
            "titles": {},
            "has_callbacks": [],
            "without_callbacks": keys,
            "amount": amount,
        }
        ControlBase._controls.append(self)

        if alternatives is not None:
            self._register_alternative_keys(alternatives)

    @staticmethod
    def _get_control_datas():
        return [control_._data for control_ in ControlBase._controls]

    def _add_key_to_has_callbacks(self, key, title, tier):
        if title is None:
            tier = 0

        if key not in self._data["has_callbacks"]:
            self._data["has_callbacks"].append(key)
            self._data["without_callbacks"].remove(key)

        if (
            key not in self._data["titles"]
            or self._data["titles"][key][1] < tier
        ):
            self._data["titles"][key] = (title, tier)

    @staticmethod
    def _get_callbacks(event):
        if event._callback_key not in ControlBase._event_callbacks:
            return []

        return ControlBase._event_callbacks[
            event._callback_key
        ]._get_instance_callbacks(event)

    def _register_alternative_keys(self, alternatives):
        assert len(alternatives) == len(self._keys)
        for key, alternative in zip(self._keys, alternatives):
            self._register_key(alternative)
            self._alternative_map[alternative] = key
            self._data["keys"][key].append(alternative)

    def _register_key(self, key):
        if key not in KEYS:
            if isinstance(key, str) and key.upper() in KEYS:
                raise RuntimeError(
                    f"Unknown key '{key}', did you mean '{key.upper()}'?"
                )
            else:
                raise RuntimeError(
                    f"Unknown key '{key}'"
                )  # TODO link to allowed keys

        new_event_callback_keys = self._get_event_callback_keys(
            key, self._sender
        )
        for callback_key in new_event_callback_keys:
            if callback_key in ControlBase._event_callbacks:
                raise RuntimeError(
                    f"Cannot create {self}. "
                    f"{ControlBase._event_callbacks[callback_key]} already "
                    "handles some of the same control events. Only one "
                    "control can handle each Event."
                )
            ControlBase._event_callbacks[callback_key] = self

    @property
    def latest_event(self):
        return self._latest_event

    @abstractmethod
    def _process_event(self, event):
        pass

    @abstractmethod
    def _get_release_callbacks_and_event(self, sender, time):
        pass

    @abstractmethod
    def __repr__(self):
        pass

    def _get_instance_callbacks(self, event):
        if event._key in self._alternative_map:
            event._key = self._alternative_map[event._key]

        ignore, event = self._process_event(event)
        self._state = event.name  # Update state even if no callbacks
        if ignore or event.name not in self._state_callbacks:
            return []

        self._latest_event = event
        event._set_active_method(lambda: self.latest_event == event)

        return self._state_callbacks[event.name]

    @staticmethod
    def _takes_event(function):
        return takes_parameter(get_params(function), "event")

    def _add_state_callback(self, name, function):
        if self._takes_event(function):  # Also validates other parameters
            CallbackExecutor.add_to_takes_event(function)

        if name in self._state_callbacks:
            self._state_callbacks[name].append(function)
        else:
            self._state_callbacks[name] = [function]

        self._callbacks_added = True

    def _sender_origin_repr(self):
        return SENDER_REPR[self._sender]

    def _get_event_callback_keys(self, key, sender):
        if sender == "any":
            return [
                (key, "host"),
                (key, "player"),
            ]
        elif sender == "host":
            return [
                (key, "host"),
            ]
        else:
            RuntimeError("This should not happen")
