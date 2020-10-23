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
        self.assertRaises(ValueError, ObjectA.objects.contains, object())

    def test_values_querysets(self):
        """ Make sure .values() and .values_list() QuerySets don't try to use ._result_cache """
        values_qs = ObjectA.objects.values('pk')
        with self.assertNumQueries(3):
            list(values_qs)
            self.assertIs(values_qs.contains(self.existing), True)
            self.assertIs(values_qs.contains(self.not_saved), False)

        with self.assertNumQueries(2):
            values_qs = ObjectA.objects.exclude(pk=self.existing.pk).values_list('pk')
            list(values_qs)
            self.assertIs(values_qs.contains(self.existing), False)
        # These should all be queries to the database

    def test_group_by(self):
        from django.db.models import Count
        a = ObjectA.objects.create(name='a')
        for _ in range(10):
            ObjectA.objects.create(name='b')
        qs = ObjectA.objects.exclude(name='a').values('name').annotate(count=Count('pk')).order_by('name')
        with self.assertNumQueries(3):
            self.assertIs(qs.contains(a), False)
            self.assertEqual(len(qs), 3, 'QuerySet should contain grouped object rows b;four;one')
            self.assertIs(qs.contains(self.existing), True)

    def test_values_list(self):
        qs = ObjectA.objects.values_list('name')
        with self.assertNumQueries(3):
            self.assertEqual(len(qs), 2)  # Evaluates queryset
            self.assertIs(qs.contains(self.existing), True)
            self.assertIs(qs.contains(self.not_saved), False)

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
