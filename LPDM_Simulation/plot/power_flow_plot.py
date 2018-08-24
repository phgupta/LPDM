import matplotlib.pyplot as plt
# import numpy as np
# %matplotlib
import pandas as pd

plt.close('all')

power_data_file = "../power_flow.csv"
power_data = pd.read_csv(power_data_file)
# print(demand_data)

time = power_data['Time']
gc2 = power_data['gc_2']
eud4 = power_data['eud_4']
pv2 = power_data['pv_2']

sec_in_day = 60*60*24
xticks = [sec_in_day*x for x in range(7)]
fig, axes = plt.subplots(3,sharex=True)
titles = ["GC 2", "EUD 4", "PV 2"]
days = ["Day " + str(x) for x in range(7)]
for i,ax in enumerate(axes):
    ax.set_title(titles[i])
    ax.set_xticks(xticks)
    ax.set_xticklabels(days)
    ax.set_ylabel('Power (W)')
    ax.grid(True, linestyle='--')

axes[2].set_xlabel("Time")


axes[0].plot(time, gc2, label='GC 2', linewidth=3)
axes[1].plot(time, eud4, 'y', label='EUD 4', linewidth=3)
axes[2].plot(time, pv2, 'r', label='PV 2', linewidth=3)

fig.tight_layout()
# ax.legend()
fig.savefig("gc_power_share.png")
