from django.conf import settings   # ใช้ settings.AUTH_USER_MODEL เพื่ออ้างถึง User
from django.db import models       # import models ของ Django


class Team(models.Model):
    # ชื่อทีม เช่น TEAMSUFFER, DEMON, etc.
    name = models.CharField(max_length=100)

    # รายละเอียดทีม (จะเว้นว่างก็ได้)
    description = models.TextField(blank=True)

    # โลโก้ทีม (อัปโหลดไฟล์)
    logo = models.ImageField(upload_to='teams/logos/', blank=True, null=True)
    # ลิงก์โลโก้ทีม (อาจเก็บ URL จาก storage หรือ external) - kept for backward compatibility
    logo_url = models.URLField(blank=True)
    # Optional join code allowing players to join via a passcode
    join_code = models.CharField(max_length=32, blank=True, null=True)

    # คนที่สร้างทีม (หัวหน้าทีมเริ่มต้น) FK ไปยัง User
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,        # ใช้ User ของ Django
        on_delete=models.CASCADE,        # ถ้าลบ user นี้ ทีมที่สร้างโดย user นี้จะถูกลบด้วย
        related_name='teams_created'     # ใช้เข้าถึงจาก user.teams_created
    )

    # สถานะของทีม (active = ใช้งานปกติ, disbanded = ยุบทีม, pending = รออนุมัติ)
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('disbanded', 'Disbanded'),
        ('pending', 'Pending'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
    )

    # Game interest / Team's main game
    game = models.ForeignKey(
        'tournaments.Game',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='teams'
    )


    # เวลาเริ่มสร้าง / แก้ไขล่าสุด
    created_at = models.DateTimeField(auto_now_add=True)  # เซ็ตตอนสร้างครั้งแรก
    updated_at = models.DateTimeField(auto_now=True)      # อัปเดตทุกครั้งที่ save()

    def __str__(self):
        # เวลา print(team) ให้แสดงชื่อทีม + ชื่อคนสร้าง
        return f"{self.name} (created by {self.created_by.username})"


class TeamMember(models.Model):
    # ทีมที่สังกัด
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='members'  # team.members.all() จะได้สมาชิกทุกคนในทีม
    )

    # user คนนี้คือใคร
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='team_memberships'  # user.team_memberships.all()
    )

    # บทบาทในทีม: หัวหน้าทีม / สมาชิก
    ROLE_CHOICES = [
        ('leader', 'Leader'),
        ('member', 'Member'),
    ]
    role_in_team = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default='member',
    )

    # สถานะการเข้าร่วม: pending = รอหัวหน้ากดรับ, accepted = อยู่ทีมแล้ว, rejected = ถูกปฏิเสธ
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending',
    )

    # วันที่เข้าทีม
    joined_at = models.DateTimeField(auto_now_add=True)

    # วันที่ออกจากทีม (ยังอยู่ทีมให้เป็น null)
    left_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        # บังคับว่า 1 user อยู่ทีมเดียวกันซ้ำ 2 แถวไม่ได้
        unique_together = ('team', 'user')

    def __str__(self):
        return f"{self.user.username} in {self.team.name} ({self.role_in_team})"
