from .serializers import  (
    TransactionSerializer, 
    WithdrawalSerializer, 
    TransactionListSerializer, 
    TransactionListPostSerializer,
    TransactionDeleteSerializer,

)
from .models import (
    Transaction, 
    check_user_transaction_permission,
    withdrawal_request,
    user_transaction_permission,
    USER_HAS_NO_BONUS,
    INSUFFICIENT_BALANCE,

    
)
from rest_framework import generics, status
from rest_framework.views import Response, APIView
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from EGT.permissions import(
    checkAdministratorEmployeeGroupMixin,
    checkAdministratorGroupMixin,
    checkEmployeeAdminGroupMixin,
    PermissionDenied 
)
from EGT.models import (
    Enterprise,
    user_belong_to_enterprise,
    check_user_enterprise_status,
    Status,

)
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
# Create your views here.

"""
    \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
    Transaction VIEW SECTION
"""    

# list Transaction
class TransactionList(APIView):
    """ 
    This return the list of user transactions under the given enterprise.
    
    Note: only the administrator and the employee get access permission
          and administrator can see even deleted transactions but the user
          can not and only the user(that made the transaction) have the 
          permission to delete the transaction.
    """
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated,]
    queryset = Transaction.objects.all()
    serializer_class = TransactionListPostSerializer
    lookup_field ="pk"

    
    def post(self, request, format=None):
        # check user group permissions
        checkAdministratorEmployeeGroupMixin(self)

        serializer = self.serializer_class(data = request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status.HTTP_400_BAD_REQUEST
            )
        
        # GET data
        user_id = serializer.validated_data["user_id"]
        enterprise_name = serializer.validated_data["enterprise_name"].upper()

        try:
            user = get_user_model().objects.get(id = user_id)
            enterprise =Enterprise.objects.get(name = enterprise_name)
        except (get_user_model().DoesNotExist, Transaction.DoesNotExist, Enterprise.DoesNotExist) as e:
            return Response(
                {
                    "detail": _(f"An error occur: {e}"),
                    "status": _("FAILED")
                },
                status.HTTP_404_NOT_FOUND
            )
        EMPLOYEE = _("EMPLOYEE")
        # check requester permission on the transaction
        if not user_belong_to_enterprise(request.user, enterprise):
            raise PermissionDenied
        if check_user_enterprise_status(request.user, enterprise) not in [Status.ACTIVE]:
            raise PermissionDenied
        
        # check user permission on the transaction
        if not user_belong_to_enterprise(user, enterprise) or check_user_enterprise_status(user, enterprise) not in [Status.ACTIVE]:
            return Response(
                {
                    "detail":_("Invalid user_id"),
                    "status":_("FAILED")
                },
                status.HTTP_400_BAD_REQUEST
            )
        
        
        # get transaction list
        if request.user.role != EMPLOYEE:
            queryset = Transaction.objects.filter(
                user = user,
                enterprise = enterprise,
            )
        else:
            queryset = Transaction.objects.filter(
                user = user,
                enterprise = enterprise,
                is_deleted = False
            )
            queryset = [t for t in queryset if user_transaction_permission(user, enterprise, t)]


        

        serialized_data = TransactionListSerializer(queryset, context={"request": request}, many =True)

        return Response(
            {
                "detail": _("successfully get all the list of transactions"),
                "status": _('SUCCESS'),
                "transactions": serialized_data.data
            },
            status.HTTP_200_OK
        )

# detail Transaction
class TransactionDetails(generics.RetrieveAPIView):
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated,]
    queryset = Transaction.objects.all()
    serializer_class = TransactionListSerializer
    lookup_field ="pk"


    def get( self, request, *args, **kwargs):
        #  check group permission
        checkAdministratorEmployeeGroupMixin(self)

        # get the transaction objects
        obj = self.get_object()
        
        enterprise = obj.get_transaction_enterprise()
        
        # check user permission over the transaction instance
        check_user_transaction_permission(request.user, enterprise, obj)

        if obj.is_deleted:
            return Response(
                {
                    "detail":_("Not found."),
                },
                status.HTTP_404_NOT_FOUND
            )

        return super().get(request, *args, **kwargs)



# delete Transaction
class TransactionDelete(generics.UpdateAPIView):
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated,]
    queryset = Transaction.objects.all()
    serializer_class = TransactionDeleteSerializer
    lookup_field = "pk"

    
    def perform_update(self, serializer):
        # check user group
        checkAdministratorEmployeeGroupMixin(self)
        obj  =self.get_object()
        enterprise = obj.get_transaction_enterprise()
        # check user permission over the transaction
        check_user_transaction_permission(user=self.request.user, enterprise=enterprise, transaction=obj)
        # check if the user is the one who performs the transaction
        if self.request.user != obj.get_transaction_user():
            raise PermissionDenied
        
        if obj.get_transaction_is_deleted():
            print(obj.get_transaction_is_deleted())
            return Response(
                {
                    "detail":_("Not found."),
                },
                status.HTTP_404_NOT_FOUND
            )

        # is_deleted = serializer.validated_data["is_deleted"]

        serializer.save(is_deleted = True)
    
class CompletionBonusWithdrawalView(APIView):
    """ This perform a completion bonus withdrawal operation """
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated,]
    serializer_class = WithdrawalSerializer

    def post(self, request, format=None):
        #  check user group permission
        checkAdministratorGroupMixin(self)

        serializer = self.serializer_class(data = request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)
        
        user_id = serializer.validated_data["user_id"]
        enterprise_name = serializer.validated_data["enterprise_name"].upper()

        try:
            user = get_user_model().objects.get(id = user_id)
            enterprise = Enterprise.objects.get(name= enterprise_name)
        except (get_user_model().DoesNotExist, Enterprise.DoesNotExist) as e:
            return Response(
                {
                    "detail": _(f"An error occur: {e}"),
                    "status": _("FAILED")
                },
                status.HTTP_400_BAD_REQUEST
            )
        
        # perform the the withdrawal
        state = withdrawal_request(user, enterprise)

        if state == True:
            return Response(
                {
                    "status": _("SUCCESS"),
                    "detail": _("The withdrawal operation was successful!")
                },
                status.HTTP_200_OK
            )
        elif state == False:
            return Response(
                {
                    "detail": _("WITHDRAWAL OPERATION REJECTED, RETRY LATER!"),
                    "status": _("FAILED")
                }, 
                status.HTTP_200_OK
            )
        elif state == USER_HAS_NO_BONUS:
            return Response(
                {
                    "detail": state,
                    "status": _("FAILED")
                }, 
                status.HTTP_200_OK
            )
        elif state == INSUFFICIENT_BALANCE:
            return Response(
                {
                    "detail": state,
                    "status": _("FAILED")
                }, 
                status.HTTP_200_OK
            )
        else:
            return Response(
                {
                    "detail": state,
                    "status": _("FAILED")
                }, 
                status.HTTP_400_BAD_REQUEST
            )


