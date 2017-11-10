################################################################################################################################
# *** Copyright Notice ***
#
# "Price Based Local Power Distribution Management System (Local Power Distribution Manager) v2.0"
# Copyright (c) 2017, The Regents of the University of California, through Lawrence Berkeley National Laboratory
# (subject to receipt of any required approvals from the U.S. Dept. of Energy).  All rights reserved.
#
# If you have questions about your rights to use or distribute this software, please contact
# Berkeley Lab's Innovation & Partnerships Office at  IPO@lbl.gov.
################################################################################################################################

"""
A priority queue implementing a queue of items sorted by priority.
Adapted from https://docs.python.org/2/library/heapq.html.
"""

import itertools
import heapq


class PriorityQueue:

    REMOVED = '<removed-task>'  # placeholder for a removed task

    def __init__(self):
        self._pq = []  # list of entries (priority, count, task) arranged in a heap
        self._entry_finder = {}  # mapping of tasks to entries
        self._counter = itertools.count()  # unique sequence count to be used as a tiebreaker comparison in heap

    ##
    # Adds a new task to the priority queue, or if that task already exists, updates that tasks priority.

    def add(self, task, priority=0):
        if task in self._entry_finder:
            self.remove(task)
        count = next(self._counter)
        entry = [priority, count, task]
        self._entry_finder[task] = entry
        heapq.heappush(self._pq, entry)

    ##
    # Updates all tasks with a given task_attribute equal to an attribute_value to have a new priority.
    def update_by_attribute(self, task_attribute, attribute_value, new_priority=0):
        for task in self._entry_finder:
            if getattr(task, task_attribute) == attribute_value:
                self.remove(task)
                count = next(self._counter)
                entry = [new_priority, count, task]
                self._entry_finder[task] = entry
                heapq.heappush(self._pq, entry)


    ##
    # Marks an existing task as REMOVED in the heap. When this value is encountered later in a pop or peek,
    # it will be removed for good from the heap. Raises a KeyError if that task is not found.
    def remove(self, task):
        entry = self._entry_finder.pop(task)
        entry[-1] = self.REMOVED

    ##
    # remove and return the lowest priority task and its priority. Raise KeyError if queue is empty.
    # @return tuple of task with lowest priority and that priority
    def pop(self):
        while self._pq:  # Must loop in case front of queue is 'REMOVED'
            priority, count, task = heapq.heappop(self._pq)
            if task is not self.REMOVED:
                del self._entry_finder[task]
                return task, priority
        raise KeyError('pop from an empty priority queue')

    ##
    # Returns the lowest priority task in the queue and its priority without removing. Raise KeyError if queue is empty.
    # @return tuple of task with lowest priority and that priority
    def peek(self):
        while self._pq:  # Must loop in case front of queue is 'removed'
            priority, count, task = heapq.heappop(self._pq)
            if task is not self.REMOVED:
                put_back = [priority, count, task]
                heapq.heappush(self._pq, put_back)
                return task, priority
        raise KeyError('peek from an empty priority queue')

    ##
    # Returns whether the queue is empty.
    def is_empty(self):
        # Implementation note: heap may still contain items, but they are all classified as 'REMOVED'.
        return len(self._entry_finder) == 0

    ##
    # Clears out all values from the priority queue
    def clear(self):
        """clear the priority queue"""
        self._pq.clear()
        self._entry_finder.clear()
        self._counter = itertools.count()


