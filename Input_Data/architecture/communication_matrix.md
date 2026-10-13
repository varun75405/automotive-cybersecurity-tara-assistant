# [SYNTHETIC/SAMPLE DATA] — Communication Matrix

*This is synthetic sample data for educational purposes. It does not represent any real OEM or confidential vehicle architecture.*

## 1. Overview
This document defines the communication pathways, protocols, and message types used between various ECUs in the synthetic vehicle architecture.

## 2. Network Protocols Used
- **CAN 2.0B / CAN-FD:** Used for control and status messaging in Powertrain and Chassis domains.
- **Automotive Ethernet (100BASE-T1):** Used for ADAS sensor data, OTA payloads, and Infotainment media.
- **SOME/IP:** Scalable service-Oriented MiddlewarE over IP. Used for service discovery and RPCs over Ethernet.
- **UDS (ISO 14229):** Unified Diagnostic Services, used for diagnostic routines and ECU flashing.
- **DoIP (ISO 13400):** Diagnostics over IP, enabling UDS over Ethernet.
- **LIN:** Local Interconnect Network, used for simple sensors and actuators.

## 3. Communication Path: TCU to Central Gateway (CGW)
- **Bus Assignment:** Automotive Ethernet
- **Protocols:** SOME/IP, TCP/IP, TLS
- **Message Types:**
  - OTA Firmware Payload (Bulk data transfer)
  - Backend configuration updates
  - Vehicle telemetry data (Status)
- **Routing Rules:** CGW inspects SOME/IP headers and decrypts TLS traffic before routing payloads to internal ECUs.

## 4. Communication Path: ADAS ECU to Braking ECU
- **Bus Assignment:** High-Speed CAN
- **Protocols:** CAN-FD, SecOC (Secure Onboard Communication)
- **Message Types:**
  - Automatic Emergency Braking Request (Control, High Priority)
  - Braking System Status (Status)
- **Routing Rules:** Routed through CGW. CGW verifies SecOC MAC before forwarding to the Braking domain.

## 5. Communication Path: IVI to Central Gateway (CGW)
- **Bus Assignment:** Automotive Ethernet
- **Protocols:** SOME/IP, DoIP
- **Message Types:**
  - Navigation turn-by-turn data (Status)
  - Diagnostic requests from user menu (Diagnostic)
- **Routing Rules:** Highly restricted. CGW drops all control messages originating from the IVI domain.

## 6. Communication Path: BCM to Door Modules
- **Bus Assignment:** Low-Speed CAN / LIN
- **Protocols:** CAN 2.0B, LIN
- **Message Types:**
  - Unlock/Lock Command (Control)
  - Door open/closed status (Status)
- **Routing Rules:** Direct communication on the Body CAN, no gateway routing required for internal domain traffic.

## 7. Communication Path: OBD-II Port to Target ECUs
- **Bus Assignment:** Direct to CGW, then routed to appropriate bus.
- **Protocols:** UDS, DoIP, CAN
- **Message Types:**
  - Read Data By Identifier (Diagnostic)
  - Security Access (Diagnostic - Seed/Key)
  - Request Download (Firmware update)
- **Routing Rules:** CGW requires physical presence (e.g., hood open, engine off) for certain UDS services and enforces UDS session transitions.

## 8. Details per Path and Matrix Summary
| Source ECU | Destination ECU | Bus Path | Protocol | Security Mechanism | Description |
|---|---|---|---|---|---|
| TCU | CGW | Ethernet | SOME/IP | TLS | Telemetry and OTA |
| ADAS | Braking | HS-CAN | CAN-FD | SecOC | Braking commands |
| IVI | CGW | Ethernet | SOME/IP | VLAN Separation | Infotainment data |
| BCM | Door LIN | LIN | LIN | None | Lock actuators |
| OBD-II | Any ECU | OBD -> CGW -> Bus | UDS | Seed/Key Auth | Diagnostics |
