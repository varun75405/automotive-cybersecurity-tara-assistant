# [SYNTHETIC/SAMPLE DATA] — Sample Vehicle Architecture

*This is synthetic sample data for educational purposes. It does not represent any real OEM or confidential vehicle architecture.*

## 1. Introduction
This document describes the synthetic Electrical/Electronic (E/E) architecture for the "CyberCar V1", a fictional modern connected vehicle. This architecture is designed to highlight various typical automotive components, networks, and communication flows to facilitate Threat Analysis and Risk Assessment (TARA).

## 2. Central Gateway (CGW) ECU
The Central Gateway is the core routing and security component of the vehicle. It sits between all major vehicle domains and external interfaces.
- **Function:** Routes traffic between domains, acts as a firewall, and enforces network segmentation.
- **Connections:** Connected to all internal buses (CAN, Ethernet, LIN) and the OBD-II diagnostic port.
- **Security Role:** Implements Intrusion Detection System (IDS) and message filtering.

## 3. Telematics Control Unit (TCU)
The TCU manages long-range wireless communications.
- **Function:** Connects the vehicle to the cellular network (4G/5G) and cloud backend.
- **Connections:** Automotive Ethernet to CGW, Cellular Antenna.
- **Security Role:** Termination point for VPN/TLS connections to the backend, handles secure OTA payload downloading.

## 4. Infotainment System (IVI)
The In-Vehicle Infotainment system provides user interface and media playback.
- **Function:** Navigation, audio, Bluetooth connectivity, and display.
- **Connections:** Automotive Ethernet to CGW, Bluetooth/Wi-Fi antennas, USB ports.
- **Security Role:** A high-risk attack surface due to rich user interfaces and external connectivity.

## 5. Advanced Driver Assistance System (ADAS) ECU
The ADAS ECU processes sensor data to provide semi-autonomous driving features.
- **Function:** Adaptive cruise control, lane keeping, automatic emergency braking.
- **Connections:** Automotive Ethernet to CGW, High-Speed CAN to sensors and actuators.
- **Sensors connected:** Radar, LiDAR, Cameras.

## 6. Powertrain Domain Controller
The Powertrain ECU manages the engine or electric motor.
- **Function:** Torque request processing, battery management, motor control.
- **Connections:** High-Speed CAN to CGW, direct connections to throttle and motor actuators.
- **Security Role:** Critical safety system, requires high integrity and availability.

## 7. Body Control Module (BCM)
The BCM manages comfort and convenience features.
- **Function:** Lighting, windows, door locks, immobilizer.
- **Connections:** Low-Speed CAN to CGW, LIN bus to simple sensors/actuators.
- **Security Role:** Keyless entry authentication and immobilizer logic.

## 8. High-Speed CAN Network
- **Speed:** 500 kbps - 1 Mbps.
- **Connected ECUs:** Powertrain, ADAS, Steering, Braking.
- **Purpose:** Time-critical control messages requiring low latency.

## 9. Low-Speed CAN Network
- **Speed:** 125 kbps.
- **Connected ECUs:** BCM, Seat Control, HVAC.
- **Purpose:** Non-critical body functions.

## 10. Automotive Ethernet Network
- **Speed:** 100 Mbps - 1 Gbps (100BASE-T1 / 1000BASE-T1).
- **Connected ECUs:** TCU, IVI, ADAS, CGW.
- **Purpose:** High bandwidth data transfer, like video streams and large OTA updates.

## 11. LIN Bus Network
- **Speed:** 20 kbps.
- **Connected ECUs:** Sensors (rain, light), Actuators (wiper motors).
- **Purpose:** Low-cost, low-speed communication for simple devices.

## 12. External Interfaces: OBD-II and Diagnostics
- **Location:** Under the steering wheel.
- **Function:** Allows mechanics and tools to query diagnostic trouble codes (DTCs) and flash ECUs.
- **Protocol:** UDS (Unified Diagnostic Services) over CAN or DoIP (Diagnostics over IP).

## 13. External Interfaces: V2X Communication
- **Function:** Vehicle-to-Everything communication for safety warnings and traffic efficiency.
- **Protocol:** DSRC or C-V2X.
- **Connection:** Managed by a dedicated V2X module connected to the ADAS ECU.

## 14. Trust Boundaries and Zones
The architecture is divided into distinct zones separated by trust boundaries:
- **Vehicle Boundary:** Separates the physical vehicle from external networks (Cellular, V2X).
- **In-Vehicle Network Boundary:** The internal segmented networks managed by the Gateway.
- **ECU Boundary:** The boundary around individual ECUs (microcontroller, memory, peripherals).
- **External Interface Boundary:** Physical interfaces like OBD-II, USB, and EV charging ports.

## 15. Key Data Flows
- **OTA Update Flow:** Cloud -> Cellular -> TCU -> Ethernet -> CGW -> Target ECU.
- **Braking Flow:** ADAS Sensor -> ADAS ECU -> High-Speed CAN -> CGW -> High-Speed CAN -> Braking ECU.
- **Diagnostic Flow:** OBD-II Port -> CGW -> Target ECU (via UDS).
- **Infotainment Flow:** Bluetooth Device -> IVI -> Audio Amplifier.
