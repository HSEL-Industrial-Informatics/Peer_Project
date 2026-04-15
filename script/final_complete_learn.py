"""
PROJECT SUMMARY:

This program performs active automata learning on an OPC UA server.

Workflow:
1. Extract communication patterns from PCAP files
2. Define protocol alphabet
3. Implement System Under Learning (SUL)
4. Apply L* learning algorithm (AALpy)
5. Generate Mealy machine model
6. Export state machine for visualization

Goal:
→ Automatically learn and model OPC UA protocol behavior
→ Identify valid and invalid system states
"""


import asyncio
import time
from asyncua import Client
from asyncua import ua
from aalpy.learning_algs import run_Lstar
from aalpy.oracles import RandomWalkEqOracle
from aalpy.SULs import SUL
import os

# OPC UA server endpoint : Prosys simulation server
SERVER_URL = "opc.tcp://localhost:53530/OPCUA/SimulationServer"
# Folder to store learned models and results
RESULTS = r"C:\Users\faiza\OneDrive\Desktop\opcua_project\results"


class FinalOpcUaSUL(SUL):
    """
    Complete OPC UA harness covering all discovered
    message types from 9 capture files and 3535 messages.

    Alphabet covers:
    - Session lifecycle: CONNECT, DISCONNECT
    - Data access: READ, WRITE
    - Address space: BROWSE
    - Subscription: CREATE_SUBSCRIPTION, DELETE_SUBSCRIPTION
    - Error triggering: INVALID_READ
    """

    def __init__(self):
        super().__init__()
        self.loop = asyncio.new_event_loop()
        self.client = None
        self.node = None
        self.subscription = None
        self.connected = False

    def pre(self):
        self.loop.run_until_complete(self._reset())
        time.sleep(0.5)

    def post(self):
        pass

    def step(self, symbol):
        return self.loop.run_until_complete(self._step(symbol))

    async def _reset(self):
        try:
            if self.subscription:
                try:
                    await self.subscription.delete()
                except Exception:
                    pass
                self.subscription = None
            if self.client:
                await self.client.disconnect()
        except Exception:
            pass
        self.client = None
        self.node = None
        self.subscription = None
        self.connected = False

    async def _find_node(self):
        try:
            objects = self.client.nodes.objects
            children = await objects.get_children()
            for child in children:
                name = await child.read_browse_name()
                if "Simulation" in str(name):
                    sim_children = await child.get_children()
                    for sc in sim_children:
                        sc_name = await sc.read_browse_name()
                        if "Counter" in str(sc_name):
                            return sc
                    if sim_children:
                        return sim_children[0]
        except Exception:
            pass
        return None

    async def _step(self, symbol):
        try:
            # ── CONNECT ───────────────────────────────────
            if symbol == "CONNECT":
                if self.connected:
                    return "ALREADY_CONNECTED"
                try:
                    self.client = Client(url=SERVER_URL)
                    self.client.session_timeout = 30000
                    await self.client.connect()
                    self.connected = True
                    self.node = await self._find_node()
                    return "CONNECT_OK"
                except Exception:
                    self.connected = False
                    return "CONNECT_ERROR"

            # ── DISCONNECT ────────────────────────────────
            elif symbol == "DISCONNECT":
                if not self.connected:
                    return "NOT_CONNECTED"
                try:
                    if self.subscription:
                        try:
                            await self.subscription.delete()
                        except Exception:
                            pass
                        self.subscription = None
                    await self.client.disconnect()
                    self.connected = False
                    self.client = None
                    self.node = None
                    return "DISCONNECT_OK"
                except Exception:
                    self.connected = False
                    return "DISCONNECT_ERROR"

            # ── READ ──────────────────────────────────────
            elif symbol == "READ":
                if not self.connected:
                    return "NOT_CONNECTED"
                try:
                    if self.node is None:
                        self.node = await self._find_node()
                    await self.node.read_value()
                    return "READ_OK"
                except Exception:
                    return "READ_ERROR"

            # ── WRITE ─────────────────────────────────────
            elif symbol == "WRITE":
                if not self.connected:
                    return "NOT_CONNECTED"
                try:
                    if self.node is None:
                        self.node = await self._find_node()
                    val = await self.node.read_value()
                    await self.node.write_value(val)
                    return "WRITE_OK"
                except ua.UaStatusCodeError:
                    return "WRITE_REJECTED"
                except Exception:
                    return "WRITE_ERROR"

            # ── BROWSE ────────────────────────────────────
            elif symbol == "BROWSE":
                if not self.connected:
                    return "NOT_CONNECTED"
                try:
                    await self.client.nodes.objects\
                        .get_children()
                    return "BROWSE_OK"
                except Exception:
                    return "BROWSE_ERROR"

            # ── CREATE_SUBSCRIPTION ───────────────────────
            elif symbol == "CREATE_SUB":
                if not self.connected:
                    return "NOT_CONNECTED"
                if self.subscription is not None:
                    return "SUB_EXISTS"
                try:
                    self.subscription = await \
                        self.client.create_subscription(
                            500, None)
                    return "CREATE_SUB_OK"
                except Exception:
                    return "CREATE_SUB_ERROR"

            # ── DELETE_SUBSCRIPTION ───────────────────────
            elif symbol == "DELETE_SUB":
                if not self.connected:
                    return "NOT_CONNECTED"
                if self.subscription is None:
                    return "NO_SUB"
                try:
                    await self.subscription.delete()
                    self.subscription = None
                    return "DELETE_SUB_OK"
                except Exception:
                    return "DELETE_SUB_ERROR"

            return "UNKNOWN"

        except Exception:
            self.connected = False
            return "ERROR"


def extract_model(model, alphabet):
    """Extract transitions using output_fun"""
    rows = []
    for state in model.states:
        out_fun = getattr(state, 'output_fun', {})
        for inp in alphabet:
            out = out_fun.get(inp, '?')
            trans = state.transitions.get(inp)
            nxt = getattr(trans, 'state_id', '?') \
                if trans else '?'
            rows.append((state.state_id, inp, out, nxt))
    return rows

# GRAPHVIZ DOT GENERATION (STATE MACHINE VISUALIZATION)
def build_dot(model, alphabet, rows):
    # Color mapping for different outputs
    colors = {
        "CONNECT_OK":       "#2E7D32",  #green (success)
        "DISCONNECT_OK":    "#1565C0",
        "READ_OK":          "#1B5E20",
        "WRITE_OK":         "#E65100",
        "WRITE_REJECTED":   "#B71C1C",   #red (error)
        "BROWSE_OK":        "#4A148C",
        "CREATE_SUB_OK":    "#00695C",
        "DELETE_SUB_OK":    "#4527A0",
        "NOT_CONNECTED":    "#C62828",
        "ALREADY_CONNECTED":"#BF360C",
        "SUB_EXISTS":       "#E65100",
        "NO_SUB":           "#C62828",
    }

    # Determine state labels from behavior
    state_info = {}
    for state in model.states:
        out = getattr(state, 'output_fun', {})
        is_init = state == model.initial_state
        can_read = out.get('READ') == 'READ_OK'
        has_sub = out.get('CREATE_SUB') == 'SUB_EXISTS'

        if is_init:
            state_info[state.state_id] = (
                f"{state.state_id}\\nDisconnected",
                "#FFD54F", "#F57F17")
        elif can_read and has_sub:
            state_info[state.state_id] = (
                f"{state.state_id}\\nConnected\\n+Subscribed",
                "#80DEEA", "#00838F")
        elif can_read:
            state_info[state.state_id] = (
                f"{state.state_id}\\nConnected",
                "#4FC3F7", "#0277BD")
        else:
            state_info[state.state_id] = (
                f"{state.state_id}",
                "#E1F5EE", "#0F6E56")

    lines = [
        'digraph "OPC_UA_Final_State_Machine" {',
        '    rankdir=LR;',
        '    bgcolor="white";',
        '    fontname="Arial";',
        '    node [fontname="Arial", fontsize=12,',
        '          style=filled, shape=circle,',
        '          width=1.8, height=1.8];',
        '    edge [fontname="Arial", fontsize=9];',
        '',
        '    __start [shape=none, label="", '
        'width=0, height=0];',
        f'    __start -> {model.initial_state.state_id}'
        f' [label="start"];',
        '',
    ]

    for state in model.states:
        sid = state.state_id
        label, fill, stroke = state_info.get(
            sid, (sid, "#E0E0E0", "#9E9E9E"))
        lines.append(
            f'    {sid} [label="{label}", '
            f'fillcolor="{fill}", color="{stroke}", '
            f'penwidth=2];')

    lines.append('')

    # Group edges by (from, to)
    from collections import defaultdict
    grouped = defaultdict(list)
    for frm, inp, out, to in rows:
        grouped[(frm, to)].append(f"{inp}/{out}")

    for (frm, to), labels in grouped.items():
        first_out = next(
            (o for f, i, o, t in rows
             if f == frm and t == to), "")
        color = colors.get(first_out, "#666666")
        label = "\\n".join(labels)
        style = "dashed" if frm == to else "solid"
        pw = "1.5" if frm == to else "2.0"
        lines.append(
            f'    {frm} -> {to} [label="{label}", '
            f'color="{color}", fontcolor="{color}", '
            f'style="{style}", penwidth={pw}];')

    lines.append('}')
    return "\n".join(lines)


def main():
    os.makedirs(RESULTS, exist_ok=True)

    # Full alphabet from all 9 captures
    alphabet = [
        "CONNECT",
        "DISCONNECT",
        "READ",
        "WRITE",
        "BROWSE",
        "CREATE_SUB",
        "DELETE_SUB",
    ]

  
    print("OPC UA STATE MACHINE LEARNING")
    print("Based on 3535 messages from 9 capture files")
    print("*************************************************")
    print(f"\nAlphabet ({len(alphabet)} symbols): {alphabet}")
    print(f"Algorithm: L* Mealy machine (AALpy)")
    print(f"Server   : {SERVER_URL}")
    print()

    sul = FinalOpcUaSUL()
    eq_oracle = RandomWalkEqOracle(
        alphabet=alphabet,
        sul=sul,
        num_steps=2000,
        reset_after_cex=True,
        reset_prob=0.1)

    print("Running L*")
    print("-" * 60)

    model = run_Lstar(
        alphabet=alphabet,
        sul=sul,
        eq_oracle=eq_oracle,
        automaton_type="mealy",
        cache_and_non_det_check=True,
        print_level=2)

    print("-" * 60)

    rows = extract_model(model, alphabet)

    # Print clearly
    print(f"\n{'='*60}")
    print(f"FINAL RESULT: {len(model.states)} states learned")
    print(f"{'='*60}\n")

    for state in model.states:
        out = getattr(state, 'output_fun', {})
        is_init = state == model.initial_state
        tag = " (START)" if is_init else ""
        print(f"State {state.state_id}{tag}:")
        for inp in alphabet:
            o = out.get(inp, '?')
            trans = state.transitions.get(inp)
            nxt = getattr(trans, 'state_id', '?') \
                if trans else '?'
            same = "(self)" if nxt == state.state_id \
                else f"-> {nxt}"
            print(f"  {inp:20} / {o:25} {same}")
        print()

    # Build and save DOT
    dot = build_dot(model, alphabet, rows)
    dot_path = os.path.join(
        RESULTS, "final_complete_state_machine.dot")
    with open(dot_path, "w") as f:
        f.write(dot)

    # Save stats
    stats_path = os.path.join(
        RESULTS, "final_learning_stats.txt")
    with open(stats_path, "w") as f:
        f.write("Final OPC UA Learning Results\n")
        f.write("=" * 40 + "\n\n")
        f.write(f"Algorithm : L* (Angluin 1987)\n")
        f.write(f"Library   : AALpy\n")
        f.write(f"Alphabet  : {alphabet}\n")
        f.write(f"States    : {len(model.states)}\n\n")
        f.write("Transitions:\n")
        for frm, inp, out, to in rows:
            f.write(f"  {frm} --{inp}/{out}--> {to}\n")

    print(f"DOT saved : {dot_path}")
    print(f"Stats saved: {stats_path}")
    print()
 
    print(dot)

    sul.loop.run_until_complete(sul._reset())
    print("\nDone!")


if __name__ == "__main__":
    main()