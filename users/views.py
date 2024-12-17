"""from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.http import JsonResponse

from rest_framework import viewsets
from .models import CustomUser
from .serializers import UserSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer


def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return JsonResponse({'message': 'Login successful'})
        else:
            return JsonResponse({'error': 'Invalid credentials'}, status=400)
    return render(request, 'users/login.html')

def user_logout(request):
    logout(request)
    return redirect('login')

from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse

@login_required
@permission_required('users.add_document', raise_exception=True)
def restricted_view(request):
    return JsonResponse({'message': 'You have access!'})"""

"""

from django.contrib.auth import login, authenticate
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponseForbidden
from django.contrib.auth.models import Group, User
from .serializers import UserSerializer
from rest_framework import viewsets

# Register view
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
             # Add the user to the 'Employees' group by default
            employees_group = Group.objects.get(name='Employee')
            user.groups.add(employees_group)
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'users/register.html', {'form': form})

# Login view
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            # Redirect based on role
            if user.groups.filter(name='Administrator').exists():
                print("User is an Administrator.")
                return redirect('admin_view')
            elif user.groups.filter(name='Employee').exists():
                return redirect('employee_dashboard')  # Redirect to document list or creation form
            elif user.groups.filter(name='Manager').exists():
                return redirect('manager_dashboard')  # Redirect to document list or creation form
            else:
                return HttpResponseForbidden("You do not have permission to access this page.")
    else:
        form = AuthenticationForm()
    return render(request, 'users/login.html', {'form': form})

# Group-required decorator
def group_required(group_name):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            if not request.user.groups.filter(name=group_name).exists():
                return HttpResponseForbidden("You do not have permission to access this page.")
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

# Admin-only view
@login_required
@group_required('Administrator')
def admin_view(request):
    return render(request, 'users/admin_page.html')


from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponseForbidden

# Function to check if user is a manager
def is_manager(user):
    return user.groups.filter(name='Manager').exists()

# Function to check if user is an employee
def is_employee(user):
    return user.groups.filter(name='Employee').exists()

@login_required
@user_passes_test(is_manager, login_url='login')
def manager_dashboard(request):
    return render(request, 'users/manager_dashboard.html')

@login_required
@user_passes_test(is_employee, login_url='login')
def employee_dashboard(request):
    return render(request, 'users/employee_dashboard.html')



class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.contrib.auth.models import Group, User
from django.contrib.auth import authenticate, login
from .serializers import UserSerializer
from rest_framework.decorators import api_view, permission_classes

# Register API
class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            employees_group, created = Group.objects.get_or_create(name='Employee')
            user.groups.add(employees_group)
            return Response({"message": "User registered successfully."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Login API

from rest_framework_simplejwt.tokens import RefreshToken

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        print("LoginView accessed")  # Debugging statement

        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user:
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)

            # Determine the user's role
            if user.groups.filter(name='Administrator').exists():
                role = 'Administrator'
            elif user.groups.filter(name='Manager').exists():
                role = 'Manager'
            elif user.groups.filter(name='Employee').exists():
                role = 'Employee'
            else:
                return Response({"error": "User does not have a valid role."}, status=status.HTTP_403_FORBIDDEN)

            return Response({
                'access_token': access_token,
                'refresh_token': str(refresh),
                'role': role
            }, status=status.HTTP_200_OK)
        else:
            print(f"Failed login attempt for username: {username}")
            return Response({"error": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)



# Group-based Views
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def admin_view(request):
    if request.user.groups.filter(name='Administrator').exists():
        return Response({"message": "Welcome, Administrator!"})
    return Response({"error": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def manager_dashboard(request):
    if request.user.groups.filter(name='Manager').exists():
        return Response({"message": "Welcome, Manager!"})
    return Response({"error": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def employee_dashboard(request):
    if request.user.groups.filter(name='Employee').exists():
        return Response({"message": "Welcome, Employee!"})
    return Response({"error": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

# User ViewSet
from rest_framework.viewsets import ModelViewSet

class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]