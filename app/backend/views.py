from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from backend.models import Productinfo, Order, \
    Orderitem, Contact, Availability, Adress
from backend.permissions import BasketOwner, IsOwner
from backend.serializers import ProductInfoSerializer, CustomUserSerializer, \
    OrderSerializer, ContactSerializer, ArdressSerializer, OrderitemGetSerizlizer, \
    OrderItemCreateSerializer, BasketSerializer, ProducInfoForBuyerSerializer
from django.contrib.auth.hashers import make_password
from rest_framework import status
import yaml
from yaml.loader import SafeLoader
import re
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiExample, OpenApiParameter
from backend.tasks import yaml_upload_task


# Вьюха для работы корзины. На вход принимает запрос с Applicetion/data в формате JSON, содержащий ключи:
# product - id продукта, добавляемого в корзину
# shop - id магазина, в котором выбирается продукт
# quantity - количество единиц добавляемого продукта
@extend_schema(tags=['Orders', ])
@extend_schema_view(
    list=extend_schema(
        summary='Получить содержимое корзины',
    ),
    create=extend_schema(
        summary='Добавление товара в корзину'
    ),
    partial_update=extend_schema(
        summary='Обновление количества товара в корзине'
    ),
    destroy=extend_schema(summary='Удаление позиции из корзины'),
    retrieve=extend_schema(summary='Получение информации по отдельной позиции товара в корзине')
)
class BasketViewSet(ModelViewSet):
    queryset = Orderitem.objects.all()
    # В serializer_class находится сериалайзер, который отвечает за вывод иноформации
    serializer_class = BasketSerializer
    permission_classes = [IsAuthenticated, BasketOwner]
    http_method_names = ["get", "post", "delete", "patch"]

    # Получение информации о текущей корзине
    # Доступна только зарегистрированным пользователям
    @extend_schema()
    def list(self, request, *args, **kwargs):
        """Получение заказа со статусом "в корзине". Если в базе данных несколько таких заказов, то получает последний созданный.
        Если заказа со статусом "в корзине" нет в базе данных - выдается статус, что корзина пуста """
        basket = Order.objects.filter(user=request.user, status="basket").order_by("-dt")
        if len(basket) == 0:
            return Response({"status": "shoppingcart is empty"},
                            status=status.HTTP_204_NO_CONTENT)
        else:
            summ = 0
            delivery_price = 0
            qs = Orderitem.objects.filter(order=basket[0])
            data = self.serializer_class(qs, many=True).data
            for item in data:
                for shop in item["product"]["availability"]:
                    if shop["shop"]["id"] == item["shop"]["id"]:
                        item["product"]["price"] = shop["price"]
                        summ += float(shop["price"]) * float(item["quantity"])
                item["product"].pop("availability")
            total = delivery_price + summ
            if request.user.type != 'shop':
                for elements in data:
                    elements['product'].pop('price_rrc')
            data.append({"summ": summ,
                         "delivery_price": delivery_price,
                         "total": total})
        return Response(data, status=status.HTTP_200_OK)

    # Заполнение корзины, создание заказа со статусом (в корзине)
    def create(self, request, *args, **kwargs):
        # Проверка на то, что в БД есть заказ со статусом "в корзине"
        if Order.objects.filter(user=request.user, status="basket").exists():
            # Если да, то он добавляется в request.data"
            request.data["order"] = Order.objects.filter(user=request.user, status="basket")[0].id

            # Проверка на наличие Orderitem в базе данных
            if Orderitem.objects.filter(order=request.data["order"], product=request.data["product"],
                                        shop=request.data["shop"]).exists():
                instance = Orderitem.objects.filter(order=request.data["order"], product=request.data["product"],
                                                    shop=request.data["shop"])[0]
                # Проверка того что в указанном магазине находится достаточное количество товара в наличии
                request.data["quantity"] = int(request.data["quantity"]) + instance.quantity
                if Availability.objects.get(shop=instance.shop, product_info=instance.product).quantity >= request.data['quantity']:
                    # Для создания новых объектов корзины используется OrderItemCreateSerializer, который принимает для создания PK Shop, Product, Order
                    serializer = OrderItemCreateSerializer(instance, data=request.data)
                    serializer.is_valid(raise_exception=True)
                    self.perform_update(serializer)
                    return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
                else:
                    return Response({'status': 'В данном магазине нет такого количества товара'},
                                    status.HTTP_400_BAD_REQUEST)
            else:
                serializer = OrderItemCreateSerializer(data=request.data)
                if serializer.is_valid(raise_exception=True):
                    serializer.save()
                    return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            if Availability.objects.get(shop=request.data['shop'], product_info=request.data['product']).quantity >= int(
                    request.data['quantity']):
                request.data['order'] = Order.objects.create(user=request.user, status="basket").id
                serializer = OrderItemCreateSerializer(data=request.data)
                if serializer.is_valid(raise_exception=True):
                    serializer.save()
                    return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response({'status': 'В данном магазине нет такого количества товара'},
                                status.HTTP_400_BAD_REQUEST)

    @extend_schema(parameters=OpenApiParameter(
        name='quantity',
        type=int,
        description='Количество товара в корзине'
    ))
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.serializer_class(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    """Тест"""
    
    # Функция, которая очищает корзину
    def delete(self, request):
        # Проверка наличия заказа или нескольких заказов, соответсвующих пользователю, со статусом "в корзине"
        if Order.objects.filter(user=request.user, status="basket").exists():
            # Заказы сохраняются в список
            basket = Order.objects.filter(user=request.user, status="basket")
            # Для каждого заказа из списка
            for element in basket:
                # Удаляется заказ со статусом "В корзине"
                element.delete()
            return Response({"status": "Корзина очищена"},
                            status=status.HTTP_204_NO_CONTENT)
        # Если заказа со статусом "в корзине" не существует, пользователь получает сообщение что корзина пуста
        else:
            return Response({"status": "Корзина уже пуста"},
                            status=status.HTTP_204_NO_CONTENT)

@extend_schema(tags=['Products', ])
@extend_schema_view(
    list=extend_schema(summary='Получение списка товаров'),
    retrieve=extend_schema(summary='Получение карточки товара',
                           description='Возвращает детальную информацию о товаре, включая список поставщиков и актуальное наличие')
)
class ProductInfoViewSet(ModelViewSet):
    queryset = Productinfo.objects.all()
    serializer_class = ProductInfoSerializer
    http_method_names = ['get']

    def list(self, request, *args, **kwargs):
        objects = Productinfo.objects.all()
        # Анонимные пользователи или пользователи с типом учетной записи "покупатель" не видят параметр price_rrc
        if request.user.is_anonymous or request.user.type == 'buyer':
            self.serializer_class = ProducInfoForBuyerSerializer
            return Response(self.serializer_class(objects, many=True).data, status.HTTP_200_OK)
        else:
            return Response(self.serializer_class(objects, many=True).data, status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        # Анонимные пользователи или пользователи с типом учетной записи "покупатель" не видят параметр price_rrc
        if request.user.is_anonymous or request.user.type == 'buyer':
            self.serializer_class = ProducInfoForBuyerSerializer
            return Response(self.serializer_class(self.get_object(), many=False).data, status.HTTP_200_OK)
        else:
            return Response(self.serializer_class(self.get_object(), many=False).data, status.HTTP_200_OK)


# Вьюха для загрузки информации из Yaml файла
@extend_schema_view(
    post=extend_schema(
        summary='Загрузка файла данных от магазина в YAML формате'
    )
)
class YamlUploadView(APIView):
    # Обрабатывает метод POST
    def post(self, request):
        pattern = r'(\.[A-Za-z]*)'
        # Выброс ошибки, если отсуствует файл - вложение
        if request.FILES.get('file') is None:
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
            yaml_upload_task.delay(data=yaml.load(request.FILES['file'].read(), Loader=SafeLoader), filename=request.FILES['file'].name)

            return Response({
                'status': 'ok'
            })

@extend_schema(tags=['Users', ])
@extend_schema_view(
    post=extend_schema(
        summary='Регистрация нового пользователя'
    )
)
class RegisterUser(APIView):
    def post(self, request):
        try:
            # проверка того, что введенные пароли совпадают
            if request.data['password'] != request.data['repeatpassword']:
                return Response({
                    'status': "password don't match"
                }, status=400)
            else:
                # Если пароль введен верно, то он хэшируется перед добавлением в базу данных
                request.data['password'] = make_password(request.data['password'])
                request.data.pop('repeatpassword')
                # Тип пользоватлея при создании - всегда покупатель, менять его могут админы. Из запроса информация удаляется.
                if request.data.get('type') is not None:
                    request.data.pop('type')
            serializer = CustomUserSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except KeyError:
            return Response(data={'status': 'input data incorrect'}, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(tags=['Users', ])
@extend_schema_view(
    get=extend_schema(summary='Личный кабинет, получение основной информации из профиля')
)
class AccountViewset(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = CustomUserSerializer(request.user)
        return Response(serializer.data, status.HTTP_200_OK)

@extend_schema(tags=['Orders', ])
@extend_schema_view(
    create=extend_schema(
        summary='Подтверждение заказа'
    )
)
class ConfirmOrderViewset(ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    http_method_names = ["post"]
    permission_classes = [IsAuthenticated, IsOwner]

    def create(self, request, *args, **kwargs):
        try:
            """ Из запроса извлекается номер заказа """
            order = Order.objects.get(id=request.data["contact"]["order"])
            if order.status == 'new':
                """ Если статус заказа - new, то в базу вносятя данные адреса и контактов """
                request.data["adress"]["order"] = [order.id, ]
                contact = ContactSerializer(data=request.data["contact"])
                adress = ArdressSerializer(data=request.data["adress"], many=False)
                # Проверка наличия в магазинах нужного количествва товара
                for item in order.items.all():
                    availability = Availability.objects.get(product_info=item.product, shop=item.shop)
                    """ Проверка того, что в магазинах имеются в наличии все товары в заказе """
                    if availability.quantity < item.quantity:
                        """ Если какого то товара нет, пользователь получает сообщение об этом """
                        return Response({
                                            'status': f'Товара {item.product.name} нет в достаточном количестве в магазине {item.shop}'},
                                        status=status.HTTP_400_BAD_REQUEST)
                    else:
                        pass
                if contact.is_valid(raise_exception=True) and adress.is_valid(raise_exception=True):
                    """ В случае успешного прохожения всех проверок, заказу присваивается статус confirmed, товар списывается из наличия """
                    availability.quantity = availability.quantity - item.quantity
                    availability.save()
                    order.status = "confirmed"
                    contact.save()
                    adress.save()
                    order.save()
                    return Response({"status": "Заказ создан", f"Заказ №{order.id}": f"{order.status}"},
                                    status=status.HTTP_201_CREATED)

            else:
                """ Если заказ имеет другой статус, пользователь получает уведомление об ошибке """
                return Response({"status": "Заказ уже оформлен"}, status=status.HTTP_204_NO_CONTENT)
        except KeyError:
            """ Если в отправленных данных не хватает необходимых записей, пользоватлеь получает уведомление об ошибке """
            return Response({'status': 'Не хватает данных'}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=['Orders', ])
@extend_schema_view(
    list=extend_schema(summary='История заказов'),
    retrieve=extend_schema(summary='Детальная информация по заказу'),
    partial_update=extend_schema(summary='Изменение заказа')
)
class OrderViewSet(ModelViewSet):
    """ История заказов пользователя """
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated, IsOwner]
    http_method_names = ['get', 'patch']


    def list(self, request, *args, **kwargs):
        """Метод list возвращает список заказов пользователя, за исключением заказов со статусом "в корзине"""
        orders = Order.objects.filter(user=request.user).exclude(status='basket')
        seriazlizer = self.serializer_class(orders, many=True)
        for order in seriazlizer.data:
            summ = 0
            for product in order['items']:
                summ += product['quantity'] * Availability.objects.get(product_info=product['product']['id'],
                                                                       shop=product['shop']['id']).price
            del order['items']
            order['summ'] = summ
        return Response(seriazlizer.data, status=status.HTTP_200_OK)

    @extend_schema(request=OrderSerializer,
                   examples=[
                       OpenApiExample(
                           'Принятый заказ',
                           description='Первый Пример',
                           value={
  "id": 1,
  "dt": "2023-08-24T08:38:18.798903Z",
  "status": "confirmed",
  "details": [
    {
      "name": "Смартфон Apple iPhone XS Max 512GB (золотистый)",
      "shop": "Связной",
      "price": 110000.0,
      "quantity": 4,
      "summ": 440000.0
    }
  ],
  "recipient": {
    "id": 1,
    "name": "somename",
    "last_name": "somename",
    "surname": "",
    "email": "somemsail@mail.com",
    "phone": "+79432567483",
    "order": 1
  },
  "adress": {
    "id": 1,
    "city": "somecity",
    "street": "somestreet",
    "home": "somehome",
    "structure": "1",
    "building": "1",
    "apartment": "1",
    "is_save": 'false',
    "order": [
      1
    ]
  }
},
                           status_codes=[str(status.HTTP_200_OK)]
                       ),
                       OpenApiExample(
                           'Новый заказ',
                           description='Принятый заказ',
                           value={
                               'id': 3,
                           }
                       )
                   ])
    def retrieve(self, request, *args, **kwargs):
        order = self.get_object()
        if order.status == "basket":
            return Response({'status': 'Заказ еще не оформлен'}, status=status.HTTP_200_OK)
        # Возврат формы - "спасибо за заказ
        elif order.status == 'new':
            order = self.get_object()
            # Тут возвращается номер заказа
            # Тут возвращаются детали заказа
            positions = OrderitemGetSerizlizer(Orderitem.objects.filter(order=order), many=True)
            # Тут возвращаются детали получаетля
            contacts = ContactSerializer(Contact.objects.get(order=order))
            return Response({"order_number": order.id,
                             "details": positions.data,
                             "contacts": contacts.data})
        else:
            detals = []
            data = self.serializer_class(self.get_object()).data
            for item in data['items']:
                price = Productinfo.objects.get(id=item['product']['id']).availability.get(
                    shop=item['shop']['id']).price
                detals.append({
                    'name': item['product']['name'],
                    'shop': item['shop']['name'],
                    'price': price,
                    'quantity': item['quantity'],
                    'summ': price * item['quantity']
                })
            data['details'] = detals
            try:
                data['recipient'] = ContactSerializer(Contact.objects.get(order=data['id'])).data
            except:
                data['recipient'] = None
            try:
                data['adress'] = ArdressSerializer(Adress.objects.get(order=data['id'])).data
            except:
                data['adress'] = None
            data.pop('items')
            return Response(data, status=status.HTTP_200_OK)
