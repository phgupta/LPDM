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

A device is a semi-autonomous agent in the simulation, which utilizes messaging and power flows to interact
with other devices. A device will be a real world appliance with 'smart' functionality: it maintains in
computerized memory a history of its transactions, its connected devices, a local time, events which
it will have to process at a set time, and other state variables.

In its implementation, a device maintains a priority queue of functions prioritized by time,
which it then processes when instructed that time has passed by the
supervisor.

Devices also maintain common functionality of messaging and receiving messages.
Any type of device must be able to receive any type of message, but the sending
of messages can be limited to the specific type of device (not all device types can send
all message types).

Note on Device Identification (include in Documentation).

All GC's Device ID's must begin with 'GC'.
All EUD's Device ID's must begin with 'EUD'.
All Utility Meter's Device ID"s must begin with UM.
All PV Device ID's must begin with PV.
"""

from .priority_queue import PriorityQueue
from .event import Event
from .message import Message, MessageType
from . import message_formatter
from abc import ABCMeta, abstractmethod
import logging


class Device(metaclass=ABCMeta):

    ##
    # Initialize a device.
    #
    # @param device_id unique device ID. Must begin with type of device (see documentation).
    # @param device_type the type of this device (the most specific class descriptor)
    # @param uuid the device's emergency shutdown priority
    # @param time device's local time, in seconds. This will be updated by the supervisor.
    # @param msg_latency the delay time before this device processes a received message.
    # @param connected_devices a list of connected devices for this Device.

    def __init__(self, device_id, device_type, supervisor, time=0, msg_latency=0, schedule=None,
                 connected_devices=None):

        if connected_devices is None:
            self._connected_devices = {}
        else:
            self._connected_devices = {device.get_id(): device for device in connected_devices}

        self._device_id = device_id
        self._device_type = device_type
        self._queue = PriorityQueue()
        self._supervisor = supervisor
        self._time = time
        self._msg_latency = msg_latency
        self._time_last_power_in_change = time  # records the last time power levels into device changed
        self._time_last_power_out_change = time  # records the last time power levels out of device changed
        self._power_in = 0.0  # the power being consumed by the device (Watts, must be > 0)
        self._power_out = 0.0  # the power being distributed by the device (Watts, must be > 0)
        self._sum_power_out = 0.0  # Record the total energy produced by this device (wH)
        self._sum_power_in = 0.0  # Record the total energy produced by this device (wH)

        if schedule:
            self.setup_schedule(schedule)

        self._logger = logging.getLogger("lpdm")  # Setup logging
        self._logger.info(
            self.build_log_notation("initialize {} - {}".format(self._device_id, self._device_type))
        )

    # ____________________________ Maintenance Functions _________________________________#

    ##
    # Getter for the Device's ID
    # We maintain ID as a protected field to avoid external modifications during messaging
    # @return the device's ID
    def get_id(self):
        return self._device_id

    ##
    # Updates the local time of the device.
    # This method is only called by the Supervisor once it is about to process a next initial event.
    # @param new_time the time to update to
    def update_time(self, new_time):
        self._time = new_time

    ##
    # Sets the power level into the device. Call this method when setting absolute power levels
    # e.g. turning the device off
    #
    # @param power_in the new amount of power in to device (non-negative).

    def set_power_in(self, power_in):
        if power_in >= 0:
            self.sum_power_in()  # record all power usage at the previous power level.
            self._power_in = power_in
        else:
            raise ValueError("Power Level In Must Be Non-Negative")

    ##
    # Sets the power level out of the device. Call this method when setting absolute power levels
    # e.g. turning the device off
    #
    # @param power_in the new amount of power in to device (non-negative).

    def set_power_out(self, power_out):
        if power_out >= 0:
            self.sum_power_out()  # record all previous power usage at the previous level.
            self._power_out = power_out
        else:
            raise ValueError("Power Level Out Must Be Non-Negative")

    ##
    # After a device has changed the quantity of power it is sending/receiving, modify the power in and power out.
    # Call whenever a load has been changed on this device.
    # @param prev_power the previous power flow from this device's perspective (in positive, out negative)
    # @param new_power the new power flow from this device's perspective (in positive, out negative)
    def recalc_sum_power(self, prev_power, new_power):
        self.sum_power_in()  # log power usage at previous power level.
        self.sum_power_out()
        if prev_power >= 0:
            if new_power >= 0:
                self._power_in += (new_power - prev_power)
            elif new_power < 0:
                self._power_in -= prev_power
                self._power_out -= new_power
        elif prev_power < 0:
            if new_power >= 0:
                self._power_in += new_power
                self._power_out += prev_power
            elif new_power < 0:
                self._power_out += (new_power - prev_power)

    ##
    # Keeps a running total of the energy output by the device
    # Call this method whenever power_out level changes.

    def sum_power_out(self):
        time_diff = self._time - self._time_last_power_out_change
        if time_diff > 0:
            self._sum_power_out += self._power_out * (time_diff / 3600.0)  # Return in wH
        self._time_last_power_out_change = self._time

    ##
    # Keeps a running total of the energy consumed by the device
    # Call this method whenever power_in level changes.

    def sum_power_in(self):
        time_diff = self._time - self._time_last_power_in_change
        if time_diff > 0:
            self._sum_power_in += self._power_in * (time_diff / 3600.0)  # Return in wH
        self._time_last_power_in_change = self._time

    #  ______________________________________Internal State Functions _________________________________#

    ##
    # Adds an event to the device's event queue and reports that event to the supervisor
    # Will replace any existing event with the new value. Hence, only one event type at a time
    # @param event the event to add to the event queue
    # @param time_stamp the time to associate with the event in the queue

    def add_event(self, event, time_stamp):
        self._queue.add(event, time_stamp)
        device_id, next_time = self.report_next_event_time()
        self._supervisor.register_event(device_id, next_time)

    ##
    # Process all events in the device's queue with a given time_stamp.
    # This function should be called after advance_time has been called by the supervisor.
    def process_events(self):
        if self.has_upcoming_event():
            event, time_stamp = self._queue.peek()
            if time_stamp < self._time:
                raise ValueError("Time was incremented while there was an unprocessed event.")
            while time_stamp == self._time and self.has_upcoming_event():
                # process current events.
                self._queue.pop()
                event.run_event()
                if self.has_upcoming_event():
                    event, time_stamp = self._queue.peek()

    def has_upcoming_event(self):
        return not self._queue.is_empty()

    ##
    # Report the time of the next earliest event in the device's event queue
    # Assumes the event queue is not empty. Call has_upcoming_event first.
    # @return a tuple of device's ID and the time of its next event

    def report_next_event_time(self):
        if not self.has_upcoming_event():
            raise ValueError("No upcoming events for this device")
        next_event, time_stamp = self._queue.peek()
        return self._device_id, time_stamp

    #  ______________________________________ Messaging/Interactive Functions_________________________________#

    ##
    # Receiving a message is modelled as putting an event with the message a certain delay after the function call.
    # @param message the message to receive.
    def receive_message(self, message):
        self.add_event(Event(self.read_message, message), message.time + self._msg_latency)

    ##
    # Reads a message and responds based on its message type
    # @param message a message to be read (must be a message object)
    def read_message(self, message):
        if message:
            self._logger.info(self.build_log_notation(
                "Read {} from {} with value {}".format(message.message_type, message.sender_id, message.value)))
            if message.message_type == MessageType.REGISTER:
                self.process_register_message(message.sender_id, message.value)
            elif message.sender_id in self._connected_devices.keys():  # Only read other messages from verified devices.
                if message.message_type == MessageType.POWER:
                    self.process_power_message(message.sender_id, message.value)
                elif message.message_type == MessageType.PRICE:
                    self.process_price_message(message.sender_id, message.value)
                elif message.message_type == MessageType.ALLOCATE:
                    self.process_allocate_message(message.sender_id, message.value)
                elif message.message_type == MessageType.REQUEST:
                    self.process_request_message(message.sender_id, message.value)
                else:
                    raise NameError('Unverified Message Type')

    ##
    # Registers or unregisters a given device from the device's connected device list
    # @param device the device to register or unregister from connected devices
    # @param that device's id
    # @param value positive to register, 0 or negative to unregister

    def register_device(self, device, device_id, value):
        if value > 0 and device_id not in self._connected_devices.keys():
            self._connected_devices[device_id] = device
            self._logger.info(
                self.build_log_notation("registered {}".format(device_id))
            )
        else:
            if device_id in self._connected_devices:
                del self._connected_devices[device_id]  # unregister
                self._logger.info(
                    self.build_log_notation("unregistered {}".format(device_id))
                )
            else:
                print("No Such Device To Unregister")

    ##
    # Method to be called when the device receives a register message, indicating a device
    # is seeking to register or unregister
    #
    # @param sender the sender of the message informing of registering.
    # @param value positive if sender is registering negative if unregistering

    def process_register_message(self, sender_id, value):
        if sender_id in self._connected_devices.keys():
            sender = self._connected_devices[sender_id]
        else:
            sender = self._supervisor.get_device(sender_id)  # not in local table. Ask supervisor for the pointer to it.
        self.register_device(sender, sender_id, value)

    ##
    # Method to be called when the device wants to register or unregister with another device
    # @param target_id the device to receive the register message
    # @param value positive if registering negative if unregistering

    def send_register_message(self, target_id, value):
        if target_id in self._connected_devices.keys():
            target = self._connected_devices[target_id]
        else:
            raise ValueError("This device is not connected to the message recipient")
            # LOG THIS ERROR AND ALL ERRORS.
        self._logger.debug(self.build_log_notation(
            "REGISTER to {}".format(target_id), tag="register msg", value=value))
        target.receive_message(Message(self._time, self._device_id, MessageType.REGISTER, value))

    ##
    # Method to be called when device is entering the grid, and is seeking to register with other devices.

    # @param device_list the connected list of devices to add to its connected device list and to inform it has
    # registered. Must be devices themselves (not ID's).
    def engage(self, device_list):
        for device in device_list:
            device_id = device.get_id()
            self._connected_devices[device_id] = device
            self.send_register_message(device_id, 1)

    ##
    # Method to be called when the device receives a power message, indicating power flows
    # have changed between two devices (either receiving or providing).
    #
    # @param sender the sender of the message providing or receiving the new power
    # @param new_power the value of power flow from sender's perspective
    # positive if sender is receiving, negative if sender is providing.

    @abstractmethod
    def process_power_message(self, sender_id, new_power):
        pass

    ##
    # Method to be called when device receives a price message
    #
    # @param new_price the new price value
    #  TODO: This occurs when a device sends a price message. Internal price modulation vs external? Different funcs?

    @abstractmethod
    def process_price_message(self, sender_id, new_price):
        pass

    ##
    # Method to be called when device receives a request message, indicating a device is requesting to
    # either provide or receive the requested quantity of power.
    #
    # @param request_amt the amount the sending device is requesting to receive (positive) or send (negative)
    @abstractmethod
    def process_request_message(self, sender_id, request_amt):
        pass

    ##
    # Method to be called once device has allocated to provide a given quantity of power to another device,
    # or to receive a given quantity of power. Allocation should only ever occur after request messages
    # have been passed and processed.
    #
    # @param allocated_amt the amount allocated from perspective of message sender.
    # Positive indicates this device is allocated to take, negative indicates this device is allocated to provide.
    # device (negative).
    @abstractmethod
    def process_allocate_message(self, sender_id, allocate_amt):
        pass

    # ______________________________LOGGING/SCHEDULING FUNCTIONALITY___________________________ #

    ##
    #
    # @param a list of scheduled events to add to the device's queue, in the format of list of list of
    # time(hours), operation_name
    #
    def setup_schedule(self, scheduled_events):
        for task in scheduled_events:
            hour, operation_name = tuple(task)
            if hasattr(self, operation_name):
                func = getattr(self, operation_name)
            else:
                raise ValueError("Called the scheduler with an incorrectly named function")
            event = Event(func)  # for now no arguments. TODO: list should be of tuples (time, func, args).
            time_sec = hour * 3600
            self.add_event(event, time_sec)

    ##
    # Builds a logging message from a message, tag, and value, which also includes time and device_id
    # @param message the message to add to logger
    # @param tag the tag to add to the logger
    # @param value the value add to the logger

    # @return a formatted string to include in the logger
    def build_log_notation(self, message="", tag="", value=None):
        """Build the log message string"""
        return message_formatter.build_log_msg(
            time_seconds=self._time,
            message=message,
            tag=tag,
            value=value,
            device_id=self._device_id
        )

    ##
    # Writes the calculations of total energy used in KwH to the database

    def write_calcs(self):
        self._logger.info(self.build_log_notation(
            message="sum Wh out".format(self._device_id),
            tag="power calcs",
            value=self._sum_power_out
        ))
        self._logger.info(self.build_log_notation(
            message="sum Wh in",
            tag="power calcs",
            value=self._sum_power_in
        ))
        self.device_specific_calcs()

    ##
    # All device specific power consumption statistics are added here

    @abstractmethod
    def device_specific_calcs(self):
        pass

    ##
    # Method to be called at end of simulation resetting power levels and calculating
    # end_time the time to update the local time to
    def finish(self, end_time):
        """"Gets called at the end of the simulation"""
        self._time = end_time
        self.set_power_in(0.0)
        self.set_power_out(0.0)
        self.write_calcs()

    # _____________________________________________________________________ #

    # INFRASTRUCTURE NECESSARY FOR TESTING ALGORITHMS.

    # TODO: (1) Change pricing model to reflect variable amount of time.
    # TODO: (2) Change input model so that the price logic is constructed outside of Grid Controller.
    # TODO: (3) Change the logging format to what Bruce Described.
    # TODO: (4) Overload constructors.

    # TODO: Add back in uuid
     # TODO: Test read_delay without battery preference, then battery preference.
    # TODO: get pricing model working.
    # TODO: (2.5) Test a more complicated multi-day schedule.
    # TODO: (3) 2-price model for utility meter, all messaging (with extended value options). Test again.
    # TODO: (3.5) Utility meter communicates price to GC.

    # TODO: (5) Refactor dependencies so this works from the command line
    # TODO: (8) Utility meter needs to communicate its price to the GC.
    # TODO: (9) Add UUID value to device initialization.

    # TODO: (9) Add documentation to the Bruce page, documentation to functions throughout.
    # TODO: (10) Add PV.
    # TODO: (11) Consider Event Model. If we want to update, add __eq__ method to Event so that we can replace them.
    # TODO: (12) Refactor the solution. Code cleanup.

    # TODO: (13) Finish considering GC load balance algorithm
    # TODO: (14) Port in Air Conditioner.
    # TODO: (15) Get to some form of backwards compatibility with the website.
    # TODO: (16) Reconsider price forecasts.
    # TODO: (17) Convert the date format to accept milliseconds in message parsing.

