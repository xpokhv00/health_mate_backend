import re
from datetime import timedelta
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from rest_framework import viewsets, permissions, generics, status
from rest_framework.views import APIView
import requests

from users.models import CustomUser
from .models import Treatment, Message, Profile, Diagnosis, Appointment
from .serializers import TreatmentSerializer, MessageSerializer, ProfileSerializer, UserSerializer, DiagnosisSerializer, \
    AppointmentSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics, permissions
from django.utils import timezone
from .models import Treatment, Medication
from .serializers import MedicationSerializer, TreatmentSerializer
from rest_framework.response import Response

from medisearch_client import MediSearchClient


# Create your views here.

class TreatmentViewSet(viewsets.ModelViewSet):
    queryset = Treatment.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = TreatmentSerializer


class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = MessageSerializer


class ProfileViewSet(viewsets.ModelViewSet):
    queryset = Profile.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = ProfileSerializer


class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Profile.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = ProfileSerializer


class TreatmentListView(generics.ListAPIView):
    serializer_class = TreatmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user  # Get the user from the JWT token
        current_date = timezone.now().date()
        return Treatment.objects.filter(patient=user, finish_date__gte=current_date)


class TreatmentWithMedicationListView(generics.ListAPIView):
    serializer_class = TreatmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user  # Get the user from the JWT token
        current_date = timezone.now().date()
        return Treatment.objects.filter(patient=user, finish_date__gte=current_date)


class UserTreatmentView(generics.ListAPIView):
    serializer_class = TreatmentSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user  # Get the user from the JWT token

        # Filter treatments by patient and finish_date
        queryset = Treatment.objects.filter(patient=user)
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        treatments_data = self.serializer_class(queryset, many=True).data
        response_data = []

        for treatment in treatments_data:
            # Extract the name value from the treatment
            treatment_name = treatment.get('name')

            # Search for a medication with the same name
            medication = Medication.objects.filter(name=treatment_name).first()

            # Serialize medication data
            medication_data = MedicationSerializer(medication).data if medication else {}

            # Create a response with treatment and medication fields
            response_data.append({
                'treatment': treatment,
                'medication': medication_data,
            })

        return Response(response_data)


class ProfileCreateView(generics.CreateAPIView, generics.RetrieveAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [permissions.AllowAny]

    def get_object(self):
        # Retrieve the user from the JWT token
        user = self.request.user

        # Get the profile associated with the user
        try:
            profile = Profile.objects.get(user=user)
            return profile
        except Profile.DoesNotExist:
            return None

    def create(self, request, *args, **kwargs):
        # Extract the user from the JWT token
        user = self.request.user

        # Merge the user with the data from the POST request
        data = request.data.copy()
        data['user'] = user.id

        # Serialize and validate the profile data
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)

        # Save the profile
        serializer.save()

        return Response(status=status.HTTP_201_CREATED)

    def retrieve(self, request, *args, **kwargs):
        profile = self.get_object()

        if profile is not None:
            serializer = self.get_serializer(profile)
            return Response(serializer.data)
        else:
            return Response({"detail": "Profile not found for this user."}, status=status.HTTP_404_NOT_FOUND)


class DoctorUserListView(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        # Retrieve all users with doctor=True
        queryset = CustomUser.objects.filter(doctor=True)
        return queryset

    def list(self, request, *args, **kwargs):
        users = self.get_queryset()
        user_data = self.serializer_class(users, many=True).data

        # Retrieve associated profiles and serialize them
        profile_data = []
        for user in users:
            try:
                profile = Profile.objects.get(user=user)
                profile_data.append(ProfileSerializer(profile).data)
            except Profile.DoesNotExist:
                profile_data.append({})  # Return an empty dictionary if no profile is found

        # Combine user and profile data in the response
        response_data = []
        for user, profile in zip(user_data, profile_data):
            response_data.append({**user, 'profile': profile})

        return Response(response_data)


class CreateMessageView(generics.CreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        # Extract the user from the JWT token
        user = request.user
        patient_email = request.user.email
        print(patient_email, "PATIENT EMAIL")

        # Extract the mail and message from the request data
        mail = request.data.get('email')
        message_text = request.data.get('message')

        # Find the doctor by email
        try:
            doctor = CustomUser.objects.get(email=mail, doctor=True)
        except CustomUser.DoesNotExist:
            return Response({"detail": "Doctor not found for the given email."}, status=status.HTTP_404_NOT_FOUND)

        # Create a new Message object
        message = Message(patient=user, doctor=doctor, message=message_text)
        message.save()

        # Send an email to the doctor
        subject = "New Message from Patient"
        message_content = render_to_string(
            'email/message_email.html',
            {
                'doctor_email': mail,  # Customize as needed
                'patient_email': patient_email,  # Customize as needed
                'message': message_text,
            }
        )
        from_email = settings.EMAIL_HOST_USER  # Replace with your email
        recipient_list = [doctor.email]

        send_mail(subject, message_content, from_email, recipient_list, fail_silently=False,
                  html_message=message_content)

        return Response(status=status.HTTP_201_CREATED)


class GetUserTreatmentsView(generics.ListAPIView):
    serializer_class = TreatmentSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        # Extract the user ID from the GET request's query parameters
        user_id = self.kwargs['user_id']

        # Retrieve all treatments with user field equal to the provided user ID
        queryset = Treatment.objects.filter(patient=user_id)
        return queryset

    def list(self, request, *args, **kwargs):
        treatments = self.get_queryset()
        treatment_data = self.serializer_class(treatments, many=True).data

        # Retrieve the profile data for the user
        user_id = self.kwargs['user_id']
        try:
            profile = Profile.objects.get(user=user_id)
            profile_data = ProfileSerializer(profile).data
        except Profile.DoesNotExist:
            profile_data = {}

        response_data = {
            'treatments': treatment_data,
            'profile': profile_data,
        }

        return Response(response_data)


class UserDiagnosesView(generics.ListAPIView):
    serializer_class = DiagnosisSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        # Retrieve the user from the JWT token
        user = self.request.user

        # Retrieve all diagnoses for the user
        queryset = Diagnosis.objects.filter(patient=user)
        return queryset


class CreateTreatmentView(generics.CreateAPIView):
    serializer_class = TreatmentSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        # Extract the doctor from the JWT token
        doctor = request.user

        # Extract the patient's ID from the URL path
        patient_id = self.kwargs['patient_id']

        # Check if the patient exists
        try:
            patient = CustomUser.objects.get(id=patient_id)
        except CustomUser.DoesNotExist:
            return Response({"detail": "Patient not found."}, status=status.HTTP_404_NOT_FOUND)

        # Combine the doctor, patient, and other data from the request
        data = request.data.copy()
        data['doctor'] = doctor.id
        data['patient'] = patient.id

        # Serialize and validate the treatment data
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(status=status.HTTP_201_CREATED)


class CreateDiagnosisView(generics.CreateAPIView):
    serializer_class = DiagnosisSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        # Extract the doctor from the JWT token
        doctor = request.user

        # Extract the patient's ID from the URL path
        patient_id = self.kwargs['patient_id']

        # Check if the patient exists
        try:
            patient = CustomUser.objects.get(id=patient_id)
        except CustomUser.DoesNotExist:
            return Response({"detail": "Patient not found."}, status=status.HTTP_404_NOT_FOUND)

        # Combine the doctor, patient, and other data from the request
        data = request.data.copy()
        data['doctor'] = doctor.id
        data['patient'] = patient.id

        # Serialize and validate the treatment data
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class MedisearchIntegrationView(APIView):
    http_method_names = ['post']
    permission_classes = (permissions.IsAuthenticated,)  # Add appropriate permission

    def post(self, request, *args, **kwargs):
        # Deserialize the message data (if you have a serializer for it)
        message = request.data.get('message')

        authorization_header = request.headers.get('Authorization')

        if authorization_header and authorization_header.startswith('Bearer '):
            # Extract the token part by removing 'Bearer ' prefix
            jwt_token = authorization_header.split(' ')[1]

            # Get the user from the JWT token

            client = MediSearch()

            response = client.ask(message, jwt_token)

            return Response(
                {'answer': response},
                status=status.HTTP_200_OK,
            )

        else:
            # Authorization header is missing or invalid
            return Response({'error': 'Invalid or missing JWT token'}, status=status.HTTP_401_UNAUTHORIZED)


class MediSearch:
    # Initialise the MediSearch client
    def __init__(self):
        self.client = MediSearchClient(api_key="1DB9Yw5rHk8dQhIG5CtR")
        self.manager = Manager()

    # Makes the API call to MediSearch
    def __askAI__(self, query):
        try:
            responses = self.client.send_user_message(
                conversation=query,
                conversation_id="",
                should_stream_response=False,
            )
        except Exception as e:
            return self.__error_handler__(e)
        # filter out the response and catch sources
        for response in responses:
            try:
                return response["text"]
            except Exception as e:
                if response["error_code"]:
                    return self.__error_handler__(response["error_code"])
                else:
                    return self.__error_handler__(e)

    # Private Method to generate the context query for the AI.
    # This and the answer the AI will give to the context needs to be filtered out in either frontend or backend
    def __generateQuery__(self, patient_data, additional_info):
        query = f"{patient_data} {additional_info} Medical knowledge: low"
        return str(query)

    def __remove_sources__(self, response):
        return re.sub(r"\s?\[\d+(,\s*\d+)*\]", "", response)

    def __request_patient_data__(self, patient_id):
        # make an api call to get the patient data
        url = "http://localhost:8000/auth/api/profile/"

        headers = {"Authorization": f"Bearer {patient_id}"}

        response = str(requests.get(url, headers=headers).json())

        if "age" not in response:
            return self.__error_handler__("Token not valid")
        else:
            return response

    def __error_handler__(self, error_code):
        error_code = str(error_code)
        print(error_code)
        if error_code == "Token not valid":
            return (
                "Oh snap! You don't seem to be logged in. Please log in and try again."
            )
        elif error_code == "error_auth":
            return "Oh snap! Some developer messed up the API key. Please contact the developers."
        elif error_code == "error_internal":
            return "Oh snap! Some developer messed up the backend. Please contact the developers."
        elif error_code == "error_llm":
            return "Oh snap! Some developer messed up the AI. Please contact the developers."
        elif error_code == "error_missing_key":
            return "Oh snap! Some developer forgot the API key. Please contact the developers."
        elif error_code in {"error_not_enough_articles", "error_out_of_tokens"}:
            return "Oh snap! You overwhelmed our AI. Please close the chat and open it again."
        else:
            return "Oh snap! Something went wrong. Please try again and if the problem persists, contact the developers."

    # Public method to ask the AI a question
    def ask(self, question, patient_id, additional_info=""):
        # If the chat does not exist, create it and ask the question with the patient data
        if not self.manager.chat_exists(patient_id):
            self.manager.init_chat(patient_id)
            query = self.__generateQuery__(patient_id, additional_info)
            if "Oh snap!" in query:
                return query
            self.manager.add_message(patient_id, question)
            message = str(self.__askAI__([f"{query} {question}"]))
            if "Oh snap!" in message:
                return message
            self.manager.add_message(patient_id, self.__remove_sources__(message))
        else:
            self.manager.add_message(patient_id, question)
            message = str(self.manager.get_chat(patient_id))
            if "Oh snap!" in message:
                return message
            self.manager.add_message(patient_id, self.__askAI__(message))
        return self.manager.get_latest_message(patient_id)

    def end_chat(self, patient_id):
        self.manager.remove_chat(patient_id)


class Manager:
    def __init__(self):
        self.chats = {}

    def init_chat(self, patient_id):
        self.chats[patient_id] = []

    def add_message(self, patient_id, message):
        self.chats[patient_id].append(message)

    def get_chat(self, patient_id):
        return self.chats[patient_id]

    def remove_chat(self, patient_id):
        del self.chats[patient_id]

    def chat_exists(self, patient_id):
        return patient_id in self.chats

    def get_latest_message(self, patient_id):
        return self.chats[patient_id][-1]
