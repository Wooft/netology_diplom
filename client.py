import datetime

import requests

def yaml_upload():
    url = 'http://127.0.0.1:6060/yamlupload/'
    file = open('example.yaml', 'rb')
    file = {'file': file}
    headers = {
        'Content-Type': 'multipart/data'
    }
    response = requests.post(url=url, files=file)

    print(response.status_code)
    print(response.text)
    return response

if __name__ == '__main__':
    yaml_upload()