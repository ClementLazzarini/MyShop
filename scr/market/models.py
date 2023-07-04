import uuid

from django.db import models
from django.db.models import Sum
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

from fshop.settings import AUTH_USER_MODEL


class Team(models.Model):
    name = models.CharField(max_length=128, unique=True)

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=128, unique=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    title = models.CharField(max_length=128, unique=True)
    slug = models.SlugField(max_length=128, blank=True, unique=True)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, blank=True, null=True)
    price = models.FloatField(default=0.0, blank=True)
    thumbnail = models.ImageField(blank=True)
    description = models.TextField(blank=True)
    stock = models.IntegerField(default=0, blank=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('detail', kwargs={"slug": self.slug})


class Cart(models.Model):
    user = models.OneToOneField(AUTH_USER_MODEL, on_delete=models.CASCADE)
    items = models.ManyToManyField('market.Product', through='CartItem')

    def __str__(self):
        return f"Cart of {self.user}"

    def get_sum_of_product(self):
        return self.items.count()

    def get_total_price(self):
        total_price = 0.0
        for item in self.cart_items.all():
            total_price += item.quantity * item.product.price
        return total_price

    def delete_cart(self):
        self.cart_items.all().delete()

    def get_total_items(self):
        total_items = self.cart_items.aggregate(total=Sum('quantity'))['total']
        return total_items if total_items else 0


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='cart_items')
    product = models.ForeignKey('market.Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"Item: {self.product.title}, Quantity: {self.quantity}"


class Order(models.Model):
    user = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE)
    products = models.ManyToManyField(Product, through='OrderItem')
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_info = models.TextField()
    order_number = models.CharField(max_length=255, unique=True)
    transaction_id = models.CharField(max_length=255, unique=True)
    date = models.DateTimeField(blank=True, null=True)
    statut = models.CharField(max_length=255)
    discount_code = models.CharField(max_length=255)

    def __str__(self):
        return f"Cart of {self.user}"

    def get_list_of_products(self):
        return self.products.all()

    def get_sum_of_product(self):
        return self.products.count()

    def get_total_price(self):
        total_price = 0.0
        for item in self.order_items.all():
            total_price += item.get_total_price()
        return total_price

    @staticmethod
    def generate_order_number():
        unique_id = uuid.uuid4().hex[:6]
        now = timezone.now()
        formatted_date = now.strftime('%Y%m%d')
        order_number = f'{formatted_date}-{unique_id}'
        return order_number

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items')
    product = models.ForeignKey('market.Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"Item: {self.product.title}, Quantity: {self.quantity}"

    def get_total_quantity(self):
        return self.quantity

    def get_total_price(self):
        return self.product.price * self.quantity


class PromotionCode(models.Model):
    code = models.CharField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)
    is_promotion = models.BooleanField(default=False)
    is_reduction = models.BooleanField(default=False)
    is_unique = models.BooleanField(default=False)
    value = models.IntegerField(default=0, blank=True)
    is_used = models.BooleanField(default=False)
    end_date = models.DateTimeField(blank=True, null=True)
    min_value = models.IntegerField(default=0, blank=True)

    def __str__(self):
        return self.code
