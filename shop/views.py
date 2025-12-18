from django.shortcuts import get_object_or_404
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiTypes,
    extend_schema,
)
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK
from rest_framework.views import APIView

from .models import Category, DoughType, Ingredient, Product
from .serializers import (
    CategorySerializer,
    DoughTypeSerializer,
    HomeResponseSerializer,
    IngredientSerializer,
    ProductSerializer,
)


@extend_schema(
    responses=HomeResponseSerializer,
    parameters=[
        OpenApiParameter(
            name="dough_type",
            description="ID типа теста. Можно передать несколько значений",
            required=False,
            type=OpenApiTypes.INT,
            many=True,
            location=OpenApiParameter.QUERY,
            # examples=[1, 2],
        ),
        OpenApiParameter(
            name="product_size",
            description="ID размера продукта. Можно передать несколько значений",
            required=False,
            type=OpenApiTypes.INT,
            many=True,
            location=OpenApiParameter.QUERY,
            # examples=[1, 3],
        ),
        OpenApiParameter(
            name="ingredient",
            description="ID ингредиента. Можно передать несколько значений",
            required=False,
            type=OpenApiTypes.INT,
            many=True,
            location=OpenApiParameter.QUERY,
            # examples=[4, 7],
        ),
        OpenApiParameter(
            name="min_price",
            description="Минимальная цена",
            required=False,
            type=OpenApiTypes.NUMBER,
            location=OpenApiParameter.QUERY,
            # examples=100,
        ),
        OpenApiParameter(
            name="max_price",
            description="Максимальная цена",
            required=False,
            type=OpenApiTypes.NUMBER,
            location=OpenApiParameter.QUERY,
            # examples=500,
        ),
    ],
)
class HomeView(APIView):
    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        category_serializer = CategorySerializer(
            Category.objects.all(), many=True, context={"request": request}
        )
        ingredients_serializer = IngredientSerializer(
            Ingredient.objects.all(), many=True, context={"request": request}
        )
        dought_tyoes_serializer = DoughTypeSerializer(
            DoughType.objects.all(), many=True, context={"request": request}
        )

        return Response(
            {
                "category": category_serializer.data,
                "ingredients": ingredients_serializer.data,
                "dought_tyoes": dought_tyoes_serializer.data,
            },
            status=HTTP_200_OK,
        )


@extend_schema(responses=ProductSerializer)
class ProductsView(APIView):
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        serializer = self.serializer_class(
            Product.objects.all(), many=True, context={"request": request}
        )
        return Response(serializer.data, status=HTTP_200_OK)

    def post(self, request: Request) -> Response:
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


@extend_schema(responses=ProductSerializer)
class ProductView(APIView):
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]

    def get(self, request: Request, pk: int) -> Response:
        product = get_object_or_404(Product, id=pk)
        serializer = self.serializer_class(product, context={"request": request})
        return Response(serializer.data, status=HTTP_200_OK)

    # def post(self, request: Request) -> Response:
    #     serializer = self.serializer_class(data=request.data)
    #     serializer.is_valid(raise_exception=True)
    #     serializer.save()
    #     return Response(serializer.data)


@extend_schema(responses=IngredientSerializer)
class IngredientsView(APIView):
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        serializer = self.serializer_class(
            Ingredient.objects.all(), many=True, context={"request": request}
        )
        return Response(serializer.data, status=HTTP_200_OK)
