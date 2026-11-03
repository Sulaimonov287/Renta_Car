from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Q

class Car(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='cars', verbose_name="Владелец")
    brand = models.CharField(max_length=50, verbose_name="Marka")
    description = models.TextField(blank=True, verbose_name="Описание")
    model = models.CharField(max_length=50, verbose_name="Model")
    year = models.PositiveIntegerField(verbose_name="God vypuska")
    price_per_day = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Tsena za sutki")
    status = models.CharField(max_length=20, default='available', verbose_name="Status")
    image = models.ImageField(upload_to='cars/', blank=True, null=True, verbose_name="Foto")
    model_3d = models.FileField(upload_to='models3d/', blank=True, null=True, verbose_name="3D-модель (.glb)")

    def __str__(self):
        return f"{self.brand} -- {self.model}"


class Dogovor(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Klient")
    car = models.ForeignKey(Car, on_delete=models.CASCADE, verbose_name="Mashina")
    start_date = models.DateField(verbose_name="Data nachala")
    end_date = models.DateField(verbose_name="Data okonchaniya")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Obshchaya tsena")
    status = models.CharField(max_length=20, default='pending', verbose_name="Status")

    def __str__(self):
        return f"Bron #{self.id} - {self.user.username}"


class Message(models.Model):
    dogovor = models.ForeignKey(Dogovor, on_delete=models.CASCADE, verbose_name="Bronirovanie")
    sender = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Otpravitel")
    text= models.TextField(verbose_name="Tekst")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Vremya")

    def __str__(self):
        return f"Soobshchenie ot {self.sender.username}"

class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Клиент")
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='reviews', verbose_name="Машина")
    dogovor = models.OneToOneField(Dogovor, on_delete=models.CASCADE, verbose_name="Бронь")
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], verbose_name="Оценка")
    text = models.TextField(blank=True, verbose_name="Отзыв")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Отзыв от {self.user.username} на {self.car}"