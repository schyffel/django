from django.test import TestCase
from .models import ChildObjectA, ObjectA, ObjectB, ProxyObjectA


class ContainsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.existing = ObjectA.objects.create(name='one')
        cls.not_saved = ObjectA(name='two')
        cls.wrong_model = ObjectB.objects.create(name='three', objecta=cls.existing, num=1)
        cls.proxy_model_existing = ProxyObjectA.objects.create(name='four')

    def test_non_model(self):
        self.assertRaises(NotImplementedError, ObjectA.objects.contains, object())

    def test_db_queries(self):
        # DB query tests
        self.assertIs(ObjectA.objects.contains(self.existing), True)
        self.assertIs(ObjectA.objects.contains(self.proxy_model_existing), True)
        self.assertIs(ProxyObjectA.objects.contains(self.existing), True)
        self.assertIs(ObjectA.objects.contains(self.wrong_model), False)
        self.assertIs(ObjectA.objects.contains(self.not_saved), False)
        self.assertIs(ChildObjectA.objects.contains(self.existing), False)
        self.assertNumQueries(1, ObjectA.objects.contains, self.existing)
        self.assertNumQueries(0, ChildObjectA.objects.contains, self.existing)

    def test_prefetch(self):
        # Prefetch tests
        all = ObjectA.objects.all()
        child_all = ChildObjectA.objects.all()
        proxy_all = ProxyObjectA.objects.all()
        list(all)
        list(child_all)
        list(proxy_all)
        self.assertIs(all.contains(self.existing), True)
        self.assertIs(all.contains(self.proxy_model_existing), True)
        self.assertIs(proxy_all.contains(self.existing), True)
        self.assertIs(all.contains(self.wrong_model), False)
        self.assertIs(all.contains(self.not_saved), False)
        self.assertIs(child_all.contains(self.existing), False)
        self.assertNumQueries(0, all.contains, self.existing)
