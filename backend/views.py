from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ViewSet
from backend.models import Shop, Category, Product, Productinfo, Parameter, ProductParameter, CustomUser, Order, \
    Orderitem
from backend.serializers import Shopserializer, CategorySerializer, ProductInfoSerializer, CustomUserSerializer, \
    OrderSerializer, OrderitemSerizlizer
from django.contrib.auth.hashers import make_password
from rest_framework import status
import yaml
from yaml.loader import SafeLoader
import re
from rest_framework.permissions import IsAuthenticated
from django.db.utils import IntegrityError
from django.forms.models import model_to_dict

class ShopViewSet(ModelViewSet):
    queryset = Shop.objects.all()
    serializer_class = Shopserializer

class CategoryViewSet(ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

#Вьюха для работы корзины. На вход принимает запрос с Applicetion/data в формате JSON, содержащий ключи:
# product - id продукта, добавляемого в корзину
# shop - id магазина, в котором выбирается продукт
# quantity - количество единиц добавляемого продукта
class ShoppingCartViewSet(ModelViewSet):
    queryset = Orderitem.objects.all()
    serializer_class = OrderitemSerizlizer
    permission_classes = [IsAuthenticated, ]
    http_method_names = ["get", "post", "delete"]

    #Получение информации о текущей корзине
    #Доступна только зарегистрированным пользователям
    def list(self, request, *args, **kwargs):
        #Получение заказа со статусом "в корзине". Если в базе данных несколько таких заказов, то получает последний созданный
        basket = Order.objects.filter(user=request.user, status="in_shoppingcart").order_by("-dt")
        #Если заказа со статусом "в корзине" нет в базе данных - выдается статус что корзина пуста
        if len(basket) == 0:
            return Response({"status": "shoppingcart is empty"},
                            status=status.HTTP_200_OK)
        else:
            qs = Orderitem.objects.filter(order=basket[0])
        return Response(self.serializer_class(qs, many=True).data,status=status.HTTP_200_OK)

    #Заполнение корзины, создание заказа со статусом (в корзине)
    def create(self, request, *args, **kwargs):
        #Проверка на то, что в БД есть заказ со статусом "в корзине"
        if Order.objects.filter(user=request.user, status="in_shoppingcart").exists():
            #Если да, то он добавляется в request.data"
            request.data["order"] = Order.objects.filter(user=request.user, status="in_shoppingcart")[0].id
            #Проверка на наличие Orderitem в базе данных
            if Orderitem.objects.filter(order=request.data["order"], product=request.data["product"], shop=request.data["shop"]).exists():
                instance = Orderitem.objects.filter(order=request.data["order"], product=request.data["product"])[0]
                request.data["quantity"] = request.data["quantity"] + instance.quantity
                serializer = self.get_serializer(instance, data=request.data)
                serializer.is_valid(raise_exception=True)
                self.perform_update(serializer)
                return Response(serializer.data)
            else:
                serializer = self.serializer_class(data=request.data)
                if serializer.is_valid(raise_exception=True):
                    serializer.save()
                    return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            request.data['order'] = Order.objects.create(user=request.user, status="in_shoppingcart").id
            serializer = self.serializer_class(data=request.data)
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
# Функция, которая очищает корзину
    def delete(self, request):
        #Проверка наличия заказа или нескольких заказов, соответсвующих пользователю, со статусом "в корзине"
        if Order.objects.filter(user=request.user, status="in_shoppingcart").exists():
            #Заказы сохраняются в список
            basket = Order.objects.filter(user=request.user, status="in_shoppingcart")
            #Для каждого заказа из списка
            for element in basket:
                #Получается список позиций Orderitems
                items = Orderitem.objects.filter(order=element)
                for item in items:
                    #Каждая позиция в списке удаляется
                    item.delete()
                #Затем удаляется заказ со статусом "В корзине"
                element.delete()
            return Response({"status": "shoppingcart empty"},
                            status=status.HTTP_200_OK)
        #Если заказа со статусом "в корзине" не существует, пользователь получает сообщение что корзина пуста
        else:
            return Response({"status": "shoppingcart is already empty"},
                            status=status.HTTP_200_OK)


class OrdersView(ViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

class ProductInfoViewSet(ModelViewSet):
    queryset = Productinfo.objects.all()
    serializer_class = ProductInfoSerializer
    http_method_names = ['post', ]
#Вьюха для загрузки информации из Yaml файла
class YamlUploadView(APIView):
    #Обрабатывает метод POST
    def post(self, request):
        pattern = '(\.[A-Za-z]*)'
        #Выброс ошибки, если отсуствует файл
        if request.FILES.get('file') == None:
            return Response(
                {'status': 'please load correct yaml file'}, status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
            )
        #Проверка на соответствие типа файла. Если это не yanl - выбрасывается ошибка
        elif re.search(pattern=pattern, string=request.FILES['file'].name)[0] != '.yaml':
            return Response(
                {'status': 'Please load file in "yaml" format'}, status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
            )
        else:
            #прием YAML файла
            filetoload = yaml.load(request.FILES['file'].read(), Loader=SafeLoader)
            #Создание нового магазина или получение уже созданного
            newshop = Shop.objects.get_or_create(
                name=filetoload['shop'],
                filename=request.FILES['file'].name
            )
            #добавление категорий
            for category in filetoload['categories']:
                newcat = Category.objects.get_or_create(
                    id=category['id'],
                    name=category['name']
                )
                #Добавление магазина в поле many-to-many field
                newcat[0].shops.add(newshop[0])
            #создание нового продукта
            for product in filetoload['goods']:
                newproduct = Product.objects.get_or_create(model=product['model'],
                                                           category=newcat[0])
                new_info=Productinfo.objects.get_or_create(
                    product=newproduct[0],
                    shop=newshop[0],
                    name=product['name'],
                    quantity=product['quantity'],
                    price=product['price'],
                    price_rrc=product['price_rrc'],
                )
                #Создание параметров
                for name, value in product['parameters'].items():
                    newparameter = Parameter.objects.get_or_create(
                        name=name
                    )
                    newparvalue = ProductParameter.objects.get_or_create(
                        product_info=new_info[0],
                        parameter=newparameter[0],
                        value=value
                    )
            return Response({
                'status': 'ok'
            })

class RegisterUser(APIView):
    def post(self, request):
        #проверка того, что введенные пароли совпадают
        if request.data['password'] != request.data['repeatpassword']:
            return Response({
                'status': "password don't match"
            },status=400)
        else:
            #Если пароль введен верно, то он хэшируется перед добавлением в базу данных
            request.data['password'] = make_password(request.data['password'])
            request.data.pop('repeatpassword')
        serializer = CustomUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

class ConfirmOrderViewset(ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def list(self, request, *args, **kwargs):
        pass

    def create(self, request, *args, **kwargs):
        pass