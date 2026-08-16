from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from accounts.models import User, Department, FacultyProfile
from academics.models import Program, Branch, AcademicYear, Semester, Subject, SubjectTask, Submission
from activities.models import ActivityCategory, ActivityCertificate
from certificates.models import Certificate, DigitalNOC, Badge, StudentBadge
from students.models import StudentProfile
from certificates.pdf_generator import generate_certificate_pdf, generate_certificate_qr, generate_noc_pdf, generate_noc_qr

class EduTrack360CalculationTests(TestCase):
    def setUp(self):
        self.dept = Department.objects.create(name='Computer Engineering', code='COMP')
        self.prog = Program.objects.create(name='B.E.', code='BE')
        self.branch = Branch.objects.create(program=self.prog, name='Computer Engineering', code='CE', department=self.dept)
        self.ay = AcademicYear.objects.create(name='Second Year', year_number=2, code='SE')
        self.sem = Semester.objects.create(academic_year=self.ay, number=3, roman_name='III')

        self.student_user = User.objects.create_user(
            username='test_sayali',
            password='password123',
            first_name='Sayali',
            last_name='Virkar',
            role=User.Role.STUDENT
        )
        self.student = StudentProfile.objects.create(
            user=self.student_user,
            prn='2026CE099',
            roll_no='99',
            program=self.prog,
            branch=self.branch,
            academic_year=self.ay,
            semester=self.sem,
            attendance_percentage=90.0
        )

        # Faculty User
        self.faculty_user = User.objects.create_user(
            username='prof_anjali',
            password='password123',
            first_name='Anjali',
            last_name='Deshmukh',
            role=User.Role.FACULTY,
            is_staff=True
        )
        self.faculty = FacultyProfile.objects.create(
            user=self.faculty_user,
            employee_id='FAC-CE-101',
            designation='Assistant Professor'
        )

        # Subject: DCN (100% completion test)
        self.sub_dcn = Subject.objects.create(
            branch=self.branch,
            semester=self.sem,
            code='DCN',
            name='Data Communication & Networks',
            assigned_faculty=self.faculty,
            assignment_weight=40,
            microproject_weight=40,
            practical_weight=20,
            ppt_manual_weight=0
        )

        # Create tasks
        self.task_assign = SubjectTask.objects.create(
            subject=self.sub_dcn,
            task_type=SubjectTask.TaskType.ASSIGNMENT,
            title='Assignment 1',
            max_marks=25
        )
        self.task_micro = SubjectTask.objects.create(
            subject=self.sub_dcn,
            task_type=SubjectTask.TaskType.MICROPROJECT,
            title='Microproject',
            max_marks=50
        )
        self.task_prac = SubjectTask.objects.create(
            subject=self.sub_dcn,
            task_type=SubjectTask.TaskType.PRACTICAL,
            title='Practical 1',
            max_marks=25
        )

        # Categories
        self.cat_nss = ActivityCategory.objects.create(code='NSS', name='NSS', target_points=20)
        self.cat_cult = ActivityCategory.objects.create(code='CULTURAL', name='Cultural', target_points=20)
        self.cat_sport = ActivityCategory.objects.create(code='SPORTS', name='Sports', target_points=20)
        self.cat_intern = ActivityCategory.objects.create(code='INTERNSHIP', name='Internship', target_points=20)
        self.cat_work = ActivityCategory.objects.create(code='WORKSHOP', name='Workshop', target_points=20)
        self.cat_hack = ActivityCategory.objects.create(code='HACKATHON', name='Hackathon', target_points=20)
        self.cat_course = ActivityCategory.objects.create(code='COURSES', name='Courses', target_points=20)

    def test_subject_progress_calculation(self):
        """Test weighted subject calculation."""
        Submission.objects.create(task=self.task_assign, student=self.student, status=Submission.Status.APPROVED)
        Submission.objects.create(task=self.task_micro, student=self.student, status=Submission.Status.APPROVED)
        Submission.objects.create(task=self.task_prac, student=self.student, status=Submission.Status.APPROVED)

        stats = self.student.get_subject_progress(self.sub_dcn)
        self.assertEqual(stats['weighted_score'], 100.0)
        self.assertEqual(stats['color_status'], 'success')

    def test_overall_progress_formula(self):
        """Test 50% Academic + 10% Attendance + 10% NSS + 10% Cultural + 10% Sports + 10% Extra formula."""
        Submission.objects.create(task=self.task_assign, student=self.student, status=Submission.Status.APPROVED)
        Submission.objects.create(task=self.task_micro, student=self.student, status=Submission.Status.APPROVED)
        Submission.objects.create(task=self.task_prac, student=self.student, status=Submission.Status.APPROVED)

        ActivityCertificate.objects.create(student=self.student, category=self.cat_nss, title='Camp', event_date=timezone.now().date(), status=ActivityCertificate.Status.APPROVED, points_awarded=20)
        ActivityCertificate.objects.create(student=self.student, category=self.cat_cult, title='Dance', event_date=timezone.now().date(), status=ActivityCertificate.Status.APPROVED, points_awarded=20)
        ActivityCertificate.objects.create(student=self.student, category=self.cat_sport, title='Cricket', event_date=timezone.now().date(), status=ActivityCertificate.Status.APPROVED, points_awarded=20)
        ActivityCertificate.objects.create(student=self.student, category=self.cat_intern, title='Intern', event_date=timezone.now().date(), status=ActivityCertificate.Status.APPROVED, points_awarded=30)

        overall = self.student.get_overall_progress()
        self.assertEqual(overall, 99.0)
        self.assertEqual(self.student.get_overall_color_status(), 'success')

    def test_milestone_and_certificate_trigger(self):
        """Test automatic certificate and all-rounder award generation."""
        Submission.objects.create(task=self.task_assign, student=self.student, status=Submission.Status.APPROVED)
        Submission.objects.create(task=self.task_micro, student=self.student, status=Submission.Status.APPROVED)
        Submission.objects.create(task=self.task_prac, student=self.student, status=Submission.Status.APPROVED)

        ActivityCertificate.objects.create(student=self.student, category=self.cat_nss, title='Camp', event_date=timezone.now().date(), status=ActivityCertificate.Status.APPROVED, points_awarded=20)
        ActivityCertificate.objects.create(student=self.student, category=self.cat_cult, title='Dance', event_date=timezone.now().date(), status=ActivityCertificate.Status.APPROVED, points_awarded=20)
        ActivityCertificate.objects.create(student=self.student, category=self.cat_sport, title='Cricket', event_date=timezone.now().date(), status=ActivityCertificate.Status.APPROVED, points_awarded=20)
        ActivityCertificate.objects.create(student=self.student, category=self.cat_intern, title='Intern', event_date=timezone.now().date(), status=ActivityCertificate.Status.APPROVED, points_awarded=30)

        self.student.check_and_award_milestones()
        self.assertTrue(Certificate.objects.filter(student=self.student, cert_type=Certificate.CertType.PERFECT_SUBMISSION).exists())
        self.assertTrue(Certificate.objects.filter(student=self.student, cert_type=Certificate.CertType.ACADEMIC_EXCELLENCE).exists())
        self.assertTrue(Certificate.objects.filter(student=self.student, cert_type=Certificate.CertType.ALL_ROUNDER).exists())
        self.assertTrue(StudentBadge.objects.filter(student=self.student, badge__code='ALL_ROUNDER').exists())

    def test_smart_login_with_prn(self):
        """Test authentication using PRN instead of username."""
        client = Client()
        response = client.post(reverse('accounts:login'), {
            'username': '2026CE099',
            'password': 'password123'
        })
        self.assertEqual(response.status_code, 302)

    def test_digital_noc_creation_and_approval(self):
        """Test Digital NOC workflow and 5-point clearance."""
        noc = DigitalNOC.objects.create(
            noc_id='NOC-TEST-001',
            student=self.student,
            purpose='Academic Clearance',
            library_clearance=True,
            academic_clearance=True,
            department_clearance=True,
            lab_clearance=True,
            fees_clearance=True,
            is_approved=True
        )
        self.assertTrue(noc.is_all_cleared)
        generate_noc_qr(noc, "http://127.0.0.1:8000")
        generate_noc_pdf(noc)
        self.assertTrue(noc.pdf_file)

    def test_qr_progress_view(self):
        """Test scanning student QR code opens the instant progress profile."""
        client = Client()
        url = reverse('students:qr_progress', kwargs={'qr_token': self.student.qr_token})
        response = client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sayali Virkar')
        self.assertContains(response, '2026CE099')

    def test_public_certificate_verification(self):
        """Test certificate public verification page."""
        cert = Certificate.objects.create(
            certificate_id='EDU-2026-99999',
            student=self.student,
            cert_type=Certificate.CertType.ACADEMIC_EXCELLENCE,
            title='Certificate of Academic Excellence',
            achievement_text='Exceptional academic results',
            score_percentage=95.0,
            issue_date=timezone.now().date()
        )
        client = Client()
        url = reverse('certificates:verify_certificate', kwargs={'cert_uuid': cert.uuid})
        response = client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'EDU-2026-99999')
        self.assertContains(response, 'Sayali Virkar')

    def test_leaderboard_and_excel_export(self):
        """Test leaderboard and Excel download."""
        client = Client()
        client.login(username='prof_anjali', password='password123')
        
        # Leaderboard
        res_lb = client.get(reverse('dashboard:leaderboard'))
        self.assertEqual(res_lb.status_code, 200)
        self.assertContains(res_lb, 'Sayali Virkar')

        # Excel Export
        res_excel = client.get(reverse('dashboard:export_excel'))
        self.assertEqual(res_excel.status_code, 200)
        self.assertEqual(res_excel['Content-Type'], 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
