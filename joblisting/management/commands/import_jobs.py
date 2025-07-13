import csv
from django.core.management.base import BaseCommand
from api.models import Company, JobListing
from users.models import User
from django.utils.text import slugify
from datetime import datetime

class Command(BaseCommand):
    help = 'Import job listings from CSV file'
    
    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to CSV file')
        parser.add_argument('--admin_email', type=str, help='Admin email to associate with jobs', default='admin@example.com')
    
    def handle(self, *args, **options):
        csv_file = options['csv_file']
        admin_email = options['admin_email']
        
        # Get or create admin user
        try:
            admin_user = User.objects.get(email=admin_email)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Admin user with email {admin_email} does not exist. Please create this user first."))
            return
        
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            job_count = 0
            company_cache = {}
            
            for row in reader:
                try:
                    # Get or create company
                    company_name = row.get('company_name', '')
                    if not company_name:
                        continue
                        
                    if company_name in company_cache:
                        company = company_cache[company_name]
                    else:
                        company, created = Company.objects.get_or_create(
                            name=company_name,
                            defaults={
                                'location': row.get('company_location', ''),
                                'website': row.get('company_website', '')
                            }
                        )
                        company_cache[company_name] = company
                        
                        if created:
                            self.stdout.write(self.style.SUCCESS(f"Created company: {company.name}"))
                    
                    # Process job type
                    job_type = 'FULL_TIME'  # Default
                    raw_job_type = row.get('job_type', '').upper()
                    if 'PART' in raw_job_type:
                        job_type = 'PART_TIME'
                    elif 'CONTRACT' in raw_job_type:
                        job_type = 'CONTRACT'
                    elif 'FREELANCE' in raw_job_type:
                        job_type = 'FREELANCE'
                    elif 'INTERN' in raw_job_type:
                        job_type = 'INTERNSHIP'
                    
                    # Process experience level
                    experience_level = 'ENTRY'  # Default
                    raw_experience = row.get('experience_level', '').upper()
                    if 'SENIOR' in raw_experience or 'SR' in raw_experience:
                        experience_level = 'SENIOR'
                    elif 'MID' in raw_experience:
                        experience_level = 'MID'
                    elif 'EXECUTIVE' in raw_experience or 'LEAD' in raw_experience:
                        experience_level = 'EXECUTIVE'
                    
                    # Process salary
                    try:
                        salary_min = float(row.get('salary_min', 0))
                    except (ValueError, TypeError):
                        salary_min = None
                        
                    try:
                        salary_max = float(row.get('salary_max', 0))
                    except (ValueError, TypeError):
                        salary_max = None
                    
                    # Process deadline
                    deadline = None
                    if row.get('deadline'):
                        try:
                            deadline = datetime.strptime(row.get('deadline'), '%Y-%m-%d').date()
                        except ValueError:
                            pass
                    
                    # Create job listing
                    job_listing = JobListing.objects.create(
                        title=row.get('title', ''),
                        company=company,
                        posted_by=admin_user,
                        description=row.get('description', ''),
                        requirements=row.get('requirements', ''),
                        job_type=job_type,
                        experience_level=experience_level,
                        location=row.get('location', ''),
                        remote='REMOTE' in row.get('location', '').upper() or row.get('remote', '').lower() == 'true',
                        salary_min=salary_min,
                        salary_max=salary_max,
                        application_url=row.get('application_url', ''),
                        deadline=deadline,
                        is_active=True
                    )
                    
                    job_count += 1
                    if job_count % 100 == 0:
                        self.stdout.write(self.style.SUCCESS(f"Imported {job_count} jobs..."))
                        
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error importing row: {e}"))
            
            self.stdout.write(self.style.SUCCESS(f"Successfully imported {job_count} job listings"))