import time

class EventWatcherDataStore:
    def __init__(self):
        self._data = {}

    def get(self, stream_id, event_id):
        epoch, value = self._data.get(f"{stream_id}_{event_id}", (0, -1))
        if not value or time.time() - 3000 > epoch:
            return None
        else:
            return value

    def set(self, stream_id, event_id, value):
        self._data[f"{stream_id}_{event_id}"] = (time.time(), value)
