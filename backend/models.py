from django.db import models
from django.contrib.auth.models import AbstractUser


class UserManager(AbstractUser):
    pass

# Create your models here.
class Shop(models.Model):
    name = models.CharField(max_length=30, null=False)
    url = models.URLField(max_length=200)
    filename = models.CharField(max_length=100)

class Category(models.Model):
    shops = models.ManyToManyField()
    name = models.CharField(max_length=100, null=False)

class Product(models.Model):
    category = models.ForeignKey(Category)
    shop = models.ManyToManyField(Shop)

class ProductInfo(models.Model):
    product = models.ForeignKey(Product)
    shop = models.ForeignKey(Shop)
    name = models.CharField(max_length=100)
    quantuty = models.PositiveIntegerField(max_length=10)
    price = models.DecimalField(decimal_places=2)
    price_rrc=models.DecimalField(decimal_places=2)

class Parameter(models.Model):
    name=models.CharField(max_length=100)

class ProductParameter(models.Model):
    product_info=models.ForeignKey(ProductInfo)
    parameter=models.ForeignKey(Parameter)
    value=models.CharField(max_length=100)

class Order(models.Model):
    user=models.ForeignKey()
    dt=models.CharField(max_length=100)
    status=models.BooleanField()

class Orderitem(models.Model):
    order=models.ForeignKey(Order)
    product=models.ManyToManyField(Product)
    shop=models.ManyToManyField(Shop)
    quantity=models.PositiveIntegerField(max_length=100000)

class Contact(models.Model):
    type=models.CharField(max_length=100)
    user=models.ForeignKey()
    value=models.PositiveIntegerField(max_length=1000)


