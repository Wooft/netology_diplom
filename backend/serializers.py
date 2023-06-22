from rest_framework import serializers
from backend.models import Shop, Product, Category, Productinfo, CustomUser, Order, Orderitem
from rest_framework.exceptions import ValidationError


class Shopserializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = "__all__"

class CategorySerializer(serializers.ModelSerializer):
    shops = Shopserializer(many=True, read_only=True)
    class Meta:
        model = Category
        fields = ['id', 'shops', 'name']


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['model', 'category']

class ProductInfoSerializer(serializers.ModelSerializer):
    product = ProductSerializer(many=True, read_only=True)
    shop = Shopserializer(many=True, read_only=True)

    class Meta:
        model = Productinfo
        fields = ['product', 'shop', 'name', 'quantity', 'price']

class CustomUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = CustomUser
        fields = ["first_name", "last_name", "username", "surname", "email", "company", "position", "type", "password"]

class OrderSerializer(serializers.ModelSerializer):

    class Meta:
        model = Order
        fields = ["id", "dt", "status"]

class OrderitemSerizlizer(serializers.ModelSerializer):
    # order = OrderSerializer(many=False, read_only=False)
    # product = ProductSerializer(many=False, read_only=True)
    # shop = Shopserializer(many=False, read_only=True)
    class Meta:
        model = Orderitem
        fields = ["id", "order", "product", "shop", "quantity"]
