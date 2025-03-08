from rest_framework import serializers
from .models import Court, Reservation

class CourtSerializer(serializers.ModelSerializer):
    class Meta:
        model = Court
        fields = ['id', 'name', 'number', 'hourly_rate', 'is_active']

class ReservationSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    court_name = serializers.CharField(source='court.name', read_only=True)

    class Meta:
        model = Reservation
        fields = ['id', 'user', 'court', 'court_name', 'start_time', 'end_time', 'status']
        read_only_fields = ['status']

    def validate(self, data):
        # Check if end time is after start time
        if data['end_time'] <= data['start_time']:
            raise serializers.ValidationError("End time must be after start time")

        # Check for overlapping reservations
        overlapping = Reservation.objects.filter(
            court=data['court'],
            start_time__lt=data['end_time'],
            end_time__gt=data['start_time']
        )
        
        if self.instance:
            overlapping = overlapping.exclude(pk=self.instance.pk)
        
        if overlapping.exists():
            raise serializers.ValidationError("This time slot is already booked")
            
        return data
