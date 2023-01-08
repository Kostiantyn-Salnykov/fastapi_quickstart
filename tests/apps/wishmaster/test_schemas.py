from apps.wishmaster.models import Tag
from apps.wishmaster.schemas import WishOutSchema


class TestWishOutSchema:
    def test_validate_tag(self) -> None:
        tags = ["test", Tag(title="Test2"), "#atata"]
        expected_result = ["test", "Test2", "#atata"]

        result = WishOutSchema.validate_tag(v=tags)

        assert result == expected_result
