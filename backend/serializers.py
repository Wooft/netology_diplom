from rest_framework import serializers
from backend.models import Shop, Product, Category, Productinfo
from django.contrib.auth.models import User

class Shopserializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = ['id', 'name', 'url', 'filename']

class CategorySerializer(serializers.ModelSerializer):
    shops = Shopserializer(many=True, read_only=True)
    class Meta:
        model = Category
        fields = ['id', 'shops', 'name']

    def create(self, validated_data):
        print(validated_data)

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['model', 'category']

class ProductInfoSerializer(serializers.ModelSerializer):
    product = ProductSerializer(many=False, read_only=True)
    shop = Shopserializer(many=False, read_only=True)

    class Meta:
        model = Productinfo
        fields = ['product', 'shop', 'name', 'quantity', 'price']