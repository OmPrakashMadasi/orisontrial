from django.shortcuts import render, get_object_or_404, redirect
from .models import *
from django.http import HttpResponseRedirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .forms import *
from uuid import uuid4
from django.utils.text import slugify
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
# Create your views here.

def regenerate_slugs():
    for school in School.objects.all():
        school.slug = slugify(school.name) + '-' + str(uuid4())
        school.save()

regenerate_slugs()

def regenerate_category_slugs():
    for category in Categories.objects.all():
        category.slug = generate_category_slug(category.name)
        category.save()
regenerate_category_slugs()
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

            messages.success(request, 'Congratulations you are into the orison world!!!...')
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
        form = AuthenticationForm(request, data=request.POST)

        if form.is_valid():
            username_or_email_or_mobile = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')

            # Try to authenticate using username first
            user = authenticate(request, username=username_or_email_or_mobile, password=password)

            # If authentication fails using username, try email
            if user is None:
                try:
                    user = authenticate(request, username=Profile.objects.get(email=username_or_email_or_mobile).user.username, password=password)
                except Profile.DoesNotExist:
                    pass  # Handle invalid email

            # If authentication fails using email, try mobile number
            if user is None:
                try:
                    profile = Profile.objects.get(mobile_number=username_or_email_or_mobile)
                    user = authenticate(request, username=profile.user.username, password=password)
                except Profile.DoesNotExist:
                    pass  # Handle invalid mobile number

            # After authentication, check if the user is valid and belongs to the selected school
            if user is not None:
                profile = Profile.objects.get(user=user)
                if profile.school.id == school.id:
                    login(request, user)

                    # Store the selected school in session
                    request.session['school_slug'] = school.slug

                    return redirect('school_detail', slug=school.slug)
                else:
                    form.add_error(None, 'Please check the school')
            else:
                form.add_error(None, 'Invalid Credentials')
        else:
            for error in list(form.errors.values()):
                messages.error(request, error)

    else:
        form = AuthenticationForm()

    return render(request, 'registration/login.html', {'schools': schools, 'form': form, 'school': school})


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

    return render(request, 'index.html', {'schools': schools, 'query': query, 'school': schools.first() })
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
    return render(request,'about.html', {'schools': schools, 'query': query, 'school': schools.first()})


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

    # categories = Categories.objects.filter(product__school=school).distinct()

    # Add pagination here
    products_by_category = {}
    for category in categories:
        products = Product.objects.filter(school=school, category=category).prefetch_related('sizes')
        paginator = Paginator(products, 8)  # 8 products per page
        page_number = request.GET.get(f'page_{category.slug}')

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
    })



def search(request, slug):
    school = get_object_or_404(School, slug=slug)
    query = request.GET.get('searched', '')  # Get the search query from the GET request
    sort_by = request.GET.get('sort', 'created_at')  # Default sorting by 'name'
    if query:
        # Query the Product model to find matches
        searched = Product.objects.filter(Q(name__icontains=query) | Q(description__icontains=query))

        # Order the results based on the 'sort' parameter
        searched = searched.order_by(sort_by)

        # Pagination logic
        paginator = Paginator(searched, 8)  # Show 12 products per page
        page_number = request.GET.get('page')  # Get the page number from query parameters
        page_obj = paginator.get_page(page_number)

        # Check if any products were found
        if page_obj:
            return render(request, 'search.html', {'searched': page_obj, 'school': school, 'query': query})
        else:
            messages.error(request, "That product does not exist. Please try again.")
            return render(request, 'schoolscreens/school_detail.html', {'query': query})
    else:
        messages.error(request, "No Input found")
        return redirect('home')


