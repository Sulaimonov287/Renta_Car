from rest_framework import serializers
from django.contrib.auth.models import User
from .models import *
from django.db.models import Avg

class CarSerializer(serializers.ModelSerializer):
    rating = serializers.SerializerMethodField()
    owner_username = serializers.ReadOnlyField(source='owner.username')

    class Meta:
        model = Car
        fields = '__all__'
        read_only_fields = ['owner']

    def get_rating(self, obj):
        avg = obj.reviews.aggregate(Avg('rating'))['rating__avg']
        return round(avg, 1) if avg else None

class DogovorSerializer(serializers.ModelSerializer):
    user_username = serializers.ReadOnlyField(source='user.username')
    car_title = serializers.ReadOnlyField(source='car.brand')

    class Meta:
        model = Dogovor
        fields = ['id', 'user', 'user_username', 'car', 'car_title', 'start_date', 'end_date', 'total_price', 'status']
        read_only_fields = ['user', 'total_price', 'status']

    def validate(self, data):
        start = data['start_date']
        end = data['end_date']
        car = data['car']

        if end <= start:
            raise serializers.ValidationError("Дата окончания должна быть позже даты начала.")

        busy = Dogovor.objects.filter(
            car=car,
            status__in=['pending', 'confirmed'],
            start_date__lt=end,
            end_date__gt=start,
        )
        if busy.exists():
            raise serializers.ValidationError("Машина уже забронирована на эти даты.")

        return data

    def create(self, validated_data):
        days = (validated_data['end_date'] - validated_data['start_date']).days
        validated_data['total_price'] = days * validated_data['car'].price_per_day
        return super().create(validated_data)

class MessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.ReadOnlyField(source='sender.username')
    
    class Meta:
        model = Message
        fields = ['id', 'dogovor', 'sender', 'sender_username', 'text', 'created_at']  
        read_only_fields = ['sender']

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']
        extra_kwargs = {'email': {'required': True}}

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Этот email уже занят.")
        return value

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)

class ReviewSerializer(serializers.ModelSerializer):
    user_username = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = Review
        fields = ['id', 'user', 'user_username', 'car', 'dogovor', 'rating', 'text', 'created_at']
        read_only_fields = ['user', 'car']

    def validate(self, data):
        dogovor = data['dogovor']
        if dogovor.user != self.context['request'].user:
            raise serializers.ValidationError("Это не ваша бронь.")
        if dogovor.status != 'completed':
            raise serializers.ValidationError("Отзыв можно оставить только после завершённой аренды.")
        return data