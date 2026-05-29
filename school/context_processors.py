from .permissions import get_teacher, is_school_admin


def school_permissions(request):
    user = request.user
    if not user.is_authenticated:
        return {'is_school_admin': False, 'current_teacher': None}
    return {
        'is_school_admin': is_school_admin(user),
        'current_teacher': get_teacher(user),
    }
