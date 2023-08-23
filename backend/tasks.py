from rest_framework.response import Response
import re
import yaml
from yaml.loader import SafeLoader
from rest_framework import status
from backend.models import Shop, Category, Product, Productinfo, Availability, Parameter, ProductParameter
from celery import shared_task
from time import sleep


@shared_task()
def yaml_upload_task(request):
    pattern = r'(\.[A-Za-z]*)'
    # Выброс ошибки, если отсуствует файл - вложение
    if request.FILES.get('file') == None:
        return Response(
            {'status': 'please load correct yaml file'}, status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
        )
    # Проверка на соответствие типа файла. Если это не yaml - выбрасывается ошибка
    elif re.search(pattern=pattern, string=request.FILES['file'].name)[0] != '.yaml':
        return Response(
            {'status': 'Please load file in "yaml" format'}, status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
        )
    else:
        # прием YAML файла
        filetoload = yaml.load(request.FILES['file'].read(), Loader=SafeLoader)
        # Создание нового магазина или получение уже созданного
        newshop = Shop.objects.get_or_create(
            name=filetoload['shop'],
            filename=request.FILES['file'].name
        )
        # добавление категорий
        for category in filetoload['categories']:
            newcat = Category.objects.get_or_create(
                id=category['id'],
                name=category['name']
            )
            # Добавление магазина в поле many-to-many field
            newcat[0].shops.add(newshop[0])
        # создание нового продукта
        for product in filetoload['goods']:
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
        return Response({'status': 'complete'}, status=status.HTTP_200_OK)

@shared_task()
def wait():
    sleep(20)
    return ({'status': 'ok'})