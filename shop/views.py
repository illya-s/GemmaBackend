from drf_spectacular.utils import extend_schema

from django.shortcuts import get_object_or_404

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


class HomeView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(responses=HomeResponseSerializer)
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
                "dought_tyoes": dought_tyoes_serializer.data
            },
            status=HTTP_200_OK,
        )


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


class IngredientsView(APIView):
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        serializer = self.serializer_class(
            Ingredient.objects.all(), many=True, context={"request": request}
        )
        return Response(serializer.data, status=HTTP_200_OK)
