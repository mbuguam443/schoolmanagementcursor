from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse


class Profile(models.Model):
    class Role(models.TextChoices):
        ADMIN = 'admin', 'Administrator'
        TEACHER = 'teacher', 'Teacher'

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
    )
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.TEACHER)
    phone = models.CharField(max_length=20, blank=True)
    avatar_color = models.CharField(max_length=7, default='#6366f1')

    def __str__(self):
        return f'{self.user.get_full_name() or self.user.username} ({self.get_role_display()})'


class AcademicYear(models.Model):
    name = models.CharField(max_length=20, unique=True)
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.is_current:
            AcademicYear.objects.filter(is_current=True).exclude(pk=self.pk).update(
                is_current=False
            )
        super().save(*args, **kwargs)


class GradeLevel(models.Model):
    name = models.CharField(max_length=50, unique=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class Classroom(models.Model):
    grade = models.ForeignKey(GradeLevel, on_delete=models.CASCADE, related_name='classrooms')
    section = models.CharField(max_length=10)
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name='classrooms',
    )
    class_teacher = models.ForeignKey(
        'Teacher',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='homerooms',
    )
    capacity = models.PositiveSmallIntegerField(default=40)

    class Meta:
        ordering = ['grade__order', 'section']
        unique_together = [['grade', 'section', 'academic_year']]

    def __str__(self):
        return f'{self.grade.name} - {self.section}'

    @property
    def display_name(self):
        return f'{self.grade.name} {self.section}'


class Subject(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Teacher(models.Model):
    employee_id = models.CharField(max_length=20, unique=True)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='teacher',
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    hire_date = models.DateField()
    subjects = models.ManyToManyField(Subject, blank=True, related_name='teachers')
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return self.full_name

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    def get_absolute_url(self):
        return reverse('school:teacher_detail', kwargs={'pk': self.pk})


class Student(models.Model):
    class Gender(models.TextChoices):
        MALE = 'M', 'Male'
        FEMALE = 'F', 'Female'
        OTHER = 'O', 'Other'

    admission_number = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=Gender.choices)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    guardian_name = models.CharField(max_length=200)
    guardian_phone = models.CharField(max_length=20)
    enrollment_date = models.DateField()
    classroom = models.ForeignKey(
        Classroom,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='students',
    )
    is_active = models.BooleanField(default=True)
    photo_color = models.CharField(max_length=7, default='#14b8a6')

    class Meta:
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return self.full_name

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    def get_absolute_url(self):
        return reverse('school:student_detail', kwargs={'pk': self.pk})

    @property
    def initials(self):
        return f'{self.first_name[:1]}{self.last_name[:1]}'.upper()


class TimetableEntry(models.Model):
    class Day(models.IntegerChoices):
        MONDAY = 1, 'Monday'
        TUESDAY = 2, 'Tuesday'
        WEDNESDAY = 3, 'Wednesday'
        THURSDAY = 4, 'Thursday'
        FRIDAY = 5, 'Friday'

    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name='timetable')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    day = models.PositiveSmallIntegerField(choices=Day.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()
    room = models.CharField(max_length=50, blank=True)

    class Meta:
        ordering = ['day', 'start_time']
        unique_together = [['classroom', 'day', 'start_time']]

    def __str__(self):
        return f'{self.classroom} - {self.get_day_display()} {self.start_time}'


class Attendance(models.Model):
    class Status(models.TextChoices):
        PRESENT = 'P', 'Present'
        ABSENT = 'A', 'Absent'
        LATE = 'L', 'Late'
        EXCUSED = 'E', 'Excused'

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendance')
    date = models.DateField()
    status = models.CharField(max_length=1, choices=Status.choices, default=Status.PRESENT)
    notes = models.CharField(max_length=255, blank=True)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ['-date']
        unique_together = [['student', 'date']]

    def __str__(self):
        return f'{self.student} - {self.date} ({self.get_status_display()})'


class Exam(models.Model):
    name = models.CharField(max_length=100)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='exams')
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name='exams')
    exam_date = models.DateField()
    max_score = models.PositiveSmallIntegerField(default=100)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)

    class Meta:
        ordering = ['-exam_date']

    def __str__(self):
        return f'{self.name} - {self.subject}'


class GradeRecord(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='grades')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='grades')
    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    remarks = models.CharField(max_length=255, blank=True)

    class Meta:
        unique_together = [['exam', 'student']]
        ordering = ['-score']

    def __str__(self):
        return f'{self.student} - {self.score}'

    @property
    def percentage(self):
        if self.exam.max_score:
            return round(float(self.score) / self.exam.max_score * 100, 1)
        return 0

    @property
    def letter_grade(self):
        pct = self.percentage
        if pct >= 90:
            return 'A'
        if pct >= 80:
            return 'B'
        if pct >= 70:
            return 'C'
        if pct >= 60:
            return 'D'
        return 'F'


class Fee(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PAID = 'paid', 'Paid'
        PARTIAL = 'partial', 'Partial'
        OVERDUE = 'overdue', 'Overdue'

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='fees')
    title = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    paid_on = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['-due_date']

    def __str__(self):
        return f'{self.student} - {self.title}'

    @property
    def balance(self):
        return self.amount - self.paid_amount
