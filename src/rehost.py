import requests
import json
import credentials

def rehost_img(image_url):
        CLIENT_ID = credentials.credentials["IMGUR_CLIENT_ID"]
        headers = {"Authorization": "Client-ID %s" % CLIENT_ID}
        url = 'https://api.imgur.com/3/upload.json'
        r2 = requests.post(
                url,
                headers = headers,
                data={'key' : CLIENT_ID,
                     'image': image_url})
        j = json.loads(r2.text)
        return str(j["data"]["link"])
