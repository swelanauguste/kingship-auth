from django.core.management.base import BaseCommand
from accounts.models import User, Role

class Command(BaseCommand):
    help = "Seed the database with fake users, roles, and departments"

    def handle(self, *args, **kwargs):
        # Create roles
        role_names = ["admin", "engineer", "reviewer", "clerk"]
        role_objs = {}
        for r in role_names:
            role, created = Role.objects.get_or_create(name=r)
            role_objs[r] = role
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created role: {r}"))
        
        # Create users
        users = [
            ("alice", "alice@example.com", ["admin"], "IT"),
            ("bob", "bob@example.com", ["engineer"], "IT"),
            ("charlie", "charlie@example.com", ["reviewer"], "Finance"),
            ("diana", "diana@example.com", ["clerk", "reviewer"], "HR"),
            ("eric", "eric@example.com", ["engineer", "reviewer"], "Operations"),
        ]

        for username, email, roles, department in users:
            user, created = User.objects.get_or_create(username=username, defaults={
                "email": email,
                "department": department,
            })
            if created:
                user.set_password("Pass1234!")  # default dev password
                user.save()
                user.roles.set([role_objs[r] for r in roles])
                self.stdout.write(self.style.SUCCESS(f"Created user: {username} with roles {roles}"))
            else:
                self.stdout.write(self.style.WARNING(f"User {username} already exists"))
