from django.test import TestCase
from joblisting.models import Company, JobListing, JobApplication
from authentication.models import User

class CompanyModelTest(TestCase):
    def setUp(self):
        self.company = Company.objects.create(
            name="Test Company",
            description="A test company",
            website="https://testcompany.com",
            location="Test City"
        )
    
    def test_company_creation(self):
        self.assertEqual(self.company.name, "Test Company")
        self.assertEqual(str(self.company), "Test Company")


class JobListingModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testemployer",
            email="employer@test.com",
            password="password123",
            role="EMPLOYER"
        )
        
        self.company = Company.objects.create(
            name="Test Company",
            location="Test City"
        )
        
        self.job = JobListing.objects.create(
            title="Test Job",
            company=self.company,
            posted_by=self.user,
            description="Test description",
            requirements="Test requirements",
            job_type="FULL_TIME",
            experience_level="MID",
            location="Test City",
            remote=False
        )
    
    def test_job_listing_creation(self):
        self.assertEqual(self.job.title, "Test Job")
        self.assertEqual(self.job.company, self.company)
        self.assertEqual(self.job.posted_by, self.user)
        self.assertEqual(str(self.job), "Test Job at Test Company")


class JobApplicationModelTest(TestCase):
    def setUp(self):
        self.employer = User.objects.create_user(
            username="testemployer",
            email="employer@test.com",
            password="password123",
            role="EMPLOYER"
        )
        
        self.job_seeker = User.objects.create_user(
            username="testjobseeker",
            email="jobseeker@test.com",
            password="password123",
            role="JOB_SEEKER"
        )
        
        self.company = Company.objects.create(
            name="Test Company",
            location="Test City"
        )
        
        self.job = JobListing.objects.create(
            title="Test Job",
            company=self.company,
            posted_by=self.employer,
            description="Test description",
            requirements="Test requirements",
            job_type="FULL_TIME",
            experience_level="MID",
            location="Test City"
        )
        
        self.application = JobApplication.objects.create(
            job=self.job,
            applicant=self.job_seeker,
            cover_letter="Test cover letter",
            status="APPLIED"
        )
    
    def test_job_application_creation(self):
        self.assertEqual(self.application.job, self.job)
        self.assertEqual(self.application.applicant, self.job_seeker)
        self.assertEqual(self.application.status, "APPLIED")
        self.assertTrue(str(self.application).startswith("Application for Test Job by"))