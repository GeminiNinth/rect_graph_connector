"""
Simple event system for model state change notifications.
"""


class Event:
    """
    A simple event system that allows subscribers to be notified when an event occurs.
    Used for implementing the observer pattern for model state changes.
    """

    def __init__(self):
        """Initialize an empty list of subscribers."""
        self._subscribers = []

    def subscribe(self, callback):
        """
        Add a subscriber callback function.

        Args:
            callback: A function to call when the event is emitted
        """
        if callback not in self._subscribers:
            self._subscribers.append(callback)

    def unsubscribe(self, callback):
        """
        Remove a subscriber callback function.

        Args:
            callback: The function to remove from subscribers
        """
        if callback in self._subscribers:
            self._subscribers.remove(callback)

    def emit(self, *args, **kwargs):
        """
        Emit the event, notifying all subscribers.

        Args:
            *args: Positional arguments to pass to the callbacks
            **kwargs: Keyword arguments to pass to the callbacks
        """
        for subscriber in self._subscribers:
            subscriber(*args, **kwargs)
