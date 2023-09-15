import pytest
from model_bakery import  baker

from app.backend.models import CustomUser, Order, Category, Product, Adress


@pytest.mark.django_db
def test_create_users():
    users = baker.make(CustomUser, _quantity=10)
    assert len(users) == 10
    new_user = CustomUser.objects.create_user(email='new_user@mail.com', password='password')
    assert new_user.email == 'new_user@mail.com'

@pytest.mark.django_db
def test_create_superuser():
    superuser = CustomUser.objects.create_superuser(email='super@mail.com', password='password')
    assert superuser.is_superuser == True

@pytest.mark.django_db
def create_superuser_fail():
    superuser = CustomUser.objects.create_superuser(email='new_super@mail.com', password='password', is_superuser=False)

def test_mytest():
    with pytest.raises(ValueError):
        create_superuser_fail()

@pytest.mark.django_db
def test_create_orders():
    orders = baker.make(Order, _quantity=10)
    for order in orders:
        assert str(order) == f'Заказ №{order.id}'

@pytest.mark.django_db
def test_categories():
    cat = baker.make(Category, _quantity=10)
    for category in cat:
        assert str(category) == f'{category.name}'

@pytest.mark.django_db
def test_product():
    products = baker.make(Product, _quantity=10)
    for product in products:
        assert str(product) == f'{product.model}'

@pytest.mark.django_db
def test_adress():
    adresses = baker.make(Adress, _quantity=10)
    for adress in adresses:
        assert str(adress) == f"Город: {adress.city}, улица: {adress.street}, дом {adress.home}"