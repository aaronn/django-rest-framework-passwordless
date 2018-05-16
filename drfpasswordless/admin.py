from django.contrib import admin
from django.urls import reverse
from drfpasswordless.models import CallbackToken


class UserLinkMixin(object):
    """
    A mixin to add a linkable list_display user field.
    """
    LINK_TO_USER_FIELD = 'link_to_user'

    def link_to_user(self, obj):
        link = reverse('admin:users_user_change', args=[obj.user.id])
        return u'<a href={}>{}</a>'.format(link, obj.user.username)
    link_to_user.allow_tags = True
    link_to_user.short_description = 'User'


class AbstractCallbackTokenInline(admin.StackedInline):
    max_num = 0
    extra = 0
    readonly_fields = ('created_at', 'key', 'is_active')
    fields = ('created_at', 'user', 'key', 'is_active')


class CallbackInline(AbstractCallbackTokenInline):
    model = CallbackToken


class AbstractCallbackTokenAdmin(UserLinkMixin, admin.ModelAdmin):
    readonly_fields = ('created_at', 'user', 'key')
    list_display = ('created_at', UserLinkMixin.LINK_TO_USER_FIELD, 'key', 'is_active')
    fields = ('created_at', 'user', 'key', 'is_active')
    extra = 0
