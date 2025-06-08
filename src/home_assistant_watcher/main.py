#!/usr/bin/env python3
import argparse
import yaml
from home_assistant_watcher.api import create_app, run_api_server
from home_assistant_watcher.mqtt_client import run_mqtt_client
from home_assistant_watcher.data import EventWatcherDataStore

def main():
    parser = argparse.ArgumentParser("Home Assistant Watcher")
    parser.add_argument("configuration", type=str, help="Path to configuration file")
    parser.add_argument("--mode", type=str, choices=["api", "mqtt"], default="mqtt",
                        help="Run mode: api (standalone API) or mqtt (MQTT publisher)")
    
    args = parser.parse_args()
    
    with open(args.configuration, "r") as fh:
        config = yaml.safe_load(fh)
    
    if args.mode == "api":
        run_api_server(config)
    else:
        run_mqtt_client(config)

if __name__ == "__main__":
    main()