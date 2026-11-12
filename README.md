# Wireless Device Observation Platform

A Raspberry Pi and AWS proof-of-concept project for passively observing nearby Wi-Fi activity, processing wireless metadata at the edge, and eventually storing and searching those observations in AWS.

The current prototype uses a Raspberry Pi 4B and an Alfa AWUS036ACM USB Wi-Fi adapter in monitor mode. The adapter hops across selected 2.4 GHz and 5 GHz channels while TShark extracts source MAC addresses, RSSI, frequency, and observation time.

The wireless observation prototype is complete. The project is now in **Milestone 2**, where I am replacing the manual TShark workflow with a Python scanner, structured observation records, SQLite persistence, JSON batching, and automatic service startup.

> **Scope:** This is a wireless observation system, not a definitive device-identification system. An observed MAC address does not necessarily identify one unique physical device, especially when MAC randomization is enabled. The project focuses on wireless metadata and does not require packet payload collection.

---

## Project Status

The project is organized around seven GitHub milestones.

| Milestone | Status | Main Deliverable |
| --- | --- | --- |
| **M1 — Raspberry Pi Hardware & Network Scanning** | Complete | Working passive Wi-Fi observation prototype |
| **M2 — Python Scanner & Data Collection** | In progress | Python scanner, aggregation, SQLite, JSON batches, and persistent services |
| **M3 — AWS Infrastructure** | Planned | IAM, VPC, S3, DynamoDB, CloudWatch, security, and cost controls |
| **M4 — AWS Lambda and Data Collection Processing** | Planned | Lambda-based ingestion, historical storage, and metadata updates |
| **M5 — EC2, Docker, Load Balance** | Planned | Two EC2 instances, two containers per instance, and an Application Load Balancer |
| **M6 — Search API & App Integrate** | Planned | Search and history APIs, Raspberry Pi uploader, and end-to-end integration |
| **M7 — Wrap Up and Documentation** | Planned | Security review, observability, testing, diagrams, documentation, and final demonstration |

Detailed milestone requirements and completion criteria are documented in [`docs/roadmap.md`](docs/roadmap.md).

---

## Milestone 1 Results

Milestone 1 established the working Raspberry Pi wireless observation prototype.

```text
[✓] Raspberry Pi 4B configured
[✓] Raspberry Pi OS Lite installed and updated
[✓] SSH and Raspberry Pi Connect Lite configured
[✓] Required wireless monitoring tools installed
[✓] Alfa AWUS036ACM detected by Linux
[✓] Monitor mode support confirmed
[✓] Dedicated monitor interface created
[✓] 2.4 GHz channel switching verified
[✓] 5 GHz channel switching verified
[✓] Dual-band channel hopping working
[✓] Nearby IEEE 802.11 traffic captured
[✓] Source MAC extraction working
[✓] RSSI extraction working
[✓] Frequency extraction working
[✓] Raspberry Pi setup documented
```

The complete Raspberry Pi setup is documented in [`docs/pi-setup.md`](docs/pi-setup.md).

---

## What Is Working Today

The Raspberry Pi uses separate radios for normal connectivity and wireless observation.

```text
Raspberry Pi 4B
|
|-- phy0 / wlan0
|   `-- Normal Wi-Fi and Internet access
|
`-- phy3 / Alfa AWUS036ACM
    |-- wlan1
    |   `-- Normal interface, unmanaged and down
    |
    `-- mon24
        `-- Monitor-mode observation interface
```

The physical radio and interface names are specific to the current Raspberry Pi. Another installation may assign different `phy` or `wlan` numbers.

### Current Data Path

The currently implemented data path ends at TShark:

```text
Nearby Wi-Fi activity
        |
        v
Alfa AWUS036ACM
        |
        v
mon24 monitor interface
        |
        v
Dual-band channel hopper
        |
        v
TShark
        |
        v
Timestamp | Source MAC | RSSI | Frequency
```

The current channel list is:

```text
2.4 GHz: 1, 6, 11
5 GHz:   36, 40, 44, 48, 149, 153, 157, 161
```

The scanner currently spends approximately one second on each channel before moving to the next.

One AWUS036ACM contains one physical Wi-Fi radio. Its two antennas do not act as two independent scanners. The radio can only listen to one channel at a time, so the scanner builds coverage over time by rotating through the selected channels.

---

## Example TShark Observation

The current prototype uses TShark to extract selected wireless metadata:

```bash
sudo tshark -l -i mon24 \
  -Y "wlan.sa" \
  -T fields \
  -E occurrence=f \
  -e frame.time \
  -e wlan.sa \
  -e radiotap.dbm_antsignal \
  -e radiotap.channel.freq
```

The output contains:

```text
Timestamp | Source MAC | RSSI | Frequency
```

Illustrative, redacted output:

```text
Nov 9 21:29:37    dc:8d:8a:xx:xx:xx    -80    2412
Nov 9 21:29:38    3c:28:6d:xx:xx:xx    -72    2437
Nov 9 21:29:39    a6:e2:d5:xx:xx:xx    -65    5180
```

Real unredacted MAC-address logs are not intended to be committed to the public repository.

---

## Why I Built This

I wanted an AWS project with a real physical data source rather than a cloud-only demonstration based entirely on generated sample records.

The Raspberry Pi gives the project a practical edge-computing and networking component:

```text
Physical wireless environment
        |
        v
Raspberry Pi edge sensor
        |
        v
Local processing and buffering
        |
        v
AWS application and storage layer
```

This creates real implementation problems to solve, including:

- Linux wireless interface management
- IEEE 802.11 monitor mode
- Channel hopping
- Repeated observation handling
- MAC-address randomization
- Local persistence
- Upload retries
- API design
- Cloud storage
- Container deployment
- High availability
- Monitoring and failure recovery

The completed project is intended to demonstrate practical work with:

```text
Linux
IEEE 802.11 monitor mode
Channel hopping
Python
SQLite
JSON data contracts
Docker
REST APIs
Amazon EC2
Elastic Load Balancing
AWS Lambda
Amazon DynamoDB
Amazon S3
Amazon CloudWatch
IAM and network security
```

---

## Current Milestone: Python Scanner & Data Collection

Milestone 2 replaces the manual terminal workflow with a persistent local application.

The planned local pipeline is:

```text
AWUS036ACM
    |
    v
Monitor mode and channel hopping
    |
    v
TShark
    |
    v
Python scanner
    |
    |-- Parse and validate observations
    |-- Normalize timestamps and MAC formatting
    |-- Convert frequency to channel and band
    |-- Aggregate repeated observations
    |-- Track first seen and last seen
    |-- Count observations and encounters
    |-- Calculate RSSI statistics
    |-- Flag locally administered addresses
    |
    v
SQLite
    |
    |-- Observation summaries
    |-- Local state
    `-- Pending upload queue
    |
    v
Validated JSON batches
```

### Active M2 Work

Milestone 2 is divided into the following GitHub sub-issues:

```text
[M2] Create the Python project structure and observation schema
[M2] Start and parse TShark from Python
[M2] Implement observation aggregation and deduplication
[M2] Add SQLite persistence
[M2] Generate JSON batches and maintain the upload queue
[M2] Add systemd startup and reboot recovery
[M2] Add tests and collector documentation
```

The GitHub Project board tracks the current status of these items.

### Planned Local Fields

The Python scanner is expected to maintain fields such as:

```text
Scanner ID
Observed MAC
First Seen
Last Seen
Frame Count
Encounter Count
Latest RSSI
Minimum RSSI
Maximum RSSI
Average RSSI
Frequency
Channel
Wi-Fi Band
Locally Administered Flag
Upload Status
```

The exact schema will be finalized as part of the first M2 sub-issue.

---

## Planned AWS Architecture

The AWS portion of the project begins in Milestone 3.

The planned design uses one Application Load Balancer and two EC2 instances. Each EC2 instance runs both application containers:

```text
EC2 Instance 1
|-- ingestion-api
`-- search-api

EC2 Instance 2
|-- ingestion-api
`-- search-api
```

This creates four running containers while keeping the application focused on two service roles.

### Planned Request Routing

```text
Raspberry Pi
    |
    v
HTTPS observation batches
    |
    v
Application Load Balancer
    |
    |-- POST /observations*
    |          |
    |          v
    |   ingestion-api target group
    |          |-- EC2 #1 / ingestion-api
    |          `-- EC2 #2 / ingestion-api
    |
    |-- GET /devices*
    |          |
    |          v
    |   search-api target group
    |          |-- EC2 #1 / search-api
    |          `-- EC2 #2 / search-api
    |
    `-- GET /history*
               |
               v
        search-api target group
```

Both EC2 instances are intended to provide the same application roles. If one instance becomes unavailable, the load balancer should be able to route requests to the remaining healthy instance.

---

## Planned Application Responsibilities

### `ingestion-api`

The ingestion service will receive observation batches from the Raspberry Pi.

```text
POST /observations
        |
        v
Validate request and scanner identity
        |
        v
Invoke ingestion-processing functions
```

It will integrate with:

```text
device-ingest
`-- Store raw or normalized historical batches in S3

metadata-update
`-- Maintain current searchable metadata in DynamoDB
```

### `search-api`

The search service will expose current observations and history.

Planned endpoints include:

```text
GET /devices
GET /devices/{id}
GET /history/{id}
```

It will integrate with:

```text
device-search
`-- Query current searchable records in DynamoDB

device-history
`-- Retrieve history indexes and S3 observation data
```

---

## Planned AWS Milestone Boundaries

The AWS work is intentionally divided into separate milestones.

### M3 — AWS Infrastructure

```text
IAM
VPC and subnet design
Routing
Security groups
S3
DynamoDB
CloudWatch foundations
Encryption
Budget and cost controls
```

### M4 — AWS Lambda and Data Collection Processing

```text
device-ingest
metadata-update
Batch validation
S3 historical writes
DynamoDB metadata updates
Idempotency
Structured logging
```

### M5 — EC2, Docker, Load Balance

```text
ingestion-api
search-api application shell
Docker images
Amazon ECR
Two EC2 instances
Application Load Balancer
Target groups
Health checks
Container logging
```

### M6 — Search API & App Integrate

```text
device-search
device-history
Search endpoints
History endpoints
Raspberry Pi uploader
Authentication
Retries and acknowledgements
End-to-end Pi-to-AWS integration
```

### M7 — Wrap Up and Documentation

```text
Least-privilege review
Security review
CloudWatch dashboards and alarms
Failure and recovery testing
Cost review
Architecture diagrams
Final documentation
End-to-end demonstration
Tagged release
```

---

## Data Responsibilities

The project separates local buffering, historical storage, and searchable state.

```text
SQLite
`-- Local observation summaries and pending upload queue

Amazon S3
`-- Raw or normalized historical observation batches

Amazon DynamoDB
`-- Current searchable metadata and history indexes

Amazon CloudWatch
`-- Logs, metrics, health information, and alarms
```

This allows each storage service to have a clear responsibility.

---

## MAC Address Identity

The project does not assume that one observed MAC address always represents one permanent physical device.

Modern devices may use:

- Randomized MAC addresses
- Private MAC addresses
- Locally administered addresses
- Different identifiers on different wireless networks

The first version treats each MAC as an **observed wireless identifier**.

Any relationship between multiple addresses and one logical physical device will remain a separate, explicit inference. A locally administered address may be a useful indicator, but it is not proof that an address is randomized.

---

## Current Limitations

- One radio cannot monitor every Wi-Fi channel simultaneously.
- A device must transmit while the scanner is listening to the relevant channel.
- Channel hopping can miss short transmissions.
- The current channel list does not include DFS channels.
- Randomized MAC addresses prevent reliable identity based on MAC alone.
- RSSI represents relative signal strength, not exact physical distance.
- The current monitor interface and channel hopper are started manually.
- The Python scanner and SQLite database are still being implemented.
- The AWS environment has not been deployed yet.

---

## Current Repository Structure

```text
aws-edge-computing-poc/
|-- .gitignore
|-- README.md
`-- docs/
    |-- README.md
    |-- architecture.md
    |-- pi-setup.md
    |-- project-structure.md
    `-- roadmap.md
```

Application directories will be added only when they contain real implementation files. Empty folders will not be created only to make the repository appear more complete.

---

## Documentation

- [Detailed Raspberry Pi setup](docs/pi-setup.md)
- [Architecture](docs/architecture.md)
- [Repository structure](docs/project-structure.md)
- [Roadmap and milestone checklists](docs/roadmap.md)
- [Documentation index](docs/README.md)

Project planning, checklist progress, sub-issues, and active work are tracked separately on the GitHub Project page.

---

## Public Repository Hygiene

The following should not be committed:

- Unredacted household MAC-address logs
- Packet capture files containing private data
- Wi-Fi passwords
- AWS access keys
- API secrets
- `.env` files containing credentials
- Runtime SQLite databases
- Private network details that are not needed for the project
- Screenshots containing sensitive information

Synthetic or redacted observations should be used in examples and tests.

---

## Authorized Use

This project is designed for authorized experimentation in my own environment.

It focuses on wireless metadata and does not require packet payload collection. Anyone adapting the project should verify that their use complies with applicable privacy, wireless, and computer-access requirements.
