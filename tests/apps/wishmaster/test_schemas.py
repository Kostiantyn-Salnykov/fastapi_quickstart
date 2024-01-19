from apps.wishmaster.schemas import WishResponseSchema
from apps.wishmaster.tables import Tag


class TestWishOutSchema:
    def test_validate_tag(self) -> None:
        tags = ["test", Tag(title="Test2"), "#atata"]
        expected_result = ["test", "Test2", "#atata"]

        result = WishResponseSchema.validate_tag(v=tags)

        assert result == expected_result
