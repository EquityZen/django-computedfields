from django.db import models
from computedfields.models import ComputedFieldsModel, computed
from typing import cast


class Foo(ComputedFieldsModel):
    name: 'models.CharField[str, str]' = models.CharField(max_length=32)

    @computed(
        cast('models.CharField[str, str]', models.CharField(max_length=32)),
        depends=[('bar_set.baz_set', ['name'])]
    )
    def bazzes(self) -> str:
        # note - the slice here is needed to get proper compare between
        # loop and bulk/fast mode in updatedata
        # background: bulk_update and fast_update do not raise on values not
        # fitting into columns of smaller size, instead silently truncating values,
        # thus a later checkdata run always reports desync values
        # (db value always != python calculated value)
        # --> created django ticket: https://code.djangoproject.com/ticket/33647
        # TODO: Do we need a warning about the silent truncation in the docs?
        return ', '.join(Baz.objects.filter(
            bar__foo=self).values_list('name', flat=True))[:32]

    def __str__(self) -> str:
        return self.name


class Bar(ComputedFieldsModel):
    name: 'models.CharField[str, str]' = models.CharField(max_length=32)
    foo: 'models.ForeignKey[Foo, Foo]' = models.ForeignKey(Foo, on_delete=models.CASCADE)

    @computed(
        cast('models.CharField[str, str]', models.CharField(max_length=32)),
        depends=[
            ('self', ['name']),
            ('foo', ['name'])
        ],
        select_related = ['foo']
    )
    def foo_bar(self) -> str:
        return self.foo.name + self.name

    def __str__(self) -> str:
        return self.name


class Baz(ComputedFieldsModel):
    name: 'models.CharField[str, str]' = models.CharField(max_length=32)
    bar: 'models.ForeignKey[Bar, Bar]' = models.ForeignKey(Bar, on_delete=models.CASCADE)

    @computed(
        cast('models.CharField[str, str]', models.CharField(max_length=32)),
        depends=[
            ('self', ['name']),
            ('bar', ['foo_bar'])
        ],
        select_related = ['bar']
    )
    def foo_bar_baz(self) -> str:
        return self.bar.foo_bar + self.name

    def __str__(self) -> str:
        return self.name


class SelfRef(ComputedFieldsModel):
    name: 'models.CharField[str, str]' = models.CharField(max_length=32)
    xy: 'models.IntegerField[int, int]' = models.IntegerField(default=0)

    @computed(
        cast('models.CharField[str, str]', models.CharField(max_length=32)),
        depends=[('self', ['name'])]
    )
    def c1(self) -> str:
        return self.name.upper()

    @computed(
        cast('models.CharField[str, str]', models.CharField(max_length=32)),
        depends=[('self', ['c1'])]
    )
    def c2(self) -> str:
        return 'c2' + self.c1

    @computed(
        cast('models.CharField[str, str]', models.CharField(max_length=32, default='')),
        depends=[('self', ['c1'])]
    )
    def c3(self) -> str:
        return 'c3' + self.c1

    @computed(
        cast('models.CharField[str, str]', models.CharField(max_length=32, default='')),
        depends=[('self', ['c3'])]
    )
    def c4(self) -> str:
        return 'c4' + self.c3

    @computed(
        cast('models.CharField[str, str]', models.CharField(max_length=32, default='')),
        depends=[('self', ['c2', 'c4', 'c6'])]
    )
    def c5(self) -> str:
        return 'c5' + self.c2 + self.c4 + self.c6

    @computed(
        cast('models.CharField[str, str]', models.CharField(max_length=32, default='')),
        depends=[('self', ['xy'])]
    )
    def c6(self) -> str:
        return 'c6' + str(self.xy)

    @computed(
        cast('models.CharField[str, str]', models.CharField(max_length=32, default='')),
        depends=[('self', ['c8'])]
    )
    def c7(self) -> str:
        return 'c7' + self.c8

    @computed(
        cast('models.CharField[str, str]', models.CharField(max_length=32, default='')),
        depends=[]
    )
    def c8(self) -> str:
        return 'c8'
