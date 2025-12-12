import json
import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gemma.settings")
print(os.environ.get("DJANGO_SETTINGS_MODULE"))
django.setup()


from urllib.parse import urlparse

import requests
from django.core.files.base import ContentFile
from tqdm import tqdm

from shop.models import Category, DoughType, Ingredient, Product, ProductSize


def download_image(url: str):
    if not url:
        return None

    response = requests.get(url)
    response.raise_for_status()

    filename = "testImage.jpg"

    return filename, ContentFile(response.content)


with open("test-data.json", encoding="utf8") as file:
    data = json.load(file)

for ingredient_data in tqdm(
    data["ingredients"],
    desc="Ingredients",
    colour="green",
    ascii=[" ", "-"],
    bar_format=f"{{desc}} {{bar:{100}}} | {{n_fmt}}/{{total_fmt}}",
):
    ingredient, created = Ingredient.objects.update_or_create(
        name=ingredient_data["name"],
        defaults={"price": ingredient_data["price"]},
    )
    if ingredient_data["imageUrl"]:
        filename, content = download_image(ingredient_data["imageUrl"])
        ingredient.image.save(filename, content, save=True)


for product_size_data in tqdm(
    data["product_sizes"],
    desc="Product Sizes",
    colour="green",
    ascii=[" ", "-"],
    bar_format=f"{{desc}} {{bar:{100}}} | {{n_fmt}}/{{total_fmt}}",
):
    product_size, created = ProductSize.objects.update_or_create(
        name=product_size_data["name"],
        defaults={
            "size": product_size_data["value"],
            "order": product_size_data["sortOrder"],
        },
    )

for dough_type_data in tqdm(
    data["dough_types"],
    desc="Dough Types",
    colour="green",
    ascii=[" ", "-"],
    bar_format=f"{{desc}} {{bar:{100}}} | {{n_fmt}}/{{total_fmt}}",
):
    dough_type, created = DoughType.objects.update_or_create(
        name=dough_type_data["name"],
        defaults={
            "value": dough_type_data["value"],
            "order": dough_type_data["sortOrder"],
        },
    )

for category_data in tqdm(
    data["categories"],
    desc="Categories",
    colour="green",
    ascii=[" ", "-"],
    bar_format=f"{{desc}} {{bar:{100}}} | {{n_fmt}}/{{total_fmt}}",
):
    category, created = Category.objects.update_or_create(name=category_data["name"])

    for product_data in tqdm(
        category_data["products"],
        desc=f"Process {category.name}",
        colour="green",
        ascii=[" ", "-"],
        bar_format=f"{{desc}} {{bar:{100}}} | {{n_fmt}}/{{total_fmt}}",
    ):
        product, created = Product.objects.update_or_create(
            name=product_data["name"],
            defaults={"category": category},
        )

        if product_data["imageUrl"]:
            filename, content = download_image(product_data["imageUrl"])
            product.image.save(filename, content, save=True)
