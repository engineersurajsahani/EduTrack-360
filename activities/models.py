from django.db import models

class ActivityCategory(models.Model):
    class CategoryType(models.TextChoices):
        NSS = 'NSS', 'NSS (National Service Scheme)'
        CULTURAL = 'CULTURAL', 'Cultural Activities'
        SPORTS = 'SPORTS', 'Sports & Games'
        INTERNSHIP = 'INTERNSHIP', 'Internship & Training'
        WORKSHOP = 'WORKSHOP', 'Workshops & Seminars'
        HACKATHON = 'HACKATHON', 'Hackathons & Competitions'
        COURSES = 'COURSES', 'Online Certifications (NPTEL/Coursera/SWAYAM)'
        RESEARCH = 'RESEARCH', 'Research Papers & Patents'
        INDUSTRIAL_VISIT = 'INDUSTRIAL_VISIT', 'Industrial Visits'
        OTHER = 'OTHER', 'Other Extracurricular Achievements'

    code = models.CharField(max_length=30, choices=CategoryType.choices, unique=True)
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, default='category') # Material icon name
    color_class = models.CharField(max_length=50, default='primary')
    target_points = models.PositiveIntegerField(default=25, help_text="Target points needed for 100% completion in this category")
    weight_percentage = models.PositiveIntegerField(default=10, help_text="Weightage in overall progress formula")
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = 'Activity Categories'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"


class ActivityScheme(models.Model):
    category = models.ForeignKey(ActivityCategory, on_delete=models.CASCADE, related_name='schemes')
    activity_name = models.CharField(max_length=150) # e.g. "Tree Plantation", "Dance Winner", "NSS Camp"
    default_points = models.PositiveIntegerField(default=5)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.category.name} - {self.activity_name} ({self.default_points} pts)"


class ActivityCertificate(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending Verification'
        APPROVED = 'APPROVED', 'Verified & Approved'
        REJECTED = 'REJECTED', 'Rejected'

    class Level(models.TextChoices):
        COLLEGE = 'COLLEGE', 'College / Institutional'
        DISTRICT = 'DISTRICT', 'District Level'
        STATE = 'STATE', 'State Level'
        NATIONAL = 'NATIONAL', 'National Level'
        INTERNATIONAL = 'INTERNATIONAL', 'International Level'

    class AchievementRole(models.TextChoices):
        PARTICIPANT = 'PARTICIPANT', 'Participant'
        WINNER = 'WINNER', '1st Prize / Winner'
        RUNNER_UP = 'RUNNER_UP', 'Runner Up / 2nd-3rd Place'
        VOLUNTEER = 'VOLUNTEER', 'Volunteer / Organizer'
        COMPLETED = 'COMPLETED', 'Successfully Completed'

    student = models.ForeignKey('students.StudentProfile', on_delete=models.CASCADE, related_name='activity_certificates')
    category = models.ForeignKey(ActivityCategory, on_delete=models.CASCADE, related_name='certificates')
    title = models.CharField(max_length=200) # e.g. Tree Plantation Drive, Hackathon 2026
    organization = models.CharField(max_length=150, blank=True, null=True) # e.g. MSBTE, IIT Bombay, Coursera
    event_date = models.DateField()
    level = models.CharField(max_length=30, choices=Level.choices, default=Level.COLLEGE)
    achievement_role = models.CharField(max_length=30, choices=AchievementRole.choices, default=AchievementRole.PARTICIPANT)
    certificate_file = models.FileField(upload_to='activity_certs/')
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    points_awarded = models.PositiveIntegerField(default=0)
    faculty_remark = models.TextField(blank=True, null=True)
    verified_by = models.ForeignKey('accounts.FacultyProfile', on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_activity_certs')
    submitted_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.student.user.get_full_name() or self.student.user.username} - {self.title} [{self.get_status_display()}]"
