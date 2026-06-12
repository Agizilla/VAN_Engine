# ChirpChat Wi-Fi-Only MVP

## Goal
Build the smallest useful ChirpChat prototype: an Android phone and a laptop that can discover each other on the same Wi-Fi network, pair once, and exchange simulated chat messages without using the internet.

## Why This Path
- No laptop microphone is required.
- No hotspot or ultrasonic hardware path is required.
- The app can be tested immediately on an ordinary Wi-Fi LAN.
- The transport can later be swapped for ultrasonic, Wi-Fi Direct, or mesh without changing the chat model.

## Chosen MVP Stack
- Android client: `Flutter`
- Laptop companion: `Rust` service with a tiny local UI or CLI
- Shared protocol: `Protobuf` messages over `WebSocket`
- Local storage: `SQLite`
- Discovery: `mDNS` first, manual IP or QR fallback second

## Architecture

### 1. Android App
Responsibilities:
- Show pairing screen, conversation list, and chat view.
- Discover the laptop service on the local Wi-Fi network.
- Store the trusted laptop fingerprint and reconnect automatically.
- Send and receive chat messages, delivery states, and presence updates.

### 2. Laptop Companion
Responsibilities:
- Advertise a local service on the LAN.
- Accept pairing requests from the phone.
- Host the chat session and echo or relay messages.
- Persist message history locally for the simulation.

### 3. Shared Transport Layer
Responsibilities:
- Open a LAN `WebSocket` between phone and laptop.
- Carry protobuf frames for pairing, chat, receipts, and presence.
- Keep the protocol versioned so we can swap transport later.

## Pairing Flow
1. Laptop starts the companion service and advertises itself on the LAN.
2. Android discovers the service through `mDNS` or accepts a manual IP/QR entry.
3. The first connection exchanges a short pairing secret.
4. Both sides derive a trusted session token and save the fingerprint locally.
5. Future launches auto-reconnect to the remembered laptop on the same Wi-Fi network.

## Message Flow
1. Android opens the chat and connects to the laptop over `WebSocket`.
2. Messages are serialized as protobuf frames.
3. The laptop stores them locally and sends a receipt back.
4. The Android UI shows sending, sent, delivered, and failed states.

## What Is In Scope
- One phone, one laptop
- Local Wi-Fi only
- Text chat simulation
- Pairing and reconnect
- Local persistence

## What Is Out Of Scope
- Ultrasonic pairing
- Wi-Fi Direct
- Multi-hop mesh routing
- Group chat
- File sharing
- Internet relay or cloud sync

## Implementation Order
1. Laptop companion service
2. Android discovery and pairing screen
3. WebSocket chat transport
4. Local SQLite persistence
5. Trust and reconnect logic
6. UI polish and delivery states

## Success Criteria
- The phone can discover the laptop on the same Wi-Fi network.
- The phone and laptop can pair once and reconnect later.
- Messages travel both ways over the local LAN.
- The demo works without a laptop microphone, hotspot, or internet dependency.

