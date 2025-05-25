import asyncio
import argparse
import uvicorn
import yaml
from home_assistant_watcher.data import EventWatcherDataStore
from home_assistant_watcher.watcher import Watcher
from fastapi import FastAPI
from threading import Thread

def create_app(config, data_store):
    app = FastAPI()

    @app.on_event("startup")
    async def startup_event():
        async def loop():
            watcher = Watcher(data_store)
            while True:
                watcher.watch(config)
                await asyncio.sleep(config.get("interval", 60))

        asyncio.create_task(loop())

    @app.get(f"/streams/")
    def streams():
        return {
            "streams": config["streams"]
        }

    @app.get("/streams/{stream_id}/")
    def get_stream(stream_id: str):
        return {
            "stream_id": stream_id,
            "events": [
                stream
                for stream in config["streams"]
                if stream["stream_id"] == stream_id
            ][0]["events"]
        }

    @app.get("/streams/{stream_id}/events/{event_id}/")
    def get_event_status(stream_id: str, event_id: str):
        print(data_store._data)
        return {
            "stream_id": stream_id,
            "event_id": event_id,
            "status": data_store.get(stream_id, event_id)
        }

    return app

if __name__ == "__main__":
    parser = argparse.ArgumentParser("Start the parser API")
    parser.add_argument("configuration", type=str)

    args = parser.parse_args()

    with open(args.configuration, "r") as fh:
        config = yaml.safe_load(fh)

    data_store = EventWatcherDataStore()
    server = create_app(config, data_store)
    uvicorn.run(server, host="0.0.0.0", port=8193)
