"""
Views for Receipe APIs
"""
from rest_framework import viewsets, mixins
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from core.models import Receipe, Tag
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

        return self.serializer_class

    def perform_create(self, serializer):
        """
        Create a new receipe
        """
        serializer.save(user=self.request.user)


class TagViewSet(mixins.DestroyModelMixin,
                 mixins.UpdateModelMixin,
                 mixins.ListModelMixin,
                 viewsets.GenericViewSet):
    """
    Manage Tags in the database
    """
    serializer_class = serializers.TagSerializer
    queryset = Tag.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Filter query set to authenticated user
        """
        return self.queryset.filter(user=self.request.user).order_by('-name')
