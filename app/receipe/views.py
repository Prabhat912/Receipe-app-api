"""
Views for Receipe APIs
"""
from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from core.models import Receipe
from receipe import serializers


class ReceipeViewSet(viewsets.ModelViewSet):
    """
    View for Manage Receipe APIs
    """
    serializer_class = serializers.ReceipeSerializer
    queryset = Receipe.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Retrieve Receipe for authenticated users
        """
        return self.queryset.filter(user=self.request.user).order_by('-id')
