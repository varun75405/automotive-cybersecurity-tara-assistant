# [SYNTHETIC/SAMPLE DATA] — Automotive Threat Library

*This is synthetic sample data for educational purposes. It does not represent any real OEM or confidential vehicle architecture.*

## TH-001: Unauthorized CAN Message Injection
- **Threat Name:** Unauthorized CAN Message Injection
- **Description:** An attacker injects malicious CAN frames onto the bus to control actuators or disrupt operations.
- **Target Asset/Interface:** High-Speed CAN, Low-Speed CAN
- **Attack Vector:** Compromised ECU, OBD-II port access.
- **Potential Impact:** Unintended acceleration, braking, or steering. Loss of vehicle control.
- **Preconditions:** Attacker has physical access to OBD-II or has compromised an ECU on the CAN bus.
- **Related STRIDE Category:** Spoofing, Tampering, Elevation of Privilege.
- **Mitigation Reference:** SecOC (Secure Onboard Communication), Gateway filtering, IDS.

## TH-002: ECU Spoofing
- **Threat Name:** ECU Spoofing
- **Description:** An attacker introduces a rogue device or compromises an existing one to impersonate a legitimate ECU.
- **Target Asset/Interface:** In-Vehicle Network, Gateway.
- **Attack Vector:** Physical addition of a device to the bus.
- **Potential Impact:** Bypassing security checks, unauthorized control commands.
- **Preconditions:** Physical access to the wiring harness.
- **Related STRIDE Category:** Spoofing.
- **Mitigation Reference:** Message Authentication Codes (MAC), SecOC.

## TH-003: Replay Attacks
- **Threat Name:** Replay Attacks
- **Description:** An attacker captures legitimate network traffic (e.g., key fob unlock signal, valid CAN command) and re-transmits it later.
- **Target Asset/Interface:** RF Interface, CAN bus.
- **Attack Vector:** Wireless interception, network sniffing.
- **Potential Impact:** Unauthorized vehicle access, repeating old commands.
- **Preconditions:** Ability to sniff and transmit on the target medium.
- **Related STRIDE Category:** Spoofing, Elevation of Privilege.
- **Mitigation Reference:** Freshness values (counters/timestamps) in SecOC, Rolling Codes.

## TH-004: Denial of Service on CAN
- **Threat Name:** Denial of Service on CAN (Bus Off Attack / Flooding)
- **Description:** An attacker floods the CAN bus with high-priority messages or exploits CAN error handling to force a target ECU into a "bus off" state.
- **Target Asset/Interface:** CAN bus, All ECUs.
- **Attack Vector:** Compromised ECU, OBD-II.
- **Potential Impact:** Loss of communication between critical ECUs, loss of safety features.
- **Preconditions:** Access to the CAN bus.
- **Related STRIDE Category:** Denial of Service.
- **Mitigation Reference:** Rate limiting in Gateway, Network Segmentation.

## TH-005: Unauthorized Diagnostic Access
- **Threat Name:** Unauthorized Diagnostic Access
- **Description:** An attacker uses UDS commands to read memory, modify configurations, or control actuators without proper authorization.
- **Target Asset/Interface:** OBD-II port, UDS services.
- **Attack Vector:** Physical access with diagnostic tool.
- **Potential Impact:** Manipulation of vehicle parameters, extraction of firmware/keys.
- **Preconditions:** Physical access to OBD-II.
- **Related STRIDE Category:** Information Disclosure, Elevation of Privilege.
- **Mitigation Reference:** UDS Security Access (Seed/Key), Certificate-based authentication.

## TH-006: Compromised OTA Path
- **Threat Name:** Compromised OTA Path
- **Description:** An attacker intercepts or manipulates the Over-The-Air update process to push malicious firmware.
- **Target Asset/Interface:** Cellular interface, TCU.
- **Attack Vector:** Man-in-the-Middle (MitM) on cellular network, compromised backend.
- **Potential Impact:** Full vehicle compromise via malicious firmware installation.
- **Preconditions:** Ability to intercept cellular traffic or compromise backend servers.
- **Related STRIDE Category:** Tampering, Spoofing.
- **Mitigation Reference:** TLS with mutual authentication, Signed firmware payloads, Secure Boot.

## TH-007: Gateway Compromise
- **Threat Name:** Gateway Compromise
- **Description:** An attacker exploits a vulnerability in the Central Gateway to bypass firewall rules and route traffic freely between domains.
- **Target Asset/Interface:** Central Gateway ECU.
- **Attack Vector:** Exploitation of network services (e.g., DoIP, SOME/IP vulnerabilities).
- **Potential Impact:** Complete breakdown of network segmentation, lateral movement to safety-critical systems.
- **Preconditions:** Access to a network segment connected to the Gateway (e.g., IVI or TCU).
- **Related STRIDE Category:** Elevation of Privilege, Tampering.
- **Mitigation Reference:** Secure coding practices, memory protection, intrusion detection.

## TH-008: Sensor Data Manipulation
- **Threat Name:** Sensor Data Manipulation (Sensor Spoofing)
- **Description:** An attacker feeds fake physical signals (light, radar waves) into vehicle sensors to deceive the ADAS system.
- **Target Asset/Interface:** Camera, Radar, LiDAR sensors.
- **Attack Vector:** External physical environment.
- **Potential Impact:** Incorrect autonomous driving decisions, phantom braking, crashing.
- **Preconditions:** Proximity to the vehicle with specialized spoofing equipment.
- **Related STRIDE Category:** Spoofing.
- **Mitigation Reference:** Sensor fusion (cross-checking multiple sensor types), plausible data checks.

## TH-009: Privilege Escalation in IVI
- **Threat Name:** Privilege Escalation
- **Description:** An attacker exploits a vulnerability in the Infotainment system's OS (e.g., Android) to gain root access.
- **Target Asset/Interface:** Infotainment System (IVI).
- **Attack Vector:** Malicious app, browser exploit, Bluetooth vulnerability.
- **Potential Impact:** Access to local IVI data, starting point for lateral movement to the vehicle network.
- **Preconditions:** Ability to execute code on the IVI.
- **Related STRIDE Category:** Elevation of Privilege.
- **Mitigation Reference:** OS sandboxing (SELinux), least privilege execution, regular patch management.

## TH-010: Malicious Firmware Update
- **Threat Name:** Malicious Firmware Update
- **Description:** An attacker flashes an ECU with modified firmware containing backdoors or malicious logic.
- **Target Asset/Interface:** Any ECU, UDS Request Download.
- **Attack Vector:** Physical OBD-II access, compromised OTA process.
- **Potential Impact:** Persistent compromise of an ECU.
- **Preconditions:** Ability to initiate a diagnostic flash session.
- **Related STRIDE Category:** Tampering, Elevation of Privilege.
- **Mitigation Reference:** Secure Boot (verifying digital signatures before execution), Secure Flashing process.

## TH-011: Eavesdropping on CAN
- **Threat Name:** Eavesdropping on CAN
- **Description:** An attacker passive sniffs the CAN bus to extract sensitive information (e.g., immobilizer seed/key exchanges, driver behavior).
- **Target Asset/Interface:** CAN bus.
- **Attack Vector:** Physical tap, compromised ECU.
- **Potential Impact:** Privacy violations, gathering intelligence for subsequent attacks.
- **Preconditions:** Read access to the CAN bus.
- **Related STRIDE Category:** Information Disclosure.
- **Mitigation Reference:** Payload encryption (though rare on CAN due to overhead), SecOC (prevents modification, not eavesdropping).

## TH-012: Man-in-the-Middle on Ethernet
- **Threat Name:** Man-in-the-Middle on Ethernet
- **Description:** An attacker intercepts and modifies Ethernet traffic between two ECUs (e.g., ADAS and CGW).
- **Target Asset/Interface:** Automotive Ethernet.
- **Attack Vector:** Physical interception, ARP spoofing (if supported).
- **Potential Impact:** Modification of sensor data or routing commands.
- **Preconditions:** Physical access to Ethernet wiring.
- **Related STRIDE Category:** Tampering, Information Disclosure.
- **Mitigation Reference:** TLS, IPsec, MACsec, SOME/IP payload protection.

## TH-013: V2X Message Spoofing
- **Threat Name:** V2X Message Spoofing
- **Description:** An attacker broadcasts fake V2X messages (e.g., false hard braking warnings) to disrupt traffic or cause accidents.
- **Target Asset/Interface:** V2X Antenna / TCU.
- **Attack Vector:** Wireless transmission.
- **Potential Impact:** Traffic disruption, unsafe vehicle reactions.
- **Preconditions:** V2X transmission equipment.
- **Related STRIDE Category:** Spoofing.
- **Mitigation Reference:** V2X PKI (Public Key Infrastructure) to verify message signatures, plausibility checks.

## TH-014: Key Extraction from Hardware
- **Threat Name:** Key Extraction
- **Description:** An attacker physically extracts cryptographic keys from an ECU's memory using debug ports (JTAG) or side-channel attacks.
- **Target Asset/Interface:** ECU Hardware.
- **Attack Vector:** Physical dismantling and hardware hacking.
- **Potential Impact:** Ability to sign malicious firmware, decrypt communications, clone vehicles.
- **Preconditions:** Prolonged physical access to the ECU.
- **Related STRIDE Category:** Information Disclosure.
- **Mitigation Reference:** Hardware Security Modules (HSM), disabling debug interfaces, tamper resistance.

## TH-015: Buffer Overflow in Network Stack
- **Threat Name:** Buffer Overflow
- **Description:** An attacker sends malformed packets to an ECU's network stack (e.g., TCP/IP or CAN stack) to cause a crash or execute arbitrary code.
- **Target Asset/Interface:** Software Network Stack.
- **Attack Vector:** Network packet injection.
- **Potential Impact:** ECU crash (DoS) or Remote Code Execution (RCE).
- **Preconditions:** Ability to send messages to the target ECU.
- **Related STRIDE Category:** Tampering, Denial of Service, Elevation of Privilege.
- **Mitigation Reference:** Secure coding standards (MISRA C, CERT C), memory-safe languages, static analysis.
