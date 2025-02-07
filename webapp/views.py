from django.shortcuts import render, get_object_or_404, redirect
from .models import *
from django.http import HttpResponseRedirect
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .forms import *
from uuid import uuid4
from django.utils.text import slugify
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json


# Create your views here.

# def regenerate_slugs():
#     for school in School.objects.all():
#         school.slug = slugify(school.name) + '-' + str(uuid4())
#         school.save()
#
# regenerate_slugs()

# def regenerate_category_slugs():
#     for category in Categories.objects.all():
#         category.slug = generate_category_slug(category.name)
#         category.save()
# regenerate_category_slugs()
# Registration views :-
def register_user(request, slug):
    schools = School.objects.all()
    school = get_object_or_404(School, slug=slug)
    form = SignUpForm()
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()

            profile, created = Profile.objects.get_or_create(user=user)
            profile.school = school
            profile.save()
            mobile_number = request.POST.get('mobile_number')

            if mobile_number:
                profile.mobile_number = mobile_number
                profile.save()

            # Store the selected school in the session
            request.session['school_slug'] = school.slug

            messages.success(request, 'registration is Successful, Please Login!!!...')
            return redirect('login', slug=school.slug)
        else:
            for error in list(form.errors.values()):
                messages.error(request, error)
            return redirect('register', slug=slug)
    else:
        return render(request, 'registration/register.html', {'form': form, 'school': school, 'schools': schools})

# Login views :-
def login_user(request, slug):
    school = get_object_or_404(School, slug=slug)
    schools = School.objects.all()

    if request.method == 'POST':
        username_or_email_or_mobile = request.POST.get('username_or_email_or_mobile')
        password = request.POST.get('password')

        # Try to authenticate using the username
        user = authenticate(request, username=username_or_email_or_mobile, password=password)

        # If not found, try email
        if not user:
            try:
                profile = Profile.objects.get(user__email=username_or_email_or_mobile)
                user = authenticate(request, username=profile.user.username, password=password)
            except Profile.DoesNotExist:
                pass  # Handle invalid email, continue to try mobile

        # If still not found, try mobile number
        if not user:
            try:
                profile = Profile.objects.get(mobile_number=username_or_email_or_mobile)
                user = authenticate(request, username=profile.user.username, password=password)
            except Profile.DoesNotExist:
                pass  # Handle invalid mobile number

        # After trying all options, if the user is authenticated
        if user:
            profile = Profile.objects.get(user=user)

            # Check if the user belongs to the selected school
            if profile.school.id == school.id:
                login(request, user)
                request.session['school_slug'] = school.slug
                return redirect('school_detail', slug=school.slug)
            else:
                messages.error(request, 'The user does not belong to the selected school.')
        else:
            messages.error(request, 'Invalid credentials, please try again.')

    return render(request, 'registration/login.html', {'schools': schools, 'school': school})


def logout_user(request):
    # Clear the school slug from session on logout
    if 'school_slug' in request.session:
        del request.session['school_slug']

    logout(request)
    messages.success(request, "You have successfully logged out from the Orison world!!!")
    return redirect('home')




def home(request):
    schools = School.objects.all()
    query = request.GET.get('query', '')
    if query:
        # If a query is provided, filter the schools by name
        schools = schools.filter(name__icontains=query)
        if schools.exists():
            # Redirect to the register page of the first matched school
            return redirect('register', slug=schools.first().slug)
        else:
            # Show a message if no schools are found
            messages.success(request, f"No schools found for '{query}'.")
            return redirect('home')

    cart_count = 0
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        cart_count = cart.items.count()
    else:
        cart_count = request.session.get("cart_count", 0)

    return render(request, 'index.html', {'schools': schools, 'query': query, 'school': schools.first(), 'cart_count': cart_count })
def about(request):
    schools = School.objects.all()
    query = request.GET.get('query', '')
    if query:
        # If a query is provided, filter the schools by name
        schools = schools.filter(name__icontains=query)
        if schools.exists():
            # Redirect to the register page of the first matched school
            return redirect('register', slug=schools.first().slug)
        else:
            # Show a message if no schools are found
            messages.success(request, f"No schools found for '{query}'.")
            return redirect('about')

    cart_count = 0
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        cart_count = cart.items.count()
    else:
        cart_count = request.session.get("cart_count", 0)

    return render(request,'about.html', {'schools': schools, 'query': query, 'school': schools.first(), 'cart_count': cart_count})


def school_detail(request, slug):
    # First, check if a school is stored in the session
    school_slug = request.session.get('school_slug', None)

    # If a school is in session, use it, otherwise, use the slug from the URL
    if school_slug:
        school = get_object_or_404(School, slug=school_slug)
    else:
        school = get_object_or_404(School, slug=slug)

    # Check if the logged-in user belongs to the school being viewed
    if request.user.is_authenticated:
        user_profile = Profile.objects.get(user=request.user)
        if user_profile.school.slug != school.slug:
            return redirect('login')  # Redirect to login or show an error message
    else:
        return redirect('login')  # Redirect to login if the user is not authenticated

    categories = Categories.objects.filter(school=school)

    # Get the user's cart
    cart = get_user_cart(request)
    cart_count = cart.items.count() if cart else 0

    # categories = Categories.objects.filter(product__school=school).distinct()

    # Add pagination here
    products_by_category = {}
    for category in categories:
        products = Product.objects.filter(school=school, category=category).prefetch_related('sizes')
        paginator = Paginator(products, 8)  # 8 products per page
        page_number = request.GET.get(f'page_{category.slug}', 1)

        try:
            products_page = paginator.page(page_number)
        except PageNotAnInteger:
            products_page = paginator.page(1)
        except EmptyPage:
            products_page = paginator.page(paginator.num_pages)

        products_by_category[category] = products_page

    return render(request, 'schoolscreens/school_detail.html', {
        'school': school,
        'categories': categories,
        'products_by_category': products_by_category,
        'cart': cart,
        'cart_count': cart_count,
    })


def get_user_cart(request):
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
    else:
        session_id = request.session.session_key or request.session.create()
        cart, _ = Cart.objects.get_or_create(session_id=session_id)

    return cart

def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)

    size_id = request.POST.get("size")
    size = Size.objects.get(id=size_id) if size_id else None

    if not size:
        size = None

    quantity = int(request.POST.get("quantity", 1))

    # Check if the item already exists in the cart with the same size
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        size=size
    )

    if not created:
        cart_item.quantity += quantity
        cart_item.save()

    request.session["cart_count"] = cart.items.count()

    messages.success(request, 'Product added to cart!!!')
    return redirect("school_detail", slug=product.school.slug)


def cart_summary(request, slug):
    school = get_object_or_404(School, slug=slug)
    cart = Cart.objects.get(user=request.user) if request.user.is_authenticated else None
    cart_count = cart.items.count() if cart else 0

    total_price = sum(
        (item.product.price or 0) * (item.quantity or 1)  # Default price to 0 and quantity to 1 if None
        for item in cart.items.all()
    ) if cart else 0

    context = {
        'cart': cart,
        'cart_count': cart_count,
        'total_price': total_price,
        'school': school,
    }
    return render(request, 'summary/cart_summary.html', context)

def remove_from_cart(request, item_id):
    cart = Cart.objects.get(user=request.user)
    cart_item = cart.items.filter(id=item_id).first()

    if cart_item:

        school_slug = cart_item.product.school.slug
        cart_item.delete()


        request.session['cart_count'] = cart.items.count()

        messages.success(request, 'Product is Removed!!!')
        return redirect('cart_summary', slug=school_slug)

        # If no cart item found, fallback to home or another page
    return redirect('home')

@csrf_exempt
def update_cart_quantity(request):
    if request.method == "POST":
        data = json.loads(request.body)
        item_id = data.get("item_id")
        new_quantity = data.get("quantity")

        try:
            cart_item = CartItem.objects.get(id=item_id)
            cart_item.quantity = new_quantity
            cart_item.save()
            return JsonResponse({"success": True})
        except CartItem.DoesNotExist:
            return JsonResponse({"success": False, "error": "Item not found"}, status=400)

    return JsonResponse({"success": False, "error": "Invalid request"}, status=400)

def cart_count_api(request):
    cart_count = request.session.get('cart_count', 0)
    return JsonResponse({"cart_count": cart_count})


def checkout(request, slug):
    school = get_object_or_404(School, slug=slug)

    if request.method == 'POST':

        #get form data
        name = request.POST.get("name")
        student_class = request.POST.get("class")
        section = request.POST.get("section")
        phone = request.POST.get("phone")
        address = request.POST.get("address")

        # Get the user's cart
        cart = Cart.objects.get(user=request.user)
        if not cart.items.exists():
            messages.error(request, "Your cart is empty!")
            return redirect("cart_summary", slug=slug)

        # Format items as a user-friendly string
        items_text = "\n".join(
            f"{item.quantity}x {item.product.name} ({item.size.size if item.size else 'No Size'}) - ₹{(item.product.price or 0) * item.quantity}"
            for item in cart.items.all()
        )

        # Calculate total price
        total_price = sum((item.product.price or 0) * item.quantity for item in cart.items.all())

        # Create the order
        Order.objects.create(
            user=request.user,
            school=school,
            name=name,
            student_class=student_class,
            section=section,
            phone=phone,
            address=address,
            total_price=total_price,
            items=items_text,
        )

        # Clear the cart
        cart.items.all().delete()
        request.session["cart_count"] = 0  # Reset session cart count

        messages.success(request, "Order placed successfully!")
        return redirect("home")  # Redirect to homepage after order is placed

    return redirect("home", slug=slug)


def custom_404(request, exception):
    return render(request, '404.html', status=404)

def custom_500(request):
    return render(request, '500.html', status=500)