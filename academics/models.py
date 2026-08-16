from django.db import models
from django.conf import settings

class Program(models.Model):
    name = models.CharField(max_length=150) # e.g. Bachelor of Engineering (B.E.)
    code = models.CharField(max_length=20, unique=True) # e.g. BE, BTECH
    duration_years = models.PositiveIntegerField(default=4)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.code})"


class Branch(models.Model):
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='branches')
    department = models.ForeignKey('accounts.Department', on_delete=models.SET_NULL, null=True, blank=True, related_name='branches')
    name = models.CharField(max_length=150) # e.g. Computer Engineering
    code = models.CharField(max_length=20) # e.g. CE, CSE
    
    class Meta:
        verbose_name_plural = 'Branches'
        unique_together = ('program', 'code')

    def __str__(self):
        return f"{self.name} ({self.program.code})"


class AcademicYear(models.Model):
    name = models.CharField(max_length=50) # e.g. "Second Year (SE)"
    year_number = models.PositiveSmallIntegerField(unique=True) # 1, 2, 3, 4
    code = models.CharField(max_length=10) # FE, SE, TE, BE

    class Meta:
        ordering = ['year_number']

    def __str__(self):
        return f"{self.name} ({self.code})"


class Semester(models.Model):
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='semesters')
    number = models.PositiveSmallIntegerField(unique=True) # 1, 2, 3, 4, 5, 6, 7, 8
    roman_name = models.CharField(max_length=10) # I, II, III, IV, V, VI, VII, VIII

    class Meta:
        ordering = ['number']

    def __str__(self):
        return f"Semester {self.roman_name} ({self.academic_year.code})"


class Division(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='divisions')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='divisions')
    name = models.CharField(max_length=10) # e.g. "A", "B", "C"

    class Meta:
        unique_together = ('branch', 'semester', 'name')
        ordering = ['name']

    def __str__(self):
        return f"{self.branch.code} - Sem {self.semester.roman_name} - Div {self.name}"


class Subject(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='subjects')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='subjects')
    code = models.CharField(max_length=30) # e.g. DCN, JAVA, OOP, DBMS
    name = models.CharField(max_length=150) # e.g. Data Communication & Networks
    credits = models.PositiveIntegerField(default=4)
    assigned_faculty = models.ForeignKey(
        'accounts.FacultyProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_subjects'
    )
    syllabus_summary = models.TextField(blank=True, null=True)
    
    # Task weighting for subject score calculation (Total = 100%)
    assignment_weight = models.PositiveIntegerField(default=30, help_text="Weightage percentage for Assignments (e.g. 30%)")
    microproject_weight = models.PositiveIntegerField(default=30, help_text="Weightage percentage for Microprojects (e.g. 30%)")
    practical_weight = models.PositiveIntegerField(default=25, help_text="Weightage percentage for Practicals (e.g. 25%)")
    ppt_manual_weight = models.PositiveIntegerField(default=15, help_text="Weightage percentage for PPT/Manual (e.g. 15%)")

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('branch', 'semester', 'code')
        ordering = ['code']

    def __str__(self):
        return f"{self.name} ({self.code}) - Sem {self.semester.roman_name}"


class SubjectTask(models.Model):
    class TaskType(models.TextChoices):
        ASSIGNMENT = 'ASSIGNMENT', 'Assignment'
        MICROPROJECT = 'MICROPROJECT', 'Microproject'
        PPT = 'PPT', 'Presentation (PPT)'
        MANUAL = 'MANUAL', 'Lab Manual'
        PRACTICAL = 'PRACTICAL', 'Practical Work'
        REPORT = 'REPORT', 'Project Report'
        VIVA = 'VIVA', 'Viva / Demo'

    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='tasks')
    task_type = models.CharField(max_length=20, choices=TaskType.choices, default=TaskType.ASSIGNMENT)
    title = models.CharField(max_length=200) # e.g. Assignment 1, Microproject Proposal
    task_number = models.PositiveIntegerField(default=1)
    description = models.TextField(blank=True, null=True)
    max_marks = models.PositiveIntegerField(default=25)
    due_date = models.DateField(blank=True, null=True)
    attachment = models.FileField(upload_to='task_resources/', blank=True, null=True)
    is_required = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['task_type', 'task_number', 'created_at']

    def __str__(self):
        return f"{self.subject.code} - {self.get_task_type_display()} #{self.task_number}: {self.title}"


class Submission(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending Approval'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'

    task = models.ForeignKey(SubjectTask, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey('students.StudentProfile', on_delete=models.CASCADE, related_name='submissions')
    submission_file = models.FileField(upload_to='submissions/')
    student_notes = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    marks_obtained = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    faculty_remark = models.TextField(blank=True, null=True)
    reviewed_by = models.ForeignKey('accounts.FacultyProfile', on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_submissions')
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('task', 'student')
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.student.user.get_full_name() or self.student.user.username} - {self.task.title} [{self.get_status_display()}]"
