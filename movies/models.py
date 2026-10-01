from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Avg, Count

SCORE_MIN = 1
SCORE_MAX = 10
RECOMMENDATION_LIMIT = 5


class MovieQuerySet(models.QuerySet):
    """Adds the aggregated score columns used by the panel and the views."""

    def with_scores(self):
        return self.annotate(
            avg_score=Avg("ratings__score"),
            rating_count=Count("ratings", distinct=True),
        )

    def best_rated(self):
        return self.with_scores().order_by("-avg_score", "title")


class TimeStampedModel(models.Model):
    """Audit fields shared by the models that need creation/update tracking."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Genre(TimeStampedModel):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = "genre"
        verbose_name_plural = "genres"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Person(TimeStampedModel):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)

    class Meta:
        verbose_name = "person"
        verbose_name_plural = "people"
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name}".strip()


class Movie(TimeStampedModel):
    title = models.CharField(max_length=200, unique=True)
    year = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1888), MaxValueValidator(2100)]
    )
    synopsis = models.TextField(blank=True)
    poster = models.ImageField(upload_to="posters/", blank=True)
    genres = models.ManyToManyField(Genre, related_name="movies", blank=True)
    people = models.ManyToManyField(Person, related_name="movies", blank=True)

    objects = MovieQuerySet.as_manager()

    class Meta:
        verbose_name = "movie"
        verbose_name_plural = "movies"
        ordering = ["title"]

    def __str__(self):
        return self.title

    def recommended_movies(self, limit=RECOMMENDATION_LIMIT):
        """Best rated movies that share at least one genre with this one."""
        genre_ids = self.genres.values_list("id", flat=True)
        return (
            Movie.objects.filter(genres__in=genre_ids)
            .exclude(pk=self.pk)
            .with_scores()
            .filter(avg_score__isnull=False)
            .order_by("-avg_score", "title")[:limit]
        )


class Rating(TimeStampedModel):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="ratings")
    reviewer = models.CharField(max_length=120, blank=True)
    score = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(SCORE_MIN), MaxValueValidator(SCORE_MAX)]
    )
    comment = models.TextField(blank=True)

    class Meta:
        verbose_name = "rating"
        verbose_name_plural = "ratings"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.movie} - {self.score}/{SCORE_MAX}"
