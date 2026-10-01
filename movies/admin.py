from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin
from django.contrib.auth.models import Group

from .models import Genre, Movie, Person, Rating


class RatingInline(admin.TabularInline):
    """Ratings are created and edited from the parent movie page."""

    model = Rating
    extra = 1
    fields = ["reviewer", "score", "comment"]


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ["title", "year", "genre_list", "average_score", "score_count"]
    list_filter = ["genres", "year"]
    search_fields = ["title", "genres__name", "people__first_name", "people__last_name"]
    ordering = ["title"]
    filter_horizontal = ["genres", "people"]
    inlines = [RatingInline]
    readonly_fields = ["created_at", "updated_at"]
    fieldsets = [
        (None, {"fields": ["title", "year", "poster", "synopsis"]}),
        ("Relations", {"fields": ["genres", "people"]}),
        ("Audit", {"fields": ["created_at", "updated_at"]}),
    ]

    def get_queryset(self, request):
        return super().get_queryset(request).with_scores()

    @admin.display(description="Genres", ordering="genres__name")
    def genre_list(self, movie):
        return ", ".join(genre.name for genre in movie.genres.all()) or "-"

    @admin.display(description="Average", ordering="avg_score")
    def average_score(self, movie):
        score = movie.avg_score
        return "-" if score is None else round(score, 2)

    @admin.display(description="Ratings", ordering="rating_count")
    def score_count(self, movie):
        return movie.rating_count


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ["name", "movie_count", "created_at"]
    search_fields = ["name"]
    ordering = ["name"]
    readonly_fields = ["created_at", "updated_at"]

    @admin.display(description="Movies", ordering="movie_count")
    def movie_count(self, genre):
        return genre.movies.count()


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ["full_name", "movie_count", "created_at"]
    search_fields = ["first_name", "last_name"]
    ordering = ["last_name", "first_name"]
    readonly_fields = ["created_at", "updated_at"]

    @admin.display(description="Name", ordering="last_name")
    def full_name(self, person):
        return str(person)

    @admin.display(description="Movies", ordering="movie_count")
    def movie_count(self, person):
        return person.movies.count()


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ["movie", "score", "reviewer", "created_at"]
    list_filter = ["score", "created_at"]
    search_fields = ["movie__title", "reviewer"]
    ordering = ["-created_at"]
    autocomplete_fields = ["movie"]
    readonly_fields = ["created_at", "updated_at"]


admin.site.unregister(Group)


@admin.register(Group)
class RoleGroupAdmin(GroupAdmin):
    """Group admin extended with the user count, used to manage the roles."""

    list_display = ["name", "user_count", "permission_count"]
    list_filter = ["permissions"]
    search_fields = ["name"]

    @admin.display(description="Users", ordering="user_count")
    def user_count(self, group):
        return group.user_set.count()

    @admin.display(description="Permissions", ordering="permission_count")
    def permission_count(self, group):
        return group.permissions.count()
