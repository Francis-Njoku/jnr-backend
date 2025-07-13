from django.db import models
from authentication.models import User
from django.core.validators import FileExtensionValidator
from django.core.serializers.json import DjangoJSONEncoder
# Create your models here.


class Company(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Companies"

class SkillType(models.TextChoices):
    SOFT = 'SOFT', 'Soft Skill'
    HARD = 'HARD', 'Hard Skill'

class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    skill_type = models.CharField(max_length=10, choices=SkillType.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_skill_type_display()})"


class JobListing(models.Model):
    class JobType(models.TextChoices):
        FULL_TIME = 'FULL_TIME', 'Full Time'
        PART_TIME = 'PART_TIME', 'Part Time'
        CONTRACT = 'CONTRACT', 'Contract'
        FREELANCE = 'FREELANCE', 'Freelance'
        INTERNSHIP = 'INTERNSHIP', 'Internship'
    
    class ExperienceLevel(models.TextChoices):
        ENTRY = 'ENTRY', 'Entry Level'
        MID = 'MID', 'Mid Level'
        SENIOR = 'SENIOR', 'Senior Level'
        EXECUTIVE = 'EXECUTIVE', 'Executive Level'
    
    title = models.CharField(max_length=200)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='job_listings')
    posted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posted_jobs')
    description = models.TextField()
    requirements = models.TextField()
    job_type = models.CharField(max_length=20, choices=JobType.choices, default=JobType.FULL_TIME)
    experience_level = models.CharField(max_length=20, choices=ExperienceLevel.choices, default=ExperienceLevel.ENTRY)
    location = models.CharField(max_length=100)
    remote = models.BooleanField(default=False)
    salary_min = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    salary_max = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    application_url = models.URLField(blank=True, null=True)
    deadline = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    skills = models.ManyToManyField(Skill, related_name='job_listings')
    extracted_skills = models.JSONField(blank=True, null=True)  # Raw extracted skills
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    
    def __str__(self):
        return f"{self.title} at {self.company.name}"


class JobApplication(models.Model):
    class Status(models.TextChoices):
        APPLIED = 'APPLIED', 'Applied'
        REVIEWING = 'REVIEWING', 'Reviewing'
        INTERVIEW = 'INTERVIEW', 'Interview'
        REJECTED = 'REJECTED', 'Rejected'
        ACCEPTED = 'ACCEPTED', 'Accepted'
    
    job = models.ForeignKey(JobListing, on_delete=models.CASCADE, related_name='applications')
    applicant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications')
    resume = models.FileField(upload_to='resumes/', blank=True, null=True)
    cover_letter = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.APPLIED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Application for {self.job.title} by {self.applicant.email}"

    class Meta:
        unique_together = ['job', 'applicant']


class UserSkill(models.Model):
    SOURCE_CHOICES = [
        ('CV_EXTRACTION', 'Extracted from CV'),
        ('MANUAL', 'Manually Added'),
        ('RECOMMENDATION', 'System Recommendation'),
        ('JOB_ANALYSIS', 'From Job Analysis')
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='skills')
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, null=True, blank=True)
    custom_name = models.CharField(max_length=100, blank=True, null=True)
    custom_type = models.CharField(max_length=10, choices=SkillType.choices, blank=True, null=True)
    proficiency = models.PositiveSmallIntegerField(default=3)
    verified = models.BooleanField(default=False)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='MANUAL')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [
            ['user', 'skill'],
            ['user', 'custom_name']
        ]

    @property
    def name(self):
        return self.skill.name if self.skill else self.custom_name

    @property
    def skill_type(self):
        if self.skill:
            return self.skill.skill_type
        return self.custom_type

class CVUpload(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cv_uploads')
    file = models.FileField(
        upload_to='user_cvs/%Y/%m/%d/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'txt'])]
    )
    original_filename = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField()
    file_type = models.CharField(max_length=50)
    upload_date = models.DateTimeField(auto_now_add=True)
    is_processed = models.BooleanField(default=False)
    processing_status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pending'),
            ('PROCESSING', 'Processing'),
            ('COMPLETED', 'Completed'),
            ('FAILED', 'Failed')
        ],
        default='PENDING'
    )
    extraction_metadata = models.JSONField(blank=True, null=True)

class CVExtractionResult(models.Model):
    cv_upload = models.OneToOneField(CVUpload, on_delete=models.CASCADE, related_name='extraction_result')
    extracted_text = models.TextField(blank=True, null=True)
    skills = models.JSONField(default=list)
    experience = models.JSONField(default=list)
    education = models.JSONField(default=list)
    certifications = models.JSONField(default=list)
    raw_response = models.JSONField(blank=True, null=True)
    processed_at = models.DateTimeField(auto_now_add=True)
    processing_time = models.FloatField(blank=True, null=True)

class CareerPath(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    industry = models.CharField(max_length=100)
    experience_level = models.CharField(max_length=20)
    salary_range = models.CharField(max_length=100)
    future_growth = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

class RecommendedCourse(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recommended_courses')
    title = models.CharField(max_length=200)
    provider = models.CharField(max_length=100)
    url = models.URLField()
    reason = models.TextField()
    source = models.CharField(max_length=50)
    recommended_at = models.DateTimeField(auto_now_add=True)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    relevance_score = models.FloatField(default=0.0)

    class Meta:
        ordering = ['-relevance_score']

class CareerRecommendation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='career_recommendations')
    career_path = models.ForeignKey(CareerPath, on_delete=models.CASCADE, null=True, blank=True)
    custom_path = models.JSONField()
    confidence_score = models.FloatField()
    reasons = models.JSONField()
    generated_at = models.DateTimeField(auto_now_add=True)
    viewed = models.BooleanField(default=False)

    def get_path_title(self):
        return self.career_path.title if self.career_path else self.custom_path.get('title', 'Custom Path')

class SkillSearch(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    search_query = models.CharField(max_length=255)
    results_count = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    session_id = models.CharField(max_length=100, blank=True)

class UserSkillProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='skill_profile')
    last_cv_processed = models.ForeignKey(CVUpload, on_delete=models.SET_NULL, null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True)