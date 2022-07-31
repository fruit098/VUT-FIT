from flask import Flask, request
from tb_device_mqtt import TBDeviceMqttClient
from flask_inputs import Inputs
from flask_inputs.validators import JsonSchema
import json
import copy
import os
import statistics

schema = {
    "required": ["data"],
    "properties": {
        "data": {
            "type": "array",
            "items": {
                "required": ["name", "temperature"],
                "properties": {
                    "name": {"type": "string"},
                    "temperature": {"type": "number"},
                    "brightness": {"type": "number"},
                },
            },
        }
    },
}
current_data = {
    "rpi": {"temperature": []},
    "esp1": {"temperature": [], "brightness": []},
    "esp2": {"temperature": [], "brightness": []},
}

app = Flask(__name__)
mqtt_client = TBDeviceMqttClient("147.229.12.176", "juGwb3wjDyGlGsi2WoHV")


class JsonInputs(Inputs):
    json = [JsonSchema(schema=schema)]


@app.route("/ping")
def ping():
    return "pong"


@app.route("/sensor_data", methods=["POST"])
def sensor_data():
    inputs = JsonInputs(request)
    if inputs.validate():
        collect_and_write(request.json["data"])
        return 'ok'
    else:
        return inputs.errors


def collect_and_write(data):
    global current_data
    for meassurements in data:
        name = meassurements["name"]
        for attribute in meassurements:
            if attribute == 'name':
                continue
            current_data[name][attribute].append(meassurements[attribute])

    current_data["rpi"]["temperature"].append(read_cpu_temp())

    if len(current_data["rpi"]["temperature"]) == 10:
        write()
        current_data = {
            "rpi": {"temperature": []},
            "esp1": {"temperature": [], "brightness": []},
            "esp2": {"temperature": [], "brightness": []},
        }


def write():
    result = {}
    mqtt_client.connect()
    for name in current_data:
        for attribute in current_data[name]:
            values = current_data[name][attribute]
            minimum = min(values)
            maximum = max(values)
            average = sum(values) / len(values)
            median = statistics.median(values)
            result.update({
                f"{name}_{attribute}_minimum": minimum,
                f"{name}_{attribute}_maximum": maximum,
                f"{name}_{attribute}_average": average,
                f"{name}_{attribute}_median": median,
            })
    print(result)
    mqtt_client.send_telemetry(result)
    mqtt_client.disconnect()



def read_cpu_temp():
    result = 0.0
    if os.path.isfile("/sys/class/thermal/thermal_zone0/temp"):
        with open("/sys/class/thermal/thermal_zone0/temp") as f:
            line = f.readline().strip()
            if line.isdigit():
                result = float(line) / 1000
    return result


if __name__ == "__main__":
    app.run('0.0.0.0')
