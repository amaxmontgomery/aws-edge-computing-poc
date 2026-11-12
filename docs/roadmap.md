# Project Roadmap

## Purpose

This roadmap tracks the project through the seven milestones already created in GitHub. I am keeping those milestone boundaries intact so the repository documentation, GitHub issues, Project views, and implementation work all describe the same plan.

The project is currently between Milestone 1 and Milestone 2:

- The wireless observation prototype is working.
- Milestone 1 remains open until the current setup is committed and documented.
- Milestone 2 is the next implementation phase.
- Milestones 3 through 7 remain planned.

## Milestone Summary

| Milestone | Status | Main Deliverable |
| --- | --- | --- |
| **M1 — Raspberry Pi Hardware & Network Scanning** | Working; documentation pending | Raspberry Pi and AWUS036ACM passively observing selected 2.4 GHz and 5 GHz channels |
| **M2 — Python Scanner & Data Collection** | Next | Python-managed scanner, normalized observations, deduplication, SQLite, and JSON batches |
| **M3 — AWS Infrastructure** | Planned | IAM, VPC, S3, DynamoDB, CloudWatch, security, and cost controls |
| **M4 — AWS Lambda and Data Collection Processing** | Planned | Lambda-based ingestion, S3 storage, and DynamoDB metadata updates |
| **M5 — EC2, Docker, Load Balance** | Planned | Two EC2 instances, two containers per instance, and an Application Load Balancer |
| **M6 — Search API & App Integrate** | Planned | Search/history APIs, a small client, and the complete Raspberry Pi-to-AWS flow |
| **M7 — Wrap Up and Documentation** | Planned | Least-privilege review, observability, testing, diagrams, final documentation, and demonstration |

---

# Milestone 1 — Raspberry Pi Hardware & Network Scanning

**Status:** Working prototype; repository documentation still needs to be completed and committed.

## GitHub Milestone Description

Configure a Raspberry Pi 4B with Raspberry Pi OS Lite and an Alfa AWUS036ACM in monitor mode, verify passive 2.4 GHz and 5 GHz observation, and document the working setup.

## Existing Checklist Issue

Use the existing issue:

```text
M1 Checklist #1
```

Do not create a duplicate Milestone 1 checklist issue.

## Checklist

```markdown
- [x] Install and configure Raspberry Pi OS Lite
- [x] Configure SSH and Raspberry Pi Connect Lite
- [x] Install wireless monitoring dependencies
- [x] Configure the Alfa AWUS036ACM and its two external antennas
- [x] Enable monitor mode
- [x] Verify that nearby wireless devices and their channels can be observed
- [ ] Commit the current setup documentation in `README.md` and `docs/pi-setup.md`
```

## What Has Been Verified

- The Raspberry Pi maintains normal network access through `wlan0`.
- The AWUS036ACM is identified separately from the Pi's built-in Wi-Fi.
- The `mon24` interface operates in monitor mode.
- TShark captures source MAC, RSSI, timestamp, and frequency metadata.
- The adapter can move between selected 2.4 GHz and 5 GHz channels.
- One AWUS036ACM is being used as one radio with two antennas.

## Completion Criteria

Milestone 1 is complete when:

- The root `README.md` is committed.
- `docs/pi-setup.md` is committed.
- The final checklist item is checked.
- `M1 Checklist #1` is closed.
- The GitHub milestone is closed.

---

# Milestone 2 — Python Scanner & Data Collection

**Status:** Next

## GitHub Milestone Description

Build the Python scanner and local data collection pipeline, including supervised channel hopping, TShark parsing, timestamps, deduplication, SQLite persistence, and JSON batch output.

## Checklist Issue Title

```text
M2 Checklist
```

## Checklist

```markdown
- [ ] Create the Python scanner project structure
- [ ] Define the normalized observation schema
- [ ] Move channel hopping from the temporary shell loop into a Python-managed or supervised process
- [ ] Start and monitor TShark from Python
- [ ] Parse timestamp, source MAC, RSSI, and frequency fields
- [ ] Normalize timestamps and MAC address formatting
- [ ] Convert frequency to Wi-Fi channel and band
- [ ] Identify locally administered MAC addresses
- [ ] Define and implement the deduplication and five-minute revisit behavior
- [ ] Track first seen, last seen, and observation count
- [ ] Calculate current, minimum, maximum, and average RSSI
- [ ] Create the SQLite database schema
- [ ] Persist observation summaries across application restarts
- [ ] Generate validated JSON observation batches
- [ ] Preserve unacknowledged batches in a local pending-upload queue
- [ ] Add configuration, structured logging, and graceful shutdown
- [ ] Add systemd services for scanner startup and reboot recovery
- [ ] Add parser, aggregation, and database tests
- [ ] Document installation, configuration, and local operation
```

## Main Output

The working terminal stream should become a structured local application:

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
     |-- Parse and validate
     |-- Normalize
     |-- Deduplicate and aggregate
     |-- Classify address metadata
     v
SQLite
     |
     v
Pending JSON batches
```

## Completion Criteria

Milestone 2 is complete when:

- The scanner starts without manually reading TShark output.
- Channel hopping runs as part of the managed scanner workflow.
- Malformed input does not stop the application.
- Repeated observations update a summarized record instead of creating uncontrolled duplicates.
- SQLite preserves records and pending batches across a restart.
- The Pi resumes scanning after a reboot.
- The scanner produces valid JSON batches ready for the AWS ingestion path.

---

# Milestone 3 — AWS Infrastructure

**Status:** Planned

## GitHub Milestone Description

Create the AWS foundation for the project, including IAM, VPC networking, S3, DynamoDB, CloudWatch, security controls, configuration handling, and cost monitoring.

## Checklist Issue Title

```text
M3 Checklist
```

## Checklist

```markdown
- [ ] Select the AWS region and document the naming convention
- [ ] Define project tags for ownership, environment, component, and cost tracking
- [ ] Configure an AWS Budget and cost alerts
- [ ] Design the VPC, subnet, routing, and availability-zone layout
- [ ] Create the VPC and required subnets
- [ ] Configure route tables and Internet access based on the documented design
- [ ] Create security-group foundations for the load balancer and EC2 instances
- [ ] Define IAM roles for EC2, Lambda, and project administration
- [ ] Apply least-privilege boundaries to the initial IAM policies
- [ ] Create the private S3 bucket for raw historical observation batches
- [ ] Enable S3 encryption, versioning as appropriate, and block public access
- [ ] Define the S3 object-key and retention strategy
- [ ] Create the DynamoDB table for searchable device metadata
- [ ] Define DynamoDB partition keys, sort keys, and required indexes
- [ ] Configure DynamoDB encryption and recovery settings
- [ ] Create CloudWatch log groups and retention settings
- [ ] Create baseline CloudWatch metrics or alarms for the planned services
- [ ] Store configuration and secrets without committing them to Git
- [ ] Document the AWS resource relationships and setup decisions
```

## Scope Boundary

Milestone 3 creates the shared AWS foundation. It does not deploy the Lambda application code or the EC2 containers yet.

## Completion Criteria

Milestone 3 is complete when:

- The network and security foundation is available for later milestones.
- S3 is private and ready to receive raw observation batches.
- DynamoDB supports the planned current-state and search access patterns.
- IAM roles exist without broad administrator permissions.
- CloudWatch and cost controls are in place.
- The resource design and deployment steps are documented.

---

# Milestone 4 — AWS Lambda and Data Collection Processing

**Status:** Planned

## GitHub Milestone Description

Implement the Lambda functions that process incoming observation batches, store raw history in S3, and maintain current searchable device metadata in DynamoDB.

## Checklist Issue Title

```text
M4 Checklist
```

## Checklist

```markdown
- [ ] Finalize the JSON observation-batch contract produced by Milestone 2
- [ ] Create shared validation and error-response behavior
- [ ] Implement the `device-ingest` Lambda
- [ ] Store accepted raw or normalized observation batches in S3
- [ ] Return a traceable S3 object reference for each accepted batch
- [ ] Implement the `metadata-update` Lambda
- [ ] Create a DynamoDB record for a newly observed address
- [ ] Preserve the original first-seen timestamp
- [ ] Update last seen, observation count, RSSI, frequency, channel, and band
- [ ] Store locally administered and possible-randomization metadata
- [ ] Implement the defined five-minute revisit and aggregation behavior
- [ ] Add idempotency so retries do not inflate counts or duplicate state
- [ ] Add structured CloudWatch logging and correlation identifiers
- [ ] Create representative sample events for local and AWS testing
- [ ] Add unit tests for validation and processing logic
- [ ] Add integration tests against S3 and DynamoDB
- [ ] Document the Lambda event flow, outputs, and failure behavior
```

## Planned Lambda Responsibilities

```text
device-ingest
     |
     `-- Store raw or normalized batches in S3

metadata-update
     |
     `-- Maintain current searchable metadata in DynamoDB
```

Search and history Lambda functions are intentionally reserved for Milestone 6.

## Completion Criteria

Milestone 4 is complete when:

- A valid sample batch creates a traceable S3 object.
- The same batch creates or updates the expected DynamoDB metadata.
- First-seen data is preserved while later observations update the current state.
- Retried batches do not create duplicate state or inaccurate counts.
- Invalid requests fail clearly and create useful logs.

---

# Milestone 5 — EC2, Docker, Load Balance

**Status:** Planned

## GitHub Milestone Description

Deploy two EC2 instances with `ingestion-api` and `search-api` containers on each instance, place them behind an Application Load Balancer, and connect the ingestion service to the processing Lambdas.

## Checklist Issue Title

```text
M5 Checklist
```

## Checklist

```markdown
- [ ] Build the `ingestion-api` application
- [ ] Add `POST /observations` request validation and response handling
- [ ] Connect `ingestion-api` to `device-ingest` and `metadata-update`
- [ ] Build the initial `search-api` application shell and health endpoint
- [ ] Create Dockerfiles for both services
- [ ] Add local container configuration and tests
- [ ] Create ECR repositories for both container images
- [ ] Build and publish versioned container images
- [ ] Provision two EC2 instances in the documented network layout
- [ ] Configure EC2 IAM roles and security groups
- [ ] Install and configure Docker on both EC2 instances
- [ ] Run `ingestion-api` and `search-api` on EC2 instance 1
- [ ] Run `ingestion-api` and `search-api` on EC2 instance 2
- [ ] Create the Application Load Balancer
- [ ] Create separate ingestion and search target groups
- [ ] Configure path-based routing for ingestion and search requests
- [ ] Configure container and load-balancer health checks
- [ ] Send application and container logs to CloudWatch
- [ ] Test ingestion routing through the load balancer
- [ ] Test operation with one EC2 instance unavailable
- [ ] Document deployment, update, and recovery procedures
```

## Required Runtime Layout

```text
EC2 Instance 1
|-- ingestion-api
`-- search-api

EC2 Instance 2
|-- ingestion-api
`-- search-api
```

The search service can remain limited to health and placeholder behavior until Milestone 6 implements the search features.

## Completion Criteria

Milestone 5 is complete when:

- Both container images run on both EC2 instances.
- The load balancer routes requests to the correct target group.
- `ingestion-api` successfully invokes the Milestone 4 Lambdas.
- Health checks remove an unhealthy target from service.
- Ingestion remains available through the other instance during a single-instance failure.

---

# Milestone 6 — Search API & App Integrate

**Status:** Planned

## GitHub Milestone Description

Build the device search and history APIs, integrate them with DynamoDB and S3, add a minimal client, connect the Raspberry Pi uploader, and validate the complete Pi-to-AWS workflow.

## Checklist Issue Title

```text
M6 Checklist
```

## Checklist

```markdown
- [ ] Define `GET /devices`
- [ ] Define `GET /devices/{id}`
- [ ] Define `GET /history/{id}`
- [ ] Implement the `device-search` Lambda
- [ ] Implement the `device-history` Lambda
- [ ] Query DynamoDB current records efficiently
- [ ] Retrieve S3 historical detail when requested
- [ ] Add pagination, filtering, and input validation
- [ ] Integrate the search and history functions with `search-api`
- [ ] Complete load-balancer routing for the search endpoints
- [ ] Build the Raspberry Pi AWS uploader
- [ ] Add endpoint authentication and secure configuration handling
- [ ] Add upload retries, timeouts, acknowledgements, and queue cleanup
- [ ] Connect pending SQLite batches to `ingestion-api`
- [ ] Build a minimal search client or demonstration interface
- [ ] Run an end-to-end Raspberry Pi-to-AWS ingestion test
- [ ] Verify that an observed address becomes searchable in DynamoDB
- [ ] Verify that historical observation data can be retrieved from S3
- [ ] Add API and integration tests
- [ ] Document the API, client, and end-to-end data flow
```

## Planned Application Flow

```text
Raspberry Pi pending batch
          |
          v
Application Load Balancer
          |
          v
ingestion-api
          |
          +--> device-ingest --> S3
          `--> metadata-update --> DynamoDB

Search client
          |
          v
Application Load Balancer
          |
          v
search-api
          |
          +--> device-search --> DynamoDB
          `--> device-history --> DynamoDB / S3
```

## Completion Criteria

Milestone 6 is complete when:

- The Pi uploads a pending batch and receives an acknowledgement.
- The batch appears in S3 and updates DynamoDB.
- The search API returns current device metadata.
- The history API returns the expected historical references or records.
- A minimal client demonstrates observation, ingestion, search, and history.

---

# Milestone 7 — Wrap Up and Documentation

**Status:** Planned

## GitHub Milestone Description

Complete least-privilege hardening, observability, failure testing, cost review, architecture diagrams, final documentation, and the end-to-end project demonstration.

## Checklist Issue Title

```text
M7 Checklist
```

## Checklist

```markdown
- [ ] Review all IAM policies for least privilege
- [ ] Review security groups and public exposure
- [ ] Confirm encryption, authentication, and secret-handling practices
- [ ] Confirm HTTPS is used for external application traffic
- [ ] Create or finalize CloudWatch dashboards
- [ ] Configure alarms for load-balancer health, EC2 health, Lambda failures, and application errors
- [ ] Set appropriate log-retention policies
- [ ] Test Raspberry Pi reboot and service recovery
- [ ] Test temporary Internet and AWS outages
- [ ] Test duplicate and replayed batches
- [ ] Test invalid API requests and error paths
- [ ] Test one-EC2-instance failure and recovery
- [ ] Review ongoing AWS costs and budget alerts
- [ ] Finalize the current-state and planned architecture diagrams
- [ ] Finalize `README.md` and all documents under `docs/`
- [ ] Add final deployment, API, testing, and troubleshooting documentation
- [ ] Redact real MAC addresses, credentials, and private network details from public examples
- [ ] Select and add a repository license if the project will permit reuse
- [ ] Create the final end-to-end demonstration
- [ ] Close remaining issues and publish a tagged release
```

## Completion Criteria

Milestone 7 is complete when:

- The complete system can be reproduced from the repository documentation.
- The Pi recovers after reboot and temporary connectivity loss.
- The AWS application remains available through a single EC2 failure.
- CloudWatch provides useful operational visibility.
- Public examples contain no sensitive household, device, or AWS information.
- The final demonstration shows observation, ingestion, storage, search, and history.

---

# GitHub Tracking Approach

The existing M1 approach can be used consistently for the remaining milestones:

```text
GitHub Milestone
        |
        `-- One umbrella checklist issue
```

Create one issue for each remaining milestone:

```text
M2 Checklist
M3 Checklist
M4 Checklist
M5 Checklist
M6 Checklist
M7 Checklist
```

Assign each issue to its matching GitHub milestone and add it to the GitHub Project.

A GitHub milestone's percentage is based on open and closed issues, not the number of checked boxes inside one issue. With one checklist issue per milestone, the milestone will remain at 0% until that issue closes. If I later want more granular GitHub percentage tracking, I can convert the larger checklist items into separate issues or sub-issues without changing these seven milestones.

# Milestone Ownership Summary

```text
M1  Working Raspberry Pi and passive wireless observation prototype
M2  Python scanner, local collection, persistence, and JSON batching
M3  Shared AWS infrastructure and security foundation
M4  Lambda ingestion and data-processing functions
M5  EC2, Docker services, and load balancing
M6  Search/history APIs, client integration, and Pi-to-AWS flow
M7  Hardening, observability, testing, diagrams, documentation, and release
```
