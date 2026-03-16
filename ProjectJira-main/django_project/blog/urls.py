from django.urls import path
from .views import (
    TicketListView, TicketDetailView, TicketCreateView, TicketUpdateView, TicketDeleteView,
    ProjectListView, ProjectDetailView, ProjectCreateView, ProjectUpdateView, ProjectDeleteView,
    SprintCreateView, SprintUpdateView, SprintDeleteView,
    EpicCreateView, EpicUpdateView, EpicDeleteView,
)
from . import views

urlpatterns = [
    path('', TicketListView.as_view(), name='blog-home'),
    path('about/', views.about, name='blog-about'),
    path('kanban/', views.kanban_board, name='kanban-board'),

    # Tickets
    path('ticket/new/', TicketCreateView.as_view(), name='ticket-create'),
    path('ticket/<int:pk>/', TicketDetailView.as_view(), name='ticket-detail'),
    path('ticket/<int:pk>/update/', TicketUpdateView.as_view(), name='ticket-update'),
    path('ticket/<int:pk>/delete/', TicketDeleteView.as_view(), name='ticket-delete'),
    path('ticket/<int:pk>/move/', views.ticket_move, name='ticket-move'),
    path('ticket/<int:pk>/up/', views.ticket_priority_up, name='ticket-priority-up'),
    path('ticket/<int:pk>/down/', views.ticket_priority_down, name='ticket-priority-down'),

    # Projects
    path('projects/', ProjectListView.as_view(), name='project-list'),
    path('project/new/', ProjectCreateView.as_view(), name='project-create'),
    path('project/<int:pk>/', ProjectDetailView.as_view(), name='project-detail'),
    path('project/<int:pk>/update/', ProjectUpdateView.as_view(), name='project-update'),
    path('project/<int:pk>/delete/', ProjectDeleteView.as_view(), name='project-delete'),
    path('project/<int:pk>/backlog/', views.product_backlog, name='product-backlog'),
    path('project/<int:pk>/issues/', views.project_issues, name='project-issues'),
    path('project/<int:pk>/epics/', views.project_epics, name='project-epics'),
    path('project/<int:project_pk>/members/', views.manage_members, name='manage-members'),
    path('project/<int:project_id>/backlog/reorder/', views.backlog_reorder, name='backlog-reorder'),

    # Sprints
    path('project/<int:project_pk>/sprint/new/', SprintCreateView.as_view(), name='sprint-create'),
    path('sprint/<int:pk>/update/', SprintUpdateView.as_view(), name='sprint-update'),
    path('sprint/<int:pk>/delete/', SprintDeleteView.as_view(), name='sprint-delete'),
    path('sprint/<int:pk>/start/', views.sprint_start, name='sprint-start'),
    path('sprint/<int:pk>/close/', views.sprint_close, name='sprint-close'),
    path('sprint/<int:pk>/kanban/', views.sprint_kanban, name='sprint-kanban'),

    # Epics
    path('project/<int:project_pk>/epic/new/', EpicCreateView.as_view(), name='epic-create'),
    path('epic/<int:pk>/update/', EpicUpdateView.as_view(), name='epic-update'),
    path('epic/<int:pk>/delete/', EpicDeleteView.as_view(), name='epic-delete'),
]
