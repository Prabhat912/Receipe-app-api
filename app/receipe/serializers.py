"""
Serializers for Receipe APIs.
"""
from rest_framework import serializers
from core.models import Receipe


class ReceipeSerializer(serializers.ModelSerializer):
    """
    Serializer for receipe
    """

    class Meta:
        model = Receipe
        fields = ['id', 'title', 'time_minutes', 'price', 'link']
        read_only_fields = ['id']


class ReceipeDetailSerializer(ReceipeSerializer):
    """
    Serializer for receipe detail view
    """

    class Meta(ReceipeSerializer.Meta):
        fields = ReceipeSerializer.Meta.fields + ['description']
