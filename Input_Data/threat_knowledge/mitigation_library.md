# [SYNTHETIC/SAMPLE DATA] — Mitigation Library

*This is synthetic sample data for educational purposes. It does not represent any real OEM or confidential vehicle architecture.*

## 1. Access Control Mechanisms
- **Description:** Restricting access to resources (memory, APIs, network interfaces) based on privileges.
- **Implementation:** ARM TrustZone, Memory Protection Unit (MPU), OS-level sandboxing (SELinux in Android Automotive).
- **Addresses Threats:** Privilege Escalation, Unauthorized Diagnostic Access, Lateral Movement.

## 2. Authentication (Symmetric, Asymmetric, Certificate-based)
- **Description:** Verifying the identity of a communicating party or user.
- **Implementation:** Shared secret keys (Symmetric), RSA/ECC pairs (Asymmetric), X.509 Certificates (PKI).
- **Addresses Threats:** ECU Spoofing, Unauthorized Diagnostic Access, Backend Compromise.

## 3. Message Authentication (MAC, CMAC)
- **Description:** Ensuring a message has not been altered and comes from a legitimate source.
- **Implementation:** AES-CMAC appended to CAN payloads.
- **Addresses Threats:** Unauthorized Message Injection, Man-in-the-Middle, Spoofing.

## 4. Secure Communication (TLS, SecOC)
- **Description:** Protecting data in transit. TLS for IP networks, SecOC for automotive buses.
- **Implementation:** TLS 1.2/1.3 for TCU to Cloud; AUTOSAR SecOC for CAN/FlexRay/LIN.
- **Addresses Threats:** Eavesdropping, Message Modification, Replay Attacks.

## 5. Secure Diagnostics (Seed-Key, Certificate Auth)
- **Description:** Protecting diagnostic routines from unauthorized execution.
- **Implementation:** UDS Service 0x27 (Security Access) using challenge-response, or UDS Service 0x29 (Authentication) using PKI.
- **Addresses Threats:** Unauthorized tuning, key extraction, mileage tampering.

## 6. Secure Boot (Verified Boot Chain)
- **Description:** Ensuring only authentic, unmodified firmware executes on an ECU.
- **Implementation:** Hardware Root of Trust verifies the digital signature of the bootloader, which verifies the OS, which verifies the application.
- **Addresses Threats:** Malicious Firmware Update, Persistent Malware.

## 7. Secure OTA (Signed Firmware, Rollback Protection)
- **Description:** Safely delivering and installing software updates over the air.
- **Implementation:** Uptane framework, cryptographic signing of payloads, hardware version counters to prevent downgrades to vulnerable versions.
- **Addresses Threats:** Compromised OTA Path, Brick attacks, Downgrade attacks.

## 8. Network Segmentation (Gateway Filtering)
- **Description:** Isolating network domains based on trust levels and function.
- **Implementation:** Central Gateway routing tables, VLANs on Ethernet, strictly dropping unauthorized cross-domain traffic.
- **Addresses Threats:** Lateral Movement, Gateway Compromise, Broadcast Storms.

## 9. Intrusion Detection (IDS/IPS)
- **Description:** Monitoring networks and systems for malicious activity.
- **Implementation:** Network IDS on Gateway (monitoring CAN IDs, message frequencies), Host IDS on ECUs (monitoring CPU usage, memory access).
- **Addresses Threats:** Denial of Service on CAN, Unauthorized Message Injection, Unknown Exploits.

## 10. Logging and Monitoring
- **Description:** Recording security-relevant events for analysis and incident response.
- **Implementation:** Centralized logging in TCU, periodic upload to a Vehicle Security Operations Center (VSOC).
- **Addresses Threats:** Assists in identifying all active attacks and determining attack vectors post-incident.

## 11. Rate Limiting
- **Description:** Restricting the frequency of requests or messages.
- **Implementation:** Gateway drops messages if a CAN ID is transmitted faster than its expected cycle time.
- **Addresses Threats:** Denial of Service on CAN, Brute-force attacks on Seed-Key.

## 12. Hardware Security Modules (HSM)
- **Description:** Dedicated, tamper-resistant hardware for cryptographic operations and key storage.
- **Implementation:** Integrated into microcontrollers (e.g., EVITA Full/Medium/Light profiles).
- **Addresses Threats:** Key Extraction, Side-channel attacks, CPU exhaustion from crypto math.
