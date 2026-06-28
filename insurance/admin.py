from django.contrib import admin
from .models import UserProfile,Policy,Claim


admin.site.register(UserProfile)
admin.site.register(Policy)
admin.site.register(Claim)
# Register your models here.
