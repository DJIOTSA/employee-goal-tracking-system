from django.urls import path
# Transaction views
from .views import (
    TransactionList, 
    TransactionDetails, 
    TransactionDelete,
    CompletionBonusWithdrawalView
)

urlpatterns = [
    # Transaction
    path("transaction/list/", TransactionList.as_view(), name="list-of-all-transaction"),
    path("transaction/<int:pk>/detail/", TransactionDetails.as_view(), name="transaction-detail"),
    path("transaction/<int:pk>/delete/", TransactionDelete.as_view(), name="delete Transaction"),
    path("withdrawal/bonus/", CompletionBonusWithdrawalView.as_view(), name ="withdraw-completion-bonus"),

]
