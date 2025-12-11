import os
from email.policy import default
from random import choices

from django.db import models
from django.utils import timezone
from django.utils.duration import datetime
from django.utils.text import slugify

from user.models import User


# Create your models here.
class Category(models.Model):
    name = models.CharField("name", null=False, blank=True, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.name)


def ingredient_upload_to(instance, filename):
    fn, ext = os.path.splitext(filename)
    return "/".join(
        [
            "content",
            f"{slugify(instance.name)}-{timezone.now().isoformat()}",
            f"image{ext}",
        ]
    )


class Ingredient(models.Model):
    name = models.CharField("name", null=False, blank=True, db_index=True)

    price = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to=ingredient_upload_to, null=True, blank=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class DoughType(models.Model):
    name = models.CharField("name", null=False, blank=True, db_index=True)
    value = models.PositiveIntegerField(null=False, blank=True)
    order = models.PositiveIntegerField(null=False, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class ProductSize(models.Model):
    name = models.CharField("name", null=False, blank=True, db_index=True)
    size = models.PositiveIntegerField("size", null=False, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


def product_upload_to(instance, filename):
    fn, ext = os.path.splitext(filename)
    return "/".join(
        [
            "content",
            f"{slugify(instance.name)}-{timezone.now().isoformat()}",
            f"image{ext}",
        ]
    )


class Product(models.Model):
    name = models.CharField("name", null=False, blank=True, db_index=True)

    image = models.ImageField(upload_to=product_upload_to, null=True, blank=False)
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=False
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    # token = models.CharField(max_length=16, null=False, blank=True)

    total = models.PositiveIntegerField()

    editable = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class CartProduct(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, null=False, blank=True)
    product = models.ForeignKey(
        Product, on_delete=models.SET_NULL, null=True, blank=False
    )

    quantity = models.PositiveIntegerField()
    product_size = models.ForeignKey(
        ProductSize, on_delete=models.SET_NULL, null=True, blank=False
    )
    dough_type = models.ForeignKey(
        DoughType, on_delete=models.SET_NULL, null=True, blank=False
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SUCCEEDED = "succeeded", "Succeeded"
        CANCELLED = "cancelled", "Cancelled"

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    status = models.CharField(
        max_length=32, choices=Status.choices, default=Status.PENDING
    )
    # token = models.CharField(max_length=16, null=False, blank=True)

    cart = models.ForeignKey(Cart, on_delete=models.SET_NULL, null=True)
    total = models.PositiveIntegerField()
    full_name = models.CharField(max_length=255)
    address = models.CharField(max_length=1000)
    comment = models.TextField(max_length=5000)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
