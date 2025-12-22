from dataclasses import dataclass, field
import json
from typing import Any

from flask import Flask, jsonify, request
import paho.mqtt.client as mqtt


class MqttJob:
    name: str
    start_requires: tuple[str, ...]
    status: dict[str, dict]
    mqttc: mqtt.Client

    def __init__(self, flaskapp: Flask, mqttc: mqtt.Client, name: str, start_requires: tuple[str, ...]) -> None:
        self.name = name
        self.start_requires = start_requires
        self.status = {}
        self.mqttc = mqttc

        flaskapp.add_url_rule(
            f"/api/{name}", f'get-{name}', self.http_get, methods=["GET"])
        flaskapp.add_url_rule(
            f"/api/{name}", f'start-{name}', self.http_start, methods=["POST"])
        flaskapp.add_url_rule(
            f"/api/{name}/stop", f'stop-{name}', self.http_stop, methods=["POST"])

        mqttc.message_callback_add(
            self.topic_status, self.mqtt_on_status)

    @property
    def topic_status(self) -> str:
        return f"vitens/{self.name}/status"

    @property
    def topic_activate(self) -> str:
        return f"vitens/{self.name}/activate"

    @property
    def topic_deactivate(self) -> str:
        return f"vitens/{self.name}/deactivate"

    def validate_start_payload(self, data: Any) -> tuple[bool, str | None]:
        if type(data) is not dict:
            return False, "invalid request"
        for k in self.start_requires:
            if k not in data:
                return False, "missing parameters"
        return True, None

    def validate_stop_payload(self, data: Any) -> tuple[bool, str | None]:
        if type(data) is not dict:
            return False, "invalid request"
        if "device" not in data:
            return False, "missing parameters"
        return True, None

    def mqtt_on_status(self, client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage) -> None:
        payload = json.loads(msg.payload)
        device = payload["device"]
        active = payload["active"]
        if active:
            self.status[device] = payload
        else:
            self.status.pop(device, None)

    def http_get(self):
        return jsonify(self.status)

    def http_start(self):
        data = request.json
        ok, err = self.validate_start_payload(data)
        if not ok:
            return jsonify({"error": err})
        self.mqttc.publish(self.topic_activate, json.dumps(data))
        return jsonify(error=None)

    def http_stop(self):
        data = request.json
        ok, err = self.validate_stop_payload(data)
        if not ok:
            return jsonify({"error": err})
        self.mqttc.publish(self.topic_deactivate, json.dumps(data))
        return jsonify(error=None)
