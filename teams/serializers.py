from rest_framework import serializers
from .models import Team, TeamMember


class TeamSerializer(serializers.ModelSerializer):
    # อ่านอย่างเดียว แสดง username ของคนสร้างทีม
    created_by_username = serializers.ReadOnlyField(source='created_by.username')

    class Meta:
        model = Team
        fields = [
            'id',
            'name',
            'description',
            'logo_url',
            'status',
            'created_by',
            'created_by_username',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_by', 'created_by_username', 'created_at', 'updated_at']


class TeamMemberSerializer(serializers.ModelSerializer):
    user_username = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = TeamMember
        fields = [
            'id',
            'team',
            'user',
            'user_username',
            'role_in_team',
            'status',
            'joined_at',
            'left_at',
        ]
        read_only_fields = ['joined_at', 'left_at']
