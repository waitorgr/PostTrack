from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = 'Створює тестові регіони, міста та локації: 25 СЦ, 50 РЦ, 200 відділень'

    REGIONS_COUNT = 25
    DCS_PER_SC = 2
    POS_PER_DC = 4

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Очистити Region/City/Location перед заповненням'
        )

    @transaction.atomic
    def handle(self, *args, **options):
        from locations.models import Region, City, Location, LocationType

        if options['clear']:
            self.stdout.write('Очищення локацій...')
            Location.objects.all().delete()
            City.objects.all().delete()
            Region.objects.all().delete()

        created_regions = 0
        created_cities = 0
        created_sc = 0
        created_dc = 0
        created_po = 0

        self.stdout.write('Створення регіонів, міст та локацій...')

        for region_index in range(1, self.REGIONS_COUNT + 1):
            sc_code = f'{region_index:02d}'
            region_code = f'REG-{region_index:02d}'
            region_name = f'Регіон {region_index}'

            region, region_created = Region.objects.get_or_create(
                code=region_code,
                defaults={'name': region_name},
            )
            if not region_created and region.name != region_name:
                region.name = region_name
                region.save(update_fields=['name'])
            if region_created:
                created_regions += 1
                self.stdout.write(f'  + Регіон: {region.name}')

            sc_city, sc_city_created = City.objects.get_or_create(
                name=f'Місто СЦ {region_index}',
                region=region,
            )
            if sc_city_created:
                created_cities += 1

            sc, sc_created = Location.objects.update_or_create(
                code=sc_code,
                defaults={
                    'name': f'СЦ {region_index}',
                    'type': LocationType.SORTING_CENTER,
                    'city': sc_city,
                    'address': f'Промислова зона {region_index}, буд. 1',
                    'is_active': True,
                    'parent_sc': None,
                    'parent_dc': None,
                }
            )
            if sc_created:
                created_sc += 1
                self.stdout.write(f'  + СЦ: {sc.code} — {sc.name}')

            for dc_index in range(1, self.DCS_PER_SC + 1):
                dc_city, dc_city_created = City.objects.get_or_create(
                    name=f'Місто РЦ {region_index}-{dc_index}',
                    region=region,
                )
                if dc_city_created:
                    created_cities += 1

                dc_code = f'{sc.code}{dc_index:03d}'
                dc, dc_created = Location.objects.update_or_create(
                    code=dc_code,
                    defaults={
                        'name': f'РЦ {region_index}-{dc_index}',
                        'type': LocationType.DISTRIBUTION_CENTER,
                        'city': dc_city,
                        'address': f'Логістична вул. {region_index}, буд. {dc_index}',
                        'is_active': True,
                        'parent_sc': sc,
                        'parent_dc': None,
                    }
                )
                if dc_created:
                    created_dc += 1
                    self.stdout.write(f'  + РЦ: {dc.code} — {dc.name}')

                for po_index in range(1, self.POS_PER_DC + 1):
                    po_code = f'{dc.code}{po_index:05d}'
                    po, po_created = Location.objects.update_or_create(
                        code=po_code,
                        defaults={
                            'name': f'Відділення {region_index}-{dc_index}-{po_index}',
                            'type': LocationType.POST_OFFICE,
                            'city': dc_city,
                            'address': f'Центральна вул. {po_index}, буд. {region_index + dc_index}',
                            'is_active': True,
                            'parent_sc': None,
                            'parent_dc': dc,
                        }
                    )
                    if po_created:
                        created_po += 1

        self.stdout.write(self.style.SUCCESS('\n✅ Seed локацій завершено'))
        self.stdout.write(
            f'Регіони: {Region.objects.count()} | '
            f'Міста: {City.objects.count()} | '
            f'СЦ: {Location.objects.filter(type=LocationType.SORTING_CENTER).count()} | '
            f'РЦ: {Location.objects.filter(type=LocationType.DISTRIBUTION_CENTER).count()} | '
            f'Відділення: {Location.objects.filter(type=LocationType.POST_OFFICE).count()}'
        )