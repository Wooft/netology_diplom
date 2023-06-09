from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ViewSet
from backend.models import Shop, Category, Product, Productinfo, Parameter, ProductParameter, CustomUser, Order, \
    Orderitem, Contact
from backend.permissions import IsOwner
from backend.serializers import Shopserializer, CategorySerializer, ProductInfoSerializer, CustomUserSerializer, \
    OrderSerializer, ContactSerializer, ArdressSerializer, OrderitemGetSerizlizer, \
    OrderItemCreateSerializer, ProductSerializer
from django.contrib.auth.hashers import make_password
from rest_framework import status
import yaml
from yaml.loader import SafeLoader
import re
from rest_framework.permissions import IsAuthenticated

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
    #В serializer_class находится сериалайзер, который отвечает за вывод иноформации
    serializer_class = OrderitemGetSerizlizer
    permission_classes = [IsAuthenticated, IsOwner]
    http_method_names = ["get", "post", "delete"]

    #Получение информации о текущей корзине
    #Доступна только зарегистрированным пользователям
    def list(self, request, *args, **kwargs):
        #Получение заказа со статусом "в корзине". Если в базе данных несколько таких заказов, то получает последний созданный
        basket = Order.objects.filter(user=request.user, status="basket").order_by("-dt")
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
        if Order.objects.filter(user=request.user, status="basket").exists():
            #Если да, то он добавляется в request.data"
            request.data["order"] = Order.objects.filter(user=request.user, status="basket")[0].id
            #Проверка на наличие Orderitem в базе данных
            if Orderitem.objects.filter(order=request.data["order"], product=request.data["product"], shop=request.data["shop"]).exists():
                instance = Orderitem.objects.filter(order=request.data["order"], product=request.data["product"])[0]
                request.data["quantity"] = request.data["quantity"] + instance.quantity
                #Для создания новых объектов корзины используется OrderItemCreateSerializer, который принимает для создания PK Shop, Product, Order
                serializer = OrderItemCreateSerializer(instance, data=request.data)
                serializer.is_valid(raise_exception=True)
                self.perform_update(serializer)
                return Response(serializer.data)
            else:
                serializer = OrderItemCreateSerializer(data=request.data)
                if serializer.is_valid(raise_exception=True):
                    serializer.save()
                    return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            #Если такого заказа нет, то создается новая корзина и заполняется указанным товаром
            request.data['order'] = Order.objects.create(user=request.user, status="basket").id
            serializer = OrderItemCreateSerializer(data=request.data)
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
# Функция, которая очищает корзину
    def delete(self, request):
        #Проверка наличия заказа или нескольких заказов, соответсвующих пользователю, со статусом "в корзине"
        if Order.objects.filter(user=request.user, status="basket").exists():
            #Заказы сохраняются в список
            basket = Order.objects.filter(user=request.user, status="basket")
            #Для каждого заказа из списка
            for element in basket:
                #Получается список позиций Orderitems
                items = Orderitem.objects.filter(order=element)
                for item in items:
                    #Каждая позиция в списке удаляется
                    item.delete()
                #Затем удаляется заказ со статусом "В корзине"
                element.delete()
            return Response({"status": "Корзина очищена"},
                            status=status.HTTP_200_OK)
        #Если заказа со статусом "в корзине" не существует, пользователь получает сообщение что корзина пуста
        else:
            return Response({"status": "Корзина уже пуста"},
                            status=status.HTTP_200_OK)

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
                category = Category.objects.get(id=product['category'])
                newproduct = Product.objects.get_or_create(model=product['model'],
                                                           category=category)
                new_info=Productinfo.objects.get_or_create(
                    id=product['id'],
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
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ConfirmOrderViewset(ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    http_method_names = ["post", "get"]

    #Используется для формы "спасибо за заказ"
    def retrieve(self, request, *args, **kwargs):
        order = self.get_object()
        #Тут возвращается номер заказа
        #Тут возвращаются детали заказа
        positions = OrderitemGetSerizlizer(Orderitem.objects.filter(order=order), many=True)
        #Тут возвращаются детали получаетля
        contacts = ContactSerializer(Contact.objects.get(order=order))
        print(contacts)
        return Response({"order_number": order.id,
                         "details": positions.data,
                         "contacts": contacts.data})

    def create(self, request, *args, **kwargs):
        order = Order.objects.get(id=request.data["contact"]["order"])
        if order.status == 'new':
            request.data["adress"]["order"] = order.id
            contact = ContactSerializer(data=request.data["contact"])
            adress = ArdressSerializer(data=request.data["adress"])
            if contact.is_valid(raise_exception=True) and adress.is_valid(raise_exception=True):
                order.status = "confirmed"
                contact.save()
                adress.save()
                order.save()
                return Response({"status": "all_valid", f"Заказ №{order.id}": f"{order.status}"},
                                status=status.HTTP_201_CREATED)

        else:
            return Response({"status": "Заказ уже оформлен"},status=status.HTTP_404_NOT_FOUND)


class OrderViewSet(ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated, IsOwner]
    http_method_names = ['get', ]

    #Метод list возвращает список заказов пользователя, за исключением заказов со статусом "в корзине"
    def list(self, request, *args, **kwargs):
        orders = Order.objects.filter(user=request.user).exclude(status='basket')
        seriazlizer = self.serializer_class(orders, many=True)
        for order in seriazlizer.data:
            sum = 0
            for item in order['items']:
                sum += Orderitem.objects.get(id=item).product.price * Orderitem.objects.get(id=item).quantity
            order.pop('items')
            #В заказ включается поле "сумма"
            order['summ'] = sum
        return Response(seriazlizer.data, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        data = self.serializer_class(self.get_object()).data
        templist = []
        for element in data['items']:
            item = OrderitemGetSerizlizer(Orderitem.objects.get(id=element)).data
            item['summ'] = float(item['product']['price']) * item['quantity']
            templist.append(item)
        data['items'] = templist
        data['contact'] = ContactSerializer(Contact.objects.get(order=data['id'])).data
        data['adress'] = ArdressSerializer(self.get_object().adress.get()).data
        return Response(data, status=status.HTTP_200_OK)


