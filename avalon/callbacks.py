
import weakref
import traceback

from . import (
    _registered_event_handlers,
)

import logging
log = logging.getLogger(__name__)



def on(event, callback):
    """Call `callback` on `event`

    Register `callback` to be run when `event` occurs.

    Example:
        >>> def on_init():
        ...    print("Init happened")
        ...
        >>> on("init", on_init)
        >>> del on_init

    Arguments:
        event (str): Name of event
        callback (callable): Any callable

    """

    if event not in _registered_event_handlers:
        _registered_event_handlers[event] = weakref.WeakSet()

    events = _registered_event_handlers[event]
    events.add(callback)


def before(event, callback):
    """Convenience to `on()` for before-events"""
    on("before_" + event, callback)


def after(event, callback):
    """Convenience to `on()` for after-events"""
    on("after_" + event, callback)


def emit(event, args=None):
    """Trigger an `event`

    Example:
        >>> def on_init():
        ...    print("Init happened")
        ...
        >>> on("init", on_init)
        >>> emit("init")
        Init happened
        >>> del on_init

    Arguments:
        event (str): Name of event
        args (list, optional): List of arguments passed to callback

    """

    callbacks = _registered_event_handlers.get(event, set())
    args = args or list()

    for callback in callbacks:
        try:
            callback(*args)
        except Exception:
            log.warning(traceback.format_exc())


