import json
import logging
import threading
import time

import paho.mqtt.client as mqtt

logger = logging.getLogger(__name__)

# paho-mqtt 2.x requires explicit callback API version
try:
    _CALLBACK_API = mqtt.CallbackAPIVersion.VERSION1
except AttributeError:
    _CALLBACK_API = None  # paho 1.x — no version needed


class MQTTClient:
    def __init__(self, broker_host: str, broker_port: int, client_id: str, on_message=None):
        self._broker_host = broker_host
        self._broker_port = broker_port
        self._client_id = client_id
        self._topic_callbacks: dict[str, callable] = {}
        self._lock = threading.Lock()

        if _CALLBACK_API is not None:
            self._client = mqtt.Client(callback_api_version=_CALLBACK_API, client_id=client_id)
        else:
            self._client = mqtt.Client(client_id=client_id)

        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._dispatch_message

        if on_message:
            self._default_callback = on_message
        else:
            self._default_callback = None

    def connect(self):
        self._client.connect(self._broker_host, self._broker_port, keepalive=60)
        self._client.loop_start()
        logger.info("MQTT loop started — connecting to %s:%s", self._broker_host, self._broker_port)

    def publish(self, topic: str, payload: dict):
        with self._lock:
            self._client.publish(topic, json.dumps(payload))

    def subscribe(self, topic: str, callback: callable):
        self._topic_callbacks[topic] = callback
        self._client.subscribe(topic)
        logger.debug("Subscribed to %s", topic)

    def disconnect(self):
        self._client.loop_stop()
        self._client.disconnect()
        logger.info("MQTT disconnected")

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.info("Connected to MQTT broker at %s:%s", self._broker_host, self._broker_port)
            # Resubscribe after reconnect
            for topic in self._topic_callbacks:
                client.subscribe(topic)
        else:
            logger.error("MQTT connection failed with code %s", rc)

    def _on_disconnect(self, client, userdata, rc):
        if rc != 0:
            logger.warning("MQTT disconnected unexpectedly (rc=%s) — reconnecting", rc)
            self._reconnect()

    def _reconnect(self):
        delay = 5
        while True:
            try:
                self._client.reconnect()
                logger.info("MQTT reconnected")
                return
            except Exception as e:
                logger.warning("MQTT reconnect failed: %s — retrying in %ss", e, delay)
                time.sleep(delay)
                delay = min(delay * 2, 60)

    def _dispatch_message(self, client, userdata, message):
        topic = message.topic
        try:
            payload = json.loads(message.payload.decode())
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.warning("Failed to decode message on %s: %s", topic, e)
            return

        if not isinstance(payload, dict):
            logger.warning("Non-dict payload on %s: %r — wrapping", topic, payload)
            payload = {"value": payload}

        callback = self._topic_callbacks.get(topic)
        if callback:
            callback(topic, payload)
        elif self._default_callback:
            self._default_callback(topic, payload)
