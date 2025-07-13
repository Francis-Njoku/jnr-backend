from rest_framework import serializers
from authentication.serializers import UserSerializer
from .models import (
    Skill, UserSkill, CVUpload, CVExtractionResult,
    CareerPath, RecommendedCourse, CareerRecommendation,
    UserSkillProfile, Company, JobListing, JobApplication
)
class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ['id', 'name', 'description', 'website', 'location', 
                  'created_at', 'updated_at']


class JobListingSerializer(serializers.ModelSerializer):
    company_details = CompanySerializer(source='company', read_only=True)
    posted_by_details = UserSerializer(source='posted_by', read_only=True)
    
    class Meta:
        model = JobListing
        fields = ['id', 'title', 'company', 'company_details', 
                  'posted_by', 'posted_by_details', 
                  'description', 'requirements', 'job_type', 
                  'experience_level', 'location', 'remote', 
                  'salary_min', 'salary_max', 'application_url', 
                  'deadline', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
    
    def create(self, validated_data):
        validated_data['posted_by'] = self.context['request'].user
        return super().create(validated_data)


class JobApplicationSerializer(serializers.ModelSerializer):
    applicant_details = UserSerializer(source='applicant', read_only=True)
    job_details = JobListingSerializer(source='job', read_only=True)
    
    class Meta:
        model = JobApplication
        fields = ['id', 'job', 'job_details', 'applicant', 'applicant_details', 
                  'resume', 'cover_letter', 'status', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at', 'applicant']
    
    def create(self, validated_data):
        validated_data['applicant'] = self.context['request'].user
        return super().create(validated_data)