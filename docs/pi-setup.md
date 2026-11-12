# Raspberry Pi Wireless Scanner Setup

This document covers the Raspberry Pi portion of my wireless device observation project, including the hardware, Linux wireless interfaces, monitor mode configuration, channel hopping, and the tools I am currently using to collect Wi-Fi metadata.

The goal of this part of the project is to use a Raspberry Pi as an edge sensor inside my home that can observe nearby Wi-Fi activity without requiring devices to be connected to my network.

At this stage, I am collecting metadata such as:

- Observed MAC address
- Timestamp
- Signal strength (RSSI)
- Frequency
- Wi-Fi channel
- Wi-Fi band

The Raspberry Pi will eventually process these observations locally and send summarized data to AWS for storage, processing, and search.

---

# Hardware

## Raspberry Pi 4B

I am using a Raspberry Pi 4B as the physical edge device for the project.

Its role is to sit between the wireless environment and the AWS infrastructure.

The basic flow is:

```text
Nearby Wi-Fi activity
        ↓
Raspberry Pi
        ↓
Wireless observations
        ↓
Local processing
        ↓
AWS
```

The Raspberry Pi does not need to perform all of the project's processing locally. Its primary responsibility is to collect and prepare observations before sending useful data to the cloud.

The Pi 4B provides more than enough processing power for the tools I plan to run locally, including:

```text
Linux
TShark
Python
SQLite
Network services
AWS API communication
```

---

# Operating System

The Raspberry Pi is running Raspberry Pi OS.

Before configuring the Wi-Fi hardware, I updated the operating system:

```bash
sudo apt update
sudo apt full-upgrade -y
sudo reboot
```

I wanted the kernel, drivers, and wireless packages to be current before configuring monitor mode.

This is especially important because the external Wi-Fi adapter relies on the Linux wireless stack and its associated drivers.

---

# Packages Installed

I installed the following packages:

```bash
sudo apt install -y \
  iw \
  tshark \
  tcpdump \
  python3 \
  python3-pip \
  python3-venv \
  sqlite3
```

Each package has a specific role in the project.

## `iw`

`iw` is the Linux command-line tool I use to inspect and configure Wi-Fi hardware.

I use it for tasks such as:

```text
Viewing wireless radios
Viewing wireless interfaces
Checking monitor mode support
Creating monitor interfaces
Changing Wi-Fi channels
Checking the current radio configuration
```

Some of the main commands I use are:

```bash
iw dev
```

```bash
iw list
```

```bash
iw dev mon24 info
```

---

## `tcpdump`

I used `tcpdump` primarily as an initial test to confirm that the adapter was actually receiving wireless traffic.

For example:

```bash
sudo tcpdump -i mon24 -c 20
```

A successful test returned:

```text
20 packets captured
20 packets received by filter
0 packets dropped by kernel
```

This was an important early milestone because it confirmed that the adapter was successfully capturing IEEE 802.11 traffic in monitor mode.

---

## `tshark`

TShark is the command-line version of Wireshark.

While `tcpdump` was useful for confirming that traffic was being captured, TShark allows me to extract only the fields that are useful for this project.

At the moment, I am collecting:

```text
Timestamp
Source MAC address
RSSI
Wireless frequency
```

Later, the Python collector will consume this output automatically rather than displaying it directly in the terminal.

---

## `python3`

Python will handle the main local processing layer.

Instead of sending every individual wireless frame directly to AWS, Python will summarize repeated observations.

For example:

```text
Same MAC observed hundreds of times
        ↓
Track one logical observation record
        ↓
Maintain:
First Seen
Last Seen
Observation Count
Average RSSI
Channel
Band
```

This should significantly reduce unnecessary data while keeping the information that is useful for the project.

---

## `sqlite3`

SQLite will provide local storage on the Raspberry Pi.

This gives the Pi somewhere to store observations before they are uploaded to AWS.

It also provides some resilience if:

```text
Internet connectivity is unavailable
AWS cannot be reached temporarily
The Pi needs to buffer observations locally
```

---

# Wi-Fi Adapter

For wireless observation, I am using an:

```text
Alfa AWUS036ACM
```

I selected this adapter because it supports the features required for the project:

```text
Linux support
Monitor mode
2.4 GHz Wi-Fi
5 GHz Wi-Fi
External antennas
```

The AWUS036ACM has two antennas, but both antennas belong to the same Wi-Fi radio.

They do not function as two independent scanners.

Conceptually:

```text
Antenna 1
Antenna 2
    ↓
One AWUS036ACM radio
```

This means the adapter can only monitor one Wi-Fi channel at a time.

---

# How Linux Represents the Wi-Fi Hardware

One of the more important parts of the setup was understanding how Linux represents the physical radios and their interfaces.

My current layout is roughly:

```text
Raspberry Pi

phy0
└── wlan0
     └── Raspberry Pi built-in Wi-Fi

phy3
├── wlan1
└── mon24
     └── Alfa AWUS036ACM
```

The `phy`, `wlan`, and `mon24` names represent different layers of the same wireless hardware.

---

# Physical Radios: `phy0` and `phy3`

A `phy` represents a physical wireless radio.

Linux assigns numbers to these radios:

```text
phy0
phy1
phy2
phy3
...
```

In my current configuration:

```text
phy0 = Raspberry Pi built-in Wi-Fi

phy3 = Alfa AWUS036ACM
```

The `phy` is the actual radio hardware responsible for transmitting and receiving Wi-Fi signals.

---

# `wlan0`

`wlan0` belongs to the Raspberry Pi's built-in wireless radio.

I am keeping this interface dedicated to normal network connectivity.

Its role is:

```text
Raspberry Pi
    ↓
wlan0
    ↓
Home Wi-Fi
    ↓
Internet
    ↓
Future AWS communication
```

Keeping this separate from the scanning adapter allows the Pi to remain connected to the Internet while the Alfa adapter is used exclusively for wireless observation.

---

# `wlan1`

When I connected the AWUS036ACM, Linux automatically created:

```text
wlan1
```

By default, `wlan1` behaves like a normal Wi-Fi client interface.

Its typical purpose would be:

```text
Find wireless network
        ↓
Connect to SSID
        ↓
Receive IP address
        ↓
Use the network normally
```

That is not the role I want the Alfa to perform.

For this project, the Alfa is dedicated to wireless observation.

---

# Removing `wlan1` From NetworkManager

NetworkManager normally controls wireless interfaces automatically.

That is useful for normal Wi-Fi connections, but it can interfere with a radio that I want to control directly.

I removed `wlan1` from NetworkManager control with:

```bash
sudo nmcli device set wlan1 managed no
```

I verified the result using:

```bash
nmcli device
```

The important output was:

```text
wlan0   wifi   connected
wlan1   wifi   unmanaged
```

This gives each adapter a clear role:

```text
wlan0
    ↓
Normal network connection

wlan1
    ↓
Reserved for scanner configuration
```

---

# Monitor Mode

A normal Wi-Fi interface typically operates in managed mode.

Managed mode works approximately like this:

```text
Find access point
        ↓
Connect to access point
        ↓
Join network
        ↓
Exchange normal network traffic
```

For this project, I need the adapter to operate in:

```text
Monitor Mode
```

Monitor mode allows the Wi-Fi radio to listen for IEEE 802.11 frames on the channel it is currently tuned to.

The adapter does not need to join the network that generated the traffic.

This is what allows the Raspberry Pi to observe nearby Wi-Fi activity rather than only devices connected to my own network.

---

# `mon24`

`mon24` is the monitor-mode interface I created on the Alfa adapter.

I created it with:

```bash
sudo iw phy phy3 interface add mon24 type monitor
```

Breaking that command down:

```text
iw
↓
Linux wireless configuration tool

phy3
↓
The physical Alfa AWUS036ACM radio

interface add
↓
Create another interface on that radio

mon24
↓
The name I assigned to the interface

type monitor
↓
Configure it for monitor mode
```

The resulting relationship is:

```text
AWUS036ACM
    ↓
phy3
    ↓
mon24
    ↓
Monitor Mode
```

I then brought the interface online using:

```bash
sudo ip link set mon24 up
```

---

# Why the Interface Is Named `mon24`

I originally planned to use this interface only for 2.4 GHz scanning.

That is why I called it:

```text
mon24
```

The name originally meant:

```text
mon = monitor
24  = 2.4 GHz
```

The design later changed so that the same AWUS036ACM scans both 2.4 GHz and 5 GHz.

The name is therefore no longer completely descriptive, but it does not affect how Linux treats the interface.

It could eventually be renamed to something more general, such as:

```text
mon0
scanner0
wifi-monitor
```

The important setting is:

```text
type monitor
```

---

# `wlan1` and `mon24` Share the Same Physical Radio

`wlan1` and `mon24` are not separate Wi-Fi adapters.

Both belong to:

```text
phy3
```

Conceptually:

```text
          phy3
         /    \
     wlan1   mon24
```

Because they share the same physical radio, they cannot independently use different channels.

I encountered this during setup when trying to change the monitor interface channel:

```text
Device or resource busy (-16)
```

The original `wlan1` interface was still interfering with control of the radio.

I resolved this by taking `wlan1` down:

```bash
sudo ip link set wlan1 down
```

After that, the monitor interface could control the radio channel normally.

---

# Verifying Monitor Mode

I used:

```bash
iw dev
```

to confirm that the interface was created correctly.

The important result was:

```text
Interface mon24
    type monitor
```

I can also inspect the current channel using:

```bash
iw dev mon24 info
```

For example:

```text
Interface mon24
    type monitor
    channel 1 (2412 MHz)
```

This confirms:

```text
Interface = mon24
Mode      = monitor
Channel   = 1
Frequency = 2412 MHz
```

---

# Checking Adapter Capabilities

I used:

```bash
iw list
```

to inspect the supported features of the Wi-Fi hardware.

Because the output is very large, I used:

```bash
iw list | less
```

Useful controls inside `less` include:

```text
Up / Down     Scroll
Space         Next page
b             Previous page
/             Search
q             Quit
```

The main section I was looking for was:

```text
Supported interface modes:
```

The AWUS036ACM showed support for:

```text
* managed
* AP
* monitor
```

The important line was:

```text
* monitor
```

This confirmed that the adapter and Linux driver support the mode required for the project.

---

# Wireless Regulatory Domain

Available Wi-Fi channels depend on the regulatory rules for the country where the radio is being used.

I configured the WLAN country using:

```bash
sudo raspi-config
```

Then selected:

```text
Localisation Options
        ↓
WLAN Country
        ↓
United States
```

I verified the regulatory configuration with:

```bash
iw reg get
```

The project only uses channels reported as available by Linux and the adapter.

---

# First Fixed-Channel Test

Before setting up automatic channel hopping, I tested the adapter on a single channel.

For example:

```bash
sudo iw dev mon24 set channel 1
```

Then:

```bash
iw dev mon24 info
```

returned:

```text
channel 1 (2412 MHz)
```

This confirmed that I could manually control the Alfa's radio channel.

---

# First Successful Packet Capture

My first monitor-mode capture test was:

```bash
sudo tcpdump -i mon24 -c 20
```

I started seeing wireless frames such as:

```text
Beacon
Probe Request
Probe Response
Acknowledgment
```

The capture completed with:

```text
20 packets captured
20 packets received by filter
0 packets dropped by kernel
```

This confirmed that the Alfa was successfully receiving nearby IEEE 802.11 traffic.

---

# Extracting Useful Wi-Fi Metadata

The raw packet output from `tcpdump` is useful for troubleshooting, but it contains much more information than I need for this project.

I switched to TShark so I could extract specific fields:

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

This produces output similar to:

```text
Nov 9, 2026 21:29:37   dc:8d:8a:xx:xx:xx   -80   2412
Nov 9, 2026 21:29:38   3c:28:6d:xx:xx:xx   -72   2437
Nov 9, 2026 21:29:39   a6:e2:d5:xx:xx:xx   -65   2462
```

The fields are:

```text
Timestamp
Source MAC
RSSI
Frequency
```

---

# TShark Command Breakdown

## `-i mon24`

This tells TShark to capture traffic from the monitor-mode interface.

```text
AWUS036ACM
    ↓
mon24
    ↓
TShark
```

---

## `-Y "wlan.sa"`

This filters the displayed frames to those containing a Wi-Fi source address.

For the current project, this is useful because I want to record:

```text
wlan.sa
```

or:

```text
Wireless LAN Source Address
```

---

## `-e frame.time`

This records when the frame was observed.

---

## `-e wlan.sa`

This extracts the source MAC address.

Example:

```text
dc:8d:8a:5c:b8:d4
```

---

## `-e radiotap.dbm_antsignal`

This extracts signal-strength information from the Radiotap header.

Example:

```text
-65
```

The number is represented approximately in dBm.

As a general reference:

```text
-35 dBm   Very strong
-50 dBm   Strong
-65 dBm   Moderate
-80 dBm   Weak
-90 dBm   Very weak
```

I am not using RSSI as an exact measurement of physical distance.

Signal strength can vary due to:

```text
Walls
Interference
Transmit power
Antenna orientation
Building materials
Signal reflections
```

---

## `-e radiotap.channel.freq`

This gives me the radio frequency where the frame was captured.

For example:

```text
2412
```

means:

```text
2412 MHz
```

which corresponds to Wi-Fi Channel 1.

---

# Frequency and Channel Mapping

For the current setup, some important 2.4 GHz frequencies are:

```text
2412 MHz = Channel 1
2437 MHz = Channel 6
2462 MHz = Channel 11
```

For 5 GHz:

```text
5180 MHz = Channel 36
5200 MHz = Channel 40
5220 MHz = Channel 44
5240 MHz = Channel 48
```

The upper channels currently included are:

```text
5745 MHz = Channel 149
5765 MHz = Channel 153
5785 MHz = Channel 157
5805 MHz = Channel 161
```

---

# Why Channel Hopping Is Required

The AWUS036ACM contains one physical Wi-Fi radio.

That means it can only listen to one channel at a time.

For example:

```text
AWUS036ACM
    ↓
Channel 6
```

While the adapter is on Channel 6, it is not simultaneously listening to Channel 36.

To improve coverage, I continuously move the adapter between a selected group of channels.

---

# Current Channel List

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

---

# Channel Hopper

The current hopping command is:

```bash
sudo bash -c 'while true; do
  for ch in 1 6 11 36 40 44 48 149 153 157 161; do
    iw dev mon24 set channel "$ch"
    sleep 1
  done
done' &
```

The loop works like this:

```text
Channel 1
   ↓
Wait 1 second
   ↓
Channel 6
   ↓
Wait 1 second
   ↓
Channel 11
   ↓
Wait 1 second
   ↓
Channel 36
   ↓
...
   ↓
Channel 161
   ↓
Return to Channel 1
```

---

# Why I Use a One-Second Dwell Time

At the moment, the adapter remains on each channel for approximately one second.

This gives it enough time to observe traffic before switching to the next channel.

The current setting is intentionally simple:

```text
1 second per channel
```

I may adjust the dwell time later after I have more data about how well the scanner performs.

---

# Running the Hopper in the Background

The:

```text
&
```

at the end of the hopping command runs the loop as a background process.

This allows the scanner to continue changing channels while I use the terminal for other tasks.

I can view the active background jobs with:

```bash
jobs -l
```

For example:

```text
[1] 1966 Running
```

If the hopper is job 1, I can stop it with:

```bash
kill %1
```

---

# DFS Channels

Some 5 GHz channels use Dynamic Frequency Selection, or DFS.

These channels have additional requirements because the frequencies may also be used by radar systems.

For the first version of the project, I am intentionally avoiding DFS channels.

This keeps the initial setup:

```text
Simpler
More predictable
Easier to troubleshoot
```

I may evaluate DFS channels later if broader coverage becomes necessary.

---

# Current Raspberry Pi Architecture

The current Raspberry Pi setup looks like this:

```text
                    Raspberry Pi 4B
                           │
             ┌─────────────┴─────────────┐
             │                           │
            phy0                        phy3
             │                           │
           wlan0                 Alfa AWUS036ACM
             │                           │
             │                    ┌──────┴──────┐
             │                    │             │
             │                  wlan1         mon24
             │                    │             │
             │               unmanaged       monitor
             │                 / down          mode
             │                                  │
             │                           Channel Hopper
             │                                  │
             │                    ┌─────────────┴─────────────┐
             │                    │                           │
             │                 2.4 GHz                     5 GHz
             │                 1/6/11             36/40/44/48
             │                                    149/153/157/161
             │                                               │
             │                                            TShark
             │                                               │
             │                         ┌─────────────────────┼─────────────┐
             │                         │                     │             │
             │                        MAC                   RSSI       Frequency
             │
             │
       Normal Wi-Fi
             │
          Internet
             │
         Future AWS
```

---

# MAC Address Randomization

A major consideration for this project is MAC address randomization.

Modern devices may use:

```text
Private MAC addresses
Randomized MAC addresses
Locally administered addresses
```

Because of this, I cannot assume:

```text
One MAC address = one physical device permanently
```

Instead, I am treating a MAC address as an:

```text
Observed wireless identifier
```

A single device may appear under multiple identifiers over time.

---

# Locally Administered MAC Addresses

One field I plan to calculate in Python is whether an observed MAC is locally administered.

A simple check looks like this:

```python
def locally_administered(mac):
    first_octet = int(mac.split(":")[0], 16)
    return bool(first_octet & 0x02)
```

A locally administered address may indicate:

```text
A randomized address
A private address
A virtual interface
A software-assigned address
```

However:

```text
Locally administered
        ≠
Definitely randomized
```

I plan to store this as supporting metadata rather than using it as proof of device identity.

---

# Data I Plan to Collect

The project is focused on wireless metadata.

The main fields I currently care about are:

```text
Timestamp
MAC Address
RSSI
Frequency
Channel
Wi-Fi Band
Observation Count
First Seen
Last Seen
```

I do not need packet payload contents for the intended project.

The purpose is device observation and presence analysis, not reconstruction of wireless communications.

---

# Current Limitations

## One Wi-Fi Radio

I currently have one AWUS036ACM.

This means the scanner cannot monitor every Wi-Fi channel simultaneously.

If the adapter is listening to:

```text
Channel 44
```

while a device transmits only on:

```text
Channel 6
```

that specific transmission may be missed.

Continuous hopping improves coverage over time, but it does not provide simultaneous monitoring of every channel.

---

## Devices Must Transmit

This is a passive scanner.

If a wireless device does not transmit anything while the scanner is listening to the relevant channel, there is nothing for the Pi to observe.

---

## MAC Addresses May Change

MAC randomization means I cannot rely on every observed address as a permanent device identifier.

Device correlation will be handled separately from raw MAC collection.

---

## RSSI Is Approximate

RSSI is useful for comparing signal strength, but it is not a reliable measurement of exact physical distance.

---

# Reboot Persistence

The current setup is still partly manual.

At the moment, I manually create the monitor interface and manually start the channel-hopping process.

For example:

```bash
sudo iw phy phy3 interface add mon24 type monitor
```

and:

```bash
sudo bash -c 'while true; do
  ...
done' &
```

These runtime configurations are not guaranteed to remain after a reboot.

A later milestone will automate startup using:

```text
systemd
```

The goal is for the Pi to eventually handle the entire startup process automatically:

```text
Boot
  ↓
Detect Alfa
  ↓
Configure scanner interface
  ↓
Create monitor interface
  ↓
Start channel hopping
  ↓
Start Python collector
  ↓
Continue running automatically
```

---

# Current Progress

The Raspberry Pi scanning portion has reached the following point:

```text
[✓] Raspberry Pi configured
[✓] Raspberry Pi OS updated
[✓] Required wireless tools installed
[✓] AWUS036ACM detected
[✓] Monitor mode support confirmed
[✓] 2.4 GHz support confirmed
[✓] 5 GHz support confirmed
[✓] NetworkManager removed from scanner control
[✓] Monitor interface created
[✓] Fixed-channel capture tested
[✓] IEEE 802.11 traffic captured
[✓] Source MAC addresses extracted
[✓] RSSI extracted
[✓] Frequency extracted
[✓] Manual channel switching verified
[✓] 2.4 GHz scanning verified
[✓] 5 GHz scanning verified
[✓] Automatic dual-band channel hopping working
```

At this point, the basic wireless observation hardware and Linux configuration are functioning.

---

# Next Milestone: Python Collector

The current process looks like:

```text
AWUS036ACM
    ↓
Monitor Mode
    ↓
Channel Hopper
    ↓
TShark
    ↓
Raw observations
```

The next step is to add a Python collector:

```text
AWUS036ACM
    ↓
Monitor Mode
    ↓
Channel Hopper
    ↓
TShark
    ↓
Python Collector
    ↓
Structured device observations
```

Instead of storing repeated output such as:

```text
da:6c:63:ef:24:30
da:6c:63:ef:24:30
da:6c:63:ef:24:30
da:6c:63:ef:24:30
```

I want the collector to maintain a summarized record:

```text
MAC                  Band   RSSI   Seen   First Seen   Last Seen
----------------------------------------------------------------
da:6c:63:ef:24:30    2.4    -71    428    21:38:12     21:44:51
3c:28:6d:af:88:67    5      -62    117    21:39:03     21:44:49
a6:e2:d5:f2:06:4a    2.4    -54     83    21:40:18     21:44:42
```

Planned fields include:

```text
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
Possible Randomized Address Flag
Scanner ID
```

---

# Planned Raspberry Pi Pipeline

The local architecture will eventually become:

```text
                 AWUS036ACM
                      │
                      ▼
                 Monitor Mode
                      │
                      ▼
                Channel Hopper
                      │
                      ▼
                    TShark
                      │
                      ▼
               Python Collector
                      │
          ┌───────────┼───────────┐
          │           │           │
          ▼           ▼           ▼
      Deduplicate   Aggregate   Classify
          │           │           │
          └───────────┼───────────┘
                      │
                      ▼
                    SQLite
                      │
                      ▼
                 AWS Uploader
                      │
                      ▼
                     AWS
```

The Raspberry Pi serves as the physical observation and edge-processing layer.

AWS will eventually handle more of the:

```text
Storage
Processing
Search
APIs
Historical data
Notifications
```

This gives the project both a physical networking component and a cloud architecture component.
