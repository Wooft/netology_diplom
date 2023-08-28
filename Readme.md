
Используемая схема данных:


Документация о точках входа сервиса доступна по маршруту:
'/api/docs'

В проекте доступна авторизация через социальные сети (модуль django-social-auth).
Для регистрации при помощи соц. сети VK необходимо:  
 - создать приложение VK с активным Open API
 - в environ указать VK_KEY (ID приложения) и VK_SECRET (Защищённый ключ приложения)
Для авторизации используется маршрут '/login/vk-oauth2'
Подробнее можно ознакомиться в документации: https://python-social-auth.readthedocs.io/en/latest/backends/vk.html

Для регистрации через Google необзодимо:
- создать новое приложение в https://console.cloud.google.com/apis/ для использования OAuth 2.0
- В environ указать GOOGLE_KEY (ID приложения) и GOOGLE_SECRET (Sexret_key приложения)

Используется маршрут: '/login/google-oauth2/'
