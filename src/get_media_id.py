import requests
import json

def get_media_id(ig_URL):
    r = requests.get("http://api.instagram.com/oembed?url=%s" % ig_URL);
    j = json.loads(r.text)
    return j["media_id"]
