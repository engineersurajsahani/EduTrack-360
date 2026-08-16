from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages

def role_required(*allowed_roles):
    """Decorator to restrict view access to specific user roles."""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.warning(request, "Please log in to access this page.")
                return redirect('accounts:login')
            
            # Superuser always has access
            if request.user.is_superuser or request.user.role in allowed_roles:
                return view_func(request, *args, **kwargs)
                
            messages.error(request, "Access Denied: You do not have permission to view this resource.")
            return redirect('dashboard:redirect_view')
        return _wrapped_view
    return decorator

def admin_required(view_func):
    return role_required('ADMIN')(view_func)

def faculty_required(view_func):
    return role_required('FACULTY', 'HOD', 'ADMIN')(view_func)

def student_required(view_func):
    return role_required('STUDENT')(view_func)
