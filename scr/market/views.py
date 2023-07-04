import uuid

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import DetailView, ListView
from fshop import settings
from market.models import Product, Cart, CartItem, Order, OrderItem, PromotionCode
import stripe
from django.http import HttpResponse
from django.contrib.auth.mixins import LoginRequiredMixin


def home(request):
    # Récupérer la liste complète des produits
    products = Product.objects.all()

    # Récupérer le mot recherché depuis les paramètres GET
    search_query = request.GET.get('search')

    # Filtrer les produits en fonction du mot recherché dans le titre
    if search_query:
        products = products.filter(title__icontains=search_query)
        # Inclure le paramètre de recherche dans l'URL de redirection
        redirect_url = reverse('products') + f'?search={search_query}'
        return redirect(redirect_url)

    return render(request, "market/index.html", {"products": products})


def products(request):
    # Récupérer la liste complète des produits
    products = Product.objects.all()

    # Récupérer le mot recherché depuis les paramètres GET
    search_query = request.GET.get('search')

    # Filtrer les produits en fonction du mot recherché dans le titre
    if search_query:
        products = products.filter(title__icontains=search_query)

    # Autres logique de la vue...
    return render(request, "market/products.html", {"products": products})


class OrderList(LoginRequiredMixin, ListView):
    model = Order
    context_object_name = "orders"
    template_name = "order_list.html"
    login_url = reverse_lazy('login')

    def get_queryset(self):
        # Récupérer uniquement les commandes de l'utilisateur connecté
        return Order.objects.filter(user=self.request.user)


class ProductDetail(DetailView):
    model = Product
    context_object_name = "product"
    template_name = "market/product_detail.html"


def add_to_cart(request, slug):
    product = get_object_or_404(Product, slug=slug)
    # Vérifie si le panier existe pour l'utilisateur connecté
    if request.user.is_authenticated:
        product = get_object_or_404(Product, slug=slug)
        cart, created = Cart.objects.get_or_create(user=request.user)

        # Vérifier si le produit est déjà présent dans le panier
        cart_item, item_created = CartItem.objects.get_or_create(cart=cart, product=product)
        if not item_created:
            # Si le produit existe déjà dans le panier, augmenter la quantité
            new_quantity = cart_item.quantity + 1

            if new_quantity <= product.stock:
                # Mettre à jour la quantité dans le panier
                cart_item.quantity = new_quantity
                cart_item.save()
            else:
                # Gérer la situation où la quantité dépasse le stock disponible
                # Vous pouvez afficher un message d'erreur ou effectuer une action appropriée
                # Par exemple, rediriger vers une page d'erreur ou proposer une alternative au client
                pass

        request.session['total_price'] = "{:.2f}".format(cart.get_total_price())

        return redirect('home')  # Redirige vers la page du panier
    else:
        cart = request.session.get('cart', {})
        if str(product.id) in cart:
            # Le produit est déjà dans le panier, augmenter la quantité
            cart[f'{product.id}'] += 1
        else:
            # Le produit n'est pas encore dans le panier, l'ajouter avec une quantité de 1
            cart[f'{product.id}'] = 1

        quantity_total = sum(cart.values())
        request.session['cart'] = dict(cart.items())  # Convertir le dictionnaire en format souhaité
        request.session['quantity_total'] = quantity_total

        return redirect('home')


def update_cart(request, item_id):
    if request.user.is_authenticated:
        cart_item = get_object_or_404(CartItem, id=item_id)

        if request.method == 'POST':
            quantity = int(request.POST.get('quantity'))

            if quantity > 0:
                cart_item.quantity = quantity
                cart_item.save()
            else:
                cart_item.delete()
    else:
        cart = request.session.get('cart', {})
        if request.method == 'POST':
            quantity = int(request.POST.get('quantity'))

            if str(item_id) in cart:
                # Le produit est déjà dans le panier, augmenter la quantité
                cart[f'{item_id}'] = 0
                cart[f'{item_id}'] += quantity
            else:
                # Le produit n'est pas encore dans le panier, l'ajouter avec la quantité spécifiée
                cart[f'{item_id}'] = quantity

        request.session['cart'] = cart
        quantity_total = sum(cart.values())
        request.session['quantity_total'] = quantity_total

    if 'total_price' in request.session:
        del request.session['total_price']

    return redirect('cart')


def cart_view(request):
    # Vérifie si l'utilisateur est connecté
    if request.user.is_authenticated:
        cart = Cart.objects.get(user=request.user)
        products = cart.items.all()
        total_price = "{:.2f}".format(cart.get_total_price())
        promotion_code = 0
        return render(request, 'market/cart.html', {'cart': cart,
                                                    'products': products,
                                                    'total_price': total_price,
                                                    'promotion': promotion_code})
    else:
        cart = request.session.get('cart', {})

        products = []
        total_price = 0
        promotion_code = 0

        for product_id, quantity in cart.items():
            product = get_object_or_404(Product, id=product_id)
            products.append({
                'product': product,
                'quantity': quantity,
                'subtotal': product.price * quantity
            })
            total_price += product.price * quantity
        return render(request, 'market/cart.html', {'cart': cart,
                                                    'products': products,
                                                    'total_price': total_price,
                                                    'promotion': promotion_code})  # Redirige vers la page de connexion


def delete_cart(request):
    if request.user.is_authenticated:
        # Vérifie si le panier existe pour l'utilisateur connecté
        cart = Cart.objects.filter(user=request.user).first()
        if cart:
            # Supprime tous les produits du panier
            cart.items.clear()
    else:
        del request.session['cart']
        del request.session['quantity_total']
    return redirect('home')


def paiement_informations(request):
    if request.user.is_authenticated:
        cart = Cart.objects.get(user=request.user)
        products = cart.items.all()
        total_price = cart.get_total_price()

        discount_code = request.session.get('discount_code')
        price = request.session.get('total_price')
        if 'total_price' in request.session:
            del request.session['total_price']
        request.session['discount_code'] = discount_code  # Stocke discount_code en session
        request.session['total_price'] = price
        del request.session['discount_code']

        return render(request, 'market/paiement.html', {'cart': cart,
                                                        'products': products,
                                                        'discount_code': discount_code,
                                                        'total_price': float("{:.2f}".format(total_price)),
                                                        'price': price})
    else:
        return redirect('login')


def update_paiement(request):
    if request.user.is_authenticated:
        cart = get_object_or_404(Cart, user=request.user)
        total_price = cart.get_total_price()

    discount_code = 0
    promotion_code = None

    if request.method == 'POST':
        code = request.POST.get('code')

        try:
            promotion_code = PromotionCode.objects.get(code=code, is_active=True)

            if promotion_code.is_promotion:
                if promotion_code.end_date and promotion_code.end_date < timezone.now():
                    pass
                elif total_price >= promotion_code.min_value:
                    discount_code = promotion_code.value
                    total_price -= (discount_code / 100) * total_price
                    promotion_code.is_used = True
                    if promotion_code.is_unique:
                        promotion_code.is_active = False
                    promotion_code.save()

            elif promotion_code.is_reduction:
                if promotion_code.end_date and promotion_code.end_date < timezone.now():
                    pass
                elif total_price >= promotion_code.min_value:
                    if promotion_code.value >= total_price:
                        discount_code = total_price
                        total_price = 0
                    else:
                        discount_code = promotion_code.value
                        total_price -= discount_code
                    promotion_code.is_used = True
                    if promotion_code.is_unique:
                        promotion_code.is_active = False
                    promotion_code.save()

        except PromotionCode.DoesNotExist:
            pass

    request.session['discount_code'] = discount_code  # Stocke discount_code en session
    request.session['discount_name'] = str(promotion_code)  # Stocke total_price en session
    if 'total_price' in request.session:
        del request.session['total_price']
    request.session['total_price'] = total_price  # Stocke total_price en session
    return redirect('paiement_informations')


def process_payment(request):
    # Récupérer le panier de l'utilisateur connecté
    cart = Cart.objects.get(user=request.user)

    # Récupérer les informations de la commande (somme totale, informations de livraison)
    total_price = request.session.get('total_price')

    if not request.session.get('discount_name'):
        discount_name = ''
    else:
        discount_name = request.session.get('discount_name')

    first_name = request.POST.get('nom')
    last_name = request.POST.get('prenom')
    address = request.POST.get('address')
    zipcode = request.POST.get('zip')
    city = request.POST.get('city')
    mail = request.POST.get('email')
    phone = request.POST.get('phone')
    date = timezone.now()

    delivery_info = f"{first_name} {last_name} {address} {zipcode} {city} {phone}"

    pre_transcation_id = uuid.uuid4().hex[:3]

    # Créer une instance de Order avec les informations de la commande
    order = Order(user=request.user,
                  total_price=total_price,
                  delivery_info=delivery_info,
                  transaction_id=pre_transcation_id,
                  date=date,
                  discount_code=discount_name,
                  statut='Création')
    order.save()

    request.session['order_id'] = order.transaction_id

    # Récupère le montant total à payer depuis ton formulaire
    amount = int(total_price * 100)

    if amount == 0:
        # Mettre à jour le stock des produits
        for cart_item in cart.cart_items.all():
            product = cart_item.product
            quantity = cart_item.quantity
            if product.stock < quantity:
                # Gérer la situation où le stock est insuffisant
                # Vous pouvez afficher un message d'erreur ou effectuer une action appropriée
                # Par exemple, rediriger vers une page d'erreur ou proposer une alternative au client
                pass
            else:
                product.stock -= quantity
                product.save()

                # Ajouter l'élément de commande à la commande
                order_item = OrderItem(order=order, product=product, quantity=quantity)
                order_item.save()

        # Supprimer les produits du panier
        cart.cart_items.all().delete()

        # Supprimer les éléments de la session
        del request.session['total_price']

        if not request.session.get('discount_name'):
            pass
        else:
            del request.session['discount_name']
        return redirect('success')
    else:
        # Crée une session de paiement avec Stripe
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            customer_email=mail,
            client_reference_id=str(order.id),  # Utilise l'ID de l'Order comme client_reference_id
            line_items=[{
                'price_data': {
                    'currency': 'eur',
                    'unit_amount': amount,
                    'product_data': {
                        'name': f"Commande test {order.id}",
                    },
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url='http://localhost:8000/success/',
            cancel_url='http://localhost:8000/cancel/',
        )

        # Mettre à jour le stock des produits
        for cart_item in cart.cart_items.all():
            product = cart_item.product
            quantity = cart_item.quantity
            if product.stock < quantity:
                # Gérer la situation où le stock est insuffisant
                # Vous pouvez afficher un message d'erreur ou effectuer une action appropriée
                # Par exemple, rediriger vers une page d'erreur ou proposer une alternative au client
                pass
            else:
                product.stock -= quantity
                product.save()

                # Ajouter l'élément de commande à la commande
                order_item = OrderItem(order=order, product=product, quantity=quantity)
                order_item.save()

        # Supprimer les produits du panier
        cart.cart_items.all().delete()

        # Supprimer les éléments de la session
        del request.session['total_price']

        if not request.session.get('discount_name'):
            pass
        else:
            del request.session['discount_name']

        # Redirige l'utilisateur vers la page de paiement de Stripe
        return redirect(session.url)


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']

        # Récupère l'ID de l'Order à partir de la session de paiement
        order_id = session['client_reference_id']

        try:
            # Récupère l'objet Order correspondant
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            # Gère le cas où l'Order n'est pas trouvé
            return HttpResponse(status=404)

        # Récupère l'ID du paiement à partir de la session de paiement
        payment_intent_id = session['payment_intent']
        if session['payment_status'] == "paid":
            order.statut = 'Transaction réussie'

        # Met à jour l'objet Order avec l'ID du paiement
        order.transaction_id = payment_intent_id
        order.save()

    return HttpResponse(status=200)


def success(request):
    return render(request, "market/success.html")


def cancel(request):
    # Récupérer l'ID de la commande annulée depuis la session de paiement
    order_id = request.session.get('order_id')

    if order_id:
        try:
            # Récupérer l'objet Order correspondant
            order = Order.objects.get(transaction_id=order_id)

            # Modifier le statut de la commande en 'Erreur'
            order.statut = 'Erreur lors du paiement'
            order.save()

        except Order.DoesNotExist:
            # Gérer le cas où l'Order n'est pas trouvé
            pass
    return render(request, "market/cancel.html")
