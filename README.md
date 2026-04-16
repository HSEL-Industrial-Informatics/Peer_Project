# OPC UA Protocol State Machine Learning

A university research project that automatically learns how the OPC UA industrial protocol behaves, using network traffic and machine learning.

**University:** Hochschule Emden/Leer  
**Supervisor:**<br />

Heiko Schoon Prof.                         &emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&nbsp; Dr. Patrick Felke <br />
Research Group Digital Factory             &emsp;&emsp;&emsp;&nbsp;&nbsp; IT-Security <br />
BMFTR-Project: Secure IoT Gateway          &emsp; BMFTR-Project: Secure IoT Gateway <br />
Email: heiko.schoon@hs-emden-leer.de

---

## What This Project Does

OPC UA is a protocol used in factories and industrial machines to communicate. This project:

1. Records real OPC UA network traffic using Wireshark
2. Analyses what types of messages appear
3. Builds a robot client that sends messages automatically
4. Uses the L* algorithm to learn how the server behaves
5. Draws a state machine diagram showing the result

---

## The Result

The algorithm automatically found a **3-state model** of OPC UA behavior:

![State Machine](https://github.com/HSEL-Industrial-Informatics/Peer_Project/blob/main/graphviz%20(2).png)

- **s0 — Disconnected:** Nothing works here. Only CONNECT moves you forward.
- **s1 — Connected:** READ, WRITE, BROWSE all work. CREATE_SUB moves to s2.
- **s2 — Connected + Subscribed:** Everything works plus subscription is active.

---

## Tools Used

| Tool | What it does |
|---|---|
| Prosys OPC UA Server | Runs a fake industrial server on your PC |
| UaExpert | Lets you click and interact with the server |
| Wireshark | Records all network traffic |
| Python + asyncua | Sends OPC UA messages automatically |
| AALpy | Runs the L* learning algorithm |
| Graphviz | Draws the final diagram |

---

## Project Files

```
opcua_project/
├── captures/          → Wireshark PCAP files (9 captures), CSV exports from Wireshark
├── scripts/
│   ├── analyse_all_scenarios.py   → counts all message types
│   ├── harness.py                 → tests the robot client
│   └── final_complete_learn.py    → runs the learning
└── results/
    ├── final_state_machine.png    → the diagram
    ├── final_complete_state_machine.dot
    └── all_scenarios_analysis.txt
```

---

## How to Run

### Install dependencies
```bash
pip install asyncua aalpy pyshark
```

### Step 1 — Analyse captured traffic
```bash
python scripts/analyse_all_scenarios.py
```

### Step 2 — Test the harness
Make sure Prosys server is running first.
```bash
python scripts/harness.py
```

### Step 3 — Learn the state machine
```bash
python scripts/final_complete_learn.py
```
Takes about 5 minutes. Saves DOT file to results folder.

### Step 4 — Draw the diagram
Paste the DOT file into: https://dreampuf.github.io/GraphvizOnline/

---

## Data Collected

9 capture files, **3535 total OPC UA messages**:

| Message Type | Count |
|---|---|
| Publish (background) | 1799 |
| Read | 712 |
| Browse | 402 |
| Write | 162 |
| Subscription setup | 148 |
| Session management | 78 |
| Discovery | 48 |
| Errors | 14 |

---

## Learning Results

| What | Value |
|---|---|
| Algorithm | L* (Angluin 1987) |
| States found | 3 |
| Time taken | ~5 minutes |
| Queries sent | 198 |
| Learning rounds | 1 |

---

## Security Analysis

The learned state machine was used to detect 5 attack types:

1. **Reconnaissance** — attacker browses all nodes to map the server
2. **Session Flooding** — attacker opens many sessions to crash the server
3. **Replay Attack** — attacker reuses old session tokens
4. **Unauthorized Write** — attacker tries to change read only values
5. **Out-of-Order Messages** — attacker sends messages in wrong sequence

Any response that does not match the learned state machine is flagged as an anomaly.

---

## Tested On Two Servers

| Server | Type | Location |
|---|---|---|
| Prosys Simulation Server | Simulation tool | localhost:53530 |
| Eclipse Milo Demo Server | Real certified server | milo.digitalpetri.com:62541 |

---

## Setup Guide

### 1. Install Prosys OPC UA Simulation Server
Download from: https://downloads.prosysopc.com  
Run it and make sure it shows **Status: Running**

### 2. Install UaExpert
Download from: https://www.unified-automation.com/downloads  
Connect to: `opc.tcp://localhost:53530/OPCUA/SimulationServer`  
Select **None-None** security when connecting

### 3. Install Wireshark
Download from: https://www.wireshark.org  
Install with Npcap loopback adapter enabled

### 4. Capture traffic
- Start Wireshark, filter: `tcp port 53530`
- Connect UaExpert, browse/read/write some nodes
- Disconnect, stop Wireshark, save as .pcap
- Export as CSV: File → Export → As CSV

---

## Contact

Altaf Ahmad - altaf.ahmad@hs-emden-leer.de  
Raja Jawad Ali - raja.jawad.ali@stud.hs-emden-leer.de

Hochschule Emden/Leer, Research Group Digital Factory
<img src="https://upload.wikimedia.org/wikipedia/commons/thumb/d/df/HS_EmdenLeer_Logo.svg/960px-HS_EmdenLeer_Logo.svg.png" alt="Alt Text" width="250" height="80">


