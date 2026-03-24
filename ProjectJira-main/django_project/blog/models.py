from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.urls import reverse


class Project(models.Model):
    WORKLOAD_UNIT_CHOICES = [
        ('sp', 'Story Points'),
        ('md', 'Man-Days'),
        ('mh', 'Man-Hours'),
    ]
    code            = models.CharField(max_length=20, unique=True)
    name            = models.CharField(max_length=100)
    description     = models.TextField(blank=True)
    start_date      = models.DateField()
    end_date        = models.DateField()
    sprint_duration = models.PositiveIntegerField(default=14)
    workload_unit   = models.CharField(max_length=2, choices=WORKLOAD_UNIT_CHOICES, default='sp')
    capacity        = models.PositiveIntegerField(null=True, blank=True)
    created_by      = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_projects')

    def __str__(self):
        return f"{self.code} - {self.name}"

    def get_absolute_url(self):
        return reverse('project-detail', kwargs={'pk': self.pk})

    def next_ticket_number(self):
        last = self.tickets.order_by('-number').first()
        return (last.number + 1) if last else 1


class ProjectMembership(models.Model):
    ROLE_CHOICES = [
        ('admin',       'Admin'),
        ('contributor', 'Contributor'),
        ('readonly',    'Read-Only'),
    ]
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='memberships')
    user    = models.ForeignKey(User, on_delete=models.CASCADE, related_name='memberships')
    role    = models.CharField(max_length=20, choices=ROLE_CHOICES, default='contributor')

    class Meta:
        unique_together = ('project', 'user')

    def __str__(self):
        return f"{self.user.username} — {self.project.code} ({self.role})"


class Sprint(models.Model):
    STATUS_CHOICES = [
        ('planned',   'Planned'),
        ('active',    'Active'),
        ('completed', 'Completed'),
    ]
    project         = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='sprints')
    name            = models.CharField(max_length=100)
    goal            = models.TextField(blank=True)
    start_date      = models.DateField()
    end_date        = models.DateField()
    status          = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planned')
    global_capacity = models.PositiveIntegerField(null=True, blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.project.code} — {self.name}"

    def get_absolute_url(self):
        return reverse('project-detail', kwargs={'pk': self.project.pk})

    def save(self, *args, **kwargs):
        if self.status == 'active':
            Sprint.objects.filter(
                project=self.project, status='active'
            ).exclude(pk=self.pk).update(status='completed')
        super().save(*args, **kwargs)


class Epic(models.Model):
    STATUS_CHOICES = [
        ('active',    'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    PRIORITY_CHOICES = [
        ('low',    'Low'),
        ('medium', 'Medium'),
        ('high',   'High'),
    ]
    project     = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='epics')
    title       = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status      = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    priority    = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    color       = models.CharField(max_length=7, default='#6366f1')
    start_date  = models.DateField(null=True, blank=True)
    end_date    = models.DateField(null=True, blank=True)
    created_by  = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_epics')

    def __str__(self):
        return f"[{self.project.code}] {self.title}"

    def get_absolute_url(self):
        return reverse('project-detail', kwargs={'pk': self.project.pk})


class Ticket(models.Model):
    TYPE_CHOICES = [
        ('story', 'User Story'),
        ('task',  'Task'),
        ('bug',   'Bug'),
    ]
    STATUS_CHOICES = [
        ('new',       'New'),
        ('active',    'Active'),
        ('closed',    'Closed'),
        ('cancelled', 'Cancelled'),
    ]
    PRIORITY_CHOICES = [
        ('low',    'Low'),
        ('medium', 'Medium'),
        ('high',   'High'),
    ]

    project     = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tickets')
    number      = models.PositiveIntegerField(editable=False, default=0)
    ticket_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='story')
    epic        = models.ForeignKey(Epic, on_delete=models.SET_NULL, null=True, blank=True, related_name='tickets')

    parent_ticket = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='subtasks',
        verbose_name="Parent User Story",
        limit_choices_to={'ticket_type': 'story'}
    )

    sprint      = models.ForeignKey(Sprint, on_delete=models.SET_NULL, null=True, blank=True, related_name='tickets')
    title       = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status      = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')

    priority    = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')

    reporter = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='reported_tickets',
        verbose_name="Reporter"
    )

    # Requester: manually selected in the form
    requester = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='requested_tickets',
        verbose_name="Requester"
    )

    assigned = models.ForeignKey(

        User, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='assigned_tickets',
        verbose_name="Assignee"
    )

    start_date = models.DateField(null=True, blank=True)
    end_date   = models.DateField(null=True, blank=True)

    workload_initial   = models.PositiveIntegerField(null=True, blank=True, verbose_name="Initial Workload")
    workload_remaining = models.PositiveIntegerField(null=True, blank=True, verbose_name="Remaining Workload")
    workload_done      = models.PositiveIntegerField(default=0, verbose_name="Workload Done")

    backlog_order = models.PositiveIntegerField(default=0)
    date_created  = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('project', 'number')
        ordering = ['backlog_order', '-date_created']

    def save(self, *args, **kwargs):
        if not self.pk:
            self.number = self.project.next_ticket_number()
            if self.workload_initial and self.workload_remaining is None:
                self.workload_remaining = self.workload_initial
        super().save(*args, **kwargs)

    @property
    def human_id(self):
        return f"{self.project.code}-{self.number}"

    def __str__(self):
        return f"{self.human_id} — {self.title}"

    def get_absolute_url(self):
        return reverse('ticket-detail', kwargs={'pk': self.pk})