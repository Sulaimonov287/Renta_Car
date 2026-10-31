from datetime import date
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db.models import Q
from rest_framework import viewsets, generics, permissions
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from .filters import CarFilter
from .models import *
from .serializer import *


def send_email_to_user(user, subject, text):
    if user and user.email:
        try:
            send_mail(subject, text, None, [user.email])
        except Exception:
            pass


class IsOwnerOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_staff or obj.owner == request.user


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        user = serializer.save()
        send_email_to_user(user, "Добро пожаловать!", f"Здравствуйте, {user.username}!")


class CarViewSet(viewsets.ModelViewSet):
    queryset = Car.objects.all()
    serializer_class = CarSerializer
    permission_classes = [IsOwnerOrAdmin]
    filterset_class = CarFilter
    search_fields = ['brand', 'model']
    ordering_fields = ['price_per_day', 'year']
    @action(detail=True, methods=['get'], url_path='busy-dates')
    def busy_dates(self, request, pk=None):
        car = self.get_object()
        items = Dogovor.objects.filter(car=car, status__in=['pending', 'confirmed']).values('start_date', 'end_date')
        return Response(list(items))

    def get_queryset(self):
        qs = Car.objects.all()
        start = self.request.query_params.get('start')
        end = self.request.query_params.get('end')
        if start and end:
            try:
                start, end = date.fromisoformat(start), date.fromisoformat(end)
            except ValueError:
                return qs
            busy = Dogovor.objects.filter(
                status__in=['pending', 'confirmed'],
                start_date__lt=end,
                end_date__gt=start,
            ).values_list('car_id', flat=True)
            qs = qs.exclude(id__in=busy)
        return qs

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def destroy(self, request, *args, **kwargs):
        car = self.get_object()
        if Dogovor.objects.filter(car=car, status__in=['pending', 'confirmed']).exists():
            return Response({'detail': 'Нельзя удалить машину с активными бронями.'}, status=400)
        return super().destroy(request, *args, **kwargs)


class DogovorViewSet(viewsets.ModelViewSet):
    serializer_class = DogovorSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'post']

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Dogovor.objects.all()
        return Dogovor.objects.filter(Q(user=user) | Q(car__owner=user))

    def perform_create(self, serializer):
        dogovor = serializer.save(user=self.request.user)
        send_email_to_user(dogovor.user, "Бронь создана", f"Вы забронировали {dogovor.car}.")
        send_email_to_user(dogovor.car.owner, "Новая бронь", f"{dogovor.user.username} забронировал {dogovor.car}.")

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        dogovor = self.get_object()
        dogovor.status = 'cancelled'
        dogovor.save()
        send_email_to_user(dogovor.user, "Бронь отменена", "Ваша бронь отменена.")
        return Response({'detail': 'Бронь отменена'})


class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'post']
    filterset_fields = ['dogovor']

    def get_queryset(self):
        user = self.request.user
        return Message.objects.filter(
            Q(dogovor__user=user) | Q(dogovor__car__owner=user)
        ).order_by('created_at')

    def perform_create(self, serializer):
        dogovor = serializer.validated_data['dogovor']
        user = self.request.user
        owner = dogovor.car.owner
        if user != dogovor.user and user != owner:
            raise PermissionDenied("Вы не участник этого чата.")
        message = serializer.save(sender=user)
        other = owner if user == dogovor.user else dogovor.user
        send_email_to_user(other, "Новое сообщение по брони", message.text)