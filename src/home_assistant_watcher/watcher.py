import argparse
import base64
import re
import requests
import uuid
import yaml
from transformers import Qwen2_5OmniForConditionalGeneration, Qwen2_5OmniProcessor, AutoTokenizer, AutoProcessor
from qwen_omni_utils import process_mm_info

class Watcher:
    def __init__(self, data_store):
        self.data_store = data_store
        self.model = Qwen2_5OmniForConditionalGeneration.from_pretrained("Qwen/Qwen2.5-Omni-3B", torch_dtype="auto", device_map="auto")#, attn_implementation="flash_attention_2",)
        self.model.disable_talker()
        self.processor = Qwen2_5OmniProcessor.from_pretrained("Qwen/Qwen2.5-Omni-3B")

    def save(self, stream, results):
        print(results)
        for k, v in results.items():
            print(stream, k)
            self.data_store.set(stream["stream_id"], k, v)

    def watch(self, config):
        for stream in config["streams"]:
            url = f'{config["home_assistant_url"]}/{stream["stream_id"]}'
            HOME_ASSISTANT_BEARER_TOKEN = "[API_KEY]"
            headers = {
                "Authorization": f"Bearer {HOME_ASSISTANT_BEARER_TOKEN}",
                "content-type": "application/json",
            }

            response = requests.get(url, headers=headers)
            print(response)
            if response.status_code == 200:
                # The request was successful
                image_data = response.content
            
                messages = [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "image": f"data:image;base64,{base64.b64encode(image_data).decode('ascii')}",
                                "resized_height": 480,
                                "resized_width": 854,
                            },
                            {
                                "type": "text",
                                "text": config["prompt"].replace(
                                    "[EVENTS]",
                                    "\n".join([f'<event id="{i}">{v}</event>' for i, (k, v) in enumerate(stream["events"].items())])
                                )
                            }
                        ],
                    }
                ]
                result = self.check(stream, messages)
                self.save(stream, result)

    def check(self, stream, messages):
        # Preparation for inference
        text = self.processor.apply_chat_template(messages, add_generation_prompt=True, tokenize=False)
        audios, images, videos = process_mm_info(messages, use_audio_in_video=False)
        inputs = self.processor(text=text, audio=audios, images=images, videos=videos, return_tensors="pt", padding=True, use_audio_in_video=False)
        inputs = inputs.to(self.model.device).to(self.model.dtype)
        text_ids = self.model.generate(**inputs, use_audio_in_video=False)
        text = self.processor.batch_decode(text_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)

        results = {}

        for i, (event_id, event_description) in enumerate(stream["events"].items()):
            pattern = r'<event id=\"' + str(i) + r'\">(\d)</event>'

            # Find all matches
            matches = re.findall(pattern, text[0])

            if not matches:
                results[event_id] = None
                continue

            # Output results
            for match in matches:
                results[event_id] = match
                continue
        
        return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser("Start the parser API")
    parser.add_argument("configuration", type=str)
    args = parser.parse_args()

    with open(args.configuration, "r") as fh:
        config = yaml.safe_load(fh)

    from home_assistant_watcher.data import EventWatcherDataStore
    data_store = EventWatcherDataStore()
    watcher = Watcher(data_store)
    watcher.watch(config)
