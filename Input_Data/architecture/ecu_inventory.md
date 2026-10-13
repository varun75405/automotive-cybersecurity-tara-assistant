# [SYNTHETIC/SAMPLE DATA] — ECU Inventory

*This is synthetic sample data for educational purposes. It does not represent any real OEM or confidential vehicle architecture.*

## 1. Central Gateway (CGW)
- **Function:** Network routing, firewall, intrusion detection, diagnostic gateway.
- **Hardware Platform:** Multi-core ARM Cortex-A + Cortex-R with dedicated Hardware Security Module (HSM).
- **Connected Interfaces:** Automotive Ethernet, HS-CAN, LS-CAN, OBD-II.
- **Software Components:** AUTOSAR Classic, Firewall module, IDS module, Routing engine.
- **Security Properties:** High Confidentiality, High Integrity, High Availability, High Authenticity.
- **Security Mechanisms:** Secure Boot, HSM-backed key storage, Network Segmentation (VLANs), Message filtering.
- **Communication Protocols:** SOME/IP, DoIP, CAN, UDS.

## 2. Telematics Control Unit (TCU)
- **Function:** Cellular connectivity, V2X, cloud backend interface, OTA orchestrator.
- **Hardware Platform:** ARM Cortex-A with Cellular Modem (5G) and Wi-Fi/BT combo chip.
- **Connected Interfaces:** Automotive Ethernet, Cellular Antenna, GPS Antenna.
- **Software Components:** Embedded Linux, OTA Client, MQTT Broker, TLS Stack.
- **Security Properties:** High Confidentiality, Medium Integrity, Medium Availability, High Authenticity.
- **Security Mechanisms:** Mutual TLS, Secure Boot, File System Encryption, Certificate Management.
- **Communication Protocols:** TCP/IP, MQTT, HTTPS, SOME/IP.

## 3. Advanced Driver Assistance System (ADAS) ECU
- **Function:** Sensor fusion, path planning, autonomous braking/steering decisions.
- **Hardware Platform:** High-performance SoC (e.g., NVIDIA or Mobileye equivalent) + Safety Microcontroller.
- **Connected Interfaces:** Automotive Ethernet, HS-CAN, Sensor links (GMSL/FPD-Link).
- **Software Components:** AUTOSAR Adaptive (on SoC), AUTOSAR Classic (on Safety MCU), AI Inference engine.
- **Security Properties:** Low Confidentiality, High Integrity, High Availability, High Authenticity.
- **Security Mechanisms:** SecOC (Secure Onboard Communication), Secure Boot, Memory Protection, Lockstep processing.
- **Communication Protocols:** SOME/IP, CAN-FD, SecOC.

## 4. In-Vehicle Infotainment (IVI)
- **Function:** User interface, media playback, navigation, smartphone integration.
- **Hardware Platform:** Multi-core ARM Cortex-A SoC.
- **Connected Interfaces:** Automotive Ethernet, Wi-Fi, Bluetooth, USB, Displays.
- **Software Components:** Android Automotive OS or Custom Linux, Media frameworks, Browser.
- **Security Properties:** Medium Confidentiality, Low Integrity, Low Availability, Medium Authenticity.
- **Security Mechanisms:** Sandboxing (SELinux), Secure Boot, Access Control Lists.
- **Communication Protocols:** SOME/IP, TCP/IP, Bluetooth profiles.

## 5. Body Control Module (BCM)
- **Function:** Keyless entry, immobilizer, lighting, window control.
- **Hardware Platform:** ARM Cortex-M with integrated HSM.
- **Connected Interfaces:** LS-CAN, LIN, RF Antenna (for key fob).
- **Software Components:** AUTOSAR Classic, Immobilizer crypto stack.
- **Security Properties:** High Confidentiality (Keys), High Integrity, Medium Availability, High Authenticity.
- **Security Mechanisms:** Challenge-Response authentication, Secure Key Storage, SecOC.
- **Communication Protocols:** CAN 2.0, LIN, UDS.

## 6. Powertrain Domain Controller
- **Function:** Engine management, transmission control, or EV inverter control.
- **Hardware Platform:** High-reliability ARM Cortex-R or PowerPC with lockstep.
- **Connected Interfaces:** HS-CAN, Direct sensor/actuator pins.
- **Software Components:** AUTOSAR Classic, Real-Time OS.
- **Security Properties:** Low Confidentiality, High Integrity, High Availability, High Authenticity.
- **Security Mechanisms:** Secure Boot, SecOC, Hardware Watchdogs.
- **Communication Protocols:** CAN-FD, UDS.
