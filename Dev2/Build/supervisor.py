########################################################################################################################
# *** Copyright Notice ***
#
# "Price Based Local Power Distribution Management System (Local Power Distribution Manager) v2.0"
# Copyright (c) 2017, The Regents of the University of California, through Lawrence Berkeley National Laboratory
# (subject to receipt of any required approvals from the U.S. Dept. of Energy).  All rights reserved.
#
# If you have questions about your rights to use or distribute this software, please contact
# Berkeley Lab's Innovation & Partnerships Office at  IPO@lbl.gov.
########################################################################################################################

"""
The supervisor's role is to

"""

from Build.priority_queue import PriorityQueue


class Supervisor:

    def __init__(self):
        self._event_queue = PriorityQueue()  # queue items are device_ids prioritized by next event time
        self._devices = {}  # dictionary of device_id's mapping to their associated devices. All devices in simulation.

    ##
    # Method to get the device pointer from a device_id, called by devices when they receive a message from a
    # device that they do not recognize.

    def get_device(self, device_id):
        if device_id in self._devices.keys():
            return self._devices[device_id]
        else:
            raise ValueError("There is no such requested device in the simulation")

    ##
    # Returns the list of all devices in the simulation.
    #
    def all_devices(self):
        return self._devices.values()

    ##
    # Given a device, adds a mapping from device_id to that device
    # @param device the device to add to the supervisor device dictionary
    #

    def register_device(self, device):
        device_id = device.get_id()
        self._devices[device_id] = device

    ##
    # Registers an event
    # @param device_id the device to add to the supervisor device dictionary
    # @param time_of_next_event the time of the next event to add to event queue

    def register_event(self, device_id, time_of_next_event):
        self._event_queue.add(device_id, time_of_next_event)

    ##
    # Runs the next event in the supervisor's queue, advancing that device's local time to that point
    # Assumes queue is not empty. Call has_next_event first.

    def occur_next_event(self):
        device_id, time_of_next_event = self._event_queue.pop()
        if device_id in self._devices.keys():
            device = self._devices[device_id]
            device.update_time(time_of_next_event)  # set the device's local time to the time of next event
            device.process_events()  # process all events at device's local time
            if device.has_upcoming_event():
                device_id, device_next_time = device.report_next_event_time()
                self.register_event(device_id, device_next_time)  # add the next earliest time for device
        else:
            raise KeyError("Device has not been properly initialized!")

    ##
    # Determines if the simulation is unfinished and there are unprocessed events in its queue

    def has_next_event(self):
        return not self._event_queue.is_empty()

    ##
    # Returns an (event, time_stamp) with next, or None.
    # Call has next event first to be safe.
    def peek_next_event(self):
        if self.has_next_event():
            return self._event_queue.peek()
        else:
            return None

    ##
    # Called at the end of the simulation. Finishes each device and instructs them to write their energy
    # consumption calculations
    # end_time the time of the finish event, to update each device to so they can perform their calculations.
    def finish_all(self, end_time):
        for device in self.all_devices():
            device.finish(end_time)