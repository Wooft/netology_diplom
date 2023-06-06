from rest_framework import serializers
from backend.models import Shop, Product, Category
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


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['',]