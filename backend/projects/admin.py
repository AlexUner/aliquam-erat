"""Django admin configuration for the Projects application."""

from django.contrib import admin
from django.db.models import Count
from django.utils.html import format_html

from .models import (
    Client,
    Developer,
    ProjectStatus,
    Language,
    Project,
    ProjectAnalysis,
)

# ---------------------------------------------------------------------------
# Client admin
# ---------------------------------------------------------------------------


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    """Admin view for `Client` model."""

    list_display = [
        'name',
        'company',
        'email',
        'phone',
        'projects_count',
        'created_at',
    ]
    list_filter = ['created_at', 'company']
    search_fields = ['name', 'company', 'email', 'phone']
    readonly_fields = ['created_at']

    fieldsets = (
        ('Basic info', {'fields': ('name', 'company')}),
        (
            'Contacts',
            {
                'fields': (
                    'email',
                    'phone',
                    'tg_username',
                    'contact_url',
                )
            },
        ),
        (
            'Additional',
            {
                'fields': ('note', 'created_at'),
                'classes': ('collapse',),
            },
        ),
    )

    # Optimize COUNT(*) for related projects
    def get_queryset(self, request):  # noqa: D401,D404  (admin override)
        qs = super().get_queryset(request)
        return qs.annotate(_projects_cnt=Count('projects'))

    def projects_count(self, obj):
        """Return cached annotation added in `get_queryset`."""
        return obj._projects_cnt

    projects_count.short_description = 'Projects'


# ---------------------------------------------------------------------------
# Developer admin
# ---------------------------------------------------------------------------


@admin.register(Developer)
class DeveloperAdmin(admin.ModelAdmin):
    """Admin view for `Developer` model."""

    list_display = [
        'name',
        'email',
        'github_username',
        'projects_count',
        'created_at',
    ]
    list_filter = ['created_at']
    search_fields = ['name', 'email', 'github_username']
    readonly_fields = ['created_at']

    fieldsets = (
        ('Basic info', {'fields': ('name',)}),
        (
            'Contacts',
            {
                'fields': (
                    'email',
                    'phone',
                    'tg_username',
                    'contact_url',
                )
            },
        ),
        (
            'Professional links',
            {'fields': ('github_username', 'portfolio_url')},
        ),
        (
            'Additional',
            {
                'fields': ('note', 'created_at'),
                'classes': ('collapse',),
            },
        ),
    )

    def get_queryset(self, request):  # noqa: D401,D404  (admin override)
        qs = super().get_queryset(request)
        return qs.annotate(_projects_cnt=Count('projects'))

    def projects_count(self, obj):
        return obj._projects_cnt

    projects_count.short_description = 'Projects'


# ---------------------------------------------------------------------------
# Project status admin
# ---------------------------------------------------------------------------


@admin.register(ProjectStatus)
class ProjectStatusAdmin(admin.ModelAdmin):
    """Admin view for `ProjectStatus` model."""

    list_display = ['name', 'color_preview', 'order', 'projects_count']
    list_editable = ['order']
    ordering = ['order', 'name']
    search_fields = ['name']

    def get_queryset(self, request):  # noqa: D401,D404  (admin override)
        qs = super().get_queryset(request)
        return qs.annotate(_projects_cnt=Count('projects'))

    def color_preview(self, obj):
        """Render small square with the status color."""
        return format_html(
            '<div style="width:20px;height:20px;background:{};'
            'border:1px solid #ccc;border-radius:3px;"></div>',
            obj.color,
        )

    color_preview.short_description = 'Color'

    def projects_count(self, obj):
        return obj._projects_cnt

    projects_count.short_description = 'Projects'


# ---------------------------------------------------------------------------
# Language / Framework admin
# ---------------------------------------------------------------------------


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    """Admin view for `Language` model."""

    list_display = ['name', 'color_preview', 'icon_preview', 'usage_count']
    search_fields = ['name']

    def get_queryset(self, request):  # noqa: D401,D404  (admin override)
        qs = super().get_queryset(request)
        return qs.annotate(_usage_cnt=Count('analysis'))

    def color_preview(self, obj):
        return format_html(
            '<div style="width:20px;height:20px;background:{};'
            'border:1px solid #ccc;border-radius:3px;"></div>',
            obj.color,
        )

    color_preview.short_description = 'Color'

    def icon_preview(self, obj):
        if not obj.icon:
            return '—'
        # Assumes icon fonts (e.g., Font Awesome) are loaded in the admin site.
        return format_html('<i class="{}"></i>', obj.icon)

    icon_preview.short_description = 'Icon'

    def usage_count(self, obj):
        return obj._usage_cnt

    usage_count.short_description = 'Used in'


# ---------------------------------------------------------------------------
# Inline analysis (read‑only)
# ---------------------------------------------------------------------------


class ProjectAnalysisInline(admin.TabularInline):
    """Read‑only inline displaying code statistics per project."""

    model = ProjectAnalysis
    extra = 0
    readonly_fields = ['language', 'lines_count', 'percentage']

    def has_add_permission(self, request, obj=None):  # noqa: D401,D404
        return False  # Records are created automatically.


# ---------------------------------------------------------------------------
# Project admin
# ---------------------------------------------------------------------------


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    """Admin view for `Project` model."""

    list_display = [
        'name',
        'client',
        'developer',
        'status_colored',
        'cost',
        'deadline_planned',
        'spent_minutes',
        'archive_exist',
        'is_public',
        'created_at',
    ]
    list_filter = [
        'status',
        'is_public',
        'created_at',
        'client',
        'developer',
    ]
    search_fields = [
        'name',
        'description',
        'client__name',
        'developer__name',
    ]
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'deadline_planned'
    list_select_related = ('client', 'developer', 'status')
    autocomplete_fields = ['client', 'developer', 'status']
    inlines = [ProjectAnalysisInline]
    actions = ['make_public', 'make_private', 'analyze_code']

    fieldsets = (
        ('Basic info', {'fields': ('name', 'description', 'image')}),
        ('Participants', {'fields': ('client', 'developer', 'status')}),
        ('Deadlines', {'fields': ('deadline_planned', 'deadline_actual')}),
        ('Resources', {'fields': ('planned_minutes', 'spent_minutes', 'cost')}),
        (
            'Files',
            {
                'fields': ('archive',),
                'description': 'ZIP‑archive used for code analysis.',
            },
        ),
        (
            'Meta & debug',
            {
                'fields': ('is_public', 'id', 'created_at', 'updated_at'),
                'classes': ('collapse',),
            },
        ),
    )

    # Render helpers ---------------------------------------------------------

    def status_colored(self, obj):
        """Colored bullet corresponding to the status color."""
        return format_html(
            '<span style="color:{};font-weight:bold;">●</span>&nbsp;{}',
            obj.status.color,
            obj.status.name,
        )

    status_colored.short_description = 'Status'

    def archive_exist(self, obj):
        """Boolean flag indicating presence of a ZIP archive."""
        return bool(obj.archive)

    archive_exist.boolean = True
    archive_exist.short_description = 'ZIP'

    # Actions ----------------------------------------------------------------

    def make_public(self, request, queryset):
        updated = queryset.update(is_public=True)
        self.message_user(request, f'Made public: {updated} project(s).')

    make_public.short_description = 'Mark as public'

    def make_private(self, request, queryset):
        updated = queryset.update(is_public=False)
        self.message_user(request, f'Made private: {updated} project(s).')

    make_private.short_description = 'Mark as private'

    def analyze_code(self, request, queryset):
        """Trigger asynchronous code analysis via Celery / RQ."""
        started = 0
        for project in queryset:
            if project.archive and hasattr(project, 'run_analysis_async'):
                project.run_analysis_async()
                started += 1

        if started:
            self.message_user(request, f'Analysis started for {started} project(s).')
        else:
            self.message_user(request, 'No archives found in selected projects.', level='WARNING')

    analyze_code.short_description = 'Analyze code'


# ---------------------------------------------------------------------------
# ProjectAnalysis admin (read‑only)
# ---------------------------------------------------------------------------


@admin.register(ProjectAnalysis)
class ProjectAnalysisAdmin(admin.ModelAdmin):
    """Read‑only admin for `ProjectAnalysis` model."""

    list_display = ['project', 'language', 'lines_count', 'percentage']
    list_filter = ['language', 'project__status']
    search_fields = ['project__name', 'language__name']
    readonly_fields = ['project', 'language', 'lines_count', 'percentage']

    def has_add_permission(self, request):
        return False  # Records are created automatically.

    def has_change_permission(self, request, obj=None):
        return False  # Read‑only admin.
