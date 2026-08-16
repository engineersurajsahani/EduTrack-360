from django.db import models
from django.contrib.auth.models import AbstractUser

class Department(models.Model):
    name = models.CharField(max_length=150, unique=True)
    code = models.CharField(max_length=20, unique=True) # e.g. COMP, IT, MECH
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Administrator'
        FACULTY = 'FACULTY', 'Faculty / Teacher'
        STUDENT = 'STUDENT', 'Student'
        HOD = 'HOD', 'Head of Department'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT
    )
    phone = models.CharField(max_length=20, blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users'
    )

    @property
    def is_admin_user(self):
        return self.role == self.Role.ADMIN or self.is_superuser

    @property
    def is_faculty_user(self):
        return self.role in [self.Role.FACULTY, self.Role.HOD]

    @property
    def is_student_user(self):
        return self.role == self.Role.STUDENT

    @property
    def is_hod_user(self):
        return self.role == self.Role.HOD

    def __str__(self):
        full_name = self.get_full_name()
        return f"{full_name} ({self.username}) - {self.get_role_display()}" if full_name else f"{self.username} - {self.get_role_display()}"


class FacultyProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='faculty_profile')
    employee_id = models.CharField(max_length=50, unique=True)
    designation = models.CharField(max_length=100, default='Assistant Professor')
    qualification = models.CharField(max_length=150, blank=True, null=True) # e.g. M.Tech, Ph.D.
    cabin_location = models.CharField(max_length=100, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.designation}"
