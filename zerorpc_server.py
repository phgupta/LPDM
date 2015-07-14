import zerorpc
from tug_simulation import TugSimulation
import json

class RpcController(object):
    interrupt = False
    sim = None
    config = None
    app_instance_id = None

    def initialize(self, params):
        RpcController.config = {
            "end_time": int(params["run_time_days"]) * 60 * 60 * 24 if params and 'run_time_days' in params.keys() and params['run_time_days'] else 60 * 60 * 24 * 2,
            "poll_interval": int(params["poll_interval_mins"]) * 60 if params and 'poll_interval_mins' in params.keys() and params['poll_interval_mins'] else 15 * 60
        }

        RpcController.sim = None
        RpcController.sim = TugSimulation(RpcController.config)
        device_info = RpcController.sim.initializeSimulation()
        RpcController.app_instance_id = RpcController.sim.app_instance_id
        print('sim initialized {0}'.format(RpcController.app_instance_id))
        return {'app_instance_id': RpcController.app_instance_id, 'device_info': device_info}

    def runSimulation(self, params):
        if RpcController.sim and RpcController.sim.app_instance_id == RpcController.app_instance_id:
            # print('run sim {0}'.format(RpcController.app_instance_id))
            return RpcController.sim.run(step=int(params['step']))
            # print(RpcController.sim.deviceStatus())
            # return json.dumps(RpcController.sim.deviceStatus())
        else:
            print('unable to run simulation ({0} != {1}'.format(RpcController.sim.app_instance_id, RpcController.app_instance_id))
            return null

    @zerorpc.stream
    def streamSimulation(self):
        print('stream simulation')
        if RpcController.sim and RpcController.sim.app_instance_id == RpcController.app_instance_id:
            print('run sim {0}'.format(RpcController.app_instance_id))
            return RpcController.sim
        else:
            print('unable to run simulation ({0} != {1}'.format(RpcController.sim.app_instance_id, RpcController.app_instance_id))
            return null

    def hello(self, params):
        # interrupt = False
        print('received event interrupt = {0}'.format(RpcController.interrupt))
        print(params)
        print(type(params))
        return "finished here"

    def stopSimulation(self):
        print('stop simulation')
        RpcController.interrupt = True
        return 500

s = zerorpc.Server(RpcController())
s.bind("tcp://0.0.0.0:4242")
s.run()


# sim = TugSimulation(sim_config)
# sim.initializeSimulation()
# sim.run(60*60)
# sim.dumpLog()
# print(sim.deviceStatus())

# sim.run(60 * 60)
# sim.dumpLog()
# print(sim.deviceStatus())