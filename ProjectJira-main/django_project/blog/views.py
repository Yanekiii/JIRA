from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.contrib.auth.models import User
from .models import Ticket, Project, Sprint, Epic, ProjectMembership
from django.db.models import Case, When, Value, IntegerField
from datetime import timedelta


# ── Helper ────────────────────────────────────────────────────────────────────
def get_user_role(user, project):
    if user.is_staff:
        return 'admin'
    membership = ProjectMembership.objects.filter(user=user, project=project).first()
    return membership.role if membership else None


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser


# ── Misc ──────────────────────────────────────────────────────────────────────
def about(request):
    return render(request, 'blog/about.html', {'title': 'About'})

def home(request):
    return render(request, 'blog/home.html', {'tickets': Ticket.objects.all()})

def kanban_board(request):
    return render(request, 'blog/kanban.html', {
        'columns': [
            ('new',       'New',       '#6c757d', Ticket.objects.filter(status='new')),
            ('active',    'Active',    '#198754', Ticket.objects.filter(status='active')),
            ('closed',    'Closed',    '#212529', Ticket.objects.filter(status='closed')),
            ('cancelled', 'Cancelled', '#dc3545', Ticket.objects.filter(status='cancelled')),
        ]
    })


# ── Tickets ───────────────────────────────────────────────────────────────────
class TicketListView(ListView):
    model = Ticket
    template_name = 'blog/home.html'
    context_object_name = 'tickets'
    ordering = ['backlog_order', '-date_created']


class TicketDetailView(LoginRequiredMixin, DetailView):
    model = Ticket
    template_name = 'blog/post_detail.html'


class TicketCreateView(LoginRequiredMixin, CreateView):
    model = Ticket
    fields = [
        'ticket_type', 'title', 'description',
        'project', 'epic', 'parent_ticket',
        'sprint', 'priority',          
        'demandeur', 'assignee',
        'start_date', 'end_date',
        'workload_initial',
    ]
    template_name = 'blog/post_form.html'

    def form_valid(self, form):
        project_pk = self.kwargs.get('project_pk')

        if project_pk:
            project = get_object_or_404(Project, pk=project_pk)
            form.instance.project = project
        else:
            project = form.cleaned_data.get('project')

        role = get_user_role(self.request.user, project)
        if role not in ['admin', 'contributor']:
            messages.error(self.request, "You don't have permission to create tickets in this project.")
            return redirect('project-detail', pk=project.pk)

        form.instance.reporter = self.request.user
        return super().form_valid(form)

    def get_initial(self):
        initial = super().get_initial()
        project_pk = self.kwargs.get('project_pk')
        if project_pk:
            initial['project'] = project_pk
        initial['demandeur'] = self.request.user
        return initial


class TicketUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Ticket
    fields = [
        'ticket_type', 'title', 'description',
        'project', 'epic', 'parent_ticket',
        'sprint', 'priority', 'status',   
        'demandeur', 'assignee',
        'start_date', 'end_date',
        'workload_initial', 'workload_remaining', 'workload_done',
    ]
    template_name = 'blog/post_form.html'

    def test_func(self):
        ticket = self.get_object()
        role = get_user_role(self.request.user, ticket.project)
        return role in ['admin', 'contributor']


class TicketDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Ticket
    template_name = 'blog/post_confirm_delete.html'
    success_url = '/'

    def test_func(self):
        ticket = self.get_object()
        role = get_user_role(self.request.user, ticket.project)
        return role == 'admin' or self.request.user == ticket.reporter


def ticket_move(request, pk):
    if request.method == 'POST':
        ticket = get_object_or_404(Ticket, pk=pk)
        role = get_user_role(request.user, ticket.project)
        if role not in ['admin', 'contributor']:
            return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
        new_status = request.POST.get('status')
        if new_status in dict(Ticket.STATUS_CHOICES):
            ticket.status = new_status
            ticket.save()
            return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)


def ticket_priority_up(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    above = Ticket.objects.filter(
        project=ticket.project, sprint__isnull=True,
        backlog_order__lt=ticket.backlog_order
    ).order_by('-backlog_order').first()
    if above:
        ticket.backlog_order, above.backlog_order = above.backlog_order, ticket.backlog_order
        ticket.save()
        above.save()
    return redirect('product-backlog', pk=ticket.project.pk)


def ticket_priority_down(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    below = Ticket.objects.filter(
        project=ticket.project, sprint__isnull=True,
        backlog_order__gt=ticket.backlog_order
    ).order_by('backlog_order').first()
    if below:
        ticket.backlog_order, below.backlog_order = below.backlog_order, ticket.backlog_order
        ticket.save()
        below.save()
    return redirect('product-backlog', pk=ticket.project.pk)


def backlog_reorder(request, project_id):
    import json
    project = get_object_or_404(Project, pk=project_id)
    try:
        data = json.loads(request.body)
        ids = data.get('order', [])
        for position, ticket_id in enumerate(ids):
            Ticket.objects.filter(id=ticket_id, project=project).update(backlog_order=position)
        return JsonResponse({'ok': True})
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=400)


# ── Projects ──────────────────────────────────────────────────────────────────
class ProjectListView(LoginRequiredMixin, ListView):
    model = Project
    template_name = 'blog/projects.html'
    context_object_name = 'projects'

    def get_queryset(self):
        if self.request.user.is_staff:
            return Project.objects.all().order_by('-start_date')
        return Project.objects.filter(
            memberships__user=self.request.user
        ).order_by('-start_date')


class ProjectDetailView(LoginRequiredMixin, DetailView):
    model = Project
    template_name = 'blog/project_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.get_object()

        sprints = project.sprints.prefetch_related('tickets').annotate(
            active_first=Case(
                When(status='active', then=Value(0)),
                default=Value(1),
                output_field=IntegerField(),
            )
        ).order_by('active_first', '-created_at')

        context['sprints'] = sprints
        context['epics'] = project.epics.all()
        context['members'] = project.memberships.select_related('user')
        context['active_sprint'] = sprints.filter(status='active').first()
        context['user_role'] = get_user_role(self.request.user, project)
        return context


class ProjectCreateView(AdminRequiredMixin, CreateView):
    model = Project
    fields = ['code', 'name', 'description', 'start_date', 'end_date',
              'sprint_duration', 'workload_unit', 'capacity']
    template_name = 'blog/project_form.html'

    def get_initial(self):
        return {'sprint_duration': 14}

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class ProjectUpdateView(AdminRequiredMixin, UpdateView):
    model = Project
    fields = ['code', 'name', 'description', 'start_date', 'end_date',
              'sprint_duration', 'workload_unit', 'capacity']
    template_name = 'blog/project_form.html'


class ProjectDeleteView(AdminRequiredMixin, DeleteView):
    model = Project
    template_name = 'blog/project_confirm_delete.html'
    success_url = reverse_lazy('project-list')


def product_backlog(request, pk):
    project = get_object_or_404(Project, pk=pk)
    role = get_user_role(request.user, project)
    backlog_items = Ticket.objects.filter(
        project=project,
        sprint__isnull=True,
        ticket_type__in=['story', 'bug']
    ).order_by('backlog_order')
    return render(request, 'blog/backlog.html', {
        'project': project,
        'backlog_items': backlog_items,
        'user_role': role,
        'active_sprint': project.sprints.filter(status='active').first(),
    })


# ── Members ───────────────────────────────────────────────────────────────────
@login_required
def manage_members(request, project_pk):
    project = get_object_or_404(Project, pk=project_pk)
    if not request.user.is_staff:
        messages.error(request, "Only admins can manage members.")
        return redirect('project-detail', pk=project_pk)

    all_users   = User.objects.exclude(pk=request.user.pk).order_by('username')
    memberships = ProjectMembership.objects.filter(project=project).select_related('user')
    member_ids  = list(memberships.values_list('user_id', flat=True))

    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        role    = request.POST.get('role')
        action  = request.POST.get('action')
        target  = get_object_or_404(User, pk=user_id)

        if action == 'add':
            ProjectMembership.objects.get_or_create(
                project=project, user=target,
                defaults={'role': role or 'contributor'}
            )
            messages.success(request, f'{target.username} added as {role}.')
        elif action == 'update':
            ProjectMembership.objects.filter(project=project, user=target).update(role=role)
            messages.success(request, f'{target.username} role updated to {role}.')
        elif action == 'remove':
            ProjectMembership.objects.filter(project=project, user=target).delete()
            messages.success(request, f'{target.username} removed from project.')

        return redirect('manage-members', project_pk=project_pk)

    return render(request, 'blog/manage_members.html', {
        'project':     project,
        'all_users':   all_users,
        'memberships': memberships,
        'member_ids':  member_ids,
    })


# ── Sprints ───────────────────────────────────────────────────────────────────
class SprintCreateView(AdminRequiredMixin, CreateView):
    model = Sprint
    fields = ['name', 'goal', 'start_date', 'global_capacity']
    template_name = 'blog/sprint_form.html'

    def form_valid(self, form):
        project = get_object_or_404(Project, pk=self.kwargs['project_pk'])
        form.instance.project = project
        start = form.cleaned_data['start_date']
        duration = int(self.request.POST.get('sprint_duration', project.sprint_duration))
        form.instance.end_date = start + timedelta(days=duration)
        return super().form_valid(form)


class SprintUpdateView(AdminRequiredMixin, UpdateView):
    model = Sprint
    fields = ['name', 'goal', 'start_date', 'end_date', 'status', 'global_capacity']
    template_name = 'blog/sprint_form.html'


class SprintDeleteView(AdminRequiredMixin, DeleteView):
    model = Sprint
    template_name = 'blog/sprint_confirm_delete.html'

    def get_success_url(self):
        return reverse_lazy('project-detail', kwargs={'pk': self.get_object().project.pk})


def sprint_start(request, pk):
    sprint = get_object_or_404(Sprint, pk=pk)
    if request.user.is_staff and sprint.status == 'planned':
        sprint.status = 'active'
        sprint.save()
        messages.success(request, f'Sprint "{sprint.name}" is now active!')
    return redirect('project-detail', pk=sprint.project.pk)


def sprint_close(request, pk):
    sprint = get_object_or_404(Sprint, pk=pk)
    if request.user.is_staff and sprint.status == 'active':
        sprint.status = 'completed'
        sprint.save()
        Ticket.objects.filter(sprint=sprint).exclude(status='closed').update(sprint=None)
        messages.success(request, f'Sprint "{sprint.name}" closed. Unfinished tickets moved back to backlog.')
    return redirect('project-detail', pk=sprint.project.pk)


def sprint_kanban(request, pk):
    sprint = get_object_or_404(Sprint, pk=pk)
    role = get_user_role(request.user, sprint.project)
    context = {
        'sprint':    sprint,
        'new':       sprint.tickets.filter(status='new'),
        'active':    sprint.tickets.filter(status='active'),
        'closed':    sprint.tickets.filter(status='closed'),
        'cancelled': sprint.tickets.filter(status='cancelled'),
        'user_role': role,
        'project':   sprint.project,
        'active_sprint': sprint if sprint.status == 'active' else None,
    }
    return render(request, 'blog/sprint_kanban.html', context)


# ── Issues & Epics ────────────────────────────────────────────────────────────
def project_issues(request, pk):
    project = get_object_or_404(Project, pk=pk)
    tickets = Ticket.objects.filter(project=project).order_by('backlog_order', '-date_created')
    return render(request, 'blog/project_issues.html', {
        'project':      project,
        'tickets':      tickets,
        'user_role':    get_user_role(request.user, project),
        'active_sprint': project.sprints.filter(status='active').first(),
    })


def project_epics(request, pk):
    project = get_object_or_404(Project, pk=pk)
    return render(request, 'blog/project_epics.html', {
        'project':      project,
        'epics':        Epic.objects.filter(project=project),
        'user_role':    get_user_role(request.user, project),
        'active_sprint': project.sprints.filter(status='active').first(),
    })


# ── Epics ─────────────────────────────────────────────────────────────────────
class EpicCreateView(AdminRequiredMixin, CreateView):
    model = Epic
    fields = ['title', 'description', 'priority', 'color', 'start_date', 'end_date']
    template_name = 'blog/epic_form.html'

    def form_valid(self, form):
        form.instance.project = get_object_or_404(Project, pk=self.kwargs['project_pk'])
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class EpicUpdateView(AdminRequiredMixin, UpdateView):
    model = Epic
    fields = ['title', 'description', 'status', 'priority', 'color', 'start_date', 'end_date']
    template_name = 'blog/epic_form.html'


class EpicDeleteView(AdminRequiredMixin, DeleteView):
    model = Epic
    template_name = 'blog/epic_confirm_delete.html'

    def get_success_url(self):
        return reverse_lazy('project-detail', kwargs={'pk': self.get_object().project.pk})