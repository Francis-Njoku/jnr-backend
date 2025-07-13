from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from joblisting.models import Company, JobListing, JobApplication
from authentication.models import User

class AuthenticationTest(APITestCase):
    def setUp(self):
        self.register_url = reverse('register')
        self.token_url = reverse('token_obtain_pair')
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'TestPassword123!',
            'password2': 'TestPassword123!',
            'first_name': 'Test',
            'last_name': 'User',
            'role': 'JOB_SEEKER'
        }
        
    def test_registration(self):
        response = self.client.post(self.register_url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        
    def test_token_obtain(self):
        # Create user first
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPassword123!'
        )
        
        # Try to get token
        response = self.client.post(self.token_url, {
            'email': 'test@example.com',
            'password': 'TestPassword123!'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)


class JobListingAPITest(APITestCase):
    def setUp(self):
        # Create employer user
        self.employer = User.objects.create_user(
            username='testemployer',
            email='employer@test.com',
            password='password123',
            role='EMPLOYER'
        )
        
        # Create job seeker user
        self.job_seeker = User.objects.create_user(
            username='testjobseeker',
            email='jobseeker@test.com',
            password='password123',
            role='JOB_SEEKER'
        )
        
        # Create company
        self.company = Company.objects.create(
            name='Test Company',
            location='Test City'
        )
        
        # Create a job listing
        self.job = JobListing.objects.create(
            title='Software Developer',
            company=self.company,
            posted_by=self.employer,
            description='Test description',
            requirements='Test requirements',
            job_type='FULL_TIME',
            experience_level='MID',
            location='Test City'
        )
        
        # API client for employer
        self.employer_client = APIClient()
        self.employer_client.force_authenticate(user=self.employer)
        
        # API client for job seeker
        self.job_seeker_client = APIClient()
        self.job_seeker_client.force_authenticate(user=self.job_seeker)
        
        # URLs
        self.jobs_url = reverse('joblisting-list')
        self.job_detail_url = reverse('joblisting-detail', args=[self.job.id])
        self.job_apply_url = reverse('joblisting-apply', args=[self.job.id])
    
    def test_get_job_listings(self):
        # Both employer and job seeker should be able to see job listings
        employer_response = self.employer_client.get(self.jobs_url)
        self.assertEqual(employer_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(employer_response.data['results']), 1)
        
        job_seeker_response = self.job_seeker_client.get(self.jobs_url)
        self.assertEqual(job_seeker_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(job_seeker_response.data['results']), 1)
    
    def test_create_job_listing(self):
        # Only employer should be able to create job listings
        job_data = {
            'title': 'Frontend Developer',
            'company': self.company.id,
            'description': 'Build amazing UIs',
            'requirements': 'React experience',
            'job_type': 'CONTRACT',
            'experience_level': 'ENTRY',
            'location': 'Remote',
            'remote': True
        }
        
        employer_response = self.employer_client.post(self.jobs_url, job_data)
        self.assertEqual(employer_response.status_code, status.HTTP_201_CREATED)
        
        job_seeker_response = self.job_seeker_client.post(self.jobs_url, job_data)
        self.assertEqual(job_seeker_response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_apply_for_job(self):
        # Only job seeker should be able to apply for jobs
        application_data = {
            'cover_letter': 'I would like to apply for this position.'
        }
        
        job_seeker_response = self.job_seeker_client.post(self.job_apply_url, application_data)
        self.assertEqual(job_seeker_response.status_code, status.HTTP_201_CREATED)
        
        employer_response = self.employer_client.post(self.job_apply_url, application_data)
        self.assertEqual(employer_response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Check that application was created
        self.assertEqual(JobApplication.objects.count(), 1)
        self.assertEqual(JobApplication.objects.first().applicant, self.job_seeker)