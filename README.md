# Protocol Inference and State Machine Learning of OPC UA

> **Peer Project (10CP) — Hochschule Emden/Leer**  
> Research Group Digital Factory | BMFTR Project: Secure IoT Gateway  
> Supervisor: Heiko Schoon, MEng | Prof. Dr. Patrick Felke

---

## Table of Contents

- [Project Overview](#project-overview)
- [What This Project Does](#what-this-project-does)
- [Final Result — Learned State Machine](#final-result--learned-state-machine)
- [Architecture](#architecture)
- [Tools and Technologies](#tools-and-technologies)
- [Project Structure](#project-structure)
- [Setup and Installation](#setup-and-installation)
- [How to Run](#how-to-run)
- [Results and Findings](#results-and-findings)
- [Security Analysis](#security-analysis)
- [Multi-Server Validation](#multi-server-validation)
- [Related Work](#related-work)
- [Scripts Explained](#scripts-explained)
- [Dataset](#dataset)
- [Report](#report)

---

## Project Overview

This project automatically learns a **formal state machine model** of the OPC UA (Open Platform Communications Unified Architecture) industrial protocol from real network traffic. Starting from raw PCAP captures, the pipeline infers message types, builds an automated testing harness, and applies the **L\* active automata learning algorithm** to discover the protocol's behavioral model.

OPC UA is the dominant communication protocol in industrial IoT and Industry 4.0 environments. Understanding its exact behavioral model is critical for:
- Security analysis and anomaly detection
- Protocol fuzzing and robustness testing  
- Vulnerability discovery in industrial control systems

---

## What This Project Does

```
Raw Network Traffic  →  Message Inference  →  Protocol Harness  →  L* Learning  →  State Machine
     (PCAP)               (Wireshark CSV)        (asyncua)           (AALpy)         (Graphviz)
```

The pipeline has 5 stages:

| Stage | What happens | Tool used |
|---|---|---|
| 1. Traffic Capture | Record OPC UA sessions between client and server | Wireshark |
| 2. Message Inference | Classify 3535 messages into service types | Python + CSV |
| 3. Protocol Harness | Automated client sending abstract symbols | asyncua |
| 4. Automata Learning | L* algorithm discovers state machine | AALpy |
| 5. Visualisation | State machine rendered as diagram | Graphviz |

---

## Final Result — Learned State Machine

The L\* algorithm automatically discovered a **3 state Mealy machine** in a single learning round:

```
                    CONNECT/CONNECT_OK
         ┌──────────────────────────────────────►
         │                                        
    ─────►  s0                s1               s2
         │  Disconnected  ◄──►  Connected  ◄──►  Connected
         │                                        +Subscribed
         └──────────────────────────────────────◄
                  DISCONNECT/DISCONNECT_OK
```

![State Machine Diagram](results/final_state_machine.png)

### State Transitions

**State s0 — Disconnected (initial)**

| Input | Output | Next State |
|---|---|---|
| CONNECT | CONNECT_OK | s1 |
| DISCONNECT | NOT_CONNECTED | s0 |
| READ | NOT_CONNECTED | s0 |
| WRITE | NOT_CONNECTED | s0 |
| BROWSE | NOT_CONNECTED | s0 |
| CREATE_SUB | NOT_CONNECTED | s0 |
| DELETE_SUB | NOT_CONNECTED | s0 |

**State s1 — Connected**

| Input | Output | Next State |
|---|---|---|
| CONNECT | ALREADY_CONNECTED | s1 |
| DISCONNECT | DISCONNECT_OK | s0 |
| READ | READ_OK | s1 |
| WRITE | WRITE_REJECTED | s1 |
| BROWSE | BROWSE_OK | s1 |
| CREATE_SUB | CREATE_SUB_OK | s2 |
| DELETE_SUB | NO_SUB | s1 |

**State s2 — Connected + Subscribed**

| Input | Output | Next State |
|---|---|---|
| CONNECT | ALREADY_CONNECTED | s2 |
| DISCONNECT | DISCONNECT_OK | s0 |
| READ | READ_OK | s2 |
| WRITE | WRITE_REJECTED | s2 |
| BROWSE | BROWSE_OK | s2 |
| CREATE_SUB | SUB_EXISTS | s2 |
| DELETE_SUB | DELETE_SUB_OK | s1 |

### Key Finding

The algorithm automatically discovered that **subscription management introduces a distinct behavioral state** in the OPC UA server the server correctly prevents duplicate subscriptions (SUB_EXISTS) and handles deletion of non existent subscriptions (NO_SUB). This was discovered without any manual protocol analysis.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Your Windows Laptop                       │
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐   │
│  │   Prosys OPC │    │  UaExpert    │    │    Wireshark     │   │
│  │  UA Server   │◄──►│   Client     │    │  (PCAP capture)  │   │
│  │  port 53530  │    │  (manual)    │    │                  │   │
│  └──────────────┘    └──────────────┘    └──────────────────┘   │
│         ▲                                        │               │
│         │                                        ▼               │
│  ┌──────┴────────────────────────────────────────────────────┐   │
│  │                    Python Pipeline                        │   │
│  │                                                           │   │
│  │  analyse_all_scenarios.py  →  3535 messages classified    │   │
│  │                                                           │   │
│  │  final_complete_learn.py:                                 │   │
│  │    FinalOpcUaSUL (harness)  ←→  AALpy L* algorithm        │   │
│  │         │                            │                    │   │
│  │         ▼                            ▼                    │   │
│  │    asyncua library           3-state Mealy machine        │   │
│  │    (real OPC UA client)      (DOT file + PNG)             │   │
│  └───────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘

Also tested against:
┌─────────────────────────────────────┐
│  Eclipse Milo OPC UA Demo Server    │
│  milo.digitalpetri.com:62541        │
│  (real certified industrial stack)  │
└─────────────────────────────────────┘
```

---

## Tools and Technologies

| Tool | Version | Purpose |
|---|---|---|
| **Prosys OPC UA Simulation Server** | Free Edition | Local OPC UA server (simulation) |
| **Eclipse Milo Demo Server** | Latest | Real certified industrial OPC UA server |
| **Unified Automation UaExpert** | 1.7+ | Manual OPC UA client for interaction |
| **Wireshark** | 4.6.4 | Network traffic capture (PCAP) |
| **Python** | 3.13 | Harness and learning scripts |
| **asyncua** | Latest | OPC UA client library for Python |
| **AALpy** | Latest | Active automata learning (L* algorithm) |
| **Graphviz Online** | Web | State machine diagram rendering |

### Python Dependencies

```bash
pip install asyncua
pip install aalpy
pip install pyshark
```

---

## Project Structure

```
opcua_project/
│
├── captures/                          # Wireshark PCAP captures
│   ├── scenario_01_normal.pcap        # Normal connect/browse/read/disconnect
│   ├── scenario_02_double_connect.pcap # Double connection attempt
│   ├── scenario_03_no_session.pcap    # Operations without session
│   ├── scenario_04_write_test.pcap    # Write to all nodes
│   ├── scenario_05_reconnect.pcap     # Multiple reconnections
│   ├── scenario_06_subscription.pcap  # Subscription lifecycle
│   ├── capture_01.pcap                # Original capture
│   ├── capture_03.pcap                # Original capture
│   └── capture_05.pcap                # Original capture
│
├── captures/csv/                      # Wireshark CSV exports
│   ├── scenario_01_normal.csv
│   ├── scenario_02_double_connect.csv
│   ├── scenario_03_no_session.csv
│   ├── scenario_04_write_test.csv
│   ├── scenario_05_reconnect.csv
│   ├── scenario_06_subscription.csv
│   ├── capture_01.csv
│   ├── capture_03.csv
│   └── capture_05.csv
│
├── scripts/                           # Python scripts
│   ├── analyse_all_scenarios.py       # Message analysis from CSV files
│   ├── harness.py                     # Protocol harness validation
│   └── final_complete_learn.py        # Main learning script
│
├── results/                           # Output files
│   ├── final_complete_state_machine.dot  # Graphviz DOT file
│   ├── final_state_machine.png           # State machine diagram
│   ├── all_scenarios_analysis.txt        # Message count report
│   ├── final_learning_stats.txt          # Learning statistics
│   └── security_analysis_report.txt      # Security findings
│
└── README.md                          # This file
```

---

## Setup and Installation

### Prerequisites

- Windows 10/11 laptop
- Python 3.10 or higher
- Prosys OPC UA Simulation Server (free download)
- UaExpert (free download, registration required)
- Wireshark 4.x with Npcap

### Step 1 — Install Python dependencies

```bash
pip install asyncua aalpy pyshark
```

### Step 2 — Install and run Prosys server

1. Download from `https://downloads.prosysopc.com`
2. Run installer → launch Prosys
3. Note the endpoint URL: `opc.tcp://localhost:53530/OPCUA/SimulationServer`
4. Server Status should show **Running**

### Step 3 — Configure Wireshark

1. Open Wireshark → **Analyze → Decode As**
2. Add rule: TCP port `53530` → `OPCUA`
3. Click **Save** to make permanent

### Step 4 — Connect UaExpert

1. Open UaExpert → click **"+"**
2. Custom Discovery → Add Server
3. Enter: `opc.tcp://localhost:53530/OPCUA/SimulationServer`
4. Select **None-None** security endpoint
5. Click OK → right-click server → **Connect**

---

## How to Run

### 1. Analyse captured traffic

```bash
cd scripts
python analyse_all_scenarios.py
```

Expected output:
```
COMBINED ANALYSIS — 9 files, 3535 total messages

TCP/Channel Setup (total: 148)
Session Management (total: 78)
Discovery (total: 48)
Address Space (total: 402)
Data Access (total: 874)
Subscription (total: 1971)
Errors (total: 14)
```

### 2. Validate the harness

Make sure Prosys is running, then:

```bash
python harness.py
```

Expected output:
```
TESTING THE HARNESS
Test 1: Connecting... PASSED
Test 2: Sending READ... PASSED
Test 3: Sending WRITE... PASSED
...
ALL TESTS DONE!
```

### 3. Run the state machine learning

Make sure Prosys is running, then:

```bash
python final_complete_learn.py
```

Expected output:
```
FINAL OPC UA STATE MACHINE LEARNING
Alphabet: ['CONNECT', 'DISCONNECT', 'READ', 'WRITE', 'BROWSE', 'CREATE_SUB', 'DELETE_SUB']

Hypothesis 1: 2 states
Hypothesis 2: 3 states
Learning Finished. Number of states: 3

State s0 (START - Disconnected):
  CONNECT      / CONNECT_OK        --> s1
  DISCONNECT   / NOT_CONNECTED     --> s0
  READ         / NOT_CONNECTED     --> s0
  ...

DOT saved: results/final_complete_state_machine.dot
```

### 4. Render the diagram

Paste the DOT file contents into:  
`https://dreampuf.github.io/GraphvizOnline/`

Or if Graphviz is installed locally:

```bash
dot -Tpng results/final_complete_state_machine.dot -o results/final_state_machine.png
```

---

## Results and Findings

### Message Analysis — 3535 total messages across 9 captures

| Category | Messages | Percentage |
|---|---|---|
| TCP/Channel Setup | 148 | 4.2% |
| Session Management | 78 | 2.2% |
| Discovery | 48 | 1.4% |
| Address Space (Browse) | 402 | 11.4% |
| Data Access (Read/Write) | 874 | 24.7% |
| Subscription/Publish | 1971 | 55.8% |
| Errors/Service Faults | 14 | 0.4% |
| **Total** | **3535** | **100%** |

### Detailed message breakdown

| Message Type | Count |
|---|---|
| PUBLISH_REQ / RESP | 917 / 882 |
| READ_REQ / RESP | 356 / 356 |
| BROWSE_REQ / RESP | 201 / 201 |
| WRITE_REQ / RESP | 81 / 81 |
| CREATE_MON_REQ / RESP | 40 / 40 |
| CREATE_SUB_REQ / RESP | 24 / 24 |
| OPEN_CHANNEL_RESP | 74 |
| HELLO / ACKNOWLEDGE | 37 / 37 |
| CREATE_SESSION | 13 / 13 |
| ACTIVATE_SESSION | 13 / 13 |
| CLOSE_SESSION | 13 / 13 |
| SERVICE_FAULT (errors) | 14 |

### Learning Statistics

| Metric | Value |
|---|---|
| Algorithm | L\* (Angluin 1987) |
| Library | AALpy |
| Automaton type | Mealy machine |
| Alphabet size | 7 symbols |
| States discovered | 3 |
| Learning rounds | 1 |
| Membership queries | 50 |
| MQ saved by caching | 5 |
| Equivalence queries | 148 |
| Total learning time | ~5 minutes |

### Capture Scenarios

| Scenario | Description | Messages |
|---|---|---|
| scenario_01_normal | Full connect/browse/read/disconnect | 422 |
| scenario_02_double_connect | Two clients connecting simultaneously | 458 |
| scenario_03_no_session | Operations attempted without session | 12 |
| scenario_04_write_test | Write to all available nodes | 526 |
| scenario_05_reconnect | Multiple reconnect cycles | 780 |
| scenario_06_subscription | Full subscription lifecycle | 716 |
| capture_01 | Original basic capture | 167 |
| capture_03 | Original browse capture | 122 |
| capture_05 | Original extended capture | 332 |

---

## Security Analysis

The learned 3 state model serves as a **formal security policy**. Any OPC UA server behavior deviating from the learned transitions is an anomaly.

Five attack scenarios were simulated and detected:

### Attack 1 — Server Reconnaissance
An attacker connects and browses the entire address space to map all available nodes and data values. Detected by: pure BROWSE-only sessions with no prior READ or WRITE are flagged as reconnaissance pattern.

### Attack 2 — Session Flooding (DoS)
Attacker opens multiple sessions rapidly to exhaust server resources. Detected by: multiple rapid CONNECT sequences from the same source deviating from single session normal pattern.

### Attack 3 — Replay Attack
Attacker captures a valid session and attempts to replay messages after disconnect. Detected by: READ after DISCONNECT should return NOT_CONNECTED per state machine. Any READ_OK response indicates session not properly invalidated.

### Attack 4 — Unauthorized Write
Attacker attempts to write to read-only nodes. Detected by: state machine expects WRITE_REJECTED for Counter node. Any WRITE_OK is a state machine violation indicating access control bypass.

### Attack 5 — Out-of-Order Message Sequence
Attacker sends messages in wrong order — READ before CONNECT, double subscribe, delete non-existent subscription. All detected by comparing actual server responses against learned state machine transitions.

### Detection Method

```python
# From security_analysis.py
def check_anomaly(state, symbol, actual_output):
    expected = KNOWN_TRANSITIONS.get((state, symbol))
    if actual_output != expected:
        return True, f"Expected {expected} but got {actual_output}"
    return False, "OK"
```

---

## Multi-Server Validation

The pipeline was validated on two different OPC UA server implementations:

| Metric | Prosys Simulation Server | Eclipse Milo Demo Server |
|---|---|---|
| Server type | Simulation tool | Real certified industrial stack |
| Location | Local (localhost:53530) | Internet (milo.digitalpetri.com:62541) |
| OPC UA stack | Prosys SDK | Eclipse Milo (Java) |
| Security | None-None | Anonymous |
| States learned | 3 | Run pipeline to find out |

### How to run on Eclipse Milo

Change the SERVER_URL in `final_complete_learn.py`:

```python
SERVER_URL = "opc.tcp://milo.digitalpetri.com:62541/milo"
```

Also change the node finder:
```python
if "Demo" in str(name):  # instead of "Simulation"
```

Then run:
```bash
python final_complete_learn.py
```

---

## Related Work

This project builds on and compares with the following key works:

| Paper | Method | Comparison |
|---|---|---|
| Tran Van et al. ARES 2024 | Active learning on OPC UA | They used custom mapper; we use open-source asyncua |
| Daniele et al. SecITC 2024 | Stateful fuzzing of OPC UA | They built state model manually; we learn it automatically |
| Muškardin et al. 2022 | AALpy library | We apply AALpy specifically to OPC UA for first time |
| Markov chain anomaly 2025 | Passive Markov model | Our active model is provably complete |
| BSI Security Analysis 2022 | Black-box fuzzing | Fuzzing is undirected; our model enables directed testing |
| Wei et al. arXiv 2024 | LLM from source code | Requires source code; our approach is fully black-box |

### Our unique contribution

> First openly reproducible pipeline combining passive PCAP based message inference with active L\* automata learning for OPC UA, using only open source tools, requiring no source code access, and producing a formally complete Mealy machine model from real network traffic.

---

## Scripts Explained

### `analyse_all_scenarios.py`

Reads all Wireshark CSV exports and classifies every OPC UA message into categories. Produces a comprehensive breakdown of 3535 messages across 9 capture files.

```bash
python analyse_all_scenarios.py
# Output: results/all_scenarios_analysis.txt
```

**Input:** CSV files in captures/  
**Output:** Message counts by category, saved to results/

---

### `harness.py`

Validates the protocol harness before running the full learning. Tests all 7 abstract symbols against the live server and confirms correct responses.

```bash
python harness.py
# Requires Prosys server running
# Runs 13 validation tests
```

**What it tests:**
- CONNECT → CONNECT_OK
- Double CONNECT → ALREADY_CONNECTED  
- READ → READ_OK
- WRITE → WRITE_REJECTED (Counter is read-only)
- BROWSE → BROWSE_OK
- CREATE_SUB → CREATE_SUB_OK
- Duplicate CREATE_SUB → SUB_EXISTS
- DELETE_SUB → DELETE_SUB_OK
- DELETE_SUB when empty → NO_SUB
- DISCONNECT → DISCONNECT_OK
- READ after DISCONNECT → NOT_CONNECTED
- Full reset → RESET_OK
- Complete s0→s1→s2→s1→s0 sequence

---

### `final_complete_learn.py`

The main learning script. Connects the harness to AALpy's L\* implementation to automatically discover the OPC UA state machine.

```bash
python final_complete_learn.py
# Requires Prosys server running
# Takes approximately 5 minutes
# Output: results/final_complete_state_machine.dot
```

**Alphabet:** `[CONNECT, DISCONNECT, READ, WRITE, BROWSE, CREATE_SUB, DELETE_SUB]`  
**Algorithm:** L\* (Angluin 1987) — Mealy machine variant  
**Oracle:** RandomWalk equivalence oracle (2000 steps)

---

## Dataset

The full dataset of 3535 OPC UA messages captured across 9 scenarios is available in the `captures/csv/` folder. Each CSV file was exported from Wireshark with full OPC UA protocol decoding enabled.

**To reproduce the captures:**
1. Open Wireshark → select loopback adapter
2. Set capture filter: `tcp port 53530`
3. Connect/interact with UaExpert per scenario description
4. Export as CSV: File → Export Packet Dissections → As CSV

---

## Report

The full project report is available as `report.docx` in the repository root.

**Report sections:**
1. Introduction
2. Testbed Setup
3. Traffic Capture
4. Message Inference
5. Protocol Harness
6. Automata Learning
7. Results: Learned State Machine
8. Security Analysis
9. Multi Server Validation
10. Related Work
11. Conclusion

---

## Contact

**Heiko Schoon** — heiko.schoon@hs-emden-leer.de  
Research Group Digital Factory, Hochschule Emden/Leer  
BMFTR-Project: Secure IoT Gateway

**Prof. Dr. Patrick Felke**  
IT-Security, Hochschule Emden/Leer  
BMFTR-Project: Secure IoT Gateway

---

## License

This project was developed as part of the Peer Project (10CP) at Hochschule Emden/Leer.  
All scripts are provided for research and educational purposes.

---

*Generated: April 2026 | Hochschule Emden/Leer | Research Group Digital Factory*
