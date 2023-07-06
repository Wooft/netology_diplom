from rest_framework import serializers
from backend.models import Shop, Product, Category, Productinfo, CustomUser, Order, Orderitem, Contact, Adress
from rest_framework.exceptions import ValidationError


class Shopserializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
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

    class Meta:
        model = Productinfo
        fields = ['name', 'price']
class CustomUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = CustomUser
        fields = ["first_name", "last_name", "username", "surname", "email", "company", "position", "type", "password"]


class OrderitemGetSerizlizer(serializers.ModelSerializer):
    product = ProductInfoSerializer(many=False, read_only=True)
    shop = Shopserializer(many=False, read_only=True)
    class Meta:
        model = Orderitem
        fields = ("id", "order", "product", "shop", "quantity")

class OrderItemCreateSerializer(serializers.ModelSerializer):


    class Meta:
        model = Orderitem
        fields = "__all__"

class ArdressSerializer(serializers.ModelSerializer):

    class Meta:
        model = Adress
        fields = '__all__'

class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ["id", "dt", "status", "items"]

class ContactSerializer(serializers.ModelSerializer):

    class Meta:
        model = Contact
        fields = '__all__'