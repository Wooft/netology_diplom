import random
import pytest
from rest_framework.test import APIClient
from model_bakery import baker
from backend.models import Productinfo, CustomUser, Shop, Availability, Order, Orderitem

@pytest.fixture()
def user():
    user = {
        "id": 1,
        "last_name": "lastname",
        "username": "username",
        "first_name": "firstname",
        "email": "email@mail.com",
        "password": "password",
        "repeatpassword": "password",
    }
    return user

@pytest.fixture()
def client():
    return APIClient()

@pytest.fixture()
def shop_bakery():
    def factory(*args, **kwargs):
        return baker.make(Shop, *args, **kwargs)
    return factory

@pytest.fixture()
def product_bakery():
    def factory(*args, **kwargs):
        return baker.make(Productinfo, *args, **kwargs, make_m2m=True)
    return factory
###фикстура, которая возвращает авторизованный клиент
@pytest.fixture
def shop_client():
    user = {
        "last_name": "lastname",
        "username": "username",
        "first_name": "firstname",
        "email": "email@mail.com",
        "password": "password",
        "repeatpassword": "password",
    }
    client_auth = APIClient()
    client_auth.post('/register/', data=user)
    patch_user = CustomUser.objects.get(email=user['email'])
    patch_user.type = 'shop'
    patch_user.save()
    client_auth.login(username=user['email'], password=user['password'])
    return client_auth

@pytest.fixture()
def buyer_client():
    buyer = {
        "last_name": "buyer",
        "username": "buyer",
        "first_name": "buyer",
        "email": "buyer@mail.com",
        "password": "password",
        "repeatpassword": "password",
    }
    client = APIClient()
    client.post('/register/', data=buyer)
    client.login(username=buyer['email'], password=buyer['password'])
    return client

@pytest.fixture()
def create_basket(client, user):
    summ = 0
    response = client.post('/register/', data=user)
    client.login(username=user['email'], password=user['password'])
    order = baker.make(Order, status='basket', user=CustomUser.objects.get(id=response.data['id']))
    shops = baker.make(Shop, _quantity=2)
    products = baker.make(Productinfo, _quantity=4)
    for shop in shops:
        for product in products:
            availability = baker.make(Availability, shop=shop, product_info=product)
            orderitem = baker.make(Orderitem, order=order, product=product, shop=shop,
                                   quantity=random.choice(range(1, 10)))
            summ += orderitem.quantity * Availability.objects.get(shop=shop, product_info=product).price
    return {
        'summ': summ,
        'order': order
    }

###Проходят проверки на то, что по URL можно получить данные по одному и нескольким продуктам,
# а также то, что неавторизованные пользователи и пользователи типа "покупатель" не видят параметр "price_rrc"
@pytest.mark.django_db
def test_get_products(client, product_bakery, shop_client, buyer_client):
    products = product_bakery(_quantity=10)
    response = client.get('/products/')
    auth_response = shop_client.get('/products/')
    buyer_response = buyer_client.get('/products/')
    assert len(products) == len(response.data)
    for product in response.data:
        assert product.get('price_rrc') == None
    for item in auth_response.data:
        assert float(item.get('price_rrc')) == float(Productinfo.objects.get(name=item['name']).price_rrc)
    for product in buyer_response.data:
        assert product.get('price_rrc') == None

@pytest.mark.django_db
def test_get_single_products(client, product_bakery, shop_client, buyer_client):
    products = product_bakery(_quantity=10)
    for product in products:
        assert product.name == client.get(f'/products/{product.id}/').data['name']
        assert client.get(f'/products/{product.id}/').data.get('price_rrc') == None
        assert float(product.price_rrc) == float(shop_client.get(f'/products/{product.id}/').data['price_rrc'])
        assert buyer_client.get(f'/products/{product.id}/').data.get('price_rrc') == None

###проверка ошибки получения корзины неавторизованного пользователя
@pytest.mark.django_db
def test_unauthorized_get_basket(client, buyer_client):
    response = client.get('/basket/')
    auth_response = buyer_client.get('/basket/')
    assert response.status_code == 401
    assert auth_response.status_code == 200
    assert auth_response.data == {'status': 'shoppingcart is empty'}

###Проверка создания корзины
@pytest.mark.django_db
def test_create_basket(product_bakery, client, buyer_client):
    shop = baker.make(Shop)
    products = product_bakery(_quantity=5)
    for product in products:
        response = client.post('/basket/', data={
            'product': product.id,
            'shop': shop.id,
            'quantuty': 1
        })
        assert response.status_code == 401

    for product in products:
        response = buyer_client.post('/basket/', data={
            'product': product.id,
            'shop': shop.id,
            'quantuty': 1
        })
        assert response.status_code == 200
##Проверка получения корзины
@pytest.mark.django_db
def test_gt_basket(client, user, buyer_client, create_basket):
    summ = create_basket['summ']
    order = create_basket['order']
    print(order)
    response = client.get('/basket/')
    #проверка суммы корзины и вхождения всех элементов списка
    assert round(float(response.data[-1]['summ']), 2) == float(summ)
    assert len(response.data) - 1 == len(Orderitem.objects.filter(order=order.id))
    ###Проверка получения корзины другого пользователя
    assert buyer_client.get('/basket/').data['status'] == 'shoppingcart is empty'
    for item in Orderitem.objects.filter(order=order.id):
        assert buyer_client.get(f'/basket/{item.id}/').status_code == 403
        ##Проверка изменения корзины
        number = random.choice(range(1, 10))
        response = client.patch(f'/basket/{item.id}/', data={
            'quantity': number
        })
        assert response.status_code == 202
        assert response.data['quantity'] == number
        buyer_response = buyer_client.patch(f'/basket/{item.id}/', data={
            'quantity': number})
        assert buyer_response.status_code == 403
        ###Проверка удаления корзины
        del_response = buyer_client.delete(f'/basket/{item.id}/')
        assert del_response.status_code == 403
        delete_basket = client.delete(f'/basket/{item.id}/')
        assert delete_basket.status_code == 204
    assert len(Orderitem.objects.filter(order=order)) == 0
    assert Order.objects.get(id=order.id) != None
    assert buyer_client.delete('/basket/').status_code == 204
    assert Order.objects.get(id=order.id) != None
    assert client.delete('/basket/').status_code == 204
    assert Order.objects.filter(id=order.id).exists() == False