import requests as r
import json
import credentials

def rehost(media_url):
    try:
        r2 = r.post('https://imgrush.com/api/upload/url', data={'url':media_url})
        j = json.loads(r2.text)
        hashcode = j['hash'].encode('utf-8')
        p_info = json.loads((r.get(url='https://imgrush.com/api/%s' % hashcode)).text)

        if p_info['blob_type'] == "image":
            return p_info['files'][0]['url'].encode('utf-8')
        elif p_info['blob_type'] == "video":
            return p_info['files'][1]['url'].encode('utf-8')
    except Exception as e:
        return "error"

def delete_rehost(hashcode):
    r2 = r.delete('https://imgrush.com/api/%s' % hashcode)
    j = json.loads(r2.text)
    if j['status'] == 'success':
        return "deleted"
    else:
        return "not deleted"
