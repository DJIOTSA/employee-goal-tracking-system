from rest_framework import serializers
from .models import Transaction

"""
\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
    TRANSACTION
"""
# transaction
class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = "__all__"


class WithdrawalSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    enterprise_name = serializers.CharField(max_length=255)


class TransactionListSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="transaction-detail", lookup_field="pk")
    class Meta:
        model = Transaction
        fields = "__all__"

class TransactionListPostSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    enterprise_name = serializers.CharField(max_length=255)

class TransactionDeleteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ["is_deleted", ]
