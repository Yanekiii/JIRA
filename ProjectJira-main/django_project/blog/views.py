from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView
)
from .models import Ticket, Project



def home(request):
    context = {
        'tickets': Ticket.objects.all()
    }
    return render(request, 'blog/home.html', context)

def kanban_board(request):
    context = {
        'todo': Ticket.objects.filter(status='todo'),
        'progress': Ticket.objects.filter(status='progress'),
        'done': Ticket.objects.filter(status='done'),
    }
    return render(request, 'blog/kanban.html', context)


class TicketListView(ListView):
    model = Ticket
    template_name = 'blog/home.html'
    context_object_name = 'tickets'
    ordering = ['-date_created']


class TicketDetailView(DetailView):
    model = Ticket
    template_name = 'blog/post_detail.html'


class TicketCreateView(LoginRequiredMixin, CreateView):
    model = Ticket
    fields = ['title', 'description', 'project', 'priority', 'status']
    template_name = 'blog/post_form.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class TicketUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Ticket
    fields = ['title', 'description', 'project', 'priority', 'status']
    template_name = 'blog/post_form.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def test_func(self):
        ticket = self.get_object()
        return self.request.user == ticket.author


class TicketDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Ticket
    template_name = 'blog/post_confirm_delete.html'
    success_url = '/'

    def test_func(self):
        ticket = self.get_object()
        return self.request.user == ticket.author


def about(request):
    return render(request, 'blog/about.html', {'title': 'About'})
class ProjectListView(ListView):
    model = Project
    template_name = 'blog/projects.html'
    context_object_name = 'projects'
    ordering = ['-start_date']


class ProjectDetailView(DetailView):
    model = Project
    template_name = 'blog/project_detail.html'


class ProjectCreateView(LoginRequiredMixin, CreateView):
    model = Project
    fields = ['code', 'name', 'description', 'start_date', 'end_date', 'sprint_duration']
    template_name = 'blog/project_form.html'

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class ProjectUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Project
    fields = ['code', 'name', 'description', 'start_date', 'end_date', 'sprint_duration']
    template_name = 'blog/project_form.html'

    def test_func(self):
        project = self.get_object()
        return self.request.user == project.created_by


class ProjectDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Project
    template_name = 'blog/project_confirm_delete.html'
    success_url = '/projects/'

    def test_func(self):
        project = self.get_object()
        return self.request.user == project.created_by
    
    