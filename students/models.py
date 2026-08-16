import uuid
import io
import qrcode
from PIL import Image
from django.db import models
from django.core.files.base import ContentFile
from django.utils import timezone
from django.db.models import Avg, Count, Q

class StudentProfile(models.Model):
    user = models.OneToOneField('accounts.User', on_delete=models.CASCADE, related_name='student_profile')
    prn = models.CharField(max_length=50, unique=True, verbose_name="PRN / Permanent Registration Number")
    roll_no = models.CharField(max_length=30)
    program = models.ForeignKey('academics.Program', on_delete=models.CASCADE, related_name='students')
    branch = models.ForeignKey('academics.Branch', on_delete=models.CASCADE, related_name='students')
    academic_year = models.ForeignKey('academics.AcademicYear', on_delete=models.CASCADE, related_name='students')
    semester = models.ForeignKey('academics.Semester', on_delete=models.CASCADE, related_name='students')
    division = models.ForeignKey('academics.Division', on_delete=models.SET_NULL, null=True, blank=True, related_name='students')
    admission_year = models.PositiveIntegerField(default=2026)
    attendance_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=85.0)
    qr_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    qr_code_image = models.ImageField(upload_to='qr_codes/students/', blank=True, null=True)
    
    # Portfolio fields
    headline = models.CharField(max_length=200, default='Aspiring Engineer & Technology Enthusiast')
    bio = models.TextField(blank=True, null=True)
    github_url = models.URLField(blank=True, null=True)
    linkedin_url = models.URLField(blank=True, null=True)
    skills = models.CharField(max_length=300, default='Python, Java, C++, Django, SQL, Data Structures')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['roll_no', 'prn']

    def __str__(self):
        full_name = self.user.get_full_name() or self.user.username
        return f"{full_name} (PRN: {self.prn} | Roll: {self.roll_no})"

    def generate_qr_code(self, base_url=""):
        """Generates or updates the student's unique QR code image."""
        # The QR code points directly to the student's QR progress dashboard / instant lookup URL
        qr_data = f"{base_url}/student/qr/{self.qr_token}/"
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#1a237e", back_color="white")
        
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        file_name = f"student_qr_{self.prn}_{self.id}.png"
        self.qr_code_image.save(file_name, ContentFile(buffer.getvalue()), save=False)

    # ------------------ PROGRESS & CALCULATION ENGINES ------------------

    def get_subject_progress(self, subject):
        """Calculates detailed and weighted progress for a specific subject."""
        tasks = subject.tasks.filter(is_required=True)
        if not tasks.exists():
            return {
                'subject': subject,
                'total_tasks': 0,
                'completed_tasks': 0,
                'raw_percentage': 100.0,
                'weighted_score': 100.0,
                'color_status': 'success',
                'badge_class': 'bg-success',
                'assignments': {'total': 0, 'completed': 0, 'percentage': 100.0},
                'microprojects': {'total': 0, 'completed': 0, 'percentage': 100.0},
                'practicals': {'total': 0, 'completed': 0, 'percentage': 100.0},
                'ppt_manual': {'total': 0, 'completed': 0, 'percentage': 100.0},
            }

        # Submissions by student for these tasks
        from academics.models import Submission
        approved_submissions = Submission.objects.filter(
            student=self,
            task__subject=subject,
            status=Submission.Status.APPROVED
        ).select_related('task')
        
        approved_task_ids = set(approved_submissions.values_list('task_id', flat=True))

        # Categorize tasks
        def get_type_stats(types):
            type_tasks = tasks.filter(task_type__in=types)
            total = type_tasks.count()
            if total == 0:
                return {'total': 0, 'completed': 0, 'percentage': 100.0}
            completed = sum(1 for t in type_tasks if t.id in approved_task_ids)
            pct = round((completed / total) * 100, 1)
            return {'total': total, 'completed': completed, 'percentage': pct}

        assign_stats = get_type_stats(['ASSIGNMENT'])
        micro_stats = get_type_stats(['MICROPROJECT', 'REPORT', 'VIVA'])
        prac_stats = get_type_stats(['PRACTICAL'])
        ppt_stats = get_type_stats(['PPT', 'MANUAL'])

        # Weighted calculation as per plan (Assignments 30%, Microprojects 30%, Practicals 25%, PPT/Manual 15%)
        # Normalizing weights if a subject doesn't have certain task types
        w_assign = subject.assignment_weight
        w_micro = subject.microproject_weight
        w_prac = subject.practical_weight
        w_ppt = subject.ppt_manual_weight

        weighted_sum = (
            (assign_stats['percentage'] * (w_assign / 100.0)) +
            (micro_stats['percentage'] * (w_micro / 100.0)) +
            (prac_stats['percentage'] * (w_prac / 100.0)) +
            (ppt_stats['percentage'] * (w_ppt / 100.0))
        )
        
        final_score = round(weighted_sum, 1)
        total_tasks_count = tasks.count()
        total_completed_count = len(approved_task_ids)
        raw_pct = round((total_completed_count / total_tasks_count) * 100, 1) if total_tasks_count > 0 else 100.0

        if final_score >= 75:
            color = 'success' # Green
            badge = 'bg-success'
        elif final_score >= 50:
            color = 'warning' # Yellow
            badge = 'bg-warning text-dark'
        else:
            color = 'danger' # Red
            badge = 'bg-danger'

        return {
            'subject': subject,
            'total_tasks': total_tasks_count,
            'completed_tasks': total_completed_count,
            'raw_percentage': raw_pct,
            'weighted_score': final_score,
            'color_status': color,
            'badge_class': badge,
            'assignments': assign_stats,
            'microprojects': micro_stats,
            'practicals': prac_stats,
            'ppt_manual': ppt_stats,
        }

    def get_all_subjects_progress(self):
        """Returns progress list for all subjects in student's current semester."""
        from academics.models import Subject
        subjects = Subject.objects.filter(
            branch=self.branch,
            semester=self.semester,
            is_active=True
        ).prefetch_related('tasks')
        
        return [self.get_subject_progress(sub) for sub in subjects]

    def get_academic_percentage(self):
        """Calculates the average academic percentage across all subjects."""
        subject_progress_list = self.get_all_subjects_progress()
        if not subject_progress_list:
            return 100.0
        scores = [item['weighted_score'] for item in subject_progress_list]
        return round(sum(scores) / len(scores), 1)

    def get_category_activity_points(self, category_code):
        """Calculates total verified points for an activity category."""
        from activities.models import ActivityCertificate
        approved_certs = ActivityCertificate.objects.filter(
            student=self,
            category__code=category_code,
            status=ActivityCertificate.Status.APPROVED
        )
        return sum(c.points_awarded for c in approved_certs)

    def get_all_activities_progress(self):
        """Calculates category-wise extracurricular activity percentages."""
        from activities.models import ActivityCategory, ActivityCertificate
        categories = ActivityCategory.objects.all()
        activity_stats = []
        
        for cat in categories:
            pts = self.get_category_activity_points(cat.code)
            pct = min(100.0, round((pts / cat.target_points) * 100, 1)) if cat.target_points > 0 else 100.0
            
            if pct >= 75:
                color = 'success'
            elif pct >= 50:
                color = 'warning'
            else:
                color = 'danger'
                
            activity_stats.append({
                'category': cat,
                'points_earned': pts,
                'target_points': cat.target_points,
                'percentage': pct,
                'color_status': color,
                'certs_count': ActivityCertificate.objects.filter(student=self, category=cat, status=ActivityCertificate.Status.APPROVED).count()
            })
            
        return activity_stats

    def get_specific_category_pct(self, category_code, default_target=25):
        """Returns the completion percentage for a specific category."""
        pts = self.get_category_activity_points(category_code)
        return min(100.0, round((pts / default_target) * 100, 1))

    def get_overall_progress(self):
        """
        Overall Progress Formula from Plan (Total 100%):
        - Academic: 50%
        - Attendance: 10%
        - NSS: 10%
        - Cultural: 10%
        - Sports: 10%
        - Extra Activities (Internship/Workshop/Courses): 10%
        """
        acad_pct = self.get_academic_percentage()
        att_pct = float(self.attendance_percentage)
        nss_pct = self.get_specific_category_pct('NSS', default_target=20)
        cultural_pct = self.get_specific_category_pct('CULTURAL', default_target=20)
        sports_pct = self.get_specific_category_pct('SPORTS', default_target=20)
        
        # Extra activities combined: Internship, Workshop, Courses, Hackathons
        extra_pts = (
            self.get_category_activity_points('INTERNSHIP') +
            self.get_category_activity_points('WORKSHOP') +
            self.get_category_activity_points('HACKATHON') +
            self.get_category_activity_points('COURSES') +
            self.get_category_activity_points('RESEARCH')
        )
        extra_pct = min(100.0, round((extra_pts / 30.0) * 100, 1))

        overall = (
            (acad_pct * 0.50) +
            (att_pct * 0.10) +
            (nss_pct * 0.10) +
            (cultural_pct * 0.10) +
            (sports_pct * 0.10) +
            (extra_pct * 0.10)
        )
        
        return round(overall, 1)

    def get_overall_color_status(self):
        score = self.get_overall_progress()
        if score >= 75:
            return 'success' # Green
        elif score >= 50:
            return 'warning' # Yellow
        return 'danger' # Red

    def get_submissions_summary(self):
        from academics.models import Submission, SubjectTask
        total_tasks = SubjectTask.objects.filter(
            subject__branch=self.branch,
            subject__semester=self.semester,
            is_required=True
        ).count()
        
        submissions = Submission.objects.filter(student=self)
        approved = submissions.filter(status=Submission.Status.APPROVED).count()
        pending = submissions.filter(status=Submission.Status.PENDING).count()
        rejected = submissions.filter(status=Submission.Status.REJECTED).count()
        
        return {
            'total_tasks': total_tasks,
            'approved': approved,
            'pending': pending,
            'rejected': rejected,
            'not_submitted': max(0, total_tasks - (approved + pending))
        }

    def get_pending_tasks_list(self):
        """Returns list of pending/rejected tasks or tasks that still need submission."""
        from academics.models import SubjectTask, Submission
        tasks = SubjectTask.objects.filter(
            subject__branch=self.branch,
            subject__semester=self.semester,
            is_required=True
        ).select_related('subject')

        submissions = {s.task_id: s for s in Submission.objects.filter(student=self)}
        pending_list = []

        for task in tasks:
            sub = submissions.get(task.id)
            if not sub:
                pending_list.append({
                    'task': task,
                    'status': 'NOT_SUBMITTED',
                    'status_label': 'Not Submitted',
                    'badge_class': 'bg-secondary',
                    'submission': None
                })
            elif sub.status == Submission.Status.PENDING:
                pending_list.append({
                    'task': task,
                    'status': 'PENDING',
                    'status_label': 'Pending Approval',
                    'badge_class': 'bg-warning text-dark',
                    'submission': sub
                })
            elif sub.status == Submission.Status.REJECTED:
                pending_list.append({
                    'task': task,
                    'status': 'REJECTED',
                    'status_label': 'Rejected (Needs Re-upload)',
                    'badge_class': 'bg-danger',
                    'submission': sub
                })

        return pending_list

    def check_and_award_milestones(self):
        """
        Automatic Award, Badge & Certificate Trigger Engine as specified in plan:
        1. Perfect Submission Certificate & Badge (100% Academic Tasks Approved)
        2. Academic Excellence (Academic >= 90%)
        3. NSS Excellence (NSS >= 90%)
        4. Cultural Excellence (Cultural >= 90%)
        5. Sports Excellence (Sports >= 90%)
        6. Activity Champion (Overall Activity >= 90%)
        7. Best All-Rounder Student (Academic >= 80%, Attendance >= 75%, NSS/Cultural/Sports/Extra >= 70%)
        """
        from certificates.models import Badge, StudentBadge, Certificate
        from certificates.pdf_generator import generate_certificate_pdf, generate_certificate_qr

        acad_pct = self.get_academic_percentage()
        att_pct = float(self.attendance_percentage)
        nss_pct = self.get_specific_category_pct('NSS', default_target=20)
        cult_pct = self.get_specific_category_pct('CULTURAL', default_target=20)
        sport_pct = self.get_specific_category_pct('SPORTS', default_target=20)
        extra_pts = (
            self.get_category_activity_points('INTERNSHIP') +
            self.get_category_activity_points('WORKSHOP') +
            self.get_category_activity_points('HACKATHON') +
            self.get_category_activity_points('COURSES')
        )
        extra_pct = min(100.0, round((extra_pts / 30.0) * 100, 1))
        overall_act_pct = round((nss_pct + cult_pct + sport_pct + extra_pct) / 4.0, 1)

        summary = self.get_submissions_summary()
        all_academic_completed = (summary['total_tasks'] > 0 and summary['approved'] == summary['total_tasks'])

        # Helper to grant badge and certificate
        def grant(cert_type, title, desc, score, badge_code, badge_title, badge_icon, badge_color):
            # Badge
            badge, _ = Badge.objects.get_or_create(
                code=badge_code,
                defaults={'title': badge_title, 'description': desc, 'icon': badge_icon, 'badge_color': badge_color}
            )
            StudentBadge.objects.get_or_create(student=self, badge=badge, defaults={'reason': desc})

            # Certificate
            if not Certificate.objects.filter(student=self, cert_type=cert_type).exists():
                cert_num = Certificate.objects.count() + 101
                cert_id = f"EDU-{timezone.now().year}-{cert_num:05d}"
                cert = Certificate.objects.create(
                    certificate_id=cert_id,
                    student=self,
                    cert_type=cert_type,
                    title=title,
                    achievement_text=desc,
                    score_percentage=score,
                    issue_date=timezone.now().date()
                )
                # Generate QR and PDF
                generate_certificate_qr(cert)
                generate_certificate_pdf(cert)

        # 1. Perfect Submission
        if all_academic_completed:
            grant(
                Certificate.CertType.PERFECT_SUBMISSION,
                "Certificate of Perfect Academic Submission",
                f"Successfully completed and received faculty approval for all 100% academic assignments, microprojects, and practical submissions.",
                100.0,
                'ASSIGNMENT_CHAMPION',
                'Assignment Champion',
                'assignment_turned_in',
                '#4caf50'
            )

        # 2. Academic Excellence (>= 90%)
        if acad_pct >= 90.0:
            grant(
                Certificate.CertType.ACADEMIC_EXCELLENCE,
                "Certificate of Academic Excellence",
                f"Demonstrated outstanding academic performance with a semester academic score of {acad_pct}%.",
                acad_pct,
                'ACADEMIC_SCHOLAR',
                'Academic Scholar',
                'military_tech',
                '#ff9800'
            )

        # 3. NSS Excellence (>= 90%)
        if nss_pct >= 90.0:
            grant(
                Certificate.CertType.NSS_EXCELLENCE,
                "Certificate of NSS & Social Excellence",
                f"Exemplary dedication and highest service contribution in National Service Scheme (NSS) activities.",
                nss_pct,
                'NSS_HERO',
                'NSS Hero',
                'volunteer_activism',
                '#2e7d32'
            )

        # 4. Cultural Excellence (>= 90%)
        if cult_pct >= 90.0:
            grant(
                Certificate.CertType.CULTURAL_EXCELLENCE,
                "Certificate of Cultural Excellence",
                f"Outstanding creativity, talent, and winning participation in college and state cultural events.",
                cult_pct,
                'CULTURAL_STAR',
                'Cultural Star',
                'theater_comedy',
                '#e91e63'
            )

        # 5. Sports Excellence (>= 90%)
        if sport_pct >= 90.0:
            grant(
                Certificate.CertType.SPORTS_EXCELLENCE,
                "Certificate of Sports & Athletic Excellence",
                f"Superb athletic sportsmanship and victorious performance in competitive tournaments.",
                sport_pct,
                'SPORTS_STAR',
                'Sports Star',
                'emoji_events',
                '#ff5722'
            )

        # 6. Activity Champion (>= 90% overall extracurriculars)
        if overall_act_pct >= 90.0:
            grant(
                Certificate.CertType.ACTIVITY_CHAMPION,
                "Certificate of Activity Champion",
                f"Demonstrated unparalleled holistic engagement achieving {overall_act_pct}% extracurricular score.",
                overall_act_pct,
                'ACTIVITY_CHAMPION',
                'Activity Champion',
                'stars',
                '#9c27b0'
            )

        # 7. All-Rounder Student
        if (acad_pct >= 80.0 and att_pct >= 75.0 and nss_pct >= 70.0 and cult_pct >= 70.0 and sport_pct >= 70.0 and extra_pct >= 70.0):
            grant(
                Certificate.CertType.ALL_ROUNDER,
                "Best All-Rounder Student Award",
                f"Conferred the prestigious All-Rounder Award for exceptional distinction across Academics, Attendance, NSS, Cultural, Sports, and Technical domains.",
                self.get_overall_progress(),
                'ALL_ROUNDER',
                'All-Rounder Luminary',
                'workspace_premium',
                '#ffd700'
            )
