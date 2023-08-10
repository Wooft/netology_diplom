from django.db import models
from django.contrib.auth.models import AbstractUser, User, BaseUserManager, PermissionsMixin
from django.contrib.auth.hashers import make_password

USER_TYPE_CHOICES = (
    ('shop', 'магазин'),
    ('buyer', 'покупатель')
)

ORDER_STATE_CHOICES = (
    ('basket', 'Корзина'),
    ('new', 'новый'),
    ('confirmed', 'Подтвержен')
)

class UserManager(BaseUserManager):
    use_in_migrations = True
    def _create_user(self, email, password, **extra_fields):
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_superuser', False)
        extra_fields.__setattr__('type', 'buyer')
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser!!!!')

        return self._create_user(email, password, **extra_fields)


class CustomUser(AbstractUser, PermissionsMixin):

    REQUIRED_FIELDS = ['username', ]
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
    model = models.CharField(verbose_name='Модель', max_length=50, unique=True)
    category = models.ForeignKey(Category, verbose_name='Категории', on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.model}'

class Productinfo(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='info')
    shop = models.ManyToManyField(Shop, through='Availability')
    name = models.CharField(verbose_name='Название', max_length=50)
    price_rrc = models.DecimalField(verbose_name='РРЦ',
                                    decimal_places=2,
                                    max_digits=10)


class Orderitem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Productinfo, on_delete=models.CASCADE, related_name='product_in_order')
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=0)

class Parameter(models.Model):
    name = models.CharField(verbose_name='Название', max_length=100, unique=True)
class ProductParameter(models.Model):
    product_info = models.ForeignKey(Productinfo, on_delete=models.CASCADE, related_name='parameters')
    parameter = models.ForeignKey(Parameter, on_delete=models.CASCADE, related_name='product_info')
    value = models.CharField()
### Таблица "Наличие", через нее реализована связь многие-ко-многим таблиц "product_info" и "shop", сожержит информацию о актуальных ценах и наличии товара
class Availability(models.Model):
    product_info = models.ForeignKey(Productinfo, on_delete=models.CASCADE, related_name='availability')
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='price')
    price = models.DecimalField(verbose_name='Цена', decimal_places=2, max_digits=10)
    quantity = models.PositiveIntegerField(verbose_name='Количество')

#Модель для сохранения адреса пользователя
class Adress(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='adress')
    city = models.CharField(max_length=50, verbose_name="Город", blank=False, null=False)
    street = models.CharField(max_length=150, verbose_name="Улица", blank=False, null=False)
    home = models.CharField(verbose_name="Дом", blank=False, null=False)
    structure = models.CharField(max_length=10, verbose_name="Корпус", blank=True)
    building = models.CharField(max_length=10, verbose_name="Строение", blank=True)
    apartment = models.CharField(max_length=10, verbose_name="Квартира / Офис", blank=True)
    is_save = models.BooleanField(default=False)

    def __str__(self):
        return f"Город: {self.city}, улица: {self.street}, дом {self.home}"

#Модель для сохранения контактного лица в заказе
class Contact(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, verbose_name="Имя", null=False)
    last_name = models.CharField(max_length=150, verbose_name="Фамилия")
    surname = models.CharField(max_length=150, verbose_name="Отчество")
    email = models.EmailField(verbose_name="Email")
    phone = models.CharField(max_length=12, verbose_name="Номер телефона", null=False)
