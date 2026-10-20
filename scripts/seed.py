"""Run in the application's Django environment after bootstrap/migrations."""
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
import json
import os
from pathlib import Path
import uuid
from django.contrib.auth.models import User
from django.db import transaction
from rest_framework.authtoken.models import Token
from wger.exercises.models import Exercise
from wger.manager.models import Routine, Day, Slot, SlotEntry, SetsConfig, RepetitionsConfig, WeightConfig, WorkoutLog
from wger.measurements.models import Category, Measurement
from wger.measurements.models.category import MetricType
from wger.core.models import Language
from wger.nutrition.models import Ingredient, NutritionPlan, Meal, MealItem, LogItem

state = Path('/runtime/credentials.json')
old = json.loads(state.read_text()) if state.exists() else {}
end = date.fromisoformat(old.get('end_date') or os.environ.get('SEED_END_DATE') or date.today().isoformat())
with transaction.atomic():
    user, _ = User.objects.get_or_create(username=os.environ['DEMO_USERNAME'])
    user.email = os.environ['DEMO_EMAIL']
    user.set_password(os.environ['DEMO_PASSWORD'])
    user.is_active = True
    user.save()
    # Replace the upstream bootstrap admin's well-known default password.
    admin = User.objects.filter(username='admin').first()
    if admin:
        admin.set_password(os.environ['DEMO_PASSWORD'])
        admin.save()
    token, _ = Token.objects.get_or_create(user=user)
    category = Category.get_or_create_official(user, MetricType.BODY_WEIGHT, name='Body weight', unit='kg')
    if isinstance(category, tuple):
        category = category[0]
    for index in range(14):
        day = end - timedelta(days=13-index)
        Measurement.objects.update_or_create(
            category=category, source='user', external_id=uuid.uuid5(uuid.NAMESPACE_URL, f'harness-weight-{day}'),
            defaults={'date': datetime.combine(day, time(8), timezone.utc),
                      'value': Decimal('82') - Decimal(index) * Decimal('0.07'), 'extra_data': {'unit': 'kg'}, 'notes': 'Harness sample'})
    routine, _ = Routine.objects.update_or_create(user=user, name='Harness Full Body', defaults={
        'start': end-timedelta(days=13), 'end': end+timedelta(days=42),
        'description': 'Three exercise sample routine for addon development.'})
    training, _ = Day.objects.get_or_create(routine=routine, order=1, defaults={'name': 'Full body'})
    rest, _ = Day.objects.get_or_create(routine=routine, order=2, defaults={'name': 'Recovery', 'is_rest': True})
    exercises = list(Exercise.objects.order_by('pk')[:3])
    if len(exercises) < 3:
        raise RuntimeError('Expected at least three exercises from upstream bootstrap fixtures')
    for index, exercise in enumerate(exercises):
        slot, _ = Slot.objects.get_or_create(day=training, order=index+1)
        entry, _ = SlotEntry.objects.get_or_create(slot=slot, order=1, defaults={'exercise': exercise})
        for model, value in [(SetsConfig, 3), (RepetitionsConfig, 10), (WeightConfig, 20+index*10)]:
            model.objects.update_or_create(slot_entry=entry, iteration=1, defaults={'value': value})
        for session_no, offset in enumerate([12, 10, 8, 5, 3, 0]):
            stamp = datetime.combine(end-timedelta(days=offset), time(17), timezone.utc)
            for set_no in range(3):
                log_id = uuid.uuid5(uuid.NAMESPACE_URL, f'harness:{user.pk}:{exercise.pk}:{stamp}:{set_no}')
                WorkoutLog.objects.update_or_create(pk=log_id, defaults={
                    'user': user, 'routine': routine, 'slot_entry': entry,
                    'exercise': exercise, 'date': stamp+timedelta(minutes=set_no),
                    'repetitions': 10, 'weight': Decimal(20+index*10) + Decimal('2.5')*session_no})
    plan, _ = NutritionPlan.objects.update_or_create(user=user, description='Harness balanced meals',
        defaults={'start': end-timedelta(days=13), 'end': end+timedelta(days=42),
                  'has_goal_calories': True, 'goal_energy': 2200, 'goal_protein': 140})
    language = Language.objects.get(short_name='en')
    for order, (name, calories, protein, carbs, fat, hour) in enumerate([
        ('Breakfast oats', 160, 6, 27, 3, 8),
        ('Chicken rice', 173, 14, 21, 4, 12),
        ('Salmon salad', 143, 13, 6, 8, 18)], start=1):
        ingredient, _ = Ingredient.objects.update_or_create(name='Harness ' + name,
            language=language, defaults={'energy': calories, 'protein': protein,
                'carbohydrates': carbs, 'fat': fat, 'license_author': 'Synthetic harness fixture'})
        meal, _ = Meal.objects.get_or_create(plan=plan, order=order, defaults={'name': name})
        MealItem.objects.update_or_create(meal=meal, order=1,
            defaults={'ingredient': ingredient, 'amount': 300})
        for offset in range(14):
            stamp = datetime.combine(end-timedelta(days=offset), time(hour), timezone.utc)
            log_id = uuid.uuid5(uuid.NAMESPACE_URL, f'harness-meal:{user.pk}:{order}:{stamp}')
            LogItem.objects.update_or_create(pk=log_id, defaults={'plan': plan, 'meal': meal,
                'ingredient': ingredient, 'amount': 300, 'datetime': stamp, 'comment': 'Harness sample'})
state.write_text(json.dumps({'username': user.username, 'email': user.email,
    'password': os.environ['DEMO_PASSWORD'], 'token': token.key,
    'end_date': str(end), 'start_date': str(end-timedelta(days=13))}, indent=2))
print('Seed complete: demo user, 14 weights, full body routine, 54 logged sets, nutrition plan and 42 diary entries.')
