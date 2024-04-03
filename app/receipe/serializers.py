"""
Serializers for Receipe APIs.
"""
from rest_framework import serializers
from core.models import Receipe, Tag, Ingredient


class IngredientSerializer(serializers.ModelSerializer):
    """Serializer for ingredients."""

    class Meta:
        model = Ingredient
        fields = ['id', 'name']
        read_only_fields = ['id']


class TagSerializer(serializers.ModelSerializer):
    """
    Serializers for Tags
    """

    class Meta:
        model = Tag
        fields = ['id', 'name']
        read_only_fields = ['id']


class ReceipeSerializer(serializers.ModelSerializer):
    """
    Serializer for receipe
    """
    tags = TagSerializer(many=True, required=False)
    ingredients = IngredientSerializer(many=True, required=False)

    class Meta:
        model = Receipe
        fields = [
            'id', 'title', 'time_minutes', 'price', 'link', 'tags',
            'ingredients',
        ]
        read_only_fields = ['id']

    def _get_or_create_tags(self, tags, receipe):
        """Handle getting or creating tags as needed."""
        auth_user = self.context['request'].user
        for tag in tags:
            tag_obj, created = Tag.objects.get_or_create(
                user=auth_user,
                **tag,
            )
            receipe.tags.add(tag_obj)
    
    def _get_or_create_ingredients(self, ingredients, receipe):
        """Handle getting or creating ingredients as needed."""
        auth_user = self.context['request'].user
        for ingredient in ingredients:
            ingredient_obj, created = Ingredient.objects.get_or_create(
                user=auth_user,
                **ingredient,
            )
            receipe.ingredients.add(ingredient_obj)

    def create(self, validated_data):
        """Create a recipe."""
        tags = validated_data.pop('tags', [])
        ingredients = validated_data.pop('ingredients', [])
        receipe = Receipe.objects.create(**validated_data)
        self._get_or_create_tags(tags, receipe)
        self._get_or_create_ingredients(ingredients, receipe)

        return receipe

    def update(self, instance, validated_data):
        """Update receipe."""
        tags = validated_data.pop('tags', None)
        ingredients =validated_data.pop('ingredients', None)

        if tags is not None:
            instance.tags.clear()
            self._get_or_create_tags(tags, instance)
        
        if ingredients is not None:
            instance.ingredients.clear()
            self._get_or_create_ingredients(ingredients, instance)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class ReceipeDetailSerializer(ReceipeSerializer):
    """
    Serializer for receipe detail view
    """

    class Meta(ReceipeSerializer.Meta):
        fields = ReceipeSerializer.Meta.fields + ['description']
