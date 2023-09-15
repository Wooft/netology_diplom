import pytest
from rest_framework.test import APIClient

from app.backend.models import CustomUser

@pytest.fixture
def user_sample():
    user = {
        "username": "test_user",
        "email": "test@mail.com",
        "first_name": "test_lastname",
        "last_name": "test_name",
        "surname": "test_surname",
        "company": "test_company",
        "position": "test_position",
        "password": "test_password",
        "repeatpassword": "test_password",
        "type": "shop"
    }
    return user

@pytest.fixture
def client():
    return APIClient()
@pytest.mark.django_db
def test_create_user(client, user_sample):
    response = client.post(path="/register/", data=user_sample)
    user = CustomUser.objects.get(email=user_sample['email'])
    assert response.status_code == 201
    assert user.first_name == user_sample['first_name']
    assert user.type == 'buyer'

@pytest.mark.django_db
def test_create_empty_user(client):
    response = client.post('/register/', data={})
    assert response.status_code == 400
    assert response.data['status'] == 'input data incorrect'
@pytest.mark.django_db
def test_wrong_user(client, user_sample):
    user = {
        "username": "test_user",
        "email": "test@mail.com",
        "first_name": "test_lastname",
        "last_name": "test_name",
        "surname": "test_surname",
        "company": "test_company",
        "position": "test_position",
        "password": "test_password",
        "repeatpassword": "test1_password"
    }
    response = client.post('/register/', data=user)
    assert response.status_code == 400
    assert response.data['status'] == "password don't match"
    client.post('/register/', data=user_sample)
    response = client.post('/register/', data=user_sample)
    assert response.status_code == 400
    assert response.data['username'][0] == 'A user with that username already exists.'
    assert response.data['email'][0] == 'Пользователь with this email already exists.'
@pytest.mark.django_db
def test_authorization(client, user_sample):
    client.post('/register/', data=user_sample)
    response = client.post('/auth/login/', data={
        'email': user_sample['email'],
        'password': user_sample['password']
    })
    assert response.status_code == 200
    response = client.post('/auth/login', data={
        'email': user_sample['email'],
        'password': 'incorrect_password'
    })
    assert response.status_code == 301

@pytest.mark.django_db
def test_get_token(client, user_sample):
    client.post('/register/', data=user_sample)
    response = client.post('/get_token/', data={
        'username': user_sample['email'],
        'password': user_sample['password']
    })

    assert response.status_code == 200

    response = client.post('/get_token/', data={
        'username': user_sample['email'],
        'password': 'wrong_password'
    })
    assert response.status_code == 400
    assert response.data['non_field_errors'][0] == 'Unable to log in with provided credentials.'
