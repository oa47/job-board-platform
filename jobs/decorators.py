from functools import wraps
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required


def role_required(required_role):
    """
    Decorator to check if user has required role.
    Usage: @role_required('employer') or @role_required('candidate') or @role_required('admin')
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            user = request.user
            
            # Check if user is superuser (admin)
            if required_role == 'admin' and user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            # Check if user has the required role
            if hasattr(user, 'role') and user.role == required_role:
                return view_func(request, *args, **kwargs)
            
            # Redirect to appropriate dashboard if unauthorized
            return redirect('dashboard')
        
        return wrapper
    return decorator
