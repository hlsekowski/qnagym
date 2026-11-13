"""Unit tests for retry authorization contracts."""

from qnagym.contracts.retry_authorization import (
    ACCOUNT_TYPE_AUTOMATED_REVIEWER,
    ACCOUNT_TYPE_COLLABORATOR,
    ACCOUNT_TYPE_OWNER,
    WORKFLOW_COMMENT_MARKER,
    AuthorizationConfig,
    AuthorizedAccount,
    FeedbackSource,
    RetryRequest,
)


class TestRetryRequest:
    def test_retry_request_roundtrip(self):
        request = RetryRequest(
            is_retry_request=True,
            reason="fix the lint failure",
            raw_comment="/retry fix the lint failure",
        )
        assert RetryRequest.from_dict(request.to_dict()) == request

    def test_not_a_retry_request(self):
        request = RetryRequest(
            is_retry_request=False,
            reason=None,
            raw_comment="just a regular comment",
        )
        assert not request.is_retry_request
        assert request.reason is None


class TestAuthorizationConfig:
    def test_config_roundtrip(self):
        config = AuthorizationConfig(
            authorized_accounts=[
                AuthorizedAccount(
                    account_id="user1",
                    account_type="owner",
                    login="owner",
                )
            ],
            eligible_feedback_sources=frozenset({"owner_comment"}),
            require_owner_for_retry=True,
        )
        assert AuthorizationConfig.from_dict(config.to_dict()) == config

    def test_is_authorized(self):
        config = AuthorizationConfig(
            authorized_accounts=[
                AuthorizedAccount(
                    account_id="user1",
                    account_type="owner",
                    login="owner",
                )
            ],
        )
        assert config.is_authorized("user1")
        assert not config.is_authorized("user2")

    def test_is_owner(self):
        config = AuthorizationConfig(
            authorized_accounts=[
                AuthorizedAccount(
                    account_id="user1",
                    account_type="owner",
                    login="owner",
                ),
                AuthorizedAccount(
                    account_id="user2",
                    account_type="collaborator",
                    login="collab",
                ),
            ],
        )
        assert config.is_owner("user1")
        assert not config.is_owner("user2")

    def test_can_trigger_retry_any_authorized(self):
        config = AuthorizationConfig(
            authorized_accounts=[
                AuthorizedAccount(
                    account_id="user1",
                    account_type="collaborator",
                    login="collab",
                )
            ],
            require_owner_for_retry=False,
        )
        assert config.can_trigger_retry("user1")
        assert not config.can_trigger_retry("user2")

    def test_can_trigger_retry_owner_only(self):
        config = AuthorizationConfig(
            authorized_accounts=[
                AuthorizedAccount(
                    account_id="user1",
                    account_type="owner",
                    login="owner",
                ),
                AuthorizedAccount(
                    account_id="user2",
                    account_type="collaborator",
                    login="collab",
                ),
            ],
            require_owner_for_retry=True,
        )
        assert config.can_trigger_retry("user1")
        assert not config.can_trigger_retry("user2")

    def test_is_feedback_source_eligible(self):
        config = AuthorizationConfig(
            eligible_feedback_sources=frozenset({"owner_comment"}),
        )
        assert config.is_feedback_source_eligible("owner_comment")
        assert not config.is_feedback_source_eligible("automated_reviewer")


class TestFeedbackSource:
    def test_feedback_source_roundtrip(self):
        source = FeedbackSource(
            source_type="owner_comment",
            account_id="user1",
            account_login="owner",
            comment_id="c1",
            is_workflow_authored=False,
        )
        assert FeedbackSource.from_dict(source.to_dict()) == source

    def test_is_eligible_not_workflow_authored(self):
        source = FeedbackSource(
            source_type="owner_comment",
            account_id="user1",
            account_login="owner",
            comment_id="c1",
            is_workflow_authored=False,
        )
        config = AuthorizationConfig(
            eligible_feedback_sources=frozenset({"owner_comment"}),
        )
        assert source.is_eligible(config)

    def test_is_eligible_workflow_authored_not_eligible(self):
        source = FeedbackSource(
            source_type="owner_comment",
            account_id="user1",
            account_login="owner",
            comment_id="c1",
            is_workflow_authored=True,
        )
        config = AuthorizationConfig(
            eligible_feedback_sources=frozenset({"owner_comment"}),
        )
        assert not source.is_eligible(config)


class TestConstants:
    def test_workflow_marker(self):
        assert WORKFLOW_COMMENT_MARKER == "<!-- qnagym-workflow -->"

    def test_account_types(self):
        assert ACCOUNT_TYPE_OWNER == "owner"
        assert ACCOUNT_TYPE_COLLABORATOR == "collaborator"
        assert ACCOUNT_TYPE_AUTOMATED_REVIEWER == "automated_revisor"
