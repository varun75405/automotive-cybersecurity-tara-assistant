# [SYNTHETIC/SAMPLE DATA] — Attack Surface Knowledge Base

*This is synthetic sample data for educational purposes. It does not represent any real OEM or confidential vehicle architecture.*

## 1. CAN Bus Interfaces
- **Exposure Level:** High (Internal), Low (External unless physically accessed).
- **Access Requirements:** Requires physical access to OBD-II port or wiring harness, or remote access via a compromised ECU connected to the bus.
- **Known Concern Categories:** Lack of inherent authentication, broadcast nature allows sniffing, lack of inherent encryption, susceptible to DoS (Bus Off).
- **Defensive Considerations:** Implement SecOC (Secure Onboard Communication), physical port locks, intrusion detection systems (IDS) on the Gateway, network segmentation.

## 2. Automotive Ethernet
- **Exposure Level:** Medium.
- **Access Requirements:** Physical access to wiring or logical access via compromised connected node (TCU, IVI).
- **Known Concern Categories:** Complex protocol stacks (TCP/IP, SOME/IP) increase software attack surface, high bandwidth allows rapid data exfiltration or flooding.
- **Defensive Considerations:** Implement VLANs, TLS/IPsec for data in transit, MACsec for Layer 2 security, strict firewall rules on the Gateway, unused port disabling.

## 3. OBD-II / Diagnostic Interface
- **Exposure Level:** High.
- **Access Requirements:** Physical presence inside the vehicle cabin.
- **Known Concern Categories:** Standardized location, provides direct access to Gateway, often used for ECU flashing and reading sensitive data, legacy UDS services may lack strong authentication.
- **Defensive Considerations:** Implement strong UDS Security Access (Seed-Key or Certificate-based), require physical state checks (e.g., engine off, doors unlocked) for sensitive routines, firewalling diagnostic requests at the Gateway.

## 4. OTA Update Interface
- **Exposure Level:** High.
- **Access Requirements:** Remote over cellular network.
- **Known Concern Categories:** MitM attacks on cellular link, DNS spoofing, compromised backend servers, rollback attacks, incomplete updates leading to bricking.
- **Defensive Considerations:** Mutual TLS authentication, payload encryption, digital signatures on firmware (verified by Secure Boot), rollback protection (version checking), A/B partitioning for fail-safe updates.

## 5. Telematics / Backend Connection (Cellular)
- **Exposure Level:** High.
- **Access Requirements:** Remote over public cellular networks (4G/5G).
- **Known Concern Categories:** Exposed IP addresses, vulnerability to network scanning, SMS-based attacks, API vulnerabilities in backend cloud services.
- **Defensive Considerations:** Private APNs, mutual authentication (mTLS), strict firewalling, disabling unused services/ports, intrusion prevention systems.

## 6. V2X Interface (DSRC / C-V2X)
- **Exposure Level:** High.
- **Access Requirements:** Proximity (within hundreds of meters) using standard V2X radios.
- **Known Concern Categories:** Message spoofing (fake traffic jams, fake braking), location tracking (privacy), DoS on V2X channels.
- **Defensive Considerations:** V2X PKI for message signing and verification, pseudonym certificates to protect privacy, message plausibility checks (cross-referencing with local sensors).

## 7. Bluetooth / Wi-Fi
- **Exposure Level:** Medium.
- **Access Requirements:** Proximity (within 10-100 meters).
- **Known Concern Categories:** Protocol stack vulnerabilities (e.g., BlueBorne), unauthorized pairing, rogue access points, extracting contact/call data.
- **Defensive Considerations:** Keep wireless stacks patched, disable visibility when paired, require strong pairing methods (numeric comparison), isolate wireless modules from critical vehicle networks.

## 8. USB / SD Card
- **Exposure Level:** Medium.
- **Access Requirements:** Physical access to the cabin (usually IVI system).
- **Known Concern Categories:** Malicious media (BadUSB), auto-run exploits, filesystem parsing vulnerabilities (buffer overflows in media players), firmware updates via USB.
- **Defensive Considerations:** Disable auto-execution of scripts, robust media parsing libraries, restrict firmware updates via USB (require digital signatures), restrict mount permissions.
