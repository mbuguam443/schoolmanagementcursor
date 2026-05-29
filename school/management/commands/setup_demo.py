from datetime import date, time, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from school.models import (
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


class Command(BaseCommand):
    help = 'Create demo admin user and sample school data'

    def handle(self, *args, **options):
        user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@kiamburdschool.local',
                'first_name': 'School',
                'last_name': 'Admin',
                'is_staff': True,
                'is_superuser': True,
            },
        )
        if created:
            user.set_password('admin123')
            user.save()
            self.stdout.write(self.style.SUCCESS('Created admin user (admin / admin123)'))
        else:
            user.set_password('admin123')
            user.save()
            self.stdout.write('Reset admin password to admin123')

        Profile.objects.update_or_create(
            user=user,
            defaults={'role': Profile.Role.ADMIN, 'phone': '+1 555 0100'},
        )

        year, _ = AcademicYear.objects.get_or_create(
            name='2025-2026',
            defaults={
                'start_date': date(2025, 9, 1),
                'end_date': date(2026, 6, 30),
                'is_current': True,
            },
        )

        grades_data = [
            ('Grade 9', 9),
            ('Grade 10', 10),
            ('Grade 11', 11),
            ('Grade 12', 12),
        ]
        grade_objs = []
        for name, order in grades_data:
            g, _ = GradeLevel.objects.get_or_create(name=name, defaults={'order': order})
            grade_objs.append(g)

        subjects_data = [
            ('Mathematics', 'MATH'),
            ('English', 'ENG'),
            ('Science', 'SCI'),
            ('History', 'HIS'),
            ('Computer Science', 'CS'),
            ('Physical Education', 'PE'),
        ]
        subject_objs = []
        for name, code in subjects_data:
            s, _ = Subject.objects.get_or_create(code=code, defaults={'name': name})
            subject_objs.append(s)

        teachers_data = [
            ('T001', 'Sarah', 'Johnson', 'sarah.j@school.edu'),
            ('T002', 'Michael', 'Chen', 'michael.c@school.edu'),
            ('T003', 'Emily', 'Davis', 'emily.d@school.edu'),
            ('T004', 'James', 'Wilson', 'james.w@school.edu'),
        ]
        teacher_objs = []
        for eid, fn, ln, email in teachers_data:
            t, _ = Teacher.objects.get_or_create(
                employee_id=eid,
                defaults={
                    'first_name': fn,
                    'last_name': ln,
                    'email': email,
                    'hire_date': date(2020, 8, 15),
                    'phone': '+1 555 0200',
                },
            )
            t.subjects.set(subject_objs[:3])
            teacher_objs.append(t)

        classrooms = []
        for grade in grade_objs[:2]:
            for section in ['A', 'B']:
                room, _ = Classroom.objects.get_or_create(
                    grade=grade,
                    section=section,
                    academic_year=year,
                    defaults={
                        'class_teacher': teacher_objs[0],
                        'capacity': 35,
                    },
                )
                classrooms.append(room)

        students_data = [
            ('STU001', 'Alex', 'Martinez', 'M'),
            ('STU002', 'Jordan', 'Lee', 'F'),
            ('STU003', 'Taylor', 'Brown', 'O'),
            ('STU004', 'Casey', 'Nguyen', 'F'),
            ('STU005', 'Riley', 'Smith', 'M'),
            ('STU006', 'Morgan', 'Garcia', 'F'),
            ('STU007', 'Jamie', 'Patel', 'M'),
            ('STU008', 'Avery', 'Kim', 'F'),
            ('STU009', 'Quinn', 'Okafor', 'M'),
            ('STU010', 'Skyler', 'Wright', 'F'),
        ]
        colors = ['#6366f1', '#14b8a6', '#f59e0b', '#ec4899', '#8b5cf6']
        student_objs = []
        for i, (adm, fn, ln, gender) in enumerate(students_data):
            s, _ = Student.objects.get_or_create(
                admission_number=adm,
                defaults={
                    'first_name': fn,
                    'last_name': ln,
                    'date_of_birth': date(2008, 3, 15) - timedelta(days=i * 40),
                    'gender': gender,
                    'guardian_name': f'{ln} Family',
                    'guardian_phone': '+1 555 030%d' % i,
                    'enrollment_date': date(2025, 9, 1),
                    'classroom': classrooms[i % len(classrooms)],
                    'photo_color': colors[i % len(colors)],
                },
            )
            student_objs.append(s)

        if not TimetableEntry.objects.exists():
            room = classrooms[0]
            slots = [
                (1, subject_objs[0], teacher_objs[0], time(8, 0), time(9, 0)),
                (1, subject_objs[1], teacher_objs[1], time(9, 15), time(10, 15)),
                (2, subject_objs[2], teacher_objs[2], time(8, 0), time(9, 0)),
                (3, subject_objs[4], teacher_objs[3], time(10, 30), time(11, 30)),
            ]
            for day, subj, teach, start, end in slots:
                TimetableEntry.objects.create(
                    classroom=room,
                    subject=subj,
                    teacher=teach,
                    day=day,
                    start_time=start,
                    end_time=end,
                    room='101',
                )

        today = date.today()
        for student in student_objs[:6]:
            Attendance.objects.get_or_create(
                student=student,
                date=today,
                defaults={
                    'status': Attendance.Status.PRESENT,
                    'recorded_by': user,
                },
            )

        exam, _ = Exam.objects.get_or_create(
            name='Mid-Term Mathematics',
            subject=subject_objs[0],
            classroom=classrooms[0],
            academic_year=year,
            defaults={'exam_date': today + timedelta(days=14), 'max_score': 100},
        )
        for student in student_objs[:5]:
            if student.classroom == classrooms[0]:
                GradeRecord.objects.get_or_create(
                    exam=exam,
                    student=student,
                    defaults={'score': Decimal('75') + student_objs.index(student) * 4},
                )

        for i, student in enumerate(student_objs[:4]):
            Fee.objects.get_or_create(
                student=student,
                title='Tuition — Term 1',
                defaults={
                    'amount': Decimal('1200.00'),
                    'due_date': today + timedelta(days=30),
                    'status': Fee.Status.PENDING if i % 2 else Fee.Status.PAID,
                    'paid_amount': Decimal('0') if i % 2 else Decimal('1200.00'),
                    'paid_on': None if i % 2 else today,
                },
            )

        self.stdout.write(self.style.SUCCESS('Demo data loaded successfully!'))
        self.stdout.write('Run: python manage.py runserver')
        self.stdout.write('Login: admin / admin123')
