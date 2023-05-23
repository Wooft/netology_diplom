from decouple import config
print(type(config('ALLOWED_HOSTS')))
print(config('ALLOWED_HOSTS').split(sep=","))