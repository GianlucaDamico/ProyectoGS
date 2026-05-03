from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta
from bookings.models import Booking

class ComplexStatsService:
    """
    Servicio para calcular estadísticas de complejos.
    Útil para el dashboard del propietario.
    """

    @staticmethod
    def get_complex_stats(complex, days=30):
        """
        Calcula estadísticas de un complejo para los últimos X días.
        
        Args:
            complex: Instancia de Complex
            days: Número de días hacia atrás
            
        Returns:
            dict: Diccionario con estadísticas
        """
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)

        bookings = Booking.objects.filter(
            court__complex=complex,
            created_at__gte=start_date,
            created_at__lte=end_date
        )

        total_bookings = bookings.count()

        confirmed_bookings = bookings.filter(
            status__in=[Booking.Status.CONFIRMED, Booking.Status.FINISHED]
        ).count()

        cancelled_bookings = bookings.filter(
            status=Booking.Status.CANCELLED
        ).count()

        revenue_bookings = bookings.filter(
            status__in=[Booking.Status.CONFIRMED, Booking.Status.FINISHED]
        )

        total_revenue = revenue_bookings.aggregate(
            total=Sum('total_price')
        )['total'] or 0

        court_stats = bookings.filter(
            status__in=[Booking.Status.CONFIRMED, Booking.Status.FINISHED]
        ).values('court__name').annotate(
            bookings_count=Count('id')
        ).order_by('-bookings_count').first()

        most_popular_court = court_stats['court__name'] if court_stats else "N/A"

        total_courts = complex.courts.count()
        avg_bookings_per_court = total_bookings / total_courts if total_courts > 0 else 0

        return {
            'period_days': days,
            'total_bookings': total_bookings,
            'confirmed_bookings': confirmed_bookings,
            'cancelled_bookings': cancelled_bookings,
            'cancellation_rate': (cancelled_bookings / total_bookings * 100) if total_bookings > 0 else 0,
            'total_revenue': float(total_revenue),
            'average_booking_value': float(total_revenue / confirmed_bookings) if confirmed_bookings > 0 else 0,
            'most_popular_court': most_popular_court,
            'total_courts': total_courts,
            'avg_bookings_per_court': avg_bookings_per_court,
        }