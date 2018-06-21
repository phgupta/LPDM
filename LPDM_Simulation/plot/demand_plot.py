import matplotlib.pyplot as plt
import numpy as np
# %matplotlib

demand_data_file = "../demand.csv"
demand_data = np.genfromtxt(demand_data_file,delimiter=',')
print(demand_data)

ph = plt.figure()
plt.title("Total Demand Curve")
plt.xlabel("Power (W)")
plt.ylabel("Price ($)")
plt.plot(demand_data[:,1],demand_data[:,0])
ph.savefig("demand_plot.png")
