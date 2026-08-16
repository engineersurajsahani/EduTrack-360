import uuid
from django.db import models
from django.utils import timezone

class Badge(models.Model):
    code = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=50, default='stars') # Material icon or emoji
    badge_color = models.CharField(max_length=30, default='gold')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.icon} {self.title}"


class StudentBadge(models.Model):
    student = models.ForeignKey('students.StudentProfile', on_delete=models.CASCADE, related_name='badges')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE, related_name='awarded_students')
    awarded_at = models.DateTimeField(auto_now_add=True)
    reason = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        unique_together = ('student', 'badge')
        ordering = ['-awarded_at']

    def __str__(self):
        return f"{self.student.user.get_full_name() or self.student.user.username} - {self.badge.title}"


class Certificate(models.Model):
    class CertType(models.TextChoices):
        PERFECT_SUBMISSION = 'PERFECT_SUBMISSION', 'Perfect Submission Certificate'
        ACADEMIC_EXCELLENCE = 'ACADEMIC_EXCELLENCE', 'Academic Excellence Certificate'
        NSS_EXCELLENCE = 'NSS_EXCELLENCE', 'NSS Excellence Certificate'
        CULTURAL_EXCELLENCE = 'CULTURAL_EXCELLENCE', 'Cultural Excellence Certificate'
        SPORTS_EXCELLENCE = 'SPORTS_EXCELLENCE', 'Sports Excellence Certificate'
        ACTIVITY_CHAMPION = 'ACTIVITY_CHAMPION', 'Activity Champion Certificate'
        ALL_ROUNDER = 'ALL_ROUNDER', 'Best All-Rounder Student Certificate'
        SEMESTER_TOPPER = 'SEMESTER_TOPPER', 'Semester Topper Certificate'

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    certificate_id = models.CharField(max_length=50, unique=True) # e.g. EDU-2026-00125
    student = models.ForeignKey('students.StudentProfile', on_delete=models.CASCADE, related_name='certificates')
    cert_type = models.CharField(max_length=30, choices=CertType.choices)
    title = models.CharField(max_length=200)
    achievement_text = models.TextField()
    score_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    issue_date = models.DateField(default=timezone.now)
    qr_code = models.ImageField(upload_to='certificates/qr/', blank=True, null=True)
    pdf_file = models.FileField(upload_to='certificates/pdf/', blank=True, null=True)
    is_verified = models.BooleanField(default=True)
    issued_by = models.CharField(max_length=200, default='EduTrack 360 Institute of Engineering & Technology')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.certificate_id} - {self.student.user.get_full_name() or self.student.user.username} ({self.get_cert_type_display()})"


class DigitalNOC(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    noc_id = models.CharField(max_length=50, unique=True) # e.g. NOC-2026-00125
    student = models.ForeignKey('students.StudentProfile', on_delete=models.CASCADE, related_name='noc_requests')
    purpose = models.CharField(max_length=200, default='Semester Exam & Academic Clearance')
    
    # 5-Point Clearance Workflow
    library_clearance = models.BooleanField(default=True, verbose_name='Library Clearance')
    academic_clearance = models.BooleanField(default=True, verbose_name='Academic Clearance')
    department_clearance = models.BooleanField(default=True, verbose_name='Department Clearance')
    lab_clearance = models.BooleanField(default=True, verbose_name='Lab / Workshop Clearance')
    fees_clearance = models.BooleanField(default=True, verbose_name='Accounts / Fees Clearance')
    
    remarks = models.TextField(blank=True, null=True)
    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_nocs')
    qr_code = models.ImageField(upload_to='noc/qr/', blank=True, null=True)
    pdf_file = models.FileField(upload_to='noc/pdf/', blank=True, null=True)
    issued_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-issued_at']

    @property
    def is_all_cleared(self):
        return (
            self.library_clearance and
            self.academic_clearance and
            self.department_clearance and
            self.lab_clearance and
            self.fees_clearance
        )

    def __str__(self):
        status = "APPROVED" if self.is_approved else "PENDING"
        return f"{self.noc_id} - {self.student.user.get_full_name() or self.student.user.username} [{status}]"
