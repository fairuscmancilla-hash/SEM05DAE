from django.shortcuts import get_object_or_404
from django.views.generic import DetailView, ListView

from .models import Genre, Movie


class MovieListView(ListView):
    """Public catalogue ordered by average score."""

    model = Movie
    template_name = "movies/movie_list.html"
    context_object_name = "movies"
    paginate_by = 12

    def get_queryset(self):
        return Movie.objects.best_rated().prefetch_related("genres")


class MovieDetailView(DetailView):
    """Public movie page with the best rated movies of the same genres."""

    model = Movie
    template_name = "movies/movie_detail.html"
    context_object_name = "movie"

    def get_queryset(self):
        return (
            Movie.objects.with_scores().prefetch_related("genres", "people", "ratings")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["recommendations"] = self.object.recommended_movies()
        return context


class GenreRecommendationView(ListView):
    """Best rated movies inside a single genre."""

    model = Movie
    template_name = "movies/genre_detail.html"
    context_object_name = "movies"

    def get_queryset(self):
        return (
            Movie.objects.filter(genres__pk=self.kwargs["pk"])
            .best_rated()
            .prefetch_related("genres")
        )
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["genre"] = get_object_or_404(Genre, pk=self.kwargs["pk"])
        return context
