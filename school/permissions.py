"""Role-based access helpers for administrators and teachers."""

from django.db.models import Q

from .models import Classroom, Exam, Profile, Student, Teacher, TimetableEntry


def is_school_admin(user):
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    profile = getattr(user, 'profile', None)
    return bool(profile and profile.role == Profile.Role.ADMIN)


def get_teacher(user):
    if not user.is_authenticated:
        return None
    return getattr(user, 'teacher', None)


def teacher_classrooms(teacher):
    if not teacher:
        return Classroom.objects.none()
    timetable_ids = TimetableEntry.objects.filter(teacher=teacher).values_list(
        'classroom_id', flat=True
    )
    return Classroom.objects.filter(
        Q(class_teacher=teacher) | Q(pk__in=timetable_ids)
    ).distinct()


def teacher_classroom_ids(teacher):
    return teacher_classrooms(teacher).values_list('pk', flat=True)


def teacher_students(teacher):
    return Student.objects.filter(
        classroom_id__in=teacher_classroom_ids(teacher),
        is_active=True,
    )


def teacher_exams(teacher):
    return Exam.objects.filter(classroom_id__in=teacher_classroom_ids(teacher))


def teacher_can_access_student(user, student):
    if is_school_admin(user):
        return True
    teacher = get_teacher(user)
    if not teacher or not student.classroom_id:
        return False
    return student.classroom_id in teacher_classroom_ids(teacher)


def teacher_can_access_classroom(user, classroom):
    if is_school_admin(user):
        return True
    teacher = get_teacher(user)
    if not teacher:
        return False
    return classroom.pk in teacher_classroom_ids(teacher)


def teacher_can_access_exam(user, exam):
    if is_school_admin(user):
        return True
    teacher = get_teacher(user)
    if not teacher:
        return False
    return exam.classroom_id in teacher_classroom_ids(teacher)
