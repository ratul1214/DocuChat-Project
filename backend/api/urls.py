from django.urls import path
from django.contrib import admin
from views import ProgressTestView, PasswordLoginView, HealthView, MeView, DocumentsView, UploadView, AskView, ReportListView, ReportDetailView, AgentReportStartView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health", HealthView.as_view()),
    path("api/auth/login", PasswordLoginView.as_view()),  # <— new
    path("api/me", MeView.as_view()),
    path("api/documents", DocumentsView.as_view()),
    path("api/upload", UploadView.as_view()),
    path("api/chat/ask", AskView.as_view()),
    path("api/agent/report", AgentReportStartView.as_view()),
    path("api/agent/report/<int:report_id>", ReportDetailView.as_view()),
path("api/progress/test", ProgressTestView.as_view()),
]
