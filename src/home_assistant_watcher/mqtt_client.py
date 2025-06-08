import argparse
import yaml
import json
import time
from home_assistant_watcher.data import EventWatcherDataStore
from home_assistant_watcher.watcher import Watcher
from home_assistant_watcher.mqtt_publisher import MQTTPublisher

def run_mqtt_client(config):
    data_store = EventWatcherDataStore()
    watcher = Watcher(data_store)
    
    # Initialize MQTT publisher
    mqtt_config = config.get("mqtt", {})
    publisher = MQTTPublisher(
        broker_host=mqtt_config.get("host", "localhost"),
        broker_port=mqtt_config.get("port", 1883),
        client_id=mqtt_config.get("client_id"),
        username=mqtt_config.get("username"),
        password=mqtt_config.get("password")
    )
    
    # Connect to MQTT broker
    publisher.connect()
    
    try:
        while True:
            # Watch for events
            watcher.watch(config)
            
            # Publish events to MQTT
            for stream in config["streams"]:
                stream_id = stream["stream_id"]
                for event_id in stream["events"]:
                    status = data_store.get(stream_id, event_id)
                    if status is not None:
                        topic = f"home_assistant_watcher/{stream_id}/{event_id}"
                        payload = json.dumps({
                            "stream_id": stream_id,
                            "event_id": event_id,
                            "status": status,
                            "timestamp": time.time()
                        })
                        publisher.publish(topic, payload)
            
            # Sleep for the configured interval
            time.sleep(config.get("interval", 60))
    except KeyboardInterrupt:
        pass
    finally:
        publisher.disconnect()

if __name__ == "__main__":
    parser = argparse.ArgumentParser("Start the MQTT client")
    parser.add_argument("configuration", type=str)
    
    args = parser.parse_args()
    
    with open(args.configuration, "r") as fh:
        config = yaml.safe_load(fh)
    
    run_mqtt_client(config)