from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Company, JobListing, JobApplication
from .serializers import CompanySerializer, JobListingSerializer, JobApplicationSerializer
from .permissions import IsEmployerOrAdmin, IsOwnerOrAdmin

class CompanyViewSet(viewsets.ModelViewSet):
    """
    API endpoint for companies.
    
    list: Get all companies
    retrieve: Get a specific company
    create: Create a new company (employers/admins only)
    update: Update a company (owner/admins only)
    partial_update: Partially update a company (owner/admins only)
    destroy: Delete a company (owner/admins only)
    """
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'location']
    ordering_fields = ['name', 'created_at']
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsEmployerOrAdmin()]
        return [permissions.IsAuthenticated()]


class JobListingViewSet(viewsets.ModelViewSet):
    """
    API endpoint for job listings.
    
    list: Get all job listings
    retrieve: Get a specific job listing
    create: Create a new job listing (employers/admins only)
    update: Update a job listing (owner/admins only)
    partial_update: Partially update a job listing (owner/admins only)
    destroy: Delete a job listing (owner/admins only)
    my_listings: Get job listings posted by the authenticated user (employers only)
    apply: Apply for a job (job seekers only)
    """
    queryset = JobListing.objects.all()
    serializer_class = JobListingSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['job_type', 'experience_level', 'remote', 'company']
    search_fields = ['title', 'description', 'company__name', 'location']
    ordering_fields = ['created_at', 'deadline']
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'my_listings']:
            return [IsEmployerOrAdmin()]
        return [permissions.IsAuthenticated()]
    
    def get_queryset(self):
        # Filter by active status unless user is employer/admin
        if self.request.user.role in ['EMPLOYER', 'ADMIN'] or self.request.user.is_staff:
            return JobListing.objects.all()
        return JobListing.objects.filter(is_active=True)
    
    @action(detail=False, methods=['get'])
    def my_listings(self, request):
        """Get job listings posted by the authenticated user (employers only)."""
        listings = JobListing.objects.filter(posted_by=request.user)
        page = self.paginate_queryset(listings)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(listings, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def apply(self, request, pk=None):
        """Apply for a job (job seekers only)."""
        if request.user.role != 'JOB_SEEKER':
            return Response({"detail": "Only job seekers can apply for jobs."},
                           status=status.HTTP_403_FORBIDDEN)
        
        job = self.get_object()
        if not job.is_active:
            return Response({"detail": "This job listing is no longer active."},
                           status=status.HTTP_400_BAD_REQUEST)
        
        # Check if the user has already applied
        existing_application = JobApplication.objects.filter(job=job, applicant=request.user).first()
        if existing_application:
            return Response({"detail": "You have already applied for this job."},
                           status=status.HTTP_400_BAD_REQUEST)
        
        serializer = JobApplicationSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(job=job, applicant=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class JobApplicationViewSet(viewsets.ModelViewSet):
    """
    API endpoint for job applications.
    
    list: Get all job applications (filtered by role)
    retrieve: Get a specific job application (owner/employers/admins only)
    create: Create a new job application (job seekers only)
    update: Update a job application (owner/employers/admins only)
    partial_update: Partially update a job application (owner/employers/admins only)
    destroy: Delete a job application (owner/admins only)
    my_applications: Get applications made by the authenticated user (job seekers only)
    """
    serializer_class = JobApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        # Admins can see all applications
        if user.role == 'ADMIN' or user.is_staff:
            return JobApplication.objects.all()
        # Employers can see applications for their job listings
        elif user.role == 'EMPLOYER':
            return JobApplication.objects.filter(job__posted_by=user)
        # Job seekers can see their own applications
        else:
            return JobApplication.objects.filter(applicant=user)
    
    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsOwnerOrAdmin()]
        return [permissions.IsAuthenticated()]
    
    @action(detail=False, methods=['get'])
    def my_applications(self, request):
        """Get applications made by the authenticated user (job seekers only)."""
        if request.user.role != 'JOB_SEEKER':
            return Response({"detail": "Only job seekers can view their applications."},
                           status=status.HTTP_403_FORBIDDEN)
        
        applications = JobApplication.objects.filter(applicant=request.user)
        page = self.paginate_queryset(applications)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(applications, many=True)
        return Response(serializer.data)