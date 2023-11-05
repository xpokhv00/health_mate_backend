"""health_brain URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

from rest_api import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('users.urls')),
    path('auth/api/', include('rest_api.urls')),
    path('user/medication_today', views.TreatmentListView.as_view(), name='treatment-list'),
    path('user/treatment', views.UserTreatmentView.as_view(), name='user-treatments'),
    path('user/info', views.ProfileCreateView.as_view(), name='create-profile'),
    path('user/doctor', views.DoctorUserListView.as_view(), name='doctor-users'),
    path('user/message/doctor', views.CreateMessageView.as_view(), name='create-message'),
    path('doctor/patient/<int:user_id>/', views.GetUserTreatmentsView.as_view(), name='get-user-treatments'),
    path('user/diagnosis', views.UserDiagnosesView.as_view(), name='user-diagnoses'),
    path('doctor/patient/<int:patient_id>/treatment', views.CreateTreatmentView.as_view(), name='create-treatment'),
    path('doctor/patient/<int:patient_id>/diagnosis', views.CreateDiagnosisView.as_view(), name='create-diagnosis'),
    path('medisearch/message', views.MedisearchIntegrationView.as_view(), name='medisearch-integration'),
]
