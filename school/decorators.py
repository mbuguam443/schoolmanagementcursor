from functools import wraps

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect

from .permissions import is_school_admin


def admin_required(view_func):
    @login_required
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if is_school_admin(request.user):
            return view_func(request, *args, **kwargs)
        messages.error(request, 'Administrator access is required for that page.')
        return redirect('school:dashboard')

    return wrapper


class AdminRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not is_school_admin(request.user):
            messages.error(request, 'Administrator access is required for that page.')
            return redirect('school:dashboard')
        return super().dispatch(request, *args, **kwargs)
