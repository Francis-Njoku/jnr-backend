from urllib import request
from django.shortcuts import render
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.viewsets import ModelViewSet
from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from rest_framework import status
#from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
#from core.auth.serializers import LoginSerializer, RegistrationSerializer
from django.core.mail import send_mail as sender
from rest_framework import filters, generics, status, views, permissions
from .serializers import ProfileInvestorSerializer, ProfileIssuerSerializer, UserSerializer, ApproveUserSerializer, VerifiedUserSerializer, SigninSerializer, ReferralSerializer, InviteSerializer, RegisterSerializer, SetNewPasswordSerializer, ResetPasswordEmailRequestSerializer, EmailVerificationSerializer, LoginSerializer, LogoutSerializer, UserSerializer
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, ListCreateAPIView, RetrieveUpdateDestroyAPIView, RetrieveAPIView
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from .models import Referrals, User
from .utils import Util
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
import jwt
import csv
import io
from django.conf import settings
from drf_yasg.utils import swagger_auto_schema
from rest_framework.parsers import MultiPartParser, FormParser
from drf_yasg import openapi
from .renderers import UserRenderer
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import smart_str, force_str, smart_bytes, DjangoUnicodeDecodeError
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from .utils import Util, username_generator, referral_generator
from django.shortcuts import redirect
from django.http import FileResponse, HttpResponsePermanentRedirect, HttpResponse, Http404
import os
import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import Image
from django_filters.rest_framework import DjangoFilterBackend
from django.template.loader import render_to_string, get_template
#from xhtml2pdf import pisa
from fpdf import FPDF
'''

from weasyprint import HTML
import tempfile
'''
# test
'''

def fetch_resources(uri, rel):
    path = os.path.join(uri.replace(settings.STATIC_URL, ""))
    return path


def render_to_pdf(template_src, context_dict={}):
    template = get_template(template_src)
    html = template.render(context_dict)
    result = io.BytesIO()
    pdf = pisa.pisaDocument(io.BytesIO(html.encode("ISO-8859-1")), result)
    if not pdf.error:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None
'''

        
class UserListAPIView(ListAPIView):
    serializer_class = UserSerializer
    queryset = User.objects.all().order_by('-created_at')
    permission_classes = (IsAuthenticated, IsAdminUser,)
    filter_backends = [DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter]

    filterset_fields = ['firstname', 'lastname',
                        'phone', 'referral_code', 'email',
                        ]
    search_fields = ['firstname', 'lastname',
                     'phone', 'email', 'referral_code']


    def get_queryset(self):
        return self.queryset.all()


class UserDetailAPIView(RetrieveUpdateDestroyAPIView):
    serializer_class = UserSerializer
    queryset = User.objects.all()
    permission_classes = (IsAuthenticated,)
    lookup_field = "id"

    def get_queryset(self):
        return self.queryset.filter(id=self.request.user)

class UserInvestorAPIView(RetrieveUpdateDestroyAPIView):
    serializer_class = UserSerializer
    queryset = User.objects.all()
    permission_classes = (IsAuthenticated,)
    lookup_field = "id"

    def get_queryset(self):
        return self.queryset.filter(id=self.request.user)

class RefreshViewSet(viewsets.ViewSet, TokenRefreshView):
    permission_classes = (AllowAny,)
    http_method_names = ['post']

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0])

        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class LoginViewSet(ModelViewSet, TokenObtainPairView):
    serializer_class = SigninSerializer
    permission_classes = (AllowAny,)
    http_method_names = ['post']

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0])

        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class Invite(views.APIView):

    serializer_class = InviteSerializer
    serializer_referral = ReferralSerializer

    invite_param_config = openapi.Parameter(
        'user', in_=openapi.IN_QUERY, description='Description', type=openapi.TYPE_STRING)

    @swagger_auto_schema(manual_parameters=[invite_param_config])
    def get(self, request):
        referral_code = request.GET.get('user')

        item = User.objects.get(referral_code=referral_code)
        # print(item)
        if item.is_approved:
            serializer = InviteSerializer(item)
            return Response({"status": "success", "data": serializer.data}, status=status.HTTP_200_OK)
        else:
            return Response({"status": "error",  "error": "Object with referral code does not exists"},
                            status=status.HTTP_400_BAD_REQUEST)


class CustomRedirect(HttpResponsePermanentRedirect):

    allowed_schemes = [os.environ.get('APP_SCHEME'), 'http', 'https']


class RegisterView(generics.GenericAPIView):

    serializer_class = RegisterSerializer
    renderer_classes = (UserRenderer,)

    def post(self, request):
        user = {
            'firstname': request.data.get('firstname'),
            'lastname': request.data.get('lastname'),
            'username': request.data.get('firstname')+request.data.get('lastname')+str(username_generator()),
            'address': request.data.get('address'),
            'is_approved':True,
            'linkedin': request.data.get('linkedln'),
            'referral_code': str(referral_generator()),
            'phone': request.data.get('phone'),
            'password': request.data.get('password'),
            'email': request.data.get('email'), }
        #user = request.data
        serializer = self.serializer_class(data=user)
        serializer.is_valid(raise_exception=True)
        serializer.save()
         
        user = User.objects.get(email=request.data.get('email'))
        token = RefreshToken.for_user(user).access_token
        current_site = get_current_site(request).domain
        relativeLink = reverse('email-verify')
        #absurl = 'https://'+current_site+relativeLink+"?token="+str(token)
        absurl = request.data.get('callBackUrl')+"?token="+str(token)
        print(absurl)
        email_body = 'Hi '+user.firstname + \
            ' Use the link below to verify your email \n' + absurl
        data = {'email_body': email_body, 'to_email': user.email,
                'email_subject': 'Verify your email'}
        sender(data['email_subject'], data['email_body'],
               'hello@roadmap.careers', [data['to_email']])
    

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class RegisterIssuerView(generics.GenericAPIView):
    serializer_class = RegisterSerializer
    profile_serializer = ProfileIssuerSerializer
    renderer_classes = (UserRenderer,)
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        user = {
            'firstname': request.data.get('firstname'),
            'lastname': request.data.get('lastname'),
            'username': str(username_generator()),
            'address': request.data.get('address'),
            'is_approved':True,
            'linkedin': request.data.get('linkedin'),
            'referral_code': str(referral_generator()),
            'phone': request.data.get('phone'),
            'password': request.data.get('password'),
            'email': request.data.get('email'), 
            }
        #user = request.data
        serializer = self.serializer_class(data=user)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        user_data = serializer.data
        user = User.objects.get(email=user_data['email'])
        token = RefreshToken.for_user(user).access_token
        current_site = get_current_site(request).domain
        relativeLink = reverse('email-verify')
        #absurl = 'https://'+current_site+relativeLink+"?token="+str(token)
        absurl = request.data.get('callBackUrl')+"?token="+str(token)
        print(absurl)
        email_body = 'Hi '+user.firstname + \
            ' Use the link below to verify your email \n' + absurl
        data = {'email_body': email_body, 'to_email': user.email,
                'email_subject': 'Verify your email'}
        sender(data['email_subject'], data['email_body'],
               'hello@roadmap.careers', [data['to_email']])

        Util.send_email(data)
        return Response(user, status=status.HTTP_201_CREATED)


class RegisterReferralView(generics.GenericAPIView):

    serializer_class = RegisterSerializer
    referal_serializer = ReferralSerializer
    renderer_classes = (UserRenderer,)

    def post(self, request):
        if request.data.get('referral_code'):
            check_user = User.objects.get(
                referral_code=request.data.get('referral_code'))
            print(check_user.id)
            if check_user:
                today = datetime.date.today()
                thirty_days_ago = today - datetime.timedelta(days=30)
                check_refers = Referrals.objects.filter(
                    referred=check_user.id, created_at__gte=thirty_days_ago)
                if len(check_refers) > 4:
                    return Response({"status": "error",  "error": "User with referral code exceeded monthly limit"},
                                    status=status.HTTP_400_BAD_REQUEST)
                else:
                    user = {
                        'firstname': request.data.get('firstname'),
                        'lastname': request.data.get('lastname'),
                        'username': str(username_generator()),
                        'address': request.data.get('address'),
                        'linkedin': request.data.get('linkedln'),
                        'referral_code': str(referral_generator()),
                        'phone': request.data.get('phone'),
                        'password': request.data.get('password'),
                        'email': request.data.get('email'), }
                    #user = request.data
                    serializer = self.serializer_class(data=user)
                    serializer.is_valid(raise_exception=True)
                    serializer.save()
                    user_data = serializer.data
                    user = User.objects.get(email=user_data['email'])
                    token = RefreshToken.for_user(user).access_token
                    current_site = get_current_site(request).domain
                    relativeLink = reverse('email-verify')
                    absurl = 'https://'+current_site + \
                        relativeLink+"?token="+str(token)
                    print(absurl)
                    email_body = 'Hi '+user.firstname + \
                        ' Use the link below to verify your email \n' + absurl
                    data = {'email_body': email_body, 'to_email': user.email,
                            'email_subject': 'Verify your email'}

                    Util.send_email(data)
                    return Response(user_data, status=status.HTTP_201_CREATED)
            else:
                return Response({"status": "error",  "error": "Referral code does not exists"},
                                status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"status": "error",  "error": "No referral code entered"},
                            status=status.HTTP_400_BAD_REQUEST)

class ResendVerificationEmailView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        email = request.data.get('email')
        callback_url = request.data.get('callBackUrl')  # Important for the frontend link
        try:
            user = User.objects.get(email=email)
            if user.is_verified:
                return Response({'detail': 'Email already verified.'}, status=status.HTTP_400_BAD_REQUEST)
            
            token = RefreshToken.for_user(user).access_token
            current_site = get_current_site(request).domain
            relativeLink = reverse('email-verify')  # e.g. 'email-verify'
            verification_url = f"{callback_url}?token={str(token)}"

            email_body = f"Hi {user.firstname},\nUse the link below to verify your email:\n{verification_url}"
            email_data = {
                'email_body': email_body,
                'to_email': user.email,
                'email_subject': 'Verify your email'
            }

            sender(email_data['email_subject'], email_data['email_body'], 'hello@roadmap.careers', [email_data['to_email']])
            Util.send_email(email_data)

            return Response({'detail': 'Verification email resent.'}, status=status.HTTP_200_OK)
        
        except User.DoesNotExist:
            return Response({'error': 'User with this email does not exist.'}, status=status.HTTP_404_NOT_FOUND)

class VerifyEmail(views.APIView):
    serializer_class = EmailVerificationSerializer

    token_param_config = openapi.Parameter(
        'token', in_=openapi.IN_QUERY, description='Description', type=openapi.TYPE_STRING)

    @swagger_auto_schema(manual_parameters=[token_param_config])
    def get(self, request):
        token = request.GET.get('token')
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms='HS256')
            user = User.objects.get(id=payload['user_id'])
            if not user.is_verified:
                user.is_verified = True
                user.save()
            return Response({'email': 'Successfully activated'}, status=status.HTTP_200_OK)
        except jwt.ExpiredSignatureError as identifier:
            return Response({'error': 'Activation Expired'}, status=status.HTTP_400_BAD_REQUEST)
        except jwt.exceptions.DecodeError as identifier:
            return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)


class LoginAPIView(generics.GenericAPIView):
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class ProfileUpdateView(generics.GenericAPIView):
    serializer_class = ProfileInvestorSerializer
    permission_classes = (IsAuthenticated,)
    parser_classes = [MultiPartParser, FormParser]

    def get_object(self, pk):
        try:
            return User.objects.get(id=pk)
        except User.DoesNotExist:
            raise Http404

    def put(self, request, format=None):
        snippet = self.get_object(self.request.user.id)
        indata = {
            'address': request.data.get('address'),
            'linkedin': request.data.get('linkedin'),
            'phone': request.data.get('phone')
        }
        ini_serial = self.serializer_class(data=indata)
        ini_serial.is_valid(raise_exception=True)
        ini_serial.save()

        return Response(ini_serial.data, status=status.HTTP_200_OK)


class RequestPasswordResetEmail(generics.GenericAPIView):
    serializer_class = ResetPasswordEmailRequestSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)

        email = request.data.get('email', '')
        # print(email)
        # print('trueee')

        if User.objects.filter(email=email).exists():
            user = User.objects.get(email=email)
            uidb64 = urlsafe_base64_encode(smart_bytes(user.id))
            token = PasswordResetTokenGenerator().make_token(user)
            if request.data.get('callbackUrl'):
                current_site = request.data.get('callbackUrl')
            else:
                current_site = get_current_site(request=request).domain
            relativeLink = reverse(
                'password-reset-confirm', kwargs={'uidb64': uidb64, 'token': token})

            redirect_url = request.data.get('redirect_url', '')
            absurl = 'https://'+current_site + relativeLink
            print("absurl")
            print(absurl)
            email_body = 'Hello, \n Use link below to reset your password  \n' + \
                absurl+"?redirect_url="+redirect_url
            print("redirect url")
            print(absurl+"?redirect_url="+redirect_url)
            data = {'email_body': email_body, 'to_email': user.email,
                    'email_subject': 'Reset your passsword'}
            sender(data['email_subject'], data['email_body'],
               'no-reply@yieldroom.ng', [data['to_email']])
            #Util.send_email(data)
        return Response({'success': 'We have sent you a link to reset your password'}, status=status.HTTP_200_OK)


class PasswordTokenCheckAPI(generics.GenericAPIView):
    serializer_class = SetNewPasswordSerializer

    def get(self, request, uidb64, token):

        redirect_url = request.GET.get('redirect_url')

        try:
            id = smart_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(id=id)

            if not PasswordResetTokenGenerator().check_token(user, token):
                if len(redirect_url) > 3:
                    return CustomRedirect(redirect_url+'?token_valid=False')
                else:
                    return CustomRedirect(os.environ.get('FRONTEND_URL', '')+'?token_valid=False')

            if redirect_url and len(redirect_url) > 3:
                return CustomRedirect(redirect_url+'?token_valid=True&message=Credentials Valid&uidb64='+uidb64+'&token='+token)
            else:
                return CustomRedirect(os.environ.get('FRONTEND_URL', '')+'?token_valid=False')

        except DjangoUnicodeDecodeError as identifier:
            try:
                if not PasswordResetTokenGenerator().check_token(user):
                    return CustomRedirect(redirect_url+'?token_valid=False')

            except UnboundLocalError as e:
                return Response({'error': 'Token is not valid, please request a new one'}, status=status.HTTP_400_BAD_REQUEST)


class SetNewPasswordAPIView(generics.GenericAPIView):
    serializer_class = SetNewPasswordSerializer

    def patch(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({'success': True, 'message': 'Password reset success'}, status=status.HTTP_200_OK)


class LogoutAPIView(generics.GenericAPIView):
    serializer_class = LogoutSerializer

    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(status=status.HTTP_204_NO_CONTENT)


class LoadUserView(APIView):
    def get(self, request, format=None):
        try:
            user = request.user
            user = UserSerializer(user)

            return Response(
                {'user': user.data},
                status=status.HTTP_200_OK
            )

        except:
            return Response(
                {'error': 'Something went wrong when trying to load user'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class LoginView2(APIView):
    def post(self, request):
        email = request.data['email']
        password = request.data['password']

        user = User.objects.filter(email=email).first()

        if user is None:
            raise AuthenticationFailed('User not found!')

        if not user.check_password(password):
            raise AuthenticationFailed('Incorrect password')

        payload = {
            'id': user.id,
            'exp': datetime.datetime.now() + datetime.timedelta(minutes=60),
            'iat': datetime.datetime.now(),
        }

        token = jwt.encode(payload, 'secret',
                           algorithm='HS256').decode('utf-8')

        '''response = Response({
            "jwt": token
        }) 
        '''
        response = Response()

        # Send only cookie
        response.set_cookie(key='jwt', value=token, httponly=True)
        response.data = {
            'jwt': token
        }

        return response


class LoginView3(APIView):
    def post(self, request):
        email = request.data['email']
        password = request.data['password']

        user = User.objects.filter(email=email).first()

        if user is None:
            raise AuthenticationFailed('User not found!')

        if not user.check_password(password):
            raise AuthenticationFailed('Incorrect password')

        payload = {
            'id': user.id,
            'exp': datetime.datetime.now() + datetime.timedelta(minutes=60),
            'iat': datetime.datetime.now(),
        }

        token = jwt.encode(payload, 'secret',
                           algorithm='HS256').decode('utf-8')

        '''response = Response({
            "jwt": token
        }) 
        '''
        response = Response()

        # Send only cookie
        response.set_cookie(key='jwt', value=token, httponly=True)
        response.data = {
            'jwt': token
        }

        return response


class ApproveUserAPIView(generics.GenericAPIView):
    serializer_class = ApproveUserSerializer
    queryset = User.objects.all()
    permission_classes = (IsAuthenticated, IsAdminUser)
    filter_backends = [DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter]

    def get_object(self, pk):
        try:
            return User.objects.get(pk=pk)
        except User.DoesNotExist:
            raise Http404

    def patch(self, request, id, format=None):
        snippet = self.get_object(id)
        isdata = {'is_approved': request.data.get('is_approved')}
        serializer = ApproveUserSerializer(snippet, data=isdata)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifiedUserAPIView(generics.GenericAPIView):
    serializer_class = VerifiedUserSerializer
    queryset = User.objects.all()
    permission_classes = (IsAuthenticated, IsAdminUser)
    filter_backends = [DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter]

    def get_object(self, pk):
        try:
            return User.objects.get(pk=pk)
        except User.DoesNotExist:
            raise Http404

    def patch(self, request, id, format=None):
        snippet = self.get_object(id)
        isdata = {'is_verified': request.data.get('is_verified')}
        serializer = VerifiedUserSerializer(snippet, data=isdata)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ExportUserAPIView(generics.GenericAPIView):
    serializer_class = RegisterSerializer
    queryset = User.objects.all()
    permission_classes = (IsAuthenticated, IsAdminUser)

    def get_serializer(self, queryset, many=True):
        return self.serializer_class(
            queryset,
            many=many,
        )

    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="export.csv"'

        serializer = self.get_serializer(
            User.objects.all(),
            many=True
        )
        header = RegisterSerializer.Meta.fields

        writer = csv.DictWriter(response, fieldnames=header)
        writer.writeheader()
        for row in serializer.data:
            writer.writerow(row)

        return response


class ExportUsersPDFAPIView(generics.GenericAPIView):
    serializer_class = RegisterSerializer
    permission_classes = (IsAuthenticated, IsAdminUser,)

    def get(self, request):
        user_db = User.objects.values()
        print(user_db)
        sales = [
            {"item": "Keyboard", "amount": "$120,00"},
            {"item": "Mouse", "amount": "$10,00"},
            {"item": "House", "amount": "$1 000 000,00"},
        ]
        pdf = FPDF('P', 'mm', 'A4')
        pdf.add_page()
        pdf.set_font('courier', 'B', 16)
        pdf.cell(40, 10, 'This is what you have sold this month so far:', 0, 1)
        pdf.cell(40, 10, '', 0, 1)
        pdf.set_font('courier', '', 12)
        pdf.cell(200, 8, f"{'Item'.ljust(30)} {'Amount'.rjust(20)}", 0, 1)
        pdf.line(10, 30, 150, 30)
        pdf.line(10, 38, 150, 38)
        for line in user_db:
            pdf.cell(
                200, 8, f"{line['firstname'].ljust(30)} {line['updated_at'].rjust(20)}", 0, 1)
        pdf.output('report.pdf', 'F')
        return FileResponse(open('report.pdf', 'rb'), as_attachment=False, content_type='application/pdf')

    '''
    def get(self, request, *args, **kwargs):
        try:
            user_db = User.objects.get(id=4)
            #user = RegisterSerializer(user_db)
            print(user_db)
        except:
            return HttpResponse("505 Not Found")
        data = {
            'firstname': user_db.firstname,
            'lastname': user_db.lastname,
        }

        pdf = render_to_pdf('auth/users.html', data)
        # return HttpResponse(pdf, content_type='applicatiion/pdf')

        # force download
        if pdf:
            response = HttpResponse(pdf, content_type='applicatiion/pdf')
            #filename = "Users_%s.pdf" %(data['order_id'])
            filename = "Users.pdf"
            content = "inline; filename='%s'" % (filename)
            content = "attachment; filename=%s" % (filename)
            response['Content-Disposition'] = content
            return response
        return Http404
        '''

    '''
    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename=Users' + \
            str(datetime.date.now())+'.pdf'
        response['Content-Transfer-Encoding'] = 'binary'

        html_string = render_to_string(
            'auth/users.html', {'auth': [], 'total': 0}
        )
        html = HTML(string=html_string)

        result = html.write_pdf()

        # Preview PDF file in memory
        with tempfile.NamedTemporaryFile(delete=True) as output:
            output.write(result)
            output.flush()
            output = open(output.name, 'rb')
            response.write(output.read())

        return response
        '''
