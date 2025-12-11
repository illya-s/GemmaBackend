import json
import os

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gemma.settings')
print(os.environ.get("DJANGO_SETTINGS_MODULE"))
django.setup()


from shop.models import Ingredient

fp = "test-data.json"

with open(fp, encoding="utf8") as file:
    data = json.load(file)

for ingredient_data in data["ingredients"]:
    ingredient, created = Ingredient.objects.update_or_create(
        name=ingredient_data["name"],
        defaults={"price": ingredient_data["price"], "image": ingredient_data["imageUrl"]},
    )
    print(created, ingredient.name)
