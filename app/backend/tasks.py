from backend.models import Shop, Category, Product, Productinfo, Availability, Parameter, ProductParameter
from celery import shared_task



@shared_task()
def yaml_upload_task(data, filename):
    # Создание нового магазина или получение уже созданного
    newshop = Shop.objects.get_or_create(
        name=data['shop'],
        filename=filename
    )
    # добавление категорий
    for category in data['categories']:
        newcat = Category.objects.get_or_create(
            id=category['id'],
            name=category['name']
        )
        # Добавление магазина в поле many-to-many field
        newcat[0].shops.add(newshop[0])
    # создание нового продукта
    for product in data['goods']:
        category = Category.objects.get(id=product['category'])
        newproduct = Product.objects.get_or_create(model=product['model'],
                                                   category=category)
        new_info = Productinfo.objects.get_or_create(
            id=product['id'],
            product=newproduct[0],
            name=product['name'],
            price_rrc=product['price_rrc'],
        )
        set_price = Availability.objects.get_or_create(
            product_info=new_info[0],
            shop=newshop[0],
            price=product['price'],
            quantity=product['quantity']
        )
        # Создание параметров
        for name, value in product['parameters'].items():
            newparameter = Parameter.objects.get_or_create(
                name=name
            )
            ProductParameter.objects.get_or_create(
                product_info=new_info[0],
                parameter=newparameter[0],
                value=value
            )