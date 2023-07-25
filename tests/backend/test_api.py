import pytest
from rest_framework.test import APIClient, force_authenticate, APIRequestFactory

from backend.models import CustomUser, Productinfo, Shop
from model_bakery import baker

from backend.views import ShoppingCartViewSet

###фикстура, которая возвращает клиент
@pytest.fixture
def client():
    return APIClient()

###фикстура, которая возвращает авторизованный клиент
@pytest.fixture
def auth_client(client):
    user = {
        "last_name": "lastname",
        "username": "username",
        "first_name": "firstname",
        "email": "email@mail.com",
        "password": "password",
        "repeatpassword": "password",
    }
    client.post('/register/', data=user)
    client.login(username=user['email'], password=user['password'])
    return client

###фикстура, которая создает пользователей
@pytest.fixture
def user_factory():
    def factory(*args, **kwargs):
        return baker.make(CustomUser, *args, **kwargs)
    return factory

@pytest.fixture
def product_info_factory():
    def factory(*args, **kwargs):
        shop = baker.make(Shop)
        return baker.make(Productinfo, *args, **kwargs, shop=shop)
    return factory

@pytest.mark.django_db
def test_YamlUploadView():
    client = APIClient()
    yaml = open("example.yaml", "rb")
    response = client.post('/yamlupload/', {"file": yaml}, format='multipart')
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

@pytest.mark.django_db
def test_empty_post():
    client = APIClient()
    response = client.post('/yamlupload/')
    assert response.status_code == 415
    assert response.json()['status'] == 'please load correct yaml file'

@pytest.mark.django_db
def test_shop_view():
    client = APIClient()
    response = client.get('/shop/')
    assert response.status_code == 200
@pytest.mark.django_db
def test_create_user(client):
    response = client.post('/register/', data= {
    "last_name": "Колесниченко",
    "username": "someusername1",
    "first_name": "Михаил",
    "surname": "Николаевич",
    "email": "some1@mail.com",
    "password": "Shambala",
    "repeatpassword": "Shambala",
    "company": "SomeCompany",
    "position": "Some"
    })
    assert response.status_code == 201
    assert response.data['username'] == 'someusername1'
#Проверка на отправку пустого запроса
def test_fail_create_user(client):
    responce = client.post('/register/')
    assert responce.status_code == 400
    assert responce.data['status'] == 'input data incorrect'

def test_register_incorrect_user(client):
    responce = client.post('/register/', data={
        'username': 'username'
    })
    assert responce.status_code == 400
    assert responce.data['status'] == 'input data incorrect'

###Проверка получения пустой корзины
@pytest.mark.django_db
def test_create_basket(auth_client):
    response = auth_client.get('/shopping_cart/')
    assert response.status_code == 200
    assert response.data['status'] == 'shoppingcart is empty'

###проверка ошибки получения корзины неавторизованного пользователя
@pytest.mark.django_db
def test_unauthorized_get_basket(client):
    response = client.get('/shopping_cart/')
    assert response.status_code == 401

###Проверка создания корзины
@pytest.mark.django_db
def test_create_basket(auth_client, product_info_factory):
    products = product_info_factory(_quantity=10)
    for product in products:
        response = auth_client.post('/shopping_cart/', data={
                                    'product': product.id,
                                    'shop': product.shop.id,
                                    'quantity': 1
                                })
        print(response.data)
        assert response.status_code == 200

###Проверка изменения корзины
@pytest.mark.django_db
def test_patch_basket(auth_client, product_info_factory):
    product = product_info_factory()
    count = 0
    response = auth_client.post('/shopping_cart/', data={
                                'product': product.id,
                                'shop': product.shop.id,
                                'quantity': 1
                            })
    count += 1
    response = auth_client.post('/shopping_cart/', data={
        'product': product.id,
        'shop': product.shop.id,
        'quantity': 1
    })
    count += 1
    assert response.status_code == 200
    assert response.data['quantity'] == count

###Тестирование удаления корзины
@pytest.mark.django_db
def test_delete_basket(auth_client):
    response = auth_client.delete('/shopping_cart/')
    print(response.data)
    assert response.status_code == 200
    assert response.data['status'] == 'Корзина уже пуста'