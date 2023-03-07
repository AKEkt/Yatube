from datetime import date


def year(request):
    """Добавляет переменную с текущим годом."""
    return {
        'year': int(date.today().strftime('%Y'))
    }
