from django.db import models
from datetime import datetime
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.utils.text import slugify
from uuid import uuid4

# Create your models here.

def generate_slug(school_name):
    """Generate a unique slug using the school name and a UUID for uniqueness."""
    base_slug = slugify(school_name)
    return f"{base_slug}-{uuid4().hex[:8]}"  # Short UUID to ensure uniqueness


class School(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='schools/', blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    slug = models.SlugField(unique=True, blank=True)  # Slug must be unique
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_slug(self.name)

        # Ensure the slug is unique
        while School.objects.filter(slug=self.slug).exists():
            self.slug = generate_slug(self.name)  # Regenerate if the slug already exists

        super(School, self).save(*args, **kwargs)

    def __str__(self):
        return self.name


# Create Category model and slug for dynamic urls :-

def generate_category_slug(category_name):
    """Generate a slug from the category name and ensure it's unique."""
    base_slug = slugify(category_name)
    # Check if the base slug already exists in the database
    if Categories.objects.filter(slug=base_slug).exists():
        return f"{base_slug}-{uuid4().hex[:8]}"
    return base_slug


class Categories(models.Model):
    name = models.CharField(max_length=100)
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='categories', null=True, blank=True)
    description = models.TextField(blank=True, null=True)
    slug = models.SlugField(unique=True, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.slug:  # Only generate slug if not already set
            self.slug = generate_category_slug(self.name)

        super(Categories, self).save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Categories"


class Size(models.Model):
    category = models.ForeignKey(Categories, on_delete=models.CASCADE, related_name="size")
    #school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="size")
    size = models.CharField(max_length=100)  # Size as a string like '40/28', '30.32', '2,3,4'

    # def __str__(self):
    #     return f"{self.category.name} ({self.size})"

    class Meta:
        unique_together = ('size', 'category')

    def __str__(self):
        return self.size

class Product(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    category = models.ForeignKey(Categories, on_delete=models.CASCADE, default=1)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    sizes = models.ManyToManyField(Size, blank=True)
    stock = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to='products/')
    created_at = models.DateTimeField(default=datetime.now, blank=True)

    def __str__(self):
        return self.name

# create Customer profile
class Profile(models.Model):
    DoesNotExist = None
    objects = None
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    school = models.ForeignKey(School, on_delete=models.SET_NULL, null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    date_modified = models.DateTimeField(User, auto_now=True)
    mobile_number = models.CharField(max_length=20, blank=True)
    address1 = models.CharField(max_length=200, blank=True)
    address2 = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=200, blank=True)
    state = models.CharField(max_length=200, blank=True)
    zipcode = models.CharField(max_length=200, blank=True)
    country = models.CharField(max_length=200, blank=True)
    old_cart = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return self.user.username


# create a user profile by default when user signs up
def create_profile(sender, instance, created, **kwargs):
    if created:
        user_profile = Profile(user=instance)
        user_profile.save()


# automate the profile
post_save.connect(create_profile, sender=User)