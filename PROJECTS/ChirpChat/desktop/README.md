# ChirpChat Desktop Companion

This crate is the laptop-side companion for the Wi-Fi-only ChirpChat MVP.

## Purpose
- Advertise a local service on the LAN.
- Accept pairing from the Android client.
- Exchange chat messages over a local transport.
- Persist local demo data for the simulation.

## Current Scope
- Service skeleton only.
- No ultrasonic pairing.
- No mesh routing yet.
- No production UI yet.

## Next Steps
1. Wire in protobuf serialization from `../proto/chirpchat.proto`.
2. Add LAN discovery and a local WebSocket endpoint.
3. Connect the Android client to the shared protocol.

## Build Note
- `cargo build` will generate the Rust message types from `../proto/chirpchat.proto` through `build.rs`.
