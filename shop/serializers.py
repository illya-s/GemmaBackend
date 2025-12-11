from rest_framework import serializers

from .models import Cart, Category, DoughType, Ingredient, Product, ProductSize


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"
        read_only_fields = ("id", "updated_at", "created_at")


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = "__all__"
        read_only_fields = ("id", "updated_at", "created_at")


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = "__all__"
        read_only_fields = ("id", "updated_at", "created_at")


class DoughTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoughType
        fields = "__all__"
        read_only_fields = ("id", "updated_at", "created_at")


class ProductSizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductSize
        fields = "__all__"
        read_only_fields = ("id", "updated_at", "created_at")


class CartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cart
        fields = "__all__"
        read_only_fields = ("id", "updated_at", "created_at")



class HomeResponseSerializer(serializers.Serializer):
    products = ProductSerializer(many=True)
    ingredients = IngredientSerializer(many=True)
