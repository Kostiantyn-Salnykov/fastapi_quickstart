import factory

from apps.wishmaster.enums import WishComplexities, WishPriorities, WishStatuses
from apps.wishmaster.models import Category, Tag, Wish, WishList, WishTag
from tests.bases import BaseModelFactory

__all__ = ("CategoryFactory", "TagFactory", "WishTagFactory", "WishListFactory", "WishFactory")


class CategoryFactory(BaseModelFactory):
    title = factory.Faker("pystr", max_chars=128)
    owner_id = factory.SelfAttribute(attribute_name="owner.id")

    owner = factory.SubFactory(factory="tests.apps.CORE.factories.UserFactory")

    class Meta:
        model = Category


class TagFactory(BaseModelFactory):
    title = factory.Faker("pystr", max_chars=64)

    class Meta:
        model = Tag


class WishTagFactory(BaseModelFactory):
    wish_id = factory.SelfAttribute(attribute_name="wish.id")
    tag_id = factory.SelfAttribute(attribute_name="tag.id")

    wish = factory.SubFactory(factory="tests.apps.wishmaster.factories.WishFactory")
    tag = factory.SubFactory(factory=TagFactory)

    class Meta:
        model = WishTag
        exclude = ("wish", "tag")
        sqlalchemy_get_or_create = ("wish_id", "tag_id")


class WishListFactory(BaseModelFactory):
    title = factory.Faker("pystr", max_chars=128)
    owner_id = factory.SelfAttribute(attribute_name="owner.id")

    owner = factory.SubFactory(factory="tests.apps.CORE.factories.UserFactory")

    class Meta:
        model = WishList


class WishFactory(BaseModelFactory):
    title = factory.Faker("pystr", max_chars=128)
    description = factory.Faker("pystr", max_chars=255)
    wishlist_id = factory.SelfAttribute(attribute_name="wishlist.id")
    category_id = factory.SelfAttribute(attribute_name="category.id")
    status = factory.Faker("word", ext_word_list=list(WishStatuses))
    complexity = factory.Faker("word", ext_word_list=list(WishComplexities))
    priority = factory.Faker("word", ext_word_list=list(WishPriorities))

    user = factory.SubFactory(factory="tests.apps.CORE.factories.UserFactory")
    wishlist = factory.SubFactory(factory=WishListFactory, owner=factory.SelfAttribute("..user"))
    category = factory.SubFactory(factory=CategoryFactory, owner=factory.SelfAttribute("..user"))
    tags = factory.RelatedFactoryList(factory=WishTagFactory, factory_related_name="wish", size=3)

    class Meta:
        model = Wish
        exclude = ("user",)
