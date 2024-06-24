from django.urls import path
from . import views

urlpatterns = [
    path('',views.login_page,name='login_page'),
    path('index/', views.index, name='index'),
    path('road_info/<int:road_type>/', views.road_info, name='road_info'),
    path('templates/<str:road_type>/', views.road_sec_info, name='road_sec_info'),
    # path('fetching_data/', views.fetching_data, name='fetching_data'),
    path('analyze_data/', views.analyze_data, name='analyze_data'),
    path('signin_page/', views.signin_page, name='signin_page'),
    path('register_page/', views.register_page, name='register_page'),
    path('verify_otp_view/', views.verify_otp_view, name='verify_otp_view'),
    # path('logout_page/', views.logout_page, name='logout_page'),
    path('generateReport/', views.generateReport, name='generateReport'),
    path('generate_pdf/', views.generate_pdf, name='generate_pdf'),
    path('intersection_list/', views.intersection_list, name='intersection_list'),
    

    ]