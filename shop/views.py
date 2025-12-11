from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK
from rest_framework.views import APIView

from .models import Ingredient, Product
from .serializers import IngredientSerializer, ProductSerializer


class ProductsView(APIView):
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        serializer = self.serializer_class(Product.objects.all(), many=True)
        return Response(serializer.data, status=HTTP_200_OK)

    def post(self, request: Request) -> Response:
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

class IngredientsView(APIView):
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]
    
    def get(self, request: Request) -> Response:
        serializer = self.serializer_class(Ingredient.objects.all(), many=True)
        return Response(serializer.data, status=HTTP_200_OK)
