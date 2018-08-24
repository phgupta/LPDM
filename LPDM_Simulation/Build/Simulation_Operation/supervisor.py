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
The supervisor's role is to maintain knowledge of all devices in the simulation and the soonest upcoming event for each.
The supervisor then 'creates time' by updating the time of each device in serial fashion when they have the next
earliest event, and then telling that device to process all of its events. The supervisor is also responsible for
calculating some of the final simulation power statistics.
"""

import logging
import csv

from Build.Simulation_Operation.queue import PriorityQueue
# from Build.Simulation_Operation.supply_demand_model import supply_demand_model


class Supervisor:

    def __init__(self):
        self._event_queue = PriorityQueue()  # queue items are device_ids prioritized by next event time
        self._devices = {}  # dictionary of device_id's mapping to their associated devices. All devices in simulation.
        self._logger = logging.getLogger("lpdm")  # Setup logging
        self._power_flow_state = [] # time series power flow data
        self._time_of_last_event = 0

    ##
    # Method to get the device pointer from a device_id, called by devices when they receive a message from a
    # device that they do not recognize.

    def get_device(self, device_id):
        if device_id in self._devices:
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
        if device_id not in self._devices:
            raise KeyError("Device has not been properly initialized!")

        device = self._devices[device_id]
        device.update_time(time_of_next_event)  # set the device's local time to the time of next event
        device.process_events()  # process all events at device's local time

        if self._time_of_last_event != time_of_next_event:
            # self._logger.info("last time: {}, next time: {}".format(self._time_of_last_event, time_of_next_event))
            self.update_stats(time_of_next_event) # update the power flow state tracker

        if device.has_upcoming_event():
            device_id, device_next_time = device.report_next_event_time()
            self.register_event(device_id, device_next_time)  # add the next earliest time for device

        self._time_of_last_event = time_of_next_event

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
    # Returns the total simulation power in and total simulation power out for the device.
    # Total simulation power in should approximately equal simulation power out, with small margin of error
    # allowed because of float rounding and because message latency slightly affects the calculations.

    def total_calcs(self):
        total_power_in = 0.0
        total_power_out = 0.0
        for device in self._devices.values():
            total_power_in += device._sum_power_in
            total_power_out += device._sum_power_out
        self._logger.info("total simulation power in: {} Wh".format(total_power_in))
        self._logger.info("total simulation power out: {} Wh".format(total_power_out))

    ##
    # Called at the end of the simulation. Finishes each device and instructs them to write their energy
    # consumption calculations
    # @param end_time the time of the finish event, to update each device to so they can perform their calculations.
    def finish_all(self, end_time):
        for device in self._devices.values():
            device.finish(end_time)
        self.total_calcs()
        with open('power_flow.csv', 'w', newline='') as csvfile:
            power_keys = list(self._power_flow_state[-1].keys()) # take last data point, which presumably has all keys
            dict_writer = csv.DictWriter(csvfile,power_keys)

            dict_writer.writeheader()
            dict_writer.writerows(self._power_flow_state)

    def update_demand_curve(self):
        # For each GC
        # Sweep price by broadcasting range of prices
        # Measure power draw
        # Export to CSV (GC ID, time, price, power)

        prices = [x * 0.01 for x in range(0, 50)]
        total_demand_curve = [0] * len(prices)
        gcs = (device for device in self._devices.values() if device.get_type() == "grid_controller")
        for gc in gcs:
            # self._logger.info("looping over gc")
            connected_devices = gc.get_connected_devices()
            euds = (connected_device for connected_device_id, connected_device in connected_devices.items() if connected_device_id.startswith("eud"))
            for eud in euds:
                    # self._logger.info("hi")
                    total_demand_curve = [a + b for a, b in zip(total_demand_curve, eud.generate_demand_curve(prices))]
        total_demand_curve = zip(prices,total_demand_curve)
        with open('demand.csv', 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(total_demand_curve)

    def update_stats(self,time_of_next_event):
        # self._logger.info("updating_stats")
        power_state = {}
        gcs = (device for device in self._devices.values() if device.get_type() == "grid_controller")
        for gc in gcs:
            power_state = {**power_state,**gc._loads}

        self._power_flow_state.append({'Time': time_of_next_event, **power_state})
