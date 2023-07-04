from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model, login, logout, authenticate
from market.models import Cart, CartItem, Product
from django.db import IntegrityError 

User = get_user_model()


def signup(request):
    if request.method == "POST":
        # traiter
        username = request.POST.get("username")
        password = request.POST.get("password")
        email = request.POST.get("email")
        
        try:
            user = User.objects.create_user(username=username,
                                            password=password,
                                            email=email)
            login(request, user)
            # Ajouter les informations du panier à l'utilisateur connecté
            if 'cart' in request.session:
                cart = request.session.get('cart')
                add_cart_items_to_user(user, cart, request)
            return redirect('home')
        except IntegrityError:  # Si une erreur d'intégrité se produit (nom d'utilisateur déjà pris)
            error_message = "Ce nom d'utilisateur est déjà pris. Veuillez choisir un autre nom d'utilisateur."
            return render(request, "accounts/signup.html", {'error_message': error_message})

    return render(request, "accounts/signup.html")


def login_user(request):
    if request.method == 'POST':
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(username=username, password=password)
        if user:
            login(request, user)

            # Ajouter les informations du panier à l'utilisateur connecté
            if 'cart' in request.session:
                cart = request.session.get('cart')
                add_cart_items_to_user(user, cart, request)

            return redirect('home')

    return render(request, "accounts/login.html")


def logout_user(request):
    logout(request)
    return redirect('home')


def add_cart_items_to_user(user, cart, request):
    user_cart, created = Cart.objects.get_or_create(user=user)

    # Supprimer le panier existant de l'utilisateur
    user_cart.delete_cart()

    # Ajouter les éléments du panier actuel à l'utilisateur
    for product_id, quantity in cart.items():
        product = Product.objects.get(id=product_id)
        cart_item = CartItem(cart=user_cart, product=product, quantity=quantity)
        cart_item.save()

    del request.session['cart']  # Supprimer le panier de la session


