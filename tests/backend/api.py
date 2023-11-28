import pytest
from rest_framework.test import APIClient, force_authenticate, APIRequestFactory

from backend.models import CustomUser, Productinfo, Shop
from model_bakery import baker

from backend.views import BasketViewSet

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



###Проверка получения пустой корзины
@pytest.mark.django_db
def test_create_basket(auth_client):
    response = auth_client.get('/shopping_cart/')
    assert response.status_code == 200
    assert response.data['status'] == 'shoppingcart is empty'



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
    assert response.status_code == 200
    assert response.data['status'] == 'Корзина уже пуста'

###Тестирование получения списка товаров
@pytest.mark.django_db
def test_get_products(auth_client, product_info_factory):
    products = product_info_factory(_quantity=10)
    response = auth_client.get('/products/')
    assert response.status_code == 200
    for product in products:
        assert product.name == auth_client.get(f'/products/{product.id}/').data['name']

###Тестирование формы входа

###Тестирование подтверждения заказа


###Тестирование формы 'спасибо за заказ'


###Тестирование заказа