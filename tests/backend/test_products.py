import pytest
from rest_framework.test import APIClient
from model_bakery import baker

from backend.models import Product, Productinfo


@pytest.fixture()
def client():
    return APIClient()

@pytest.fixture()
def product_bakery():
    def factory(*args, **kwargs):
        return baker.make(Productinfo, *args, **kwargs)
    return factory

@pytest.mark.django_db
def test_get_products(client, product_bakery):
    products = product_bakery(_quantity=10)
    response = client.get('/products/')
    assert len(products) == len(response.data)

@pytest.mark.django_db
def test_get_single_products(client, product_bakery):
    products = product_bakery(_quantity=10)
    for product in products:
        assert product.name == client.get(f'/products/{product.id}/').data['name']