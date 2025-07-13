from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from joblisting.models import Company, JobListing, JobApplication
from authentication.models import User

class PermissionTest(APITestCase):
    def setUp(self):
        # Create admin user
        self.admin = User.objects.create_user(
            username='testadmin',
            email='admin@test.com',
            password='password123',
            role='ADMIN',
            is_staff=True
        )
        
        # Create employer user
        self.employer1 = User.objects.create_user(
            username='employer1',
            email='employer1@test.com',
            password='password123',
            role='EMPLOYER'
        )
        
        # Create another employer user
        self.employer2 = User.objects.create_user(
            username='employer2',
            email='employer2@test.com',
            password='password123',
            role='EMPLOYER'
        )
        
        # Create job seeker user
        self.job_seeker1 = User.objects.create_user(
            username='jobseeker1',
            email='jobseeker1@test.com',
            password='password123',
            role='JOB_SEEKER'
        )
        
        # Create another job seeker user
        self.job_seeker2 = User.objects.create_user(
            username='jobseeker2',
            email='jobseeker2@test.com',
            password='password123',
            role='JOB_SEEKER'
        )
        
        # Create company
        self.company = Company.objects.create(
            name='Test Company',
            location='Test City'
        )
        
        # Create a job listing by employer1
        self.job1 = JobListing.objects.create(
            title='Software Developer',
            company=self.company,
            posted_by=self.employer1,
            description='Test description',
            requirements='Test requirements',
            job_type='FULL_TIME',
            experience_level='MID',
            location='Test City'
        )
        
        # Create a job listing by employer2
        self.job2 = JobListing.objects.create(
            title='Data Scientist',
            company=self.company,
            posted_by=self.employer2,
            description='Test description',
            requirements='Test requirements',
            job_type='FULL_TIME',
            experience_level='SENIOR',
            location='Remote',
            remote=True
        )
        
        # Create a job application by job_seeker1
        self.application1 = JobApplication.objects.create(
            job=self.job1,
            applicant=self.job_seeker1,
            cover_letter='Test cover letter',
            status='APPLIED'
        )
        
        # API clients
        self.admin_client = APIClient()
        self.admin_client.force_authenticate(user=self.admin)
        
        self.employer1_client = APIClient()
        self.employer1_client.force_authenticate(user=self.employer1)
        
        self.employer2_client = APIClient()
        self.employer2_client.force_authenticate(user=self.employer2)
        
        self.job_seeker1_client = APIClient()
        self.job_seeker1_client.force_authenticate(user=self.job_seeker1)
        
        self.job_seeker2_client = APIClient()
        self.job_seeker2_client.force_authenticate(user=self.job_seeker2)
    
    def test_update_own_job_listing(self):
        """Test that employers can update their own job listings but not others'."""
        job1_url = reverse('joblisting-detail', args=[self.job1.id])
        job2_url = reverse('joblisting-detail', args=[self.job2.id])
        
        update_data = {'title': 'Updated Job Title'}
        
        # Employer1 should be able to update their own job listing
        response = self.employer1_client.patch(job1_url, update_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.job1.refresh_from_db()
        self.assertEqual(self.job1.title, 'Updated Job Title')
        
        # Employer1 should not be able to update employer2's job listing
        response = self.employer1_client.patch(job2_url, update_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Admin should be able to update any job listing
        admin_update_data = {'title': 'Admin Updated'}
        response = self.admin_client.patch(job2_url, admin_update_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.job2.refresh_from_db()
        self.assertEqual(self.job2.title, 'Admin Updated')
    
    def test_view_own_applications(self):
        """Test that job seekers can only view their own applications."""
        applications_url = reverse('jobapplication-list')
        
        # Job seeker1 should see only their own application
        response = self.job_seeker1_client.get(applications_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
        # Job seeker2 should see no applications
        response = self.job_seeker2_client.get(applications_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)
        
        # Employer1 should see the application for their job
        response = self.employer1_client.get(applications_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
        # Employer2 should see no applications
        response = self.employer2_client.get(applications_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)
        
        # Admin should see all applications
        response = self.admin_client.get(applications_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)