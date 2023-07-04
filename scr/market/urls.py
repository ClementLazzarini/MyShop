from django.conf.urls.static import static
from django.urls import path
from market.views import home, ProductDetail, add_to_cart, cart_view, delete_cart, paiement_informations, process_payment, stripe_webhook, success, cancel, update_cart, update_paiement, OrderList, products

from fshop import settings

urlpatterns = [
    path('', home, name='home'),
    path('products/', products, name="products"),
    path('success/', success, name="success"),
    path('cancel/', cancel, name="cancel"),
    path('stripe-webhook/', stripe_webhook, name='stripe_webhook'),
    path('cart/', cart_view, name="cart"),
    path('cart/update/<int:item_id>/', update_cart, name='update_cart'),
    path('delete_cart/', delete_cart, name="delete_cart"),
    path('paiement_informations/', paiement_informations, name="paiement_informations"),
    path('update_paiement_informations/', update_paiement, name="update_paiement_informations"),
    path('process_payment/', process_payment, name="process_payment"),
    path('order_list/', OrderList.as_view(), name="order_list"),
    path('<str:slug>/add_to_cart/', add_to_cart, name="add_to_cart"),
    path('<str:slug>/', ProductDetail.as_view(), name="detail"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
