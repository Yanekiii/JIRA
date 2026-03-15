from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.http import JsonResponse
from .models import Ticket, Project, Sprint, Epic


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser


# ── Misc ──────────────────────────────────────────────────────────────────────
def home(request):
    return render(request, 'blog/home.html', {'tickets': Ticket.objects.all()})


# Kanbann
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
    fields = ['ticket_type', 'title', 'description', 'project', 'epic',
              'sprint', 'priority', 'status', 'assignee',
              'start_date', 'end_date', 'workload_initial']
    template_name = 'blog/post_form.html'

    def form_valid(self, form):
        form.instance.reporter = self.request.user
        return super().form_valid(form)

class TicketUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Ticket
    fields = ['ticket_type', 'title', 'description', 'project', 'epic',
              'sprint', 'priority', 'status', 'assignee',
              'start_date', 'end_date', 'workload_initial', 'workload_remaining', 'workload_done']
    template_name = 'blog/post_form.html'

    def test_func(self):
        return self.request.user == self.get_object().reporter or self.request.user.is_staff

class TicketDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Ticket
    template_name = 'blog/post_confirm_delete.html'
    success_url = '/'

    def test_func(self):
        return self.request.user == self.get_object().reporter or self.request.user.is_staff

def ticket_move(request, pk):
    if request.method == 'POST':
        ticket = get_object_or_404(Ticket, pk=pk)
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


# ── Projects ──────────────────────────────────────────────────────────────────
class ProjectListView(ListView):
    model = Project
    template_name = 'blog/projects.html'
    context_object_name = 'projects'
    ordering = ['-start_date']

class ProjectDetailView(LoginRequiredMixin, DetailView):
    model = Project
    template_name = 'blog/project_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.get_object()

        sprints = project.sprints.all().prefetch_related('tickets')
        active_sprint = sprints.filter(status='active').first()

        context['sprints'] = sprints
        context['epics'] = project.epics.all()
        context['members'] = project.memberships.select_related('user')
        context['active_sprint'] = active_sprint

        return context

class ProjectCreateView(AdminRequiredMixin, CreateView):
    model = Project
    fields = ['code', 'name', 'description', 'start_date', 'end_date',
              'sprint_duration', 'workload_unit', 'capacity']
    template_name = 'blog/project_form.html'

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
    backlog_items = Ticket.objects.filter(
        project=project,
        sprint__isnull=True,
        ticket_type__in=['story', 'bug']
    ).order_by('backlog_order')
    return render(request, 'blog/backlog.html', {
        'project': project,
        'backlog_items': backlog_items,
    })


# ── Sprints ───────────────────────────────────────────────────────────────────
class SprintCreateView(AdminRequiredMixin, CreateView):
    model = Sprint
    fields = ['name', 'goal', 'start_date', 'end_date', 'global_capacity']
    template_name = 'blog/sprint_form.html'

    def form_valid(self, form):
        form.instance.project = get_object_or_404(Project, pk=self.kwargs['project_pk'])
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
    context = {
        'sprint': sprint,
        'new':       sprint.tickets.filter(status='new'),
        'active':    sprint.tickets.filter(status='active'),
        'closed':    sprint.tickets.filter(status='closed'),
        'cancelled': sprint.tickets.filter(status='cancelled'),
    }
    return render(request, 'blog/sprint_kanban.html', context)


# ── Epics ─────────────────────────────────────────────────────────────────────
class EpicCreateView(AdminRequiredMixin, CreateView):
    model = Epic
    fields = ['title', 'description', 'status', 'priority', 'color', 'start_date', 'end_date']
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
