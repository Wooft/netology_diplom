Маршруты:
 - register - регистрация нового пользователя. На вход принимает списо, состоящий из полей:
 - get_token - получение существующего или создание нового токена пользователя для взаиможействия с приложением
 - yamlupload - Загрузка YAML файла с информацией от интернет-магазина
 - products - информация о товарах в базе данных
 - products/<id> - карточка товара с определнным ID


Корзина: \
Создается заказ со статусом "в корзине" при POST запросе \
Одновременно в базе данных может быть только один заказ со статусом "в корзине" \
При GET запросе получаем информацию по текущей корзине \


