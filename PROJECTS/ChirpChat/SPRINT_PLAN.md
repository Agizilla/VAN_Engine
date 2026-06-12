# ChirpChat Sprint Plan

## Comparison Summary
- `MEMORY/WORK/20260602_chirpchat-full-spec/PRD.md` is a completion record for the spec work: it defines scope, risks, criteria, and a verification checklist, but it does not contain implementation code.
- `PROJECTS/ChirpChat/specs/SPECIFICATION.html` is the actual product spec: it adds the detailed architecture, wire formats, security model, storage model, UI, and a five-phase roadmap.
- There is currently no implementation tree under `PROJECTS/ChirpChat/` beyond `specs/`, so the next step is greenfield delivery rather than refactoring existing code.

## MVP Direction
- The first build target is now the Wi-Fi-only laptop/Android simulation path, documented in `WIFI_ONLY_MVP.md`.
- That MVP uses local LAN discovery and a `WebSocket` chat channel, which avoids the laptop microphone problem and gets us to a working demo faster.
- Ultrasonic pairing, Wi-Fi Direct, and full mesh routing remain later phases after the chat loop is proven.

## My Plan

### Sprint 0 - Project Skeleton And Decisions
Goal: establish a buildable monorepo shell and lock the Wi-Fi-only MVP choices before coding.

- Create the repository layout: `core/`, `app/`, `desktop/`, `docs/`, `tests/`.
- Confirm the MVP stack: Rust laptop service, Flutter Android client, SQLite, protobuf, WebSocket over LAN.
- Define the shared protobuf contract in `proto/chirpchat.proto`, then freeze the trust model, discovery strategy, and project-level test strategy.
- Add CI, formatting, linting, and local developer setup docs.

Exit criteria:
- Repo builds cleanly with placeholder modules.
- Architectural decisions are captured and frozen for Sprint 1.

### Sprint 1 - Wi-Fi Chat Pairing MVP
Goal: get the phone and laptop connected over the same Wi-Fi network and exchanging messages.

- Implement LAN discovery via `mDNS` with manual IP or QR fallback.
- Implement the initial pairing handshake and trusted reconnect token.
- Add the WebSocket chat channel and basic message receipts.
- Build a prototype pairing screen and chat screen for the demo loop.

Exit criteria:
- Phone and laptop can pair on the same Wi-Fi network.
- Messages can be sent both directions through the local chat link.

### Sprint 2 - Local Mesh Messaging
Goal: move from paired devices to durable text messaging over the mesh.

- Implement node identity, discovery, and topology selection.
- Add message routing with TTL, duplicate suppression, and seen-cache behavior.
- Define and implement the protobuf wire format for text, typing, and receipts.
- Persist conversations and messages in encrypted SQLite.

Exit criteria:
- A text message can traverse at least three hops in the mesh.
- Messages survive restart and rejoin without corrupting state.

### Sprint 3 - Security And Group Chat
Goal: make the transport safe enough for real use.

- Implement X3DH or the chosen key exchange path, then ratchet per conversation.
- Add end-to-end encryption for direct and group messages.
- Implement TOFU fingerprint verification and local key storage.
- Add group creation, membership changes, and key rotation on removal.

Exit criteria:
- Direct and group chats are encrypted end-to-end.
- Key changes and trust changes are visible to the user.

### Sprint 4 - File Sharing
Goal: ship resilient file transfer on top of the mesh.

- Implement file metadata, chunking, and reassembly.
- Add Reed-Solomon erasure coding with the spec’s target chunk model.
- Add transfer progress, retries, partial recovery, and hash verification.
- Support thumbnails or previews where appropriate.

Exit criteria:
- Large files can be transferred with partial-loss recovery.
- Failed transfers resume without duplicate corruption.

### Sprint 5 - Productization
Goal: turn the core into a usable app.

- Complete the core UI screens: conversations, chat, pairing, settings, mesh map.
- Add delivery state UI and offline state visibility.
- Tighten battery behavior, background constraints, and platform-specific limits.
- Run device matrix tests, document open questions, and prepare a v1.0 release checklist.

Exit criteria:
- The app is usable on the target mobile platform.
- Known platform limits and unresolved research items are documented.

## Risks To Recheck Early
- LAN discovery reliability on home and office routers.
- Cross-platform background limits for the Android client.
- Message ordering and reconnect behavior after Wi-Fi drops.
- Later migration from LAN chat to full offline mesh transport.

## Recommended Delivery Order
1. Wi-Fi pairing and reconnect
2. Text chat over LAN
3. Trust and persistence
4. File transfer
5. Mesh and offline transport
