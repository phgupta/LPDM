""" A non-'smart' EUD that does not modulate its price based on any pricing information.
Model of all the simplest EUD's. """

from Build.eud import Eud


class FixedConsumption(Eud):

    def __init__(self, device_id, supervisor, total_runtime, modulation_interval, desired_power_level,
                 schedule=None, multiday=0, time=0, msg_latency=0):
        super().__init__(device_id=device_id, device_type="fixed_consumption", supervisor=supervisor,
                         time=time, msg_latency=msg_latency, schedule=schedule,
                         total_runtime=total_runtime, multiday=multiday, modulation_interval=modulation_interval)
        self._desired_power_level = desired_power_level

    ##
    # Always returns the device's fixed consumption levels
    def calculate_desired_power_level(self):
        return self._desired_power_level

    ##
    def begin_internal_operation(self):
        pass

    def end_internal_operation(self):
        pass

    def update_state(self):
        pass

    ##
    # If the fixed consumption does not receive all the power it would like, it simply continues to operate at the
    # lower specified level.
    def respond_to_power(self, received_power):
        pass

    def device_specific_calcs(self):
        pass
