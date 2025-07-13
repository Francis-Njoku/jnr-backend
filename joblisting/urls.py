from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CompanyViewSet, JobListingViewSet, JobApplicationViewSet

router = DefaultRouter()
router.register('companies', CompanyViewSet)
router.register('job/listing', JobListingViewSet)
router.register('applications', JobApplicationViewSet, basename='jobapplication')

urlpatterns = [
    path('', include(router.urls)),
]
