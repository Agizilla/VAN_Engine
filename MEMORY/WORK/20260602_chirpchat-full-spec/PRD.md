---
task: Create full specification for ChirpChat
slug: 20260602_chirpchat-full-spec
effort: extended
phase: complete
progress: 32/32
mode: interactive
started: 2026-06-02T00:28:00Z
updated: 2026-06-02T00:37:00Z
---

## Context

ChirpChat is a zero-internet WhatsApp competitor — a decentralized mesh messaging application that operates entirely offline using ultrasonic audio chirps (19-24kHz) for device pairing and WebRTC over local Wi-Fi hotspots for message relay. It is the next priority project in the VAN_Engine ecosystem.

**Explicitly requested:** Full specification document for ChirpChat covering ultrasonic pairing, Wi-Fi Direct mesh, distributed file sharing with erasure coding.

**Explicitly not requested:** Implementation code, working prototype, cloud backend.

**Implied requirements:** Must be a separate project (ISO_004), must operate fully offline (no internet dependency), must include security model, must provide an implementation roadmap.

**Key constraints:** Separated from VAN_Engine per ISO_004. All Python files must include UTF-8 wrapper for Windows. Bridges disabled by default (ISO_019). No external API dependencies.

### Risks
- Ultrasonic audio is range-limited (~10m) and affected by ambient noise — pairing may fail in noisy environments
- Wi-Fi Direct peer-to-peer is Android-focused; iOS and desktop support varies widely
- WebRTC without signaling server requires mDNS or Bluetooth LE for initial handshake — chicken-and-egg problem
- Erasure coding adds latency; real-time file sharing UX may suffer with large files

## Criteria

- [x] ISC-1: Spec contains executive summary with ChirpChat value proposition
- [x] ISC-2: Spec defines system scope: what ChirpChat is and is not
- [x] ISC-3: Architecture overview describes three-layer model (audio, mesh, application)
- [x] ISC-4: Architecture diagram specified (component or data flow)
- [x] ISC-5: Ultrasonic pairing protocol specifies frequency band (19-24kHz)
- [x] ISC-6: Ultrasonic pairing protocol defines chirp frame structure
- [x] ISC-7: Ultrasonic pairing protocol defines handshake (discover-chirp, challenge-response, confirm, encrypt)
- [x] ISC-8: Ultrasonic pairing protocol addresses collision detection for multiple devices
- [x] ISC-9: Ultrasonic pairing protocol specifies fallback to QR/NFC
- [x] ISC-10: Mesh layer specifies topology (flooding mesh or structured routing)
- [x] ISC-11: Mesh layer defines node identity and discovery mechanism
- [x] ISC-12: Mesh layer defines message propagation and TTL strategy
- [x] ISC-13: Mesh layer addresses NAT traversal and network boundaries
- [x] ISC-14: Mesh layer specifies database sync / conflict resolution model
- [x] ISC-15: Message protocol defines wire format (protobuf or JSON schema)
- [x] ISC-16: Message protocol defines message types (text, image, file, typing, receipt)
- [x] ISC-17: Message protocol specifies delivery semantics (at-most-once, at-least-once)
- [x] ISC-18: Message protocol specifies encryption (end-to-end, per-conversation key)
- [x] ISC-19: Message protocol defines group chat model (broadcast or multicast)
- [x] ISC-20: File sharing specifies erasure coding algorithm (Reed-Solomon or similar)
- [x] ISC-21: File sharing defines chunk size and reassembly procedure
- [x] ISC-22: File sharing defines metadata schema (filename, size, hash, chunks)
- [x] ISC-23: Security model defines device identity (Ed25519 keypair per device)
- [x] ISC-24: Security model defines key exchange (X3DH or Noise protocol)
- [x] ISC-25: Security model specifies trust model (TOFU with fingerprint verification)
- [x] ISC-26: Security model addresses forward secrecy via ratcheting
- [x] ISC-27: Security model specifies local data encryption (at-rest, passphrase or biometric)
- [x] ISC-28: UI/UX section defines core screens (conversation list, chat view, pairing screen, settings)
- [x] ISC-29: UI/UX section defines message delivery states (sending, sent, delivered, read, failed)
- [x] ISC-30: Data storage specifies local database (SQLite with encrypted WAL)
- [x] ISC-31: Tech stack recommended per layer (Python/Go, SQLite, WebRTC library)
- [x] ISC-32: Implementation roadmap defines phases and milestone criteria

## Decisions

<!-- Key architectural decisions will be documented here -->

## Verification

- ISC-1: Executive summary written with ChirpChat value proposition (zero-internet mesh messaging)
- ISC-2: System scope section defines what ChirpChat is and is not (6 items each)
- ISC-3: Architecture overview describes three-layer model (Audio Pairing, Mesh Transport, Application)
- ISC-4: Architecture component diagram and two data flow diagrams included
- ISC-5: Ultrasonic protocol specifies frequency band 19,000-24,000 Hz
- ISC-6: Chirp frame structure defined: Preamble + Sync Word + Header + Payload + CRC-32
- ISC-7: Handshake sequence: Discover -> Challenge -> Response -> Confirm -> Key Established
- ISC-8: Collision detection addressed: random backoff, carrier sensing, CRC retry, frequency hopping
- ISC-9: Fallback pairing specified: QR code, NFC, manual 6-digit code
- ISC-10: Topology defined as flooding mesh (epidemic routing)
- ISC-11: Node identity defined: Ed25519 keypair, NodeID = base58(hash), display name
- ISC-12: Message propagation with TTL, seen_cache, hop_count, jitter delay specified
- ISC-13: NAT traversal addressed: Wi-Fi Direct Layer 2, mDNS on LAN, bridge nodes, no STUN/TURN
- ISC-14: Database sync: Lamport timestamps, last-writer-wins, tombstoned deletes, incremental sync
- ISC-15: Wire format: Protocol Buffers with full schema definition
- ISC-16: Message types defined: TEXT, IMAGE, FILE_METADATA, FILE_CHUNK, TYPING, RECEIPT, GROUP actions
- ISC-17: Delivery semantics specified for each message type (at-least-once, at-most-once, best-effort)
- ISC-18: Encryption: X3DH key exchange + Double Ratchet + AES-256-GCM per message
- ISC-19: Group chat model: broadcast group, symmetric group key, append-only membership log, key rotation on removal
- ISC-20: Erasure coding: Reed-Solomon GF(2^16), k=8 data, m=4 parity, n=12 total chunks
- ISC-21: Chunk size = 64KB, reassembly waits for any 8-of-12 chunks per block, SHA-256 verification
- ISC-22: FileMetadata protobuf schema defined with all fields (file_id, name, size, hash, chunks, recipients)
- ISC-23: Device identity: Ed25519 keypair stored in OS keychain, NodeID derivation, 12-word BIP39 fingerprint
- ISC-24: Key exchange: X3DH with identity key, signed pre-key, one-time pre-key, ephemeral key
- ISC-25: Trust model: TOFU with physical presence during ultrasonic pairing, key change warning
- ISC-26: Forward secrecy: Signal Double Ratchet per-conversation, ratchet step per message
- ISC-27: Local data encryption: AES-256-GCM, PKDF2-derived master secret, SQLCipher
- ISC-28: Core screens defined: Conversation List, Chat View, Pairing Screen, Settings, Mesh Map
- ISC-29: Delivery states defined: Sending, Sent, Delivered, Read, Failed with icons
- ISC-30: SQLite schema defined with 5 tables (conversations, messages, file_transfers, group_members, peer_devices)
- ISC-31: Tech stack recommended per layer: Flutter, Rust, SQLite, libsodium, Reed-Solomon
- ISC-32: Roadmap defines 5 phases with milestone criteria per phase
