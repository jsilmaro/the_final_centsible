from rest_framework import serializers
from accounts.models import CustomUser
from .models import Budget, Report
from datetime import datetime


class RegisterSerializer(serializers.ModelSerializer):
    name = serializers.CharField(write_only=True)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = CustomUser
        fields = ("name", "email", "password")

    def create(self, validated_data):
        name = validated_data.pop("name")
        email = validated_data["email"]
        password = validated_data["password"]

        user = CustomUser.objects.create_user(
            email=email,
            password=password,
            name=name
        )
        return user

    def to_representation(self, instance):
        return {
            "id": instance.id,  # Frontend expects an ID field
            "name": instance.name,
            "email": instance.email,
            "avatar": instance.avatar.url if instance.avatar else None,  # Ensuring compatibility with frontend data handling
            "preferences": instance.preferences  # Providing structured preferences data
        }

from rest_framework import serializers
from .models import Transaction

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['id', 'amount', 'type', 'category', 'description', 'date', 'created_at']
        read_only_fields = ['created_at']

    def validate(self, data):
        if data['type'] == 'expense' and data['category'] in dict(Transaction.INCOME_CATEGORIES):
            raise serializers.ValidationError("Invalid category for expense type")
        elif data['type'] == 'income' and data['category'] in dict(Transaction.EXPENSE_CATEGORIES):
            raise serializers.ValidationError("Invalid category for income type")
        return data

class BudgetSerializer(serializers.ModelSerializer):
    spent = serializers.SerializerMethodField()
    
    class Meta:
        model = Budget
        fields = ['id', 'category', 'amount', 'period', 'start_date', 'end_date', 'created_at', 'spent']
        read_only_fields = ['created_at', 'spent']
        
    def get_spent(self, obj):
        from .models import Transaction
        transactions = Transaction.objects.filter(
            user=obj.user,
            type='expense',
            category=obj.category,
            date__gte=obj.start_date,
            date__lte=obj.end_date
        )
        return sum(t.amount for t in transactions)

    def validate(self, data):
        if float(data.get('amount', 0)) <= 0:
            raise serializers.ValidationError("Budget amount must be greater than 0")
        
        if not data.get('start_date'):
            data['start_date'] = datetime.date.today()
        
        if not data.get('end_date'):
            # Set end date to last day of current month for monthly budgets
            if data.get('period') == 'monthly':
                today = datetime.date.today()
                data['end_date'] = today.replace(day=1) + datetime.timedelta(days=32)
                data['end_date'] = data['end_date'].replace(day=1) - datetime.timedelta(days=1)
            else:
                data['end_date'] = data['start_date'] + datetime.timedelta(days=365)
                
        return data
class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = ['id', 'report_type', 'start_date', 'end_date', 'created_at', 'data']
        read_only_fields = ['created_at', 'data']

    def validate(self, data):
        if data['start_date'] > data['end_date']:
            raise serializers.ValidationError("End date must be after start date")
        return data
