from django.urls import path
from . import views 
from .views import login_view, signup_view, logout_view
from .views import profile_view
urlpatterns = [
    path('', views.intro, name='intro'), 
    path('login/', login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', profile_view, name='profile'),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("fund-allocation/", views.fund_allocation, name="fund_allocation"),
    path("visualize-funds/", views.visualize_funds, name="visualize_funds"),
    path("portfolio-insights/", views.portfolio_insights, name="portfolio_insights"),
    path("generate-report/", views.generate_pdf_report, name="generate_pdf_report"),
    path('risk-return-analysis/', views.risk_return_analysis, name='risk_return_analysis'), 
    path('tax-optimization/', views.tax_optimization, name='tax_optimization'),
    path('about-us/', views.about_us, name='about_us'),  # New URL
]
