from django.contrib import admin
from market.models import Product, Team, Category, Order, OrderItem, PromotionCode


class ProductAdmin(admin.ModelAdmin):
    list_display = ("title", "team", "category", "price", "stock")


class TeamAdmin(admin.ModelAdmin):
    list_display = ("name",)


class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'quantity', 'get_total_price']
    fields = ['product', 'quantity', 'get_total_price']
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    readonly_fields = ['user',
                       'total_price',
                       'get_total_price',
                       'discount_code',
                       'date',
                       'delivery_info',
                       'order_number',
                       'transaction_id']
    fields = ['user',
              'total_price',
              'get_total_price',
              'discount_code',
              'date',
              'delivery_info',
              'order_number',
              'transaction_id',
              'statut']
    inlines = [OrderItemInline]
    list_display = ['user', 'get_total_price', 'delivery_info', 'order_number']


# class CartAdmin(admin.ModelAdmin):
#    list_display = ("user", )

class PromotionCodeAdmin(admin.ModelAdmin):
    list_display = ("code",)


admin.site.register(Product, ProductAdmin)
admin.site.register(Team, TeamAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(PromotionCode, PromotionCodeAdmin)
