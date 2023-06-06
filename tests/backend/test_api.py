import pytest
from rest_framework.test import APIClient

@pytest.mark.django_db
def test_YamlUploadView():
    client = APIClient()
    yaml = open("example.yaml", "rb")
    response = client.post('/yamlupload/', {"file": yaml})
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

@pytest.mark.django_db
def test_empty_post():
    client = APIClient()
    response = client.post('/yamlupload/')
    assert response.status_code == 400
    assert response.json()['status'] == 'please load correct yaml file'

@pytest.mark.django_db
def test_shop_view():
    client = APIClient()
    response = client.get('/shop/')
    assert response.status_code == 200