# ══════════════════════════════════════════════════════════════
# apps/notifications/message_serializers.py
# ══════════════════════════════════════════════════════════════

from rest_framework import serializers
from .models import Message
 
 
class MessageSerializer(serializers.ModelSerializer):
    sender_name    = serializers.CharField(source='sender.full_name', read_only=True)
    recipient_name = serializers.CharField(source='recipient.full_name', read_only=True)
 
    class Meta:
        model = Message
        fields = [
            'id', 'sender', 'sender_name', 'recipient', 'recipient_name',
            'appointment', 'content', 'is_read', 'read_at', 'sent_at',
        ]
        read_only_fields = ['id', 'sender', 'is_read', 'read_at', 'sent_at']
 
    def create(self, validated_data):
        validated_data['sender'] = self.context['request'].user
        return super().create(validated_data)

