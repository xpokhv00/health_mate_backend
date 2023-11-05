from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken

from .serializers import UserSerializer, TokenObtainPairSerializer


# class RegisterView(APIView):
#     http_method_names = ['post']
#
#     def post(self, *args, **kwargs):
#         serializer = UserSerializer(data=self.request.data)
#         if serializer.is_valid():
#             get_user_model().objects.create_user(**serializer.validated_data)
#             return Response(status=HTTP_201_CREATED)
#         return Response(status=HTTP_400_BAD_REQUEST, data={'errors': serializer.errors})

class RegisterView(APIView):
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = get_user_model().objects.create_user(**serializer.validated_data)

            # Generate access and refresh tokens
            refresh = RefreshToken.for_user(user)

            refresh['doctor'] = user.doctor  # Assuming user.doctor is a boolean field
            refresh['email'] = user.email

            access = AccessToken.for_user(user)

            access['doctor'] = user.doctor  # Assuming user.doctor is a boolean field
            access['email'] = user.email

            return Response(
                {
                    'access': str(access),
                    'refresh': str(refresh),
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(status=status.HTTP_400_BAD_REQUEST, data={'errors': serializer.errors})


class EmailTokenObtainPairView(TokenObtainPairView):
    serializer_class = TokenObtainPairSerializer
