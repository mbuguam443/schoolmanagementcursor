from django.contrib import admin

from .models import (
    AcademicYear,
    Attendance,
    Classroom,
    Exam,
    Fee,
    GradeLevel,
    GradeRecord,
    Profile,
    Student,
    Subject,
    Teacher,
    TimetableEntry,
)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'phone']


@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ['name', 'start_date', 'end_date', 'is_current']


@admin.register(GradeLevel)
class GradeLevelAdmin(admin.ModelAdmin):
    list_display = ['name', 'order']


@admin.register(Classroom)
class ClassroomAdmin(admin.ModelAdmin):
    list_display = ['display_name', 'academic_year', 'class_teacher', 'capacity']


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['code', 'name']


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ['employee_id', 'full_name', 'email', 'is_active']
    filter_horizontal = ['subjects']


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['admission_number', 'full_name', 'classroom', 'is_active']
    list_filter = ['classroom', 'gender', 'is_active']


@admin.register(TimetableEntry)
class TimetableAdmin(admin.ModelAdmin):
    list_display = ['classroom', 'day', 'subject', 'teacher', 'start_time']


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['student', 'date', 'status']
    list_filter = ['date', 'status']


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ['name', 'subject', 'classroom', 'exam_date']


@admin.register(GradeRecord)
class GradeRecordAdmin(admin.ModelAdmin):
    list_display = ['student', 'exam', 'score']


@admin.register(Fee)
class FeeAdmin(admin.ModelAdmin):
    list_display = ['student', 'title', 'amount', 'status', 'due_date']
