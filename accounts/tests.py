from django.core.exceptions import ValidationError
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Role, User
from locations.models import Region, City, Location, LocationType


@override_settings(ROOT_URLCONF="accounts.urls")
class AccountsTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.region = Region.objects.create(
            name="Kyiv Region",
            code="80",
        )

        cls.city = City.objects.create(
            name="Kyiv",
            region=cls.region,
        )

        cls.sorting_center = Location.objects.create(
            name="Sorting Center 1",
            type=LocationType.SORTING_CENTER,
            city=cls.city,
            address="SC Address",
            code="80",
        )

        cls.distribution_center = Location.objects.create(
            name="Distribution Center 1",
            type=LocationType.DISTRIBUTION_CENTER,
            city=cls.city,
            address="DC Address",
            code="80001",
            parent_sc=cls.sorting_center,
        )

        cls.post_office = Location.objects.create(
            name="Post Office 1",
            type=LocationType.POST_OFFICE,
            city=cls.city,
            address="PO Address",
            code="8000100001",
            parent_dc=cls.distribution_center,
        )

    def create_user(
        self,
        username,
        role,
        password="StrongPass123!",
        email=None,
        phone=None,
        location=None,
        region=None,
        is_active=True,
    ):
        if email is None:
            email = f"{username}@example.com"

        if phone is None:
            index = User.objects.count() + 1
            phone = f"+38099000{index:04d}"[-13:]

            if len(phone) != 13:
                phone = "+380" + str(900000000 + index)[-9:]

        return User.objects.create_user(
            username=username,
            password=password,
            first_name="Test",
            last_name="User",
            patronymic="Testovych",
            email=email,
            phone=phone,
            role=role,
            location=location,
            region=region,
            is_active=is_active,
        )

    def test_customer_register_creates_customer(self):
        response = self.client.post(
            "/register/",
            {
                "username": "customer1",
                "first_name": "Ivan",
                "last_name": "Petrenko",
                "patronymic": "Ivanovych",
                "email": "customer1@example.com",
                "phone": "+380991112233",
                "password": "StrongPass123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        user = User.objects.get(username="customer1")
        self.assertEqual(user.role, Role.CUSTOMER)
        self.assertTrue(user.check_password("StrongPass123!"))

    def test_hr_can_create_logist_with_region(self):
        hr = self.create_user("hr1", Role.HR)

        self.client.force_authenticate(user=hr)
        response = self.client.post(
            "/workers/",
            {
                "username": "logist1",
                "first_name": "Log",
                "last_name": "Ist",
                "patronymic": "Test",
                "email": "logist1@example.com",
                "phone": "+380991112234",
                "role": Role.LOGIST,
                "region": self.region.pk,
                "password": "StrongPass123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        user = User.objects.get(username="logist1")
        self.assertEqual(user.role, Role.LOGIST)
        self.assertEqual(user.region_id, self.region.pk)

    def test_customer_cannot_access_workers_endpoint(self):
        customer = self.create_user("customer2", Role.CUSTOMER)

        self.client.force_authenticate(user=customer)
        response = self.client.get("/workers/")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_worker_list_searches_by_email_and_phone(self):
        hr = self.create_user("hr2", Role.HR)
        worker = self.create_user(
            "postal1",
            Role.POSTAL_WORKER,
            email="postal-search@example.com",
            phone="+380991112235",
            location=self.post_office,
        )

        self.client.force_authenticate(user=hr)

        response_email = self.client.get("/workers/?search=postal-search@example.com")
        self.assertEqual(response_email.status_code, status.HTTP_200_OK)

        email_results = response_email.data["results"] if isinstance(response_email.data, dict) else response_email.data
        self.assertEqual(len(email_results), 1)
        self.assertEqual(email_results[0]["id"], worker.id)

        response_phone = self.client.get("/workers/", {"search": "+380991112235"})
        self.assertEqual(response_phone.status_code, status.HTTP_200_OK)

        phone_results = response_phone.data["results"] if isinstance(response_phone.data, dict) else response_phone.data
        self.assertEqual(len(phone_results), 1)
        self.assertEqual(phone_results[0]["id"], worker.id)

    def test_logout_without_refresh_returns_400(self):
        hr = self.create_user("hr3", Role.HR)

        self.client.force_authenticate(user=hr)
        response = self.client.post("/logout/", {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", response.data)

    def test_postal_worker_must_match_post_office_location_type(self):
        with self.assertRaises(ValidationError) as exc:
            self.create_user(
                "postal_wrong",
                Role.POSTAL_WORKER,
                email="postal_wrong@example.com",
                phone="+380991112236",
                location=self.sorting_center,
            )

        self.assertIn("location", exc.exception.message_dict)

    def test_logist_requires_region(self):
        with self.assertRaises(ValidationError) as exc:
            self.create_user(
                "logist_no_region",
                Role.LOGIST,
                email="logist_no_region@example.com",
                phone="+380991112237",
                region=None,
            )

        self.assertIn("region", exc.exception.message_dict)

    def test_hr_must_not_have_location(self):
        with self.assertRaises(ValidationError) as exc:
            self.create_user(
                "hr_with_location",
                Role.HR,
                email="hr_with_location@example.com",
                phone="+380991112238",
                location=self.post_office,
            )

        self.assertIn("location", exc.exception.message_dict)

    def test_worker_update_rejects_invalid_partial_patch(self):
        hr = self.create_user("hr4", Role.HR)
        logist = self.create_user(
            "logist2",
            Role.LOGIST,
            email="logist2@example.com",
            phone="+380991112239",
            region=self.region,
        )

        self.client.force_authenticate(user=hr)
        response = self.client.patch(
            f"/workers/{logist.pk}/",
            {"region": None},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("region", response.data)

    def test_worker_register_rejects_duplicate_email(self):
        hr = self.create_user("hr5", Role.HR)
        self.create_user(
            "postal2",
            Role.POSTAL_WORKER,
            email="duplicate@example.com",
            phone="+380991112240",
            location=self.post_office,
        )

        self.client.force_authenticate(user=hr)
        response = self.client.post(
            "/workers/",
            {
                "username": "postal3",
                "first_name": "P",
                "last_name": "W",
                "patronymic": "Test",
                "email": "duplicate@example.com",
                "phone": "+380991112241",
                "role": Role.POSTAL_WORKER,
                "location": self.post_office.pk,
                "password": "StrongPass123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_me_endpoint_returns_current_user(self):
        user = self.create_user(
            "me_user",
            Role.LOGIST,
            email="me_user@example.com",
            phone="+380991112242",
            region=self.region,
        )

        self.client.force_authenticate(user=user)
        response = self.client.get("/me/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "me_user")
        self.assertEqual(response.data["role"], Role.LOGIST)
        self.assertEqual(response.data["region"], self.region.pk)