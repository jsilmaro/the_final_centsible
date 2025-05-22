from rest_framework.views import APIView
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .models import CustomUser
from .serializers import UserSerializer, LoginSerializer
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import check_password
from django.utils import timezone
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import api_view, permission_classes, parser_classes
from django.conf import settings

def get_user_data(user):
    avatar_url = None
    if user.avatar:
        avatar_url = f"http://0.0.0.0:8000/api{settings.MEDIA_URL}{user.avatar}"
    
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "avatar": avatar_url,
        "preferences": user.preferences,
        "is_active": user.is_active,
        "is_staff": user.is_staff,
    }

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_profile(request):
    return Response(get_user_data(request.user), status=200)

class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Create user with proper password hashing
        user = CustomUser.objects.create_user(
            email=request.data["email"],
            name=request.data["name"],
            password=request.data["password"]
        )

        # Handle avatar upload (if provided)
        if "avatar" in request.FILES:
            user.avatar = request.FILES["avatar"]

        # Initialize preferences (default settings or user-provided preferences)
        user.preferences = {
            "currency": request.data.get("currency", "USD"),
            "email_alerts": request.data.get("email_alerts", True),
            "weekly_reports": request.data.get("weekly_reports", False),
            "budget_alerts": request.data.get("budget_alerts", True)
        }

        user.save()

        refresh = RefreshToken.for_user(user)
        return Response({
            "token": str(refresh.access_token),
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "avatar": user.avatar.url if user.avatar else None,
                "preferences": user.preferences,
            }
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    def post(self, request):
        # Step 1: Get email and password from the request
        email = request.data.get("email")
        password = request.data.get("password")

        # Step 2: Check if both fields are provided
        if not email or not password:
            return Response({"error": "Email and password are required."}, status=status.HTTP_400_BAD_REQUEST)

        # Step 3: Find user in the database using email
        user = CustomUser.objects.filter(email=email).first()
        print("User Found:", user)  # Debugging step: Prints None if no user exists

        # Step 4: Check if user exists and if password matches
        if not user or not check_password(password, user.password):
            return Response({"error": "Invalid email or password."}, status=status.HTTP_401_UNAUTHORIZED)

        # Step 5: Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        # Step 6: Return the access token and user info in the response
        return Response({
            "token": str(refresh.access_token),
            "user": UserSerializer(user).data
        }, status=status.HTTP_200_OK)

@api_view(["GET"])
@permission_classes([IsAuthenticated])  # Requires authentication to access this endpoint
def get_user(request):
    user = request.user
    return Response({
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "avatar": user.avatar.url if user.avatar else None,
        "preferences": user.preferences,
    })



@api_view(["PUT"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])  
def update_profile(request):
    user = request.user
    data = request.data

    user.name = data.get("name", user.name)
    user.email = data.get("email", user.email)

    # ✅ Handle avatar upload properly
    if "avatar" in request.FILES:
        user.avatar = request.FILES["avatar"]
    elif data.get("remove_avatar") == "true":
        user.avatar = None  # ✅ Allows avatar removal

    user.save()

    return Response({
        "message": "Profile updated successfully.",
        "avatar_url": user.avatar.url if user.avatar else None,  # ✅ Returns updated avatar URL
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    user = request.user
    if not check_password(request.data['current_password'], user.password):
        return Response({'error': 'Current password is incorrect'}, status=400)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    user = request.user
    if not check_password(request.data['current_password'], user.password):
        return Response({'error': 'Current password is incorrect'}, status=400)
    user.set_password(request.data['new_password'])
    user.last_password_change = timezone.now()
    user.save()
    return Response({'message': 'Password updated successfully'})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_preferences(request):
    VALID_CURRENCIES = ['USD', 'EUR', 'GBP', 'JPY', 'CAD']

    user = request.user
    data = request.data

    if 'currency' in data and data['currency'] not in VALID_CURRENCIES:
        return Response({'error': 'Invalid currency'}, status=400)

    preferences = {
        'currency': data.get('currency', user.preferences.get('currency', 'USD')),
        'email_alerts': data.get('email_alerts', user.preferences.get('email_alerts', True)),
        'weekly_reports': data.get('weekly_reports', user.preferences.get('weekly_reports', False)),
        'budget_alerts': data.get('budget_alerts', user.preferences.get('budget_alerts', True))
    }

    user.preferences = preferences
    user.save()

    return Response(user.preferences)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    user = request.user
    if 'avatar' in request.FILES:
        user.avatar = request.FILES['avatar']
    if 'name' in request.data:
        user.name = request.data['name']
    user.save()
    return Response(UserSerializer(user).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    user = request.user
    data = request.data

    if not check_password(data.get("current_password"), user.password):
        return Response({"error": "Current password is incorrect."}, status=status.HTTP_400_BAD_REQUEST)
    user.set_password(request.data['new_password'])
    user.last_password_change = timezone.now()
    user.save()
    return Response({'message': 'Password updated successfully'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_preferences(request):
    VALID_CURRENCIES = ['USD', 'EUR', 'GBP', 'JPY', 'CAD']
    user = request.user
    data = request.data
    
    if 'currency' in data and data['currency'] not in VALID_CURRENCIES:
        return Response({'error': 'Invalid currency'}, status=400)
        
    preferences = user.preferences or {}
    
    # Update only provided fields
    if 'currency' in data:
        preferences['currency'] = data['currency']
    if 'email_alerts' in data:
        preferences['email_alerts'] = data['email_alerts']
    if 'weekly_reports' in data:
        preferences['weekly_reports'] = data['weekly_reports']
    if 'budget_alerts' in data:
        preferences['budget_alerts'] = data['budget_alerts']
    
    user.preferences = preferences
    user.save()
    
    # Return complete user data to update frontend state
    return Response({
        'message': 'Preferences updated successfully',
        'preferences': user.preferences,
        'user': UserSerializer(user).data,
        'success': True
    })



@api_view(["PUT"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def update_profile(request):
    try:
        user = request.user
        data = request.data

        if "email" in data:
            user.email = data["email"]
        if "name" in data:
            user.name = data["name"]

        if "avatar" in request.FILES:
            user.avatar = request.FILES["avatar"]
        elif data.get("remove_avatar") == "true":
            user.avatar = None

        user.save()
        
        return Response({
            "message": "Profile updated successfully",
            "user": UserSerializer(user).data,
            "avatar_url": user.avatar.url if user.avatar else None,
            "success": True
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            "error": "Failed to update profile",
            "detail": str(e),
            "success": False
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    user = request.user
    current_password = request.data.get('current_password')
    new_password = request.data.get('new_password')

    if not current_password or not new_password:
        return Response({
            'error': 'Both current and new password are required'
        }, status=status.HTTP_400_BAD_REQUEST)

    # Use authenticate to verify current password
    if not authenticate(email=user.email, password=current_password):
        return Response({
            'error': 'Current password is incorrect'
        }, status=status.HTTP_400_BAD_REQUEST)

    user.set_password(new_password)
    user.save()
    
    # Generate new token after password change
    refresh = RefreshToken.for_user(user)
    return Response({
        'message': 'Password updated successfully',
        'token': str(refresh.access_token),
        'success': True
    }, status=status.HTTP_200_OK)

@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_preferences(request):
    user = request.user
    preferences = request.data.get("preferences", {})

    if not isinstance(preferences, dict):
        return Response({"error": "Invalid preferences format"}, status=status.HTTP_400_BAD_REQUEST)

    # Update only valid fields
    user.preferences.update({
        "currency": preferences.get("currency", user.preferences.get("currency", "USD")),
        "email_alerts": preferences.get("email_alerts", user.preferences.get("email_alerts", True)),
        "weekly_reports": preferences.get("weekly_reports", user.preferences.get("weekly_reports", True)),
        "budget_alerts": preferences.get("budget_alerts", user.preferences.get("budget_alerts", True))
    })

    user.save()
    return Response(user.preferences)