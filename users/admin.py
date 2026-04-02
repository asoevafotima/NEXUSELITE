from django.contrib import admin
from .models import Users
 
 
@admin.register(Users)
class UsersAdmin(admin.ModelAdmin):
    list_display  = ('username', 'email', 'is_email_verified', 'get_roles')
    list_filter   = ('is_email_verified', 'groups')
    search_fields = ('username', 'email')
    filter_horizontal = ('groups', 'user_permissions')
 
    def get_roles(self, obj):
        return ', '.join(obj.get_role_names()) or '—'
    get_roles.short_description = 'Roles'
 
