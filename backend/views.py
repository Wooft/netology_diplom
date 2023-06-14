from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from backend.models import Shop, Category, Product, Productinfo, Parameter, ProductParameter
from backend.serializers import Shopserializer, CategorySerializer, ProductInfoSerializer
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated
import yaml
from yaml.loader import SafeLoader
import re

class ExampleView(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        content = {
            'user': str(request.user),
            'auth': str(request.auth)
        }
        return Response(content)

class ShopViewSet(ModelViewSet):
    queryset = Shop.objects.all()
    serializer_class = Shopserializer

class CategoryViewSet(ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class ProductInfoViewSet(ModelViewSet):
    queryset = Productinfo.objects.all()
    serializer_class = ProductInfoSerializer

#Вьюха для загрузки информации из Yaml файла
class YamlUploadView(APIView):
    #Обрабатывает метод POST
    def post(self, request):
        pattern = '(\.[A-Za-z]*)'
        #Выброс ошибки, если отсуствует файл
        if request.FILES.get('file') == None:
            return Response(
                {'status': 'please load correct yaml file'}, status='400'
            )
        #Проверка на соответствие типа файла. Если это не yanl - выбрасывается ошибка
        elif re.search(pattern=pattern, string=request.FILES['file'].name)[0] != '.yaml':
            return Response(
                {'status': 'Please load file in "yaml" format'}, status='400'
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