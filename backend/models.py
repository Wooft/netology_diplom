from django.db import models
from django.contrib.auth.models import AbstractUser, User, BaseUserManager
from django.contrib.auth.hashers import make_password

USER_TYPE_CHOICES = (
    ('shop', 'магазин'),
    ('buyer', 'покупатель')
)

class UserManager(BaseUserManager):
    use_in_migrations = True
    def _create_user(self, email, password, **extra_fields):
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(raw_password=make_password(password))
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser!!!!')

        return self._create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):

    REQUIRED_FIELDS = ['username',]
    USERNAME_FIELD = 'email'

    objects = UserManager()

    surname = models.CharField(verbose_name='Отчество', max_length=50, blank=True, null=True)
    email = models.EmailField(unique=True, null=False)
    company = models.CharField(max_length=100, blank=True, null=True)
    position = models.CharField(max_length=100, null=True, blank=True)
    type = models.CharField(verbose_name='Тип пользователя', choices=USER_TYPE_CHOICES, max_length=5, default='buyer', blank=False, null=False)\


    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('email', )


#Модель заказа, содержит информацию о дате создания и статусе заказа
class Order(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    dt = models.DateTimeField(verbose_name="Создан",
                              auto_now_add=True)
    status = models.CharField(verbose_name='Статус заказа',
                              max_length=15)

    def __str__(self):
        return f'Заказ №{self.id}'

class Shop(models.Model):
    name = models.CharField(verbose_name='Название магазина',
                            max_length=50,
                            null=False,
                            blank=False)
    url = models.URLField(verbose_name='Ссылка на сайт магазина',
                          max_length=40,
                          unique=True,
                          blank=True)
    filename = models.CharField(verbose_name='Файл',
                                max_length=20)
    state = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.name}'

class Category(models.Model):
    shops = models.ManyToManyField(Shop, related_name='categories')
    name = models.CharField(verbose_name='Категория', max_length=50, unique=True)

    def __str__(self):
        return f'{self.name}'

class Product(models.Model):
    model = models.CharField(verbose_name='Модель', max_length=50)
    category = models.ForeignKey(Category, verbose_name='Категории', on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.model}'


class Orderitem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()

class Productinfo(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    shop = models.ForeignKey(Shop, on_delete=models.SET_NULL, null=True)
    name = models.CharField(verbose_name='Название', max_length=50)
    quantity = models.PositiveIntegerField(verbose_name='Количество')
    price = models.DecimalField(verbose_name='Цена',
                                decimal_places=2,
                                max_digits=10)
    price_rrc = models.DecimalField(verbose_name='РРЦ',
                                    decimal_places=2,
                                    max_digits=10)

class Parameter(models.Model):
    name = models.CharField(verbose_name='Название', max_length=100, unique=True)
class ProductParameter(models.Model):
    product_info = models.ForeignKey(Productinfo, on_delete=models.CASCADE)
    parameter = models.ForeignKey(Parameter, on_delete=models.CASCADE)
    value = models.CharField()