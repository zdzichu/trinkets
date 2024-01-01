
Utility to query Candy appliances and publish status to MQTT topic.

Configuration:
==============

In the `ConfigMap`:
- `CANDY_HOST` - IP address or hostname of the Candy appliance
- `MQTT_HOST` - IP address or hostname of MQTT broker
- `MQTT_USER` - username for authenticating with MQTT broker
- `MQTT_TOPIC` - where to publish data

In the `Secret`:
- `CANDY_KEY` - a key to decrypting appliance response. Key can be recovered
  using https://github.com/MelvinGr/CandySimplyFi-tool
- `MQTT_PASSWORD` - password for MQTT broker

TODO:
=====

1. Listening on `MQTT_TOPIC/control` and reacting to commands:
  - switching log level between DEBUG and INFO
  - programming the appliance (start program on washer/dryer, set temperatur of hog etc.)

