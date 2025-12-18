from django.db.models import Q
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from .models import Cart, Category, DoughType, Ingredient, Product, ProductSize


class ProductSizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductSize
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


class ProductSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    ingredients = serializers.SerializerMethodField()
    dough_types = serializers.SerializerMethodField()

    def get_image(self, obj) -> str | None:
        request = self.context.get("request")
        if request is None:
            return obj.image.url
        return request.build_absolute_uri(obj.image.url) if obj.image else None

    @extend_schema_field(IngredientSerializer(many=True))
    def get_ingredients(self, obj):
        if self.context.get("minimal"):
            return [pi.ingredient.name for pi in obj.product_ingredient.all()]
        serializer = IngredientSerializer(
            [pi.ingredient for pi in obj.product_ingredient.all()],
            many=True,
            context={
                **self.context,
                "minimal": True,
            },
        )
        return serializer.data

    @extend_schema_field(DoughTypeSerializer(many=True))
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
        request = self.context.get("request")

        filters_list = Q()
        qs = obj.products.all()

        dough_types = request.query_params.getlist("dough_type")
        if dough_types:
            filters_list &= Q(dough_types__in=map(int, dough_types))

        product_sizes = request.query_params.getlist("product_size")
        if product_sizes:
            filters_list &= Q(
                category__category_product_size__product_size_id__in=map(
                    int, product_sizes
                )
            )

        ingredients = request.query_params.getlist("ingredient")
        if ingredients:
            filters_list &= Q(
                product_ingredient__ingredient_id__in=map(int, ingredients)
            )

        min_price = request.query_params.get("min_price")
        if min_price:
            filters_list &= Q(price__gte=min_price)

        max_price = request.query_params.get("max_price")
        if max_price:
            filters_list &= Q(price__lte=max_price)

        qs = qs.filter(filters_list)

        serializer = ProductSerializer(
            qs.distinct(),
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


class CartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cart
        fields = "__all__"
        read_only_fields = ("id", "updated_at", "created_at")


class HomeResponseSerializer(serializers.Serializer):
    categories = CategorySerializer(many=True)
    ingredients = IngredientSerializer(many=True)
    dought_tyoes = DoughTypeSerializer(many=True)
