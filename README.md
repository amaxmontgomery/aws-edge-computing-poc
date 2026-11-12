# Wireless Device Observation Platform

A Raspberry Pi and AWS project for passively observing nearby Wi-Fi activity, processing wireless metadata at the edge, and eventually storing and searching those observations in AWS.

The current prototype uses a Raspberry Pi 4B and an Alfa AWUS036ACM USB Wi-Fi adapter in monitor mode. The adapter hops across selected 2.4 GHz and 5 GHz channels while TShark extracts source MAC addresses, RSSI, frequency, and observation time.

The wireless scanner is working now. The Python collector, SQLite database, persistent services, and AWS backend are the next milestones.

## Current Status

**Milestone 1: Wireless observation prototype - complete**

```text
[✓] Raspberry Pi 4B configured
[✓] AWUS036ACM detected by Linux
[✓] Monitor mode confirmed
[✓] 2.4 GHz and 5 GHz channel switching verified
[✓] Dual-band channel hopping working
[✓] Source MAC extraction working
[✓] RSSI extraction working
[✓] Frequency extraction working
[ ] Python collector
[ ] SQLite persistence
[ ] Automatic startup with systemd
[ ] AWS ingestion and storage
[ ] Search API
```

## What Is Working Today

The Pi uses separate radios for connectivity and observation:

```text
Raspberry Pi 4B
|
|-- phy0 / wlan0
|   `-- Normal Wi-Fi and Internet access
|
`-- phy3 / Alfa AWUS036ACM
    |-- wlan1
    |   `-- Normal interface, left unmanaged and down
    |
    `-- mon24
        `-- Monitor-mode scanning interface
```

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

One AWUS036ACM contains one physical radio, so it can only listen to one channel at a time. The scanner builds coverage over time by rotating through the selected channels.

## Why I Built This

I wanted an AWS project with a real physical data source rather than a cloud-only demonstration using sample records.

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

The completed project is intended to demonstrate practical work with:

```text
Linux
IEEE 802.11 monitor mode
Channel hopping
Python
SQLite
Docker
REST APIs
Amazon EC2
Elastic Load Balancing
AWS Lambda
Amazon DynamoDB
Amazon S3
Amazon CloudWatch
```

## Next Local Milestone

The next version of the Pi pipeline will add a Python collector and local persistence:

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
Python collector
    |
    |-- Normalize observations
    |-- Deduplicate repeated frames
    |-- Track first seen and last seen
    |-- Count observations
    |-- Aggregate RSSI
    |-- Identify channel and band
    `-- Flag locally administered addresses
    |
    v
SQLite
    |
    v
AWS upload queue
```

Planned local fields include:

```text
Scanner ID
Observed MAC
First Seen
Last Seen
Observation Count
Latest RSSI
Average RSSI
Frequency
Channel
Wi-Fi Band
Locally Administered Flag
Upload Status
```

## Planned AWS Architecture

The AWS design uses one Application Load Balancer and two EC2 instances. Each EC2 instance runs both application containers:

```text
EC2 Instance 1
|-- ingestion-api
`-- search-api

EC2 Instance 2
|-- ingestion-api
`-- search-api
```

This creates four running containers while keeping the application focused on two service roles.

```text
Raspberry Pi
    |
    v
HTTPS observation batches
    |
    v
Application Load Balancer
    |
    |-- /observations* --> ingestion-api target group
    |                       |-- EC2 #1 / ingestion-api
    |                       `-- EC2 #2 / ingestion-api
    |
    `-- /devices* -------> search-api target group
        /history*            |-- EC2 #1 / search-api
                             `-- EC2 #2 / search-api
```

The containers call four Lambda functions:

```text
ingestion-api
|-- device-ingest      --> S3 historical batches
`-- metadata-update    --> DynamoDB searchable state

search-api
|-- device-search      --> DynamoDB current records
`-- device-history     --> DynamoDB indexes and S3 history
```

CloudWatch will collect application logs, Lambda logs, load balancer health, system metrics, and alarms.

## Data Responsibilities

```text
SQLite
`-- Local buffer and pending upload queue

Amazon S3
`-- Raw or normalized historical observation batches

Amazon DynamoDB
`-- Current searchable device metadata and history indexes
```

## MAC Address Identity

The project does not assume that one observed MAC address always represents one permanent physical device.

Modern devices may use randomized, private, or locally administered addresses. The first version treats each MAC as an **observed wireless identifier**. Any relationship between multiple addresses and one logical device will remain a separate, explicit inference.

## Current Limitations

- One radio cannot monitor every channel simultaneously.
- A device must transmit while the scanner is listening to the relevant channel.
- Channel hopping can miss short transmissions.
- Randomized MAC addresses prevent reliable identity based on MAC alone.
- RSSI represents relative signal strength, not exact distance.
- The current monitor interface and channel hopper are started manually.
- The Python collector and AWS environment are not implemented yet.

## Repository Documentation

- [Full project README](PROJECT_README.md)
- [Detailed Raspberry Pi setup](docs/pi-setup.md)
- [Architecture](docs/architecture.md)
- [Repository structure](docs/project-structure.md)
- [Roadmap](docs/roadmap.md)
- [Documentation index](docs/README.md)

## Authorized Use

This project is designed for authorized experimentation in my own environment. It focuses on wireless metadata and does not require packet payload collection.
