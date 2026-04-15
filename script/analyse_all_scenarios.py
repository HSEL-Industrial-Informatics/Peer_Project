import csv
import os
from collections import Counter

CAPTURES = r"C:\Users\faiza\OneDrive\Desktop\opcua_project\captures"
RESULTS = r"C:\Users\faiza\OneDrive\Desktop\opcua_project\results"

csv_files = [
    "scenario_01_normal.csv",
    "scenario_02_double_connect.csv",
    "scenario_03_no_session.csv",
    "scenario_04_write_test.csv",
    "scenario_05_reconnect.csv",
    "scenario_06_subscription.csv",
    # Also include your old captures
    "capture_01.csv",
    "capture_03.csv",
    "capture_04.csv",
    "capture_05.csv",
]

def classify(info):
    if not info:
        return None
    checks = [
        ('OpenSecureChannel', 'Req',   'OPEN_CHANNEL_REQ'),
        ('OpenSecureChannel', None,    'OPEN_CHANNEL_RESP'),
        ('CreateSession',     'Req',   'CREATE_SESSION_REQ'),
        ('CreateSession',     None,    'CREATE_SESSION_RESP'),
        ('ActivateSession',   'Req',   'ACTIVATE_SESSION_REQ'),
        ('ActivateSession',   None,    'ACTIVATE_SESSION_RESP'),
        ('CloseSession',      'Req',   'CLOSE_SESSION_REQ'),
        ('CloseSession',      None,    'CLOSE_SESSION_RESP'),
        ('CreateSubscription','Req',   'CREATE_SUB_REQ'),
        ('CreateSubscription',None,    'CREATE_SUB_RESP'),
        ('CreateMonitored',   'Req',   'CREATE_MON_REQ'),
        ('CreateMonitored',   None,    'CREATE_MON_RESP'),
        ('ModifySubscription','Req',   'MODIFY_SUB_REQ'),
        ('ModifySubscription',None,    'MODIFY_SUB_RESP'),
        ('DeleteSubscription','Req',   'DELETE_SUB_REQ'),
        ('DeleteSubscription',None,    'DELETE_SUB_RESP'),
        ('DeleteMonitored',   'Req',   'DELETE_MON_REQ'),
        ('DeleteMonitored',   None,    'DELETE_MON_RESP'),
        ('BrowseNext',        'Req',   'BROWSE_NEXT_REQ'),
        ('BrowseNext',        None,    'BROWSE_NEXT_RESP'),
        ('Browse',            'Req',   'BROWSE_REQ'),
        ('Browse',            None,    'BROWSE_RESP'),
        ('Read',              'Req',   'READ_REQ'),
        ('Read',              None,    'READ_RESP'),
        ('Write',             'Req',   'WRITE_REQ'),
        ('Write',             None,    'WRITE_RESP'),
        ('Publish',           'Req',   'PUBLISH_REQ'),
        ('Publish',           None,    'PUBLISH_RESP'),
        ('TransferSub',       'Req',   'TRANSFER_SUB_REQ'),
        ('TransferSub',       None,    'TRANSFER_SUB_RESP'),
        ('FindServers',       'Req',   'FIND_SERVERS_REQ'),
        ('FindServers',       None,    'FIND_SERVERS_RESP'),
        ('GetEndpoints',      'Req',   'GET_ENDPOINTS_REQ'),
        ('GetEndpoints',      None,    'GET_ENDPOINTS_RESP'),
        ('Hello',             None,    'HELLO'),
        ('Acknowledge',       None,    'ACKNOWLEDGE'),
        ('Error',             None,    'OPC_ERROR'),
        ('ServiceFault',      None,    'SERVICE_FAULT'),
    ]
    for keyword, req_keyword, label in checks:
        if keyword in info:
            if req_keyword is None:
                return label
            if req_keyword in info:
                return label
    return None

all_messages = []
per_file = {}
found_files = 0

for filename in csv_files:
    path = os.path.join(CAPTURES, filename)
    if not os.path.exists(path):
        continue

    found_files += 1
    file_msgs = []

    with open(path, 'r', encoding='utf-8',
              errors='ignore') as f:
        reader = csv.DictReader(f)
        for row in reader:
            info = (row.get('Info') or
                    row.get('info') or
                    row.get('_ws.col.Info') or '')
            msg = classify(info)
            if msg:
                file_msgs.append(msg)
                all_messages.append(msg)

    per_file[filename] = Counter(file_msgs)
    print(f"  {filename}: {len(file_msgs)} messages")

counts = Counter(all_messages)

print(f"\n{'='*60}")
print(f"COMBINED ANALYSIS — {found_files} files, "
      f"{len(all_messages)} total messages")
print(f"{'='*60}")

# Categories
categories = {
    "TCP/Channel Setup": [
        'HELLO', 'ACKNOWLEDGE',
        'OPEN_CHANNEL_REQ', 'OPEN_CHANNEL_RESP'],
    "Session Management": [
        'CREATE_SESSION_REQ', 'CREATE_SESSION_RESP',
        'ACTIVATE_SESSION_REQ', 'ACTIVATE_SESSION_RESP',
        'CLOSE_SESSION_REQ', 'CLOSE_SESSION_RESP'],
    "Discovery": [
        'FIND_SERVERS_REQ', 'FIND_SERVERS_RESP',
        'GET_ENDPOINTS_REQ', 'GET_ENDPOINTS_RESP'],
    "Address Space": [
        'BROWSE_REQ', 'BROWSE_RESP',
        'BROWSE_NEXT_REQ', 'BROWSE_NEXT_RESP'],
    "Data Access": [
        'READ_REQ', 'READ_RESP',
        'WRITE_REQ', 'WRITE_RESP'],
    "Subscription": [
        'CREATE_SUB_REQ', 'CREATE_SUB_RESP',
        'MODIFY_SUB_REQ', 'MODIFY_SUB_RESP',
        'DELETE_SUB_REQ', 'DELETE_SUB_RESP',
        'CREATE_MON_REQ', 'CREATE_MON_RESP',
        'DELETE_MON_REQ', 'DELETE_MON_RESP',
        'PUBLISH_REQ', 'PUBLISH_RESP'],
    "Errors": [
        'OPC_ERROR', 'SERVICE_FAULT'],
}

grand_total = 0
for category, msgs in categories.items():
    cat_total = sum(counts.get(m, 0) for m in msgs)
    if cat_total == 0:
        continue
    print(f"\n{category} (total: {cat_total}):")
    for msg in msgs:
        if msg in counts:
            pct = (counts[msg]/len(all_messages))*100
            bar = "█" * min(counts[msg]//2, 30)
            print(f"  {msg:30} {counts[msg]:5} "
                  f"({pct:4.1f}%)  {bar}")
    grand_total += cat_total

print(f"\n{'='*60}")
print(f"GRAND TOTAL: {grand_total} messages")
print(f"{'='*60}")

# Save
os.makedirs(RESULTS, exist_ok=True)
path = os.path.join(RESULTS, "all_scenarios_analysis.txt")
with open(path, "w") as f:
    f.write("OPC UA Complete Message Analysis\n")
    f.write("=" * 40 + "\n\n")
    f.write(f"Files: {found_files}\n")
    f.write(f"Total: {len(all_messages)}\n\n")
    for category, msgs in categories.items():
        cat_total = sum(counts.get(m, 0) for m in msgs)
        if cat_total == 0:
            continue
        f.write(f"\n{category}:\n")
        for msg in msgs:
            if msg in counts:
                f.write(f"  {msg}: {counts[msg]}\n")

print(f"\nSaved: {path}")
print("\nNow do all 6 capture scenarios")
print("then run this script again for complete results!")