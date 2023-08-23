import datetime

import requests

def yaml_upload():
    url = 'http://127.0.0.1:8000/yamlupload/'
    file = open('example.yaml', 'rb')
    file = {'file': file}
    headers = {
        'Content-Type': 'multipart/data'
    }
    response = requests.post(url=url, files=file)

    print(response.status_code)
    print(response.text)
    return response

def upload():
    time = datetime.datetime.now()
    for i in range(3):
        print(yaml_upload())
    end_time = datetime.datetime.now() - time
    return end_time

if __name__ == '__main__':
    print(upload())