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
Main run portal for the simulation. Calls run simulation in simulation.py.
"""

import sys

import Build.Simulation_Operation.simulation as sim
import Build.Output.plotter as plt

if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == 'plot': # python3 main.py plot simulation_1
        plt.create_plots(sys.argv[2])
    elif len(sys.argv) == 3 and sys.argv[1] == 'csv': # python3 main.py csv simulation_1
        plt.create_CSVs(sys.argv[2])
    elif len(sys.argv) == 3 and sys.argv[1] == 'csvplot': # python3 main.py csvplot simulation_1
        plt.create_CSVs(sys.argv[2])
        plt.create_plots(sys.argv[2])
    elif len(sys.argv) == 2 and sys.argv[1] == 'clean': # python3 main.py clean
        plt.clean_workspace()
    elif len(sys.argv) >= 3: # can use additional arguments
        sim.run_simulation(sys.argv[1], sys.argv[2:])
        plt.create_CSVs(plt.get_last_log())
        plt.create_plots(plt.get_last_log())
    elif len(sys.argv) == 2: # default command
        sim.run_simulation(sys.argv[1], [])
        plt.create_CSVs(plt.get_last_log())
        plt.create_plots(plt.get_last_log())
    else:
        raise FileNotFoundError("Must enter a configuration filename")
