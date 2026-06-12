#!/usr/bin/env python3
"""
MM458.1 Bluetooth Speaker Debugger - Windows UTF-8 Fixed
Author: AI Pairing
Purpose: Diagnose disconnection issues, capture GATT services, attempt keep-alive

Run: python mm458_debug.py
"""

import sys
import io

# ========== WINDOWS UTF-8 FIX ==========
if sys.platform == 'win32':
    if hasattr(sys.stdout, 'buffer') and sys.stdout.buffer and not isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    if hasattr(sys.stderr, 'buffer') and sys.stderr.buffer and not isinstance(sys.stderr, io.TextIOWrapper):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
# ========================================

import asyncio
import logging
import time
from datetime import datetime

# Requires: pip install bleak
try:
    from bleak import BleakScanner, BleakClient
    from bleak.backends.characteristic import BleakGATTCharacteristic
except ImportError:
    print("ERROR: bleak not installed. Run: pip install bleak")
    sys.exit(1)

# ========== CONFIGURATION ==========
SPEAKER_NAME_PATTERNS = ["MM458", "Aim", "Speaker", "MM458.1", "458"]
KEEP_ALIVE_INTERVAL = 30  # seconds
AUTO_RECONNECT = True
LOG_FILE = f"mm458_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
SCAN_TIMEOUT = 8.0
# ===================================

# Configure logging with UTF-8 handler
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class MM458SpeakerDebugger:
    def __init__(self):
        self.client = None
        self.device = None
        self.device_address = None
        self.disconnect_count = 0
        self.keep_alive_task = None
        self.characteristics = {}
        self.reconnect_attempts = 0

    async def discover_speaker(self):
        """Find MM458.1 speaker via Bluetooth LE scanning"""
        logger.info("Scanning for MM458.1 speaker...")

        try:
            devices = await BleakScanner.discover(timeout=SCAN_TIMEOUT)
        except Exception as e:
            logger.error(f"Scan failed: {e}")
            logger.info("Make sure Bluetooth is enabled and speaker is in pairing mode")
            return None

        found_devices = []
        for dev in devices:
            name = dev.name or ""
            found_devices.append(f"{name} - {dev.address}")
            logger.debug(f"Found: {name} - {dev.address}")

            for pattern in SPEAKER_NAME_PATTERNS:
                if pattern.lower() in name.lower():
                    logger.info(f"Found speaker: {name} at {dev.address}")
                    self.device = dev
                    self.device_address = dev.address
                    return dev

        logger.info(f"Found {len(devices)} devices but none matching {SPEAKER_NAME_PATTERNS}")
        logger.info("Try putting speaker in pairing mode (usually hold power button 5-10 seconds)")
        return None

    async def explore_services(self, client: BleakClient):
        """Discover all GATT services and characteristics"""
        logger.info("Exploring GATT services...")

        for service in client.services:
            logger.info(f"  Service: {service.uuid}")
            if service.description:
                logger.info(f"    Description: {service.description}")

            for char in service.characteristics:
                props = ",".join(char.properties)
                logger.info(f"    Characteristic: {char.uuid} [{props}]")
                self.characteristics[char.uuid] = char

                # Try to read if readable
                if "read" in char.properties:
                    try:
                        value = await client.read_gatt_char(char.uuid)
                        hex_preview = value.hex()[:50]
                        ascii_preview = ''.join(chr(b) if 32 <= b < 127 else '.' for b in value[:20])
                        logger.info(f"      Read: {hex_preview}... | {ascii_preview}")

                        # Check for battery characteristic
                        if "battery" in char.uuid.lower() or "2a19" in char.uuid:
                            if len(value) == 1:
                                logger.info(f"      Battery: {value[0]}%")
                    except Exception as e:
                        logger.debug(f"      Read failed: {e}")

                # Subscribe to notifications if available
                if "notify" in char.properties or "indicate" in char.properties:
                    try:
                        await client.start_notify(char.uuid, self.notification_handler)
                        logger.info(f"      Subscribed to notifications")
                    except Exception as e:
                        logger.debug(f"      Notification subscribe failed: {e}")

    def notification_handler(self, char: BleakGATTCharacteristic, data: bytearray):
        """Handle notifications from speaker (battery, status, etc)"""
        logger.info(f"Notification from {char.uuid}: {data.hex()}")

        # Parse common Bluetooth speaker notifications
        if len(data) == 1:
            battery = data[0]
            if 0 <= battery <= 100:
                logger.info(f"Battery level: {battery}%")
        elif len(data) >= 2:
            if data[0] == 0x02:  # Common volume notification
                logger.info(f"Volume notification: {data[1]}")
            elif data[0] == 0x03:  # Common play/pause
                logger.info(f"Playback status: {'Playing' if data[1] else 'Paused'}")

    async def send_keep_alive(self, client: BleakClient):
        """Send periodic keep-alive to prevent disconnection"""
        keep_alive_sent = 0
        while self.keep_alive_task and not self.keep_alive_task.cancelled():
            await asyncio.sleep(KEEP_ALIVE_INTERVAL)
            if client and client.is_connected:
                sent = False
                # Try common keep-alive characteristics
                for uuid, char in self.characteristics.items():
                    if "write" in char.properties and not sent:
                        try:
                            # Send empty or ping packet
                            await client.write_gatt_char(uuid, b"\x00")
                            keep_alive_sent += 1
                            logger.debug(f"Keep-alive sent to {uuid} (count: {keep_alive_sent})")
                            sent = True
                        except:
                            pass

                if not sent:
                    logger.debug("No writable characteristic found for keep-alive")

    async def handle_disconnect(self, client: BleakClient):
        """Called when speaker disconnects"""
        self.disconnect_count += 1
        logger.warning(f"Disconnected! Total disconnections: {self.disconnect_count}")

        if AUTO_RECONNECT and self.disconnect_count < 10:
            self.reconnect_attempts += 1
            wait_time = min(30, 5 * self.reconnect_attempts)
            logger.info(f"Reconnecting in {wait_time} seconds (attempt {self.reconnect_attempts})...")
            await asyncio.sleep(wait_time)
            await self.run()

    async def run(self):
        """Main connection loop"""
        if not self.device:
            self.device = await self.discover_speaker()
            if not self.device:
                logger.error("Speaker not found. Make sure it's in pairing mode and Bluetooth is on.")
                return

        try:
            async with BleakClient(self.device, disconnected_callback=self.handle_disconnect) as client:
                self.client = client
                self.reconnect_attempts = 0
                logger.info(f"Connected to {self.device.name or self.device_address}")

                # Explore all services
                await self.explore_services(client)

                # Start keep-alive task
                self.keep_alive_task = asyncio.create_task(self.send_keep_alive(client))

                # Keep connection alive
                logger.info("Speaker connected. Monitoring for disconnections...")
                logger.info(f"Logging to {LOG_FILE}")
                logger.info("Press Ctrl+C to stop")

                # Print connection stats every 60 seconds
                last_stats = time.time()
                start_time = time.time()
                while client.is_connected:
                    await asyncio.sleep(1)

                    if time.time() - last_stats > 60:
                        last_stats = time.time()
                        uptime = int(time.time() - start_time)
                        logger.info(f"Still connected - uptime: {uptime}s, disconnects: {self.disconnect_count}")

        except Exception as e:
            logger.error(f"Connection error: {e}")
            if AUTO_RECONNECT and self.reconnect_attempts < 5:
                await asyncio.sleep(5)
                await self.run()
        finally:
            if self.keep_alive_task:
                self.keep_alive_task.cancel()

    def print_summary(self):
        """Print diagnostic summary"""
        print("\n" + "="*60)
        print("MM458.1 DEBUG SUMMARY")
        print("="*60)
        print(f"Device found: {self.device.name if self.device else 'No'}")
        print(f"Device address: {self.device_address or 'Unknown'}")
        print(f"Disconnections detected: {self.disconnect_count}")
        print(f"Characteristics discovered: {len(self.characteristics)}")
        print(f"Log file: {LOG_FILE}")

        if self.disconnect_count > 0:
            print("\nPossible causes:")
            print("  1. Power saving mode on speaker (auto-sleep after idle)")
            print("  2. Low battery")
            print("  3. Interference (2.4GHz WiFi nearby)")
            print("  4. Windows Bluetooth power management")
            print("\nTry these fixes:")
            print("  - Disable Bluetooth power saving in Device Manager")
            print("  - Keep audio playing continuously")
            print("  - Move speaker closer to computer")
            print("  - Update Bluetooth drivers")
            print("  - Turn off 'Allow computer to turn off this device'")
            print("    in Bluetooth adapter properties")

        # Check for OTA update capability
        ota_services = [uuid for uuid in self.characteristics.keys()
                       if "ff" in uuid.lower() or "firmware" in uuid.lower() or "ota" in uuid.lower()]
        if ota_services:
            print("\nOTA/Firmware update services found!")
            print(f"  Services: {ota_services}")
            print("  Firmware update MAY be possible with manufacturer tool")
        else:
            print("\nNo OTA services detected. Firmware update likely requires")
            print("  manufacturer's proprietary tool or USB connection.")


async def main():
    debugger = MM458SpeakerDebugger()
    try:
        await debugger.run()
    except KeyboardInterrupt:
        logger.info("\nShutting down...")
    finally:
        debugger.print_summary()


if __name__ == "__main__":
    asyncio.run(main())
