from datetime import date
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.db.models import Avg, Count, Q, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .analytics import build_dashboard_charts
from .decorators import admin_required
from .pdf_utils import render_html_to_pdf
from .report_card import build_report_card_context
from .forms import (
    AcademicYearForm,
    AttendanceBulkForm,
    ClassroomForm,
    ExamForm,
    FeeForm,
    GradeLevelForm,
    GradeRecordForm,
    LoginForm,
    StudentForm,
    SubjectForm,
    TeacherForm,
    TimetableForm,
)
from .models import (
    AcademicYear,
    Attendance,
    Classroom,
    Exam,
    Fee,
    GradeLevel,
    GradeRecord,
    Student,
    Subject,
    Teacher,
    TimetableEntry,
)


class SchoolLoginView(LoginView):
    template_name = 'school/login.html'
    authentication_form = LoginForm
    redirect_authenticated_user = True


def logout_view(request):
    logout(request)
    return redirect('school:login')


@login_required
def dashboard(request):
    today = date.today()
    stats = {
        'students': Student.objects.filter(is_active=True).count(),
        'teachers': Teacher.objects.filter(is_active=True).count(),
        'classrooms': Classroom.objects.count(),
        'subjects': Subject.objects.count(),
        'present_today': Attendance.objects.filter(date=today, status=Attendance.Status.PRESENT).count(),
        'absent_today': Attendance.objects.filter(date=today, status=Attendance.Status.ABSENT).count(),
        'fees_pending': Fee.objects.filter(status__in=[Fee.Status.PENDING, Fee.Status.OVERDUE]).count(),
        'fees_collected': Fee.objects.aggregate(total=Sum('paid_amount'))['total'] or Decimal('0'),
    }
    recent_students = Student.objects.filter(is_active=True).select_related('classroom__grade')[:5]
    upcoming_exams = Exam.objects.select_related('subject', 'classroom__grade')[:5]
    attendance_trend = (
        Attendance.objects.filter(date__gte=today.replace(day=1))
        .values('status')
        .annotate(count=Count('id'))
    )
    top_classrooms = (
        Student.objects.filter(is_active=True, classroom__isnull=False)
        .values('classroom__grade__name', 'classroom__section')
        .annotate(count=Count('id'))
        .order_by('-count')[:5]
    )
    charts = build_dashboard_charts(today)
    return render(request, 'school/dashboard.html', {
        'stats': stats,
        'recent_students': recent_students,
        'upcoming_exams': upcoming_exams,
        'attendance_trend': attendance_trend,
        'top_classrooms': top_classrooms,
        'today': today,
        'charts': charts,
    })


class StudentListView(LoginRequiredMixin, ListView):
    model = Student
    template_name = 'school/student_list.html'
    context_object_name = 'students'
    paginate_by = 12

    def get_queryset(self):
        qs = Student.objects.select_related('classroom__grade', 'classroom__academic_year')
        q = self.request.GET.get('q', '').strip()
        classroom = self.request.GET.get('classroom', '')
        if q:
            qs = qs.filter(
                Q(first_name__icontains=q)
                | Q(last_name__icontains=q)
                | Q(admission_number__icontains=q)
            )
        if classroom:
            qs = qs.filter(classroom_id=classroom)
        status = self.request.GET.get('status', 'active')
        if status == 'active':
            qs = qs.filter(is_active=True)
        elif status == 'inactive':
            qs = qs.filter(is_active=False)
        elif status == 'all':
            pass
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['classrooms'] = Classroom.objects.select_related('grade')
        ctx['search_query'] = self.request.GET.get('q', '')
        ctx['selected_classroom'] = self.request.GET.get('classroom', '')
        ctx['status_filter'] = self.request.GET.get('status', 'active')
        return ctx


class StudentDetailView(LoginRequiredMixin, DetailView):
    model = Student
    template_name = 'school/student_detail.html'
    context_object_name = 'student'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        student = self.object
        ctx['attendance'] = student.attendance.order_by('-date')[:10]
        ctx['grades'] = student.grades.select_related('exam__subject').order_by('-exam__exam_date')[:10]
        ctx['fees'] = student.fees.all()[:10]
        return ctx


@login_required
def report_card(request, pk):
    student = get_object_or_404(Student, pk=pk)
    context = build_report_card_context(student)
    context['student'] = student
    return render(request, 'school/report_card.html', context)


@login_required
def report_card_pdf(request, pk):
    student = get_object_or_404(Student, pk=pk)
    context = build_report_card_context(student)
    context['student'] = student
    pdf_bytes, error = render_html_to_pdf('school/report_card_document.html', context, request=request)
    if error:
        messages.error(request, error)
        return redirect('school:report_card', pk=pk)
    filename = f'report_card_{student.admission_number}.pdf'
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


class StudentCreateView(LoginRequiredMixin, CreateView):
    model = Student
    form_class = StudentForm
    template_name = 'school/form_page.html'
    success_url = reverse_lazy('school:student_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(page_title='Add Student', page_subtitle='Register a new student', back_url=reverse('school:student_list'))
        return ctx

    def form_valid(self, form):
        messages.success(self.request, 'Student added successfully.')
        return super().form_valid(form)


class StudentUpdateView(LoginRequiredMixin, UpdateView):
    model = Student
    form_class = StudentForm
    template_name = 'school/form_page.html'
    success_url = reverse_lazy('school:student_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(page_title='Edit Student', page_subtitle=self.object.full_name, back_url=reverse('school:student_list'))
        return ctx

    def form_valid(self, form):
        messages.success(self.request, 'Student updated successfully.')
        return super().form_valid(form)


class StudentDeleteView(LoginRequiredMixin, DeleteView):
    model = Student
    template_name = 'school/confirm_delete.html'
    success_url = reverse_lazy('school:student_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['object_label'] = self.object.full_name
        return ctx


class TeacherListView(LoginRequiredMixin, ListView):
    model = Teacher
    template_name = 'school/teacher_list.html'
    context_object_name = 'teachers'
    paginate_by = 12

    def get_queryset(self):
        qs = Teacher.objects.prefetch_related('subjects')
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(first_name__icontains=q)
                | Q(last_name__icontains=q)
                | Q(employee_id__icontains=q)
            )
        return qs.filter(is_active=True) if self.request.GET.get('status', 'active') == 'active' else qs


class TeacherDetailView(LoginRequiredMixin, DetailView):
    model = Teacher
    template_name = 'school/teacher_detail.html'
    context_object_name = 'teacher'


class TeacherCreateView(LoginRequiredMixin, CreateView):
    model = Teacher
    form_class = TeacherForm
    template_name = 'school/form_page.html'
    success_url = reverse_lazy('school:teacher_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(page_title='Add Teacher', page_subtitle='Register teaching staff', back_url=reverse('school:teacher_list'))
        return ctx

    def form_valid(self, form):
        messages.success(self.request, 'Teacher added successfully.')
        return super().form_valid(form)


class TeacherUpdateView(LoginRequiredMixin, UpdateView):
    model = Teacher
    form_class = TeacherForm
    template_name = 'school/form_page.html'
    success_url = reverse_lazy('school:teacher_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(page_title='Edit Teacher', page_subtitle=self.object.full_name, back_url=reverse('school:teacher_list'))
        return ctx


class TeacherDeleteView(LoginRequiredMixin, DeleteView):
    model = Teacher
    template_name = 'school/confirm_delete.html'
    success_url = reverse_lazy('school:teacher_list')


class ClassroomListView(LoginRequiredMixin, ListView):
    model = Classroom
    template_name = 'school/classroom_list.html'
    context_object_name = 'classrooms'

    def get_queryset(self):
        return Classroom.objects.select_related('grade', 'academic_year', 'class_teacher').annotate(
            student_count=Count('students', filter=Q(students__is_active=True))
        )


class ClassroomCreateView(LoginRequiredMixin, CreateView):
    model = Classroom
    form_class = ClassroomForm
    template_name = 'school/form_page.html'
    success_url = reverse_lazy('school:classroom_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(page_title='Add Classroom', page_subtitle='Create a new class section', back_url=reverse('school:classroom_list'))
        return ctx


class SubjectListView(LoginRequiredMixin, ListView):
    model = Subject
    template_name = 'school/subject_list.html'
    context_object_name = 'subjects'


class SubjectCreateView(LoginRequiredMixin, CreateView):
    model = Subject
    form_class = SubjectForm
    template_name = 'school/form_page.html'
    success_url = reverse_lazy('school:subject_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(page_title='Add Subject', page_subtitle='Curriculum subject', back_url=reverse('school:subject_list'))
        return ctx


class SubjectUpdateView(LoginRequiredMixin, UpdateView):
    model = Subject
    form_class = SubjectForm
    template_name = 'school/form_page.html'
    success_url = reverse_lazy('school:subject_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(page_title='Edit Subject', page_subtitle=self.object.name, back_url=reverse('school:subject_list'))
        return ctx


class SubjectDeleteView(LoginRequiredMixin, DeleteView):
    model = Subject
    template_name = 'school/confirm_delete.html'
    success_url = reverse_lazy('school:subject_list')


@login_required
def timetable_view(request):
    classroom_id = request.GET.get('classroom')
    classrooms = Classroom.objects.select_related('grade', 'academic_year')
    selected = None
    entries = TimetableEntry.objects.none()
    if classroom_id:
        selected = get_object_or_404(Classroom, pk=classroom_id)
        entries = (
            TimetableEntry.objects.filter(classroom=selected)
            .select_related('subject', 'teacher')
            .order_by('day', 'start_time')
        )
    days = TimetableEntry.Day.choices
    grid = {}
    if selected:
        for day_val, day_label in days:
            grid[day_val] = {
                'label': day_label,
                'slots': [e for e in entries if e.day == day_val],
            }
    return render(request, 'school/timetable.html', {
        'classrooms': classrooms,
        'selected_classroom': selected,
        'grid': grid,
        'days': days,
    })


class TimetableCreateView(LoginRequiredMixin, CreateView):
    model = TimetableEntry
    form_class = TimetableForm
    template_name = 'school/form_page.html'
    success_url = reverse_lazy('school:timetable')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(page_title='Add Timetable Slot', page_subtitle='Schedule a class period', back_url=reverse('school:timetable'))
        return ctx


@login_required
def attendance_mark(request):
    form = AttendanceBulkForm(request.GET or None)
    rows = []
    selected_date = request.GET.get('date') or str(date.today())
    selected_classroom = request.GET.get('classroom')

    if request.method == 'POST':
        mark_date = request.POST.get('date')
        classroom_id = request.POST.get('classroom')
        classroom = get_object_or_404(Classroom, pk=classroom_id)
        students = Student.objects.filter(classroom=classroom, is_active=True)
        for student in students:
            status = request.POST.get(f'status_{student.pk}', Attendance.Status.PRESENT)
            Attendance.objects.update_or_create(
                student=student,
                date=mark_date,
                defaults={'status': status, 'recorded_by': request.user},
            )
        messages.success(request, f'Attendance saved for {mark_date}.')
        return redirect(f"{reverse('school:attendance_mark')}?date={mark_date}&classroom={classroom_id}")

    if selected_classroom:
        classroom = get_object_or_404(Classroom, pk=selected_classroom)
        students = Student.objects.filter(classroom=classroom, is_active=True)
        existing = {
            a.student_id: a.status
            for a in Attendance.objects.filter(
                date=selected_date,
                student__in=students,
            )
        }
        for student in students:
            rows.append({
                'student': student,
                'status': existing.get(student.pk, Attendance.Status.PRESENT),
            })

    return render(request, 'school/attendance_mark.html', {
        'form': form,
        'rows': rows,
        'selected_date': selected_date,
        'selected_classroom': selected_classroom,
    })


class ExamListView(LoginRequiredMixin, ListView):
    model = Exam
    template_name = 'school/exam_list.html'
    context_object_name = 'exams'

    def get_queryset(self):
        return Exam.objects.select_related('subject', 'classroom__grade', 'academic_year')


class ExamCreateView(LoginRequiredMixin, CreateView):
    model = Exam
    form_class = ExamForm
    template_name = 'school/form_page.html'
    success_url = reverse_lazy('school:exam_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(page_title='Schedule Exam', page_subtitle='Create a new examination', back_url=reverse('school:exam_list'))
        return ctx


@login_required
def exam_grades(request, pk):
    exam = get_object_or_404(Exam.objects.select_related('subject', 'classroom'), pk=pk)
    students = Student.objects.filter(classroom=exam.classroom, is_active=True)
    existing = {g.student_id: g for g in GradeRecord.objects.filter(exam=exam)}

    if request.method == 'POST':
        for student in students:
            score = request.POST.get(f'score_{student.pk}', '').strip()
            if score:
                GradeRecord.objects.update_or_create(
                    exam=exam,
                    student=student,
                    defaults={'score': Decimal(score)},
                )
        messages.success(request, 'Grades saved successfully.')
        return redirect('school:exam_grades', pk=pk)

    rows = []
    for student in students:
        record = existing.get(student.pk)
        rows.append({'student': student, 'record': record})

    class_avg = existing and GradeRecord.objects.filter(exam=exam).aggregate(avg=Avg('score'))['avg']

    return render(request, 'school/exam_grades.html', {
        'exam': exam,
        'rows': rows,
        'class_avg': class_avg,
    })


class FeeListView(LoginRequiredMixin, ListView):
    model = Fee
    template_name = 'school/fee_list.html'
    context_object_name = 'fees'
    paginate_by = 15

    def get_queryset(self):
        qs = Fee.objects.select_related('student')
        status = self.request.GET.get('status', '')
        if status:
            qs = qs.filter(status=status)
        return qs


class FeeCreateView(LoginRequiredMixin, CreateView):
    model = Fee
    form_class = FeeForm
    template_name = 'school/fee_form.html'
    success_url = reverse_lazy('school:fee_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(page_title='Record Fee', page_subtitle='Student fee entry', back_url=reverse('school:fee_list'))
        return ctx


class FeeUpdateView(LoginRequiredMixin, UpdateView):
    model = Fee
    form_class = FeeForm
    template_name = 'school/fee_form.html'
    success_url = reverse_lazy('school:fee_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(page_title='Update Fee', page_subtitle=self.object.title, back_url=reverse('school:fee_list'))
        return ctx


@login_required
@admin_required
def settings_view(request):
    years = AcademicYear.objects.all()
    grades = GradeLevel.objects.all()
    year_form = AcademicYearForm(request.POST or None, prefix='year')
    grade_form = GradeLevelForm(request.POST or None, prefix='grade')

    if request.method == 'POST':
        if 'year' in request.POST and year_form.is_valid():
            year_form.save()
            messages.success(request, 'Academic year saved.')
            return redirect('school:settings')
        if 'grade' in request.POST and grade_form.is_valid():
            grade_form.save()
            messages.success(request, 'Grade level saved.')
            return redirect('school:settings')

    return render(request, 'school/settings.html', {
        'years': years,
        'grades': grades,
        'year_form': year_form,
        'grade_form': grade_form,
    })
