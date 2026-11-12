# Repository Structure

## Purpose

This document defines how I plan to organize the repository as the project grows.

The goal is to keep the Raspberry Pi code, AWS application code, infrastructure, tests, diagrams, and documentation separate enough to understand without creating empty folders for work that has not started yet.

## Current Repository Structure

At the current milestone, the repository only needs the documentation and files that actually exist.

```text
.
|-- README.md
|-- PROJECT_README.md
`-- docs/
    |-- README.md
    |-- pi-setup.md
    |-- architecture.md
    |-- project-structure.md
    `-- roadmap.md
```

### README.md

The repository landing page. It explains what the project is, what currently works, what is planned, and where to find the detailed documentation.

### PROJECT_README.md

The full project narrative. It explains the motivation, current implementation, planned local pipeline, AWS application design, limitations, and success criteria.

### docs/README.md

The documentation index. It links the detailed guides and identifies documents that will be added later.

### docs/pi-setup.md

The detailed Raspberry Pi setup guide. This is the hands-on record of how the Pi, AWUS036ACM, Linux interfaces, monitor mode, TShark, and channel hopping were configured.

### docs/architecture.md

The technical architecture document. It separates the current scanner from the planned Python and AWS components and defines the responsibility of each service.

### docs/project-structure.md

This document. It explains how the repository is organized now and how it will expand.

### docs/roadmap.md

The implementation sequence and acceptance criteria for each milestone.

## Planned Repository Structure

I will add folders when the matching implementation begins. The planned structure is:

```text
.
|-- README.md
|-- PROJECT_README.md
|
|-- docs/
|   |-- README.md
|   |-- pi-setup.md
|   |-- architecture.md
|   |-- project-structure.md
|   |-- roadmap.md
|   |-- aws-setup.md
|   |-- api.md
|   `-- testing.md
|
|-- pi/
|   |-- scanner/
|   |   |-- monitor-setup.sh
|   |   `-- channel-hopper.sh
|   |
|   |-- collector/
|   |   |-- collector.py
|   |   |-- database.py
|   |   |-- models.py
|   |   `-- requirements.txt
|   |
|   |-- uploader/
|   |   |-- uploader.py
|   |   `-- client.py
|   |
|   |-- config/
|   |   `-- example.env
|   |
|   `-- systemd/
|       |-- monitor-setup.service
|       |-- channel-hopper.service
|       |-- collector.service
|       `-- uploader.service
|
|-- aws/
|   |-- containers/
|   |   |-- ingestion-api/
|   |   |   |-- app/
|   |   |   |-- tests/
|   |   |   |-- requirements.txt
|   |   |   `-- Dockerfile
|   |   |
|   |   `-- search-api/
|   |       |-- app/
|   |       |-- tests/
|   |       |-- requirements.txt
|   |       `-- Dockerfile
|   |
|   |-- lambdas/
|   |   |-- device-ingest/
|   |   |-- metadata-update/
|   |   |-- device-search/
|   |   `-- device-history/
|   |
|   `-- infrastructure/
|       |-- networking/
|       |-- alb/
|       |-- ec2/
|       |-- iam/
|       |-- s3/
|       |-- dynamodb/
|       `-- cloudwatch/
|
|-- tests/
|   |-- pi/
|   |-- api/
|   |-- integration/
|   `-- lambdas/
|
`-- diagrams/
    |-- current-pi-scanner.svg
    |-- local-collector-pipeline.svg
    `-- planned-aws-architecture.svg
```

## Directory Responsibilities

# pi/

Contains everything that runs directly on the Raspberry Pi.

## pi/scanner/

Shell scripts that configure the wireless radio.

### monitor-setup.sh

Expected responsibilities:

- Identify the Alfa radio reliably
- Remove the managed interface from normal control
- Create the monitor interface if it does not exist
- Bring the monitor interface up
- Verify that monitor mode is active

### channel-hopper.sh

Expected responsibilities:

- Load the configured channel list
- Retune the monitor interface
- Apply the dwell time
- Log channel-change failures
- Stop cleanly when managed by systemd

## pi/collector/

The Python observation collector.

### collector.py

Expected responsibilities:

- Start or connect to the TShark stream
- Parse observations
- Normalize values
- Aggregate repeated observations
- Pass structured records to the database layer

### database.py

Expected responsibilities:

- Create and migrate the SQLite schema
- Insert or update observation records
- Create upload batches
- Track pending and acknowledged uploads

### models.py

Shared data models for observations, summaries, and upload batches.

### requirements.txt

Python dependencies for the collector.

## pi/uploader/

The AWS upload client.

### uploader.py

Expected responsibilities:

- Read pending batches
- Submit batches to the ingestion endpoint
- Retry temporary failures
- Mark acknowledged batches as uploaded

### client.py

HTTP client logic, authentication headers, timeouts, and response parsing.

## pi/config/

Contains example configuration only.

### example.env

Documents required configuration variables without including real secrets.

Possible fields:

```text
SCANNER_ID
MONITOR_INTERFACE
CHANNEL_LIST
CHANNEL_DWELL_SECONDS
DATABASE_PATH
INGESTION_URL
API_TOKEN
UPLOAD_INTERVAL_SECONDS
```

The real `.env` file should not be committed.

## pi/systemd/

Service definitions that make the Pi restart the scanner and application automatically.

# aws/

Contains the AWS application code and infrastructure definitions.

## aws/containers/ingestion-api/

The containerized ingestion service. The same image runs on both EC2 instances.

## aws/containers/search-api/

The containerized search service. The same image runs on both EC2 instances.

## aws/lambdas/device-ingest/

Writes raw or normalized observation batches to S3.

## aws/lambdas/metadata-update/

Updates current searchable state in DynamoDB.

## aws/lambdas/device-search/

Queries current device records from DynamoDB.

## aws/lambdas/device-history/

Queries history indexes and retrieves detailed historical data when needed.

## aws/infrastructure/

Infrastructure configuration grouped by AWS responsibility.

```text
networking/   VPC, subnets, routing, and security groups
alb/          Load balancer, listeners, rules, and target groups
ec2/          Instance definitions and application hosts
iam/          Roles and policies
s3/           Historical storage configuration
dynamodb/     Searchable table definitions
cloudwatch/   Logs, metrics, dashboards, and alarms
```

The exact infrastructure-as-code tool has not been selected in this document. The folder layout can support Terraform, CloudFormation, or another approach later.

# tests/

Cross-component tests that do not belong inside one application package.

## tests/pi/

Tests for frequency mapping, MAC classification, parsing, and local database behavior.

## tests/api/

Tests for ingestion and search endpoints.

## tests/integration/

End-to-end tests across multiple components.

## tests/lambdas/

Shared Lambda tests or fixtures that do not fit inside one Lambda package.

# diagrams/

Source-controlled architecture diagrams.

The diagram names should describe whether they represent the current or planned state.

```text
current-pi-scanner.svg
local-collector-pipeline.svg
planned-aws-architecture.svg
```

This avoids presenting future components as though they already exist.

## Naming Conventions

I plan to use:

- Lowercase folder names
- Hyphens in service and Lambda names
- Snake case in Python modules and variables
- Clear filenames that describe one responsibility

Examples:

```text
ingestion-api
metadata-update
channel-hopper.sh
database.py
```

## Repository Hygiene

The repository should not contain:

- Real API tokens or credentials
- A real `.env` file
- Local SQLite databases
- Packet captures
- Runtime logs
- Python virtual environments
- Python cache directories
- Large generated artifacts

Recommended `.gitignore` entries include:

```gitignore
.env
*.db
*.sqlite
*.sqlite3
*.pcap
*.pcapng
*.log
.venv/
venv/
__pycache__/
*.py[cod]
.pytest_cache/
.DS_Store
```

## When to Add Planned Folders

I do not want the repository to look complete before the implementation exists.

I will add each major folder when its work begins:

```text
pi/collector/       when the Python collector starts
pi/systemd/         when startup automation starts
aws/containers/     when the APIs are implemented
aws/lambdas/        when the functions are implemented
aws/infrastructure/ when the AWS environment is defined
```

This keeps the repository honest and makes the commit history easier to follow.
