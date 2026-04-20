import dbus
import threading
import logging
import time

logger = logging.getLogger(__name__)

BLUEZ_SERVICE = 'org.bluez'
ADAPTER_INTERFACE = 'org.bluez.Adapter1'
DEVICE_INTERFACE = 'org.bluez.Device1'
MEDIA_CONTROL_INTERFACE = 'org.bluez.MediaControl1'

class BluetoothManager:
    def __init__(self, mac_address: str, on_status_change=None):
        self.mac = mac_address
        self.on_status_change = on_status_change
        self._bus = dbus.SystemBus()
        self._reconnect_thread = None
        self._running = False

    def _get_device_path(self):
        """Convert MAC to BlueZ object path."""
        mac_fmt = self.mac.upper().replace(':', '_')
        return f'/org/bluez/hci0/dev_{mac_fmt}'

    def _get_device_proxy(self):
        path = self._get_device_path()
        return dbus.Interface(
            self._bus.get_object(BLUEZ_SERVICE, path),
            DEVICE_INTERFACE
        )

    def connect(self):
        if not self.mac:
            return False
        try:
            device = self._get_device_proxy()
            device.Connect()
            logger.info(f"Connected to {self.mac}")
            if self.on_status_change:
                self.on_status_change(True, self.get_device_name())
            return True
        except dbus.exceptions.DBusException as e:
            logger.warning(f"BT connect failed: {e}")
            return False

    def disconnect(self):
        try:
            device = self._get_device_proxy()
            device.Disconnect()
            if self.on_status_change:
                self.on_status_change(False, None)
        except dbus.exceptions.DBusException as e:
            logger.warning(f"BT disconnect failed: {e}")

    def is_connected(self) -> bool:
        if not self.mac:
            return False
        try:
            path = self._get_device_path()
            props = dbus.Interface(
                self._bus.get_object(BLUEZ_SERVICE, path),
                'org.freedesktop.DBus.Properties'
            )
            return bool(props.Get(DEVICE_INTERFACE, 'Connected'))
        except dbus.exceptions.DBusException:
            return False

    def get_device_name(self) -> str:
        try:
            path = self._get_device_path()
            props = dbus.Interface(
                self._bus.get_object(BLUEZ_SERVICE, path),
                'org.freedesktop.DBus.Properties'
            )
            return str(props.Get(DEVICE_INTERFACE, 'Name'))
        except dbus.exceptions.DBusException:
            return self.mac

    def send_media_command(self, command: str):
        """Send AVRCP command via MediaControl1."""
        try:
            path = self._get_device_path()
            media = dbus.Interface(
                self._bus.get_object(BLUEZ_SERVICE, path),
                MEDIA_CONTROL_INTERFACE
            )
            method = getattr(media, command, None)
            if method:
                method()
        except dbus.exceptions.DBusException as e:
            logger.warning(f"Media command {command} failed: {e}")

    def start_auto_reconnect(self):
        self._running = True
        self._reconnect_thread = threading.Thread(target=self._reconnect_loop, daemon=True)
        self._reconnect_thread.start()

    def stop_auto_reconnect(self):
        self._running = False

    def _reconnect_loop(self):
        while self._running:
            if self.mac and not self.is_connected():
                logger.info("BT disconnected — attempting reconnect")
                self.connect()
            time.sleep(30)
