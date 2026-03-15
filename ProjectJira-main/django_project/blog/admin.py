from django.contrib import admin
from .models import Project, ProjectMembership, Sprint, Epic, Ticket

admin.site.register(Project)
admin.site.register(ProjectMembership)
admin.site.register(Sprint)
admin.site.register(Epic)
admin.site.register(Ticket)
