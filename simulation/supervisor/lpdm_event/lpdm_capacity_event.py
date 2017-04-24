from lpdm_base_event import LpdmBaseEvent

class LpdmCapacityEvent(LpdmBaseEvent):
    def __init__(self, source_device_id, target_device_id, time, value):
        LpdmBaseEvent.__init__(self, source_device_id, target_device_id, time, value)
        self.event_type = "capacity"

