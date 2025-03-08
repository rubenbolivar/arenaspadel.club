from reservations.models import Court

def global_context(request):
    """Add global context variables to all templates."""
    return {
        'latest_courts': Court.objects.all()[:3],
    }
