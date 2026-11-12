# Architecture

## Purpose of This Document

This document separates the architecture that is working today from the architecture I plan to build next.

That distinction is important because the repository currently contains a functioning Raspberry Pi wireless scanner, while the Python collector and AWS services are still planned components.

## Status Legend

```text
CURRENT   Implemented and tested on the Raspberry Pi
NEXT      The next local milestone
PLANNED   Designed but not implemented yet
```

# 1. Current Architecture

The currently implemented system ends at TShark.

```text
                         Nearby Wi-Fi Activity
                                  |
                                  v
                         IEEE 802.11 Frames
                                  |
                                  v
                    Alfa AWUS036ACM USB Adapter
                                  |
                                phy3
                                  |
                                mon24
                         Monitor-Mode Interface
                                  |
                                  v
                           Channel Hopper
                                  |
                 +----------------+----------------+
                 |                                 |
              2.4 GHz                           5 GHz
             1 / 6 / 11              36 / 40 / 44 / 48
                                    149 / 153 / 157 / 161
                 |                                 |
                 +----------------+----------------+
                                  |
                                  v
                               TShark
                                  |
                                  v
                     Raw Wireless Observations
                                  |
                    +-------------+-------------+
                    |             |             |
                    v             v             v
              Source MAC        RSSI       Frequency
```

The Pi's normal network connection is separate from the scanning radio:

```text
Raspberry Pi Built-In Wi-Fi
          |
        phy0
          |
        wlan0
          |
     Home Wi-Fi
          |
       Internet
          |
   SSH / Future AWS
```

## Current Component Roles

### Raspberry Pi 4B

Runs Raspberry Pi OS and hosts the wireless-scanning tools.

### wlan0

Provides the Pi's normal Wi-Fi and Internet connection.

### AWUS036ACM

Provides the dedicated monitor-mode radio.

### mon24

The monitor-mode interface created on the Alfa radio.

### Channel hopper

Retunes `mon24` through the selected 2.4 GHz and 5 GHz channels.

### TShark

Extracts timestamp, source MAC, RSSI, and frequency from observed frames.

# 2. Next Local Architecture

The next local milestone adds the Python collector and SQLite.

```text
                         AWUS036ACM
                              |
                              v
                         Monitor Mode
                              |
                              v
                        Channel Hopper
                              |
                              v
                            TShark
                              |
                              v
                       Python Collector
                              |
             +----------------+----------------+
             |                |                |
             v                v                v
        Normalize        Deduplicate       Classify
        observations       repeated       MAC address
                            frames            type
             |                |                |
             +----------------+----------------+
                              |
                              v
                         Local SQLite
                              |
                +-------------+-------------+
                |                           |
                v                           v
        Local history                  Upload queue
                                            |
                                            v
                                      AWS uploader
```

## Planned Local Responsibilities

### Python collector

- Start TShark as a child process.
- Parse line-buffered field output.
- Validate MAC, RSSI, and frequency values.
- Normalize timestamps.
- Convert frequency to channel and band.
- Determine whether the MAC is locally administered.
- Maintain first seen, last seen, and observation count.
- Aggregate RSSI.
- Write summarized observations to SQLite.

### SQLite

- Store current observation summaries.
- Store pending upload batches.
- Retain data when AWS is unavailable.
- Mark successfully uploaded batches.

### AWS uploader

- Read pending batches from SQLite.
- Send HTTPS requests to the ingestion endpoint.
- Retry temporary failures.
- Avoid deleting local records until the server acknowledges them.

# 3. Planned AWS Architecture

The planned AWS environment uses one Application Load Balancer, two EC2 instances, two container images, four Lambda functions, DynamoDB, S3, and CloudWatch.

Each EC2 instance runs both application containers:

```text
EC2 Instance 1
|-- ingestion-api
`-- search-api

EC2 Instance 2
|-- ingestion-api
`-- search-api
```

This creates four running containers while maintaining two clear application roles.

## End-to-End Architecture

```text
                               RASPBERRY PI 4B
                                      |
                              Python Collector
                                      |
                              Local SQLite Queue
                                      |
                              HTTPS / JSON Batches
                                      |
                                      v
                         Application Load Balancer
                                      |
                 +--------------------+--------------------+
                 |                                         |
        POST /observations                     GET /devices/*
                                               GET /history/*
                 |                                         |
                 v                                         v
      Ingestion API Target Group                Search API Target Group
                 |                                         |
        +--------+--------+                       +---------+---------+
        |                 |                       |                   |
        v                 v                       v                   v
     EC2 #1            EC2 #2                  EC2 #1              EC2 #2
 ingestion-api     ingestion-api              search-api          search-api
        |                 |                       |                   |
        +--------+--------+                       +---------+---------+
                 |                                          |
        +--------+---------+                      +---------+---------+
        |                  |                      |                   |
        v                  v                      v                   v
  device-ingest      metadata-update        device-search       device-history
     Lambda              Lambda                Lambda               Lambda
        |                  |                      |                   |
        v                  v                      v                   v
       S3             DynamoDB               DynamoDB            DynamoDB
 Raw observation     Current device         Device lookup       History index
     batches             state                                       |
                                                                     v
                                                            S3 historical data
                                                            when detail is needed
```

# 4. Load Balancer Design

The Application Load Balancer uses path-based routing.

```text
/observations*  --> ingestion-api target group
/devices*       --> search-api target group
/history*       --> search-api target group
```

The ingestion target group contains:

```text
EC2 #1 / ingestion-api
EC2 #2 / ingestion-api
```

The search target group contains:

```text
EC2 #1 / search-api
EC2 #2 / search-api
```

Each container will listen on its own host port or container-routing configuration so the load balancer can target the correct service on each EC2 instance.

# 5. Request Flows

## Observation ingestion flow

```text
Raspberry Pi
    |
    v
POST /observations
    |
    v
Application Load Balancer
    |
    v
ingestion-api
    |
    |-- invoke device-ingest
    |      `-- write batch to S3
    |
    `-- invoke metadata-update
           `-- update DynamoDB
```

The ingestion response should tell the Pi whether the batch was accepted. The Pi keeps the local batch until it receives a successful acknowledgement.

## Device search flow

```text
Client
   |
   v
GET /devices or GET /devices/{id}
   |
   v
Application Load Balancer
   |
   v
search-api
   |
   v
device-search Lambda
   |
   v
DynamoDB
```

## Device history flow

```text
Client
   |
   v
GET /history/{id}
   |
   v
Application Load Balancer
   |
   v
search-api
   |
   v
device-history Lambda
   |
   |-- read summary or index from DynamoDB
   `-- retrieve detailed historical objects from S3 when needed
```

# 6. Data Ownership

## SQLite

The Pi's operational buffer.

```text
Pending upload batches
Recent local observation summaries
Retry state
Upload acknowledgement state
```

## Amazon S3

The historical archive.

```text
Raw observation batches
Normalized batch files
Long-term records
Source data for later analysis
```

## Amazon DynamoDB

The searchable application state.

```text
Current device records
First seen and last seen
Observation counts
RSSI summaries
Recent channel and band
Address classification
History indexes
```

# 7. Lambda Responsibilities

## device-ingest

Input:

```text
Validated observation batch
```

Output:

```text
S3 object location and write result
```

Primary responsibility:

```text
Preserve the submitted historical batch
```

## metadata-update

Input:

```text
Validated observation records
```

Output:

```text
Updated DynamoDB state
```

Primary responsibilities:

```text
Upsert current records
Maintain first seen and last seen
Increment observation counts
Update RSSI summaries
Update channel and band fields
Apply five-minute observation logic
```

## device-search

Input:

```text
Search parameters or device identifier
```

Output:

```text
Current device or observation summary
```

## device-history

Input:

```text
Device identifier and history range
```

Output:

```text
Historical summary and optional detailed records
```

# 8. Monitoring Architecture

CloudWatch supports the AWS components without sitting in the direct request path.

```text
                    Amazon CloudWatch
                           ^
              +------------+------------+
              |            |            |
             ALB       EC2 / Docker    Lambda
              |            |            |
          Access data   App logs     Function logs
          Target health System data  Errors/duration
```

Planned monitoring includes:

- ALB request counts and target health
- EC2 CPU and system health
- Container application logs
- Lambda invocation count, errors, and duration
- Ingestion failure count
- Search failure count
- Alarms for unhealthy targets or repeated failures

# 9. Reliability Design

## Pi or network interruption

SQLite retains pending upload batches until connectivity returns.

## One EC2 instance unavailable

The matching containers on the second EC2 instance remain available through the target groups.

## One container unhealthy

The load balancer removes the unhealthy target from rotation.

## Lambda error

The API returns a failure that can be logged and retried according to the final retry policy.

## Pi reboot

Future systemd services recreate the monitor interface and restart the scanner, collector, and uploader.

# 10. Security Direction

The exact implementation is still planned, but the design should include:

- HTTPS between the Pi and the load balancer
- Scanner authentication
- Secrets stored outside the repository
- Least-privilege IAM roles
- Input validation in both container services
- No public database access
- No packet payload storage unless the project scope explicitly changes

# 11. Current Limitations

- The current implementation ends at TShark.
- The Pi uses one scanning radio.
- Channel hopping is not simultaneous channel coverage.
- MAC addresses are not reliable permanent identities.
- The final authentication, retry, database-key, and retention designs have not been implemented yet.
