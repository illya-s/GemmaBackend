from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from .models import Cart, Category, DoughType, Ingredient, Product, ProductSize


class ProductSizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductSize
        fields = "__all__"
        read_only_fields = ("id", "updated_at", "created_at")


class ProductSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    ingredients = serializers.SerializerMethodField()
    dough_types = serializers.SerializerMethodField()

    def get_image(self, obj) -> str | None:
        request = self.context.get("request")
        if request is None:
            return obj.image.url
        return request.build_absolute_uri(obj.image.url) if obj.image else None

    @extend_schema_field(OpenApiTypes.STR)
    def get_ingredients(self, obj):
        if self.context.get("minimal"):
            return [pi.ingredient.name for pi in obj.product_ingredient.all()]

        ingredient_serializer = IngredientSerializer(
            [pi.ingredient for pi in obj.product_ingredient.all()],
            many=True,
            context={
                **self.context,
                "minimal": True,
            },
        )
        return ingredient_serializer.data

    @extend_schema_field(OpenApiTypes.STR)
    def get_dough_types(self, obj):
        if self.context.get("minimal"):
            return [str(dt.name) for dt in obj.dough_types.all()]

        dough_type_serializer = DoughTypeSerializer(
            obj.dough_types.all(),
            many=True,
            context={
                **self.context,
                "minimal": True,
            },
        )
        return dough_type_serializer.data

    class Meta:
        model = Product
        fields = "__all__"
        read_only_fields = ("id", "updated_at", "created_at")


class CategorySerializer(serializers.ModelSerializer):
    products = serializers.SerializerMethodField()
    product_sizes = serializers.SerializerMethodField()

    @extend_schema_field(ProductSerializer(many=True))
    def get_products(self, obj):
        serializer = ProductSerializer(
            obj.products.all(),
            many=True,
            context={
                **self.context,
                "minimal": True,
            },
        )
        return serializer.data

    @extend_schema_field(ProductSizeSerializer(many=True))
    def get_product_sizes(self, obj):
        serializer = ProductSizeSerializer(
            [cp.product_size for cp in obj.category_product_size.all()],
            many=True,
            context={
                **self.context,
                "minimal": True,
            },
        )
        return serializer.data

    class Meta:
        model = Category
        fields = "__all__"
        read_only_fields = ("id", "updated_at", "created_at")


class IngredientSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    def get_image(self, obj) -> str | None:
        request = self.context.get("request")
        return request.build_absolute_uri(obj.image.url) if obj.image else None

    class Meta:
        model = Ingredient
        fields = "__all__"
        read_only_fields = ("id", "updated_at", "created_at")


class DoughTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoughType
        fields = "__all__"
        read_only_fields = ("id", "updated_at", "created_at")


class CartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cart
        fields = "__all__"
        read_only_fields = ("id", "updated_at", "created_at")


class HomeResponseSerializer(serializers.Serializer):
    categories = CategorySerializer(many=True)
    ingredients = IngredientSerializer(many=True)
    dought_tyoes = DoughTypeSerializer(many=True)
