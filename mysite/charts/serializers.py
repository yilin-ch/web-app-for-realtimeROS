from rest_framework import serializers

class TopicSerializer(serializers.Serializer):
    topic = serializers.CharField(max_length=200)
    message = serializers.CharField(max_length=200)
