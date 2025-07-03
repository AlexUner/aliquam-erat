import os
import uuid

from django.core.validators import FileExtensionValidator, RegexValidator
from django.db import models
from django.utils import timezone


# Validators
phone_validator = RegexValidator(
    regex=r'^\+?\d{7,15}$',
    message='Введите корректный номер телефона в международном формате.',
)

hex_color_validator = RegexValidator(
    regex=r'^#(?:[0-9a-fA-F]{3}){1,2}$',
    message='Введите цвет в формате HEX, например "#FFAA00".',
)

github_validator = RegexValidator(
    regex=r'^[A-Za-z0-9-]{1,39}$',
    message='Некорректный GitHub-логин.',
)


# Abstract contact model ------------------------------------------------------
class Contact(models.Model):
    """Reusable contact card inherited by Client and Developer."""

    name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Имя / название',
    )
    email = models.EmailField(
        blank=True,
        verbose_name='E-mail',
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        validators=[phone_validator],
        verbose_name='Телефон',
    )
    tg_username = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Telegram',
    )
    contact_url = models.URLField(
        blank=True,
        verbose_name='Ссылка на контакт',
    )
    note = models.TextField(
        blank=True,
        verbose_name='Примечание',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Добавлен',
    )

    class Meta:
        abstract = True


# Client ----------------------------------------------------------------------
class Client(Contact):
    company = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Компания',
    )

    class Meta:
        verbose_name = 'Заказчик'
        verbose_name_plural = 'Заказчики'

    def __str__(self) -> str:
        base = self.name or 'Безымянный'
        return f"{base}" + (f" ({self.company})" if self.company else '')


# Developer -------------------------------------------------------------------
class Developer(Contact):
    github_username = models.CharField(
        max_length=39,
        blank=True,
        validators=[github_validator],
        verbose_name='GitHub',
    )
    portfolio_url = models.URLField(
        blank=True,
        verbose_name='Портфолио',
    )

    class Meta:
        verbose_name = 'Исполнитель'
        verbose_name_plural = 'Исполнители'

    def __str__(self) -> str:
        return self.name or 'Исполнитель'


# Project status --------------------------------------------------------------
class ProjectStatus(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Название статуса',
    )
    color = models.CharField(
        max_length=7,
        default='#808080',
        validators=[hex_color_validator],
        verbose_name='Цвет (HEX)',
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name='Порядок отображения',
    )

    class Meta:
        verbose_name = 'Статус проекта'
        verbose_name_plural = 'Статусы проектов'
        ordering = ['order', 'name']

    def __str__(self) -> str:
        return self.name


# Language / Framework --------------------------------------------------------
class Language(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Название',
    )
    color = models.CharField(
        max_length=7,
        default='#808080',
        validators=[hex_color_validator],
        verbose_name='Цвет (HEX)',
    )
    icon = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Иконка',
    )

    class Meta:
        verbose_name = 'Язык программирования'
        verbose_name_plural = 'Языки программирования'
        ordering = ['name']

    def __str__(self) -> str:
        return self.name


# Helper to build archive path ------------------------------------------------

def project_archive_path(instance: 'Project', filename: str) -> str:
    """Return path like project_archives/<YEAR>/<MONTH>/<uuid>.zip."""
    ext = os.path.splitext(filename)[1] or '.zip'
    now = timezone.now()
    return f'project_archives/{now:%Y/%m}/{instance.id}{ext}'


# Project ---------------------------------------------------------------------
class Project(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    name = models.CharField(
        max_length=255,
        verbose_name='Название проекта',
    )
    description = models.TextField(
        blank=True,
        verbose_name='Описание проекта',
    )

    client = models.ForeignKey(
        Client,
        on_delete=models.PROTECT,
        related_name='projects',
        verbose_name='Заказчик',
    )
    developer = models.ForeignKey(
        Developer,
        on_delete=models.PROTECT,
        related_name='projects',
        verbose_name='Исполнитель',
    )
    status = models.ForeignKey(
        ProjectStatus,
        on_delete=models.PROTECT,
        verbose_name='Статус',
    )

    image = models.ImageField(
        upload_to='project_images/',
        blank=True,
        null=True,
        verbose_name='Фото проекта',
    )
    archive = models.FileField(
        upload_to=project_archive_path,
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['zip'])],
        verbose_name='Архив проекта (.zip)',
    )

    deadline_planned = models.DateTimeField(
        verbose_name='Указанный дедлайн',
    )
    deadline_actual = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Фактический дедлайн',
    )

    planned_minutes = models.PositiveIntegerField(
        default=0,
        verbose_name='Запланировано (минут)',
    )
    spent_minutes = models.PositiveIntegerField(
        default=0,
        verbose_name='Затрачено (минут)',
    )

    cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='Стоимость',
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name='Дата создания',
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления',
    )
    is_public = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name='Публичный проект',
    )

    class Meta:
        verbose_name = 'Проект'
        verbose_name_plural = 'Проекты'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
        ]

    def __str__(self) -> str:
        return self.name


# Project analysis by languages ----------------------------------------------
class ProjectAnalysis(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='analysis',
        verbose_name='Проект',
    )
    language = models.ForeignKey(
        Language,
        on_delete=models.CASCADE,
        verbose_name='Язык / фреймворк',
    )
    lines_count = models.PositiveIntegerField(
        verbose_name='Количество строк',
    )
    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name='Процент кода',
    )

    class Meta:
        verbose_name = 'Анализ проекта'
        verbose_name_plural = 'Анализ проектов'
        constraints = [
            models.UniqueConstraint(
                fields=['project', 'language'],
                name='unique_project_language',
            ),
            models.CheckConstraint(
                check=models.Q(percentage__gte=0) & models.Q(percentage__lte=100),
                name='percentage_0_100',
            ),
        ]
        ordering = ['-percentage']

    def __str__(self) -> str:
        return f'{self.project.name} — {self.language.name}: {self.percentage}%'
