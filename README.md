# AWS Edge Computing & Wireless Observation - Proof of Concept
Raspberry Pi network scanner using AWS infrastructure, device search, and serverless processing. 

A Raspberry Pi and AWS proof-of-concept project for passively observing nearby Wi-Fi activity, processing wireless metadata at the edge, and eventually storing and searching the resulting observations in AWS.

The project currently has a working Raspberry Pi wireless scanner using an Alfa AWUS036ACM in monitor mode.

The AWS portion is still under development.

---

## Current Status

**Current milestone: Raspberry Pi wireless observation prototype is working.**

The scanner currently supports:

```text
[✓] 2.4 GHz observation
[✓] 5 GHz observation
[✓] Monitor mode
[✓] Channel hopping
[✓] Source MAC extraction
[✓] RSSI collection
[✓] Frequency collection
[ ] Python collector
[ ] SQLite
[ ] AWS ingestion
[ ] AWS backend
```

---

## What the Project Does

The Raspberry Pi acts as a wireless edge sensor.

It does not require nearby devices to connect to the Raspberry Pi or to my home Wi-Fi network.

Instead, a dedicated Wi-Fi adapter operates in monitor mode and listens for observable IEEE 802.11 traffic on the current wireless channel.

The current data flow is:

```text
Nearby Wi-Fi activity
        ↓
Alfa AWUS036ACM
        ↓
Monitor Mode
        ↓
Channel Hopper
        ↓
TShark
        ↓
Wireless Metadata
```

The next stage will add:

```text
Wireless Metadata
        ↓
Python Collector
        ↓
SQLite
        ↓
AWS
```

---

## Hardware

### Raspberry Pi

```text
Raspberry Pi 4B
```

The Pi handles the physical scanner and will eventually perform local data processing before sending observations to AWS.

### Wi-Fi Adapter

```text
Alfa AWUS036ACM
```

The adapter provides:

- Linux support
- Monitor mode
- 2.4 GHz support
- 5 GHz support
- External antennas

The AWUS036ACM contains one physical Wi-Fi radio, so it can only listen to one channel at a time.

---

## Current Network Layout

The Raspberry Pi's built-in Wi-Fi remains dedicated to normal network connectivity.

The Alfa adapter is dedicated to wireless observation.

```text
 Pi 4B
│
├── wlan0
│   └── Normal Wi-Fi / Internet
│
└── AWUS036ACM
    │
    └── mon24
        └── Monitor-mode scanning
```

This allows the  Pi to remain online while the external adapter continuously changes channels.

---

## Monitor Interface

The Alfa adapter is represented by a physical wireless radio in Linux.

In the current setup:

```text
phy0 =  Pi built-in Wi-Fi

phy3 = Alfa AWUS036ACM
```

The monitor interface was created with:

```bash
sudo iw phy phy3 interface add mon24 type monitor
```

and enabled with:

```bash
sudo ip link set mon24 up
```

The current interface relationship is:

```text
phy3
├── wlan1
│   └── Normal Alfa interface
│
└── mon24
    └── Monitor-mode interface
```

`wlan1` and `mon24` are not separate physical radios. They both use the same AWUS036ACM hardware.

A more detailed explanation of this setup is available in:

```text
docs/pi-setup.md
```

---

## Channel Hopping

Because one radio cannot monitor all channels simultaneously, the scanner continuously changes channels.

The current 2.4 GHz channels are:

```text
1
6
11
```

The current 5 GHz channels are:

```text
36
40
44
48
149
153
157
161
```

Current hopping command:

```bash
sudo bash -c 'while true; do
  for ch in 1 6 11 36 40 44 48 149 153 157 161; do
    iw dev mon24 set channel "$ch"
    sleep 1
  done
done' &
```

The current dwell time is approximately one second per channel.

This setting is intentionally simple for the first version and may be adjusted later.

---

## Wireless Metadata Collection

TShark currently extracts the fields needed for the prototype:

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

Current fields:

```text
Timestamp
Source MAC
RSSI
Frequency
```

Example:

```text
Nov 9, 2026 21:29:37   dc:8d:8a:xx:xx:xx   -80   2412
Nov 9, 2026 21:29:38   3c:28:6d:xx:xx:xx   -72   2437
Nov 9, 2026 21:29:39   a6:e2:d5:xx:xx:xx   -65   5180
```

The project does not require packet payload contents.

The goal is to work with wireless observation metadata.

---

## MAC Address Randomization

The project does not assume that every observed MAC address represents one permanent physical device.

Modern devices may use:

- Randomized MAC addresses
- Private MAC addresses
- Locally administered addresses

Because of this:

```text
Observed MAC
    ≠
Guaranteed permanent device identity
```

The initial system will treat each MAC as an observed wireless identifier.

Later processing may associate observations with logical devices when there is enough information to do so, but raw MAC addresses will not automatically be treated as permanent identities.

---

## Planned Python Collector

The next milestone is a Python collector running on the Raspberry Pi.

Current:

```text
TShark
   ↓
Raw observations
```

Planned:

```text
TShark
   ↓
Python Collector
   ↓
Deduplication
   ↓
Aggregation
   ↓
SQLite
```

The collector will maintain fields such as:

```text
Observed MAC
First Seen
Last Seen
Observation Count
Latest RSSI
Average RSSI
Frequency
Channel
Band
Locally Administered Flag
Possible Randomized Address Flag
Scanner ID
```

Instead of storing hundreds of repeated observations for the same address, the collector will maintain a summarized record.

---

## Planned AWS Architecture

The Raspberry Pi is the edge layer of a larger AWS proof-of-concept architecture.

Current planned design:

```text
                 Raspberry Pi
                      │
                      ▼
               Python Collector
                      │
                      ▼
                     AWS
                      │
               Load Balancer
                      │
             ┌────────┴────────┐
             ▼                 ▼
           EC2 #1            EC2 #2
             │                 │
      ┌──────┴──────┐   ┌──────┴──────┐
      ▼             ▼   ▼             ▼
 Container 1   Container 2       Container 3/4
             │
             ▼
           Lambda
             │
      ┌──────┴──────┐
      ▼             ▼
  DynamoDB          S3
```

The exact architecture may change as I build and test each component.

---

## Planned AWS Responsibilities

### EC2

EC2 will host containerized application services.

### Containers

The current design includes two EC2 instances with two containers on each instance.

Potential responsibilities include:

- Observation ingestion
- Search API
- Device queries
- Application processing

### Load Balancer

The load balancer will distribute requests across multiple application instances and provide health checking.

### Lambda

Lambda functions will handle event-driven processing and metadata updates.

### DynamoDB

DynamoDB will store searchable device and observation metadata.

### S3

S3 will provide historical observation storage.

---

## Project Progress

### Raspberry Pi

```text
[✓] Raspberry Pi OS configured
[✓] Required packages installed
[✓] AWUS036ACM detected
[✓] Monitor mode verified
[✓] Monitor interface created
[✓] 2.4 GHz capture tested
[✓] 5 GHz capture tested
[✓] Channel switching verified
[✓] Dual-band channel hopping working
[✓] Source MAC extraction working
[✓] RSSI extraction working
[✓] Frequency extraction working
```

### Local Application

```text
[ ] Python collector
[ ] MAC deduplication
[ ] Observation aggregation
[ ] SQLite database
[ ] systemd startup service
```

### AWS

```text
[ ] AWS ingestion endpoint
[ ] EC2 instances
[ ] Docker containers
[ ] Load balancer
[ ] Lambda functions
[ ] DynamoDB
[ ] S3
[ ] Search API
[ ] Monitoring
```

---

## Repository Structure

The repository will eventually follow a structure similar to:

```text
.
├── README.md
│
├── docs/
│   ├── pi-setup.md
│   ├── architecture.md
│   └── aws-setup.md
│
├── pi/
│   ├── collector/
│   ├── channel-hopper/
│   └── systemd/
│
├── aws/
│   ├── containers/
│   ├── lambdas/
│   └── infrastructure/
│
└── diagrams/
```

The structure will be expanded as each part of the project is implemented.

---

## Documentation

Detailed Raspberry Pi configuration:

```text
docs/pi-setup.md
```

Future documentation will include:

```text
AWS architecture
AWS deployment
Python collector
Database design
API design
Container setup
Testing
```

---

## Current Milestone

### Milestone 1 — Wireless Observation Prototype

```text
COMPLETE
```

The Raspberry Pi can currently:

```text
Scan selected 2.4 GHz and 5 GHz channels
        ↓
Capture nearby IEEE 802.11 traffic
        ↓
Extract source MAC addresses
        ↓
Measure RSSI
        ↓
Record capture frequency
```

### Milestone 2 — Python Collector

```text
NEXT
```

The next goal is to turn the working scanner into a persistent application that maintains structured observations and stores them locally.

---

## Project Goal

The completed project is intended to demonstrate practical experience with:

```text
Linux
Networking
Wi-Fi / IEEE 802.11
Monitor Mode
Python
SQLite
Docker
REST APIs
AWS EC2
Elastic Load Balancing
AWS Lambda
Amazon DynamoDB
Amazon S3
Cloud monitoring
```

The Raspberry Pi gives the project a physical networking component, while AWS provides the cloud architecture and application layer.

The goal is to build both sides into one working system.
