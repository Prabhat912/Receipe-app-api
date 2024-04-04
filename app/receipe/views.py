"""
Views for Receipe APIs
"""
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from core.models import Receipe, Tag, Ingredient
from receipe import serializers


class ReceipeViewSet(viewsets.ModelViewSet):
    """
    View for Manage Receipe APIs
    """
    serializer_class = serializers.ReceipeDetailSerializer
    queryset = Receipe.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Retrieve Receipe for authenticated users
        """
        return self.queryset.filter(user=self.request.user).order_by('-id')

    def get_serializer_class(self):
        """
        Return the serializer class for request
        """
        if self.action == 'list':
            return serializers.ReceipeSerializer
        elif self.action == 'upload_image':
            return serializers.ReceipeImageSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        """
        Create a new receipe
        """
        serializer.save(user=self.request.user)
    
    @action(methods=['POST'], detail=True, url_path='upload-image')
    def upload_image(self, request, pk=None):
        """Upload an image to recipe."""
        receipe = self.get_object()
        serializer = self.get_serializer(receipe, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BaseRecipeAttrViewSet(mixins.DestroyModelMixin,
                            mixins.UpdateModelMixin,
                            mixins.ListModelMixin,
                            viewsets.GenericViewSet):
    """Base viewset for receipe attributes."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Filter query set to authenticated user
        """
        return self.queryset.filter(user=self.request.user).order_by('-name')


class TagViewSet(BaseRecipeAttrViewSet):
    """
    Manage Tags in the database
    """
    serializer_class = serializers.TagSerializer
    queryset = Tag.objects.all()


class IngredientViewSet(BaseRecipeAttrViewSet):
    """Manage ingredients in the database."""
    serializer_class = serializers.IngredientSerializer
    queryset = Ingredient.objects.all()
