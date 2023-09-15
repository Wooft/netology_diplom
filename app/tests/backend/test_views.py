import copy
import random
import pytest
from rest_framework.test import APIClient
from model_bakery import baker
from app.backend.models import Productinfo, CustomUser, Shop, Availability, Order, Orderitem, Contact, Adress
import tempfile


# Возвращает подготовленного пользователя для запросов от авторизованного клиента
@pytest.fixture()
def user():
    user = {
        "last_name": "lastname",
        "username": "username",
        "first_name": "firstname",
        "email": "email@mail.com",
        "password": "password",
        "repeatpassword": "password",
    }
    return user


@pytest.fixture()
def confirm_order_data():
    data = {
        "contact": {
            "order": '',
            "name": "somename",
            "last_name": "somename",
            "surname": "somename",
            "email": "somemsail@mail.com",
            "phone": "+79432567483"
        },
        "adress": {
            "city": "somecity",
            "street": "somestreet",
            "home": "somehome",
            "structure": "1",
            "building": "1",
            "apartment": "1"
        }
    }
    return data
# Возращает неавторизованный клиент
@pytest.fixture()
def unauth_client():
    return APIClient()


@pytest.fixture()
def client():
    return APIClient()


@pytest.fixture()
def auth_client(user, client):
    response = client.post(path="/register/", data=user)
    auth_client = APIClient()
    auth_client.login(username=user['email'], password=user['password'])
    return auth_client

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


# фикстура, которая возвращает авторизованный клиент
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
    client.post('/register/', data=user)
    client.login(username=user['email'], password=user['password'])
    order = baker.make(Order, status='basket', user=CustomUser.objects.get(email=user['email']))
    shops = baker.make(Shop, _quantity=2)
    products = baker.make(Productinfo, _quantity=4)
    for shop in shops:
        for product in products:
            baker.make(Availability, shop=shop, product_info=product)
            orderitem = baker.make(Orderitem, order=order, product=product, shop=shop,
                                   quantity=random.choice(range(1, 10)))
            summ += orderitem.quantity * Availability.objects.get(shop=shop, product_info=product).price
    return {
        'summ': summ,
        'order': order
    }

@pytest.fixture()
def order_bakery(user):
    def factory(*args, **kwargs):
        list_orders = []
        statuses = ['basket', 'new', 'created', 'confirmed']
        for status in statuses:
            orders = baker.make(Order, status=status, user=CustomUser.objects.get(email=user['email']), _quantity=4)
            if status == 'created' or status == 'confirmed':
                for order in orders:
                    baker.make(Contact, order=order)
                    adress = baker.make(Adress)
                    adress.order.add(order)
            list_orders.extend(orders)
        shops = baker.make(Shop, _quantity=5)
        products = baker.make(Productinfo, _quantity=10)
        for shop in shops:
            for product in products:
                baker.make(Availability, shop=shop, product_info=product)
                baker.make(Orderitem, shop=shop, product=product, order=random.choice(list_orders))
        return list_orders
    return factory
@pytest.mark.django_db
def test_myaccount(unauth_client, user, buyer_client):
    response = buyer_client.get('/myaccount/')
    assert response.status_code == 200
    response = unauth_client.get('/myaccount/')
    assert response.status_code == 401

@pytest.mark.django_db
def test_yamluploadview():
    client = APIClient()
    yaml = open("example.yaml", "rb")
    response = client.post('/yamlupload/', {"file": yaml}, format='multipart')
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    temp_file = tempfile.NamedTemporaryFile(suffix='.jpg')
    response = client.post('/yamlupload/', {"file": temp_file}, format="multipart")
    assert response.data['status'] == 'Please load file in "yaml" format'
    assert response.status_code == 415


@pytest.mark.django_db
def test_empty_post():
    client = APIClient()
    response = client.post('/yamlupload/')
    assert response.status_code == 415
    assert response.json()['status'] == 'please load correct yaml file'


# Проходят проверки на то, что по URL можно получить данные по одному и нескольким продуктам,
# а также то, что неавторизованные пользователи и пользователи типа "покупатель" не видят параметр "price_rrc"
@pytest.mark.django_db
def test_get_products(client, product_bakery, shop_client, buyer_client):
    products = product_bakery(_quantity=10)
    response = client.get('/products/')
    auth_response = shop_client.get('/products/')
    buyer_response = buyer_client.get('/products/')
    assert len(products) == len(response.data)
    for product in response.data:
        assert product.get('price_rrc') is None
    for item in auth_response.data:
        assert float(item.get('price_rrc')) == float(Productinfo.objects.get(name=item['name']).price_rrc)
    for product in buyer_response.data:
        assert product.get('price_rrc') is None


@pytest.mark.django_db
def test_get_single_products(client, product_bakery, shop_client, buyer_client):
    products = product_bakery(_quantity=10)
    for product in products:
        assert product.name == client.get(f'/products/{product.id}/').data['name']
        assert client.get(f'/products/{product.id}/').data.get('price_rrc') is None
        assert float(product.price_rrc) == float(shop_client.get(f'/products/{product.id}/').data['price_rrc'])
        assert buyer_client.get(f'/products/{product.id}/').data.get('price_rrc') is None


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
        baker.make(Availability, shop=shop, product_info=product)
    for product in products:
        response = client.post('/basket/', data={
            'product': product.id,
            'shop': shop.id,
            'quantity': 1
        })
        assert response.status_code == 401
    # проверка создания корзины с количеством товара большим, чем есть в наличии
    for product in products:
        response = buyer_client.post('/basket/', data={
            'product': product.id,
            'shop': shop.id,
            'quantity': Availability.objects.get(product_info=product.id, shop=shop).quantity + 1
        })
        assert response.status_code == 400

    for product in products:
        response_first = buyer_client.post('/basket/', data={
            'product': product.id,
            'shop': shop.id,
            'quantity': 1
        })
        response_two = buyer_client.post('/basket/', data={
            'product': product.id,
            'shop': shop.id,
            'quantity': Availability.objects.get(product_info=product.id, shop=shop).quantity + 1
        })

        assert response_first.status_code == 200
        assert response_two.status_code == 400

    for product in products:
        response = buyer_client.post('/basket/', data={
            'product': product.id,
            'shop': shop.id,
            'quantity': 1
        })
        assert response.status_code == 202

##Проверка получения корзины
@pytest.mark.django_db
def test_get_basket(client, user, buyer_client, create_basket):
    summ = create_basket['summ']
    order = create_basket['order']
    response = client.get('/basket/')
    # проверка суммы корзины и вхождения всех элементов списка
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
    client.logout()


### Тестирование подтверждаения заказа
@pytest.mark.django_db
def test_confirm_order(auth_client, buyer_client, create_basket, unauth_client):
    basket = create_basket['order']
    buyer_response = buyer_client.patch(f'/orders/{basket.id}/', data={
        'status': 'new'
    })
    unauth_response = unauth_client.patch(f'/orders/{basket.id}/', data={
        'status': 'new'
    })
    assert buyer_response.status_code == 403
    assert unauth_response.status_code == 401
    auth_response = auth_client.patch(f'/orders/{basket.id}/', data={
        'status': 'new'
    })
    assert auth_response.status_code == 200
    assert Order.objects.get(id=basket.id).status == 'new'


@pytest.mark.django_db
def test_confirm_order(auth_client, unauth_client, order_bakery, confirm_order_data):
    orders = order_bakery()
    data = confirm_order_data
    for order in orders:
        data['contact']['order'] = order.id
        response = auth_client.post('/confirm_order/', data=data)
        unauth_response = unauth_client.post('confirm_order', data=data)
        assert unauth_response.status_code == 404
        if order.status == 'new':
            assert response.status_code == 201
        else:
            assert response.status_code == 204
    new_orders = order_bakery()
    for order in new_orders:
        if order.status == 'new':
            for item in order.items.all():
                data['contact']['order'] = order.id
                item.quantity = Availability.objects.get(product_info=item.product, shop=item.shop).quantity + 1
                item.save()
                response = auth_client.post('/confirm_order/', data=data)
                assert response.status_code == 400
                assert Order.objects.get(id=order.id).status == 'new'

    #Тест на ответ, если количество товара в заказе больше, чем количество товара в наличии
    order = baker.make(Order, status='new')
    data['contact']['order'] = order.id
    for contact in data['contact']:
        wrong_data = copy.deepcopy(data)
        wrong_data['contact'].pop(contact)
        response = auth_client.post('/confirm_order/', data=wrong_data)
        if contact == 'surname':
            assert response.status_code == 201
            order.status == 'new'
            order.save()
        else:
            assert response.status_code == 400

###Тест на получение истории заказов
@pytest.mark.django_db
def test_history_orders(auth_client, unauth_client, order_bakery, buyer_client):
    orders = order_bakery()
    response = unauth_client.get('/orders/')
    assert response.status_code == 401
    response = auth_client.get('/orders/')
    print(response)
    assert response.status_code == 200
    for order in response.data:
        assert order['status'] != 'basket'
    assert len(Order.objects.all().exclude(status='basket')) == len(response.data)
    for order in orders:
        buyer_response = buyer_client.get(f'/orders/{order.id}/')
        assert buyer_response.status_code == 403
        response = auth_client.get(f'/orders/{order.id}/')
        assert response.status_code == 200
        if order.status == 'created':
            assert order.adress.all()[0].city == response.data['adress']['city']
            assert order.contact.all()[0].name == response.data['recipient']['name']
