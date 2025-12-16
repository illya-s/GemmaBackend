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
        return request.build_absolute_uri(obj.image.url) if obj.image else None

    def get_ingredients(self, obj) -> list[str]:
        return [str(pi.ingredient.name) for pi in obj.product_ingredient.all()]

    def get_dough_types(self, obj) -> list[str]:
        return [str(dt.name) for dt in obj.dough_types.all()]

    class Meta:
        model = Product
        fields = "__all__"
        read_only_fields = ("id", "updated_at", "created_at")


class CategorySerializer(serializers.ModelSerializer):
    products = ProductSerializer(many=True, read_only=True)
    product_sizes = serializers.SerializerMethodField()
    # product_sizes = ProductSizeSerializer(many=True, read_only=True)

    @extend_schema_field(ProductSizeSerializer(many=True))
    def get_product_sizes(self, obj):
        serializer = ProductSizeSerializer(
            [cp.product_size for cp in obj.category_product_size.all()],
            many=True,
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
