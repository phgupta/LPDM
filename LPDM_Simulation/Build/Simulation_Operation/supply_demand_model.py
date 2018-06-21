

class supply_demand_model:

    def __init__(self):
        # self._supervisor = supervisor
        # Schedule initial curve generation at .1 s after appropriate devices have been turned on


    # def setup_sd_curves(self):
    #     self.supervisor = supervisor
    #     self.setup_demand_curve()
    #     # self.setup_supply_curve()

    def update_demand_curve(self):
        # For each GC
        # Sweep price by broadcasting range of prices
        # Measure power draw
        # Export to CSV (GC ID, time, price, power)

        prices = (x * 0.01 for x in range(0, 50))
        devices = self.supervisor.all_devices()
        gcs = (device for device in devices if device.get_type == "grid_controller")

        for gc in gcs:
            connected_devices = device.get_connected_devices()
            euds = (connected_device for connected_device_id, connected_device in connected_devices.iterItems() if connected_device_id.startswith("eud"))
            for price in prices:
                demand_power = 0
                for eud in euds:
                    # Have to remember to save the old price
