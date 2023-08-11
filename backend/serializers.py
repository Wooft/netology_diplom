from rest_framework import serializers
from backend.models import Shop, Product, Category, Productinfo, CustomUser, Order, Orderitem, Contact, Adress, \
    Parameter, ProductParameter, Availability
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

class ParameterSerializer(serializers.ModelSerializer):

    class Meta:
        model = Parameter
        fields = ['name']

class AvailableSerializer(serializers.ModelSerializer):
    shop = Shopserializer(many=False)
    class Meta:
        model = Availability
        fields = ['shop', 'price', 'quantity']

class ProductParameterSerializer(serializers.ModelSerializer):
    parameter = ParameterSerializer(many=False)
    class Meta:
        model = ProductParameter
        fields = ['parameter', 'value']

class ProductInfoSerializer(serializers.ModelSerializer):
    availability = AvailableSerializer(many=True)
    parameters = ProductParameterSerializer(many=True)
    class Meta:
        model = Productinfo
        fields = ['id', 'name', 'availability', 'parameters', 'price_rrc']

class ProducInfoForBuyerSerializer(serializers.ModelSerializer):
    availability = AvailableSerializer(many=True)
    parameters = ProductParameterSerializer(many=True)

    class Meta:
        model = Productinfo
        fields = ['id', 'name', 'availability', 'parameters']


class CustomUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = CustomUser
        fields = ["id", "first_name", "last_name", "username", "surname", "email", "company", "position", "type", "password"]


class OrderitemGetSerizlizer(serializers.ModelSerializer):
    product = ProductInfoSerializer(many=False, read_only=True)
    shop = Shopserializer(many=False, read_only=True)
    class Meta:
        model = Orderitem
        fields = ("id", "order", "product", "shop", "quantity")
        depth = 1

class BasketSerializer(serializers.ModelSerializer):
    product = ProductInfoSerializer(many=False, read_only=True)
    shop = Shopserializer(many=False, read_only=True)
    class Meta:
        model = Orderitem
        fields = ("id", "product", "shop", "quantity")

class OrderItemCreateSerializer(serializers.ModelSerializer):


    class Meta:
        model = Orderitem
        fields = "__all__"

class ArdressSerializer(serializers.ModelSerializer):

    class Meta:
        model = Adress
        fields = '__all__'

class OrderSerializer(serializers.ModelSerializer):
    # items = OrderitemGetSerizlizer(many=True, read_only=True)
    class Meta:
        model = Order
        fields = ["id", "dt", "status", "items"]
        depth = 2

class ContactSerializer(serializers.ModelSerializer):

    class Meta:
        model = Contact
        fields = '__all__'