import asyncio
import time
from asyncua import Client, ua
from aalpy.learning_algs import run_Lstar
from aalpy.oracles import RandomWalkEqOracle
from aalpy.SULs import SUL

SERVER = "opc.tcp://localhost:53530/OPCUA/SimulationServer"

class OpcUaSUL(SUL):
    def __init__(self):
        super().__init__()
        self.loop = asyncio.new_event_loop()
        self.client = None
        self.node = None
        self.connected = False
        self.sub = None

    def pre(self):
        self.loop.run_until_complete(self._reset())
        time.sleep(0.4)

    def post(self): pass

    def step(self, s):
        return self.loop.run_until_complete(self._step(s))

    async def _reset(self):
        try:
            if self.client:
                await self.client.disconnect()
        except Exception:
            pass
        self.client = None
        self.node = None
        self.connected = False
        self.sub = None

    async def _step(self, s):
        try:
            if s == "CONNECT":
                if self.connected:
                    return "ALREADY_CONNECTED"
                self.client = Client(url=SERVER)
                await self.client.connect()
                self.connected = True
                # find node
                for child in await self.client.nodes\
                        .objects.get_children():
                    name = str(await child
                               .read_browse_name())
                    if "Simulation" in name:
                        kids = await child.get_children()
                        if kids:
                            self.node = kids[0]
                            break
                return "CONNECT_OK"

            if not self.connected:
                return "NOT_CONNECTED"

            if s == "DISCONNECT":
                await self.client.disconnect()
                self.connected = False
                return "DISCONNECT_OK"
            elif s == "READ":
                await self.node.read_value()
                return "READ_OK"
            elif s == "WRITE":
                try:
                    v = await self.node.read_value()
                    await self.node.write_value(v)
                    return "WRITE_OK"
                except ua.UaStatusCodeError:
                    return "WRITE_REJECTED"
            elif s == "BROWSE":
                await self.client.nodes.objects\
                    .get_children()
                return "BROWSE_OK"
            elif s == "CREATE_SUB":
                if self.sub:
                    return "SUB_EXISTS"
                self.sub = await self.client\
                    .create_subscription(500, None)
                return "CREATE_SUB_OK"
            elif s == "DELETE_SUB":
                if not self.sub:
                    return "NO_SUB"
                await self.sub.delete()
                self.sub = None
                return "DELETE_SUB_OK"

        except Exception:
            self.connected = False
            return "ERROR"

# Run learning
alphabet = ["CONNECT","DISCONNECT",
            "READ","WRITE","BROWSE",
            "CREATE_SUB","DELETE_SUB"]
sul = OpcUaSUL()
oracle = RandomWalkEqOracle(alphabet, sul,
                            num_steps=2000)
model = run_Lstar(alphabet, sul, oracle,
                  automaton_type="mealy",
                  cache_and_non_det_check=True,
                  print_level=2)
print(f"States found: {len(model.states)}")
sul.loop.run_until_complete(sul._reset())