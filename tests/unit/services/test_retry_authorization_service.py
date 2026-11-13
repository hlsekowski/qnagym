"""Unit tests for the retry authorization service."""

from qnagym.contracts.retry_authorization import (
    AuthorizationConfig,
    AuthorizedAccount,
    FeedbackSource,
)
from qnagym.services import retry_authorization as ras


class TestCreateAuthorizationConfig:
    def test_create_default_config(self):
        config = ras.create_authorization_config()
        assert len(config.authorized_accounts) == 0
        assert config.require_owner_for_retry is False

    def test_create_with_accounts(self):
        config = ras.create_authorization_config(
            authorized_accounts=[
                {
                    "account_id": "user1",
                    "account_type": "owner",
                    "login": "owner",
                }
            ],
            require_owner_for_retry=True,
        )
        assert len(config.authorized_accounts) == 1
        assert config.require_owner_for_retry


class TestParseCommentForRetry:
    def test_parse_retry_request(self):
        request = ras.parse_comment_for_retry("/retry fix the lint")
        assert request.is_retry_request
        assert request.reason == "fix the lint"

    def test_parse_not_retry(self):
        request = ras.parse_comment_for_retry("hello")
        assert not request.is_retry_request


class TestCheckCommentIsWorkflowAuthored:
    def test_workflow_comment(self):
        assert ras.check_comment_is_workflow_authored("<!-- qnagym-workflow --> body")

    def test_regular_comment(self):
        assert not ras.check_comment_is_workflow_authored("hello")


class TestClassifyFeedback:
    def test_classify_owner_comment(self):
        source = ras.classify_feedback(
            "owner_comment",
            "user1",
            "owner",
            "c1",
            False,
        )
        assert source.source_type == "owner_comment"
        assert not source.is_workflow_authored


class TestCheckFeedbackEligible:
    def test_eligible(self):
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
        assert ras.check_feedback_eligible(source, config)

    def test_not_eligible_workflow_authored(self):
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
        assert not ras.check_feedback_eligible(source, config)


class TestCheckAccountCanTriggerRetry:
    def test_can_trigger(self):
        config = AuthorizationConfig(
            authorized_accounts=[
                AuthorizedAccount(
                    account_id="user1",
                    account_type="owner",
                    login="owner",
                )
            ],
        )
        assert ras.can_account_trigger_retry(config, "user1")

    def test_cannot_trigger_unauthorized(self):
        config = AuthorizationConfig(
            authorized_accounts=[
                AuthorizedAccount(
                    account_id="user1",
                    account_type="owner",
                    login="owner",
                )
            ],
        )
        assert not ras.can_account_trigger_retry(config, "user2")


class TestCheckAccountIsAuthorized:
    def test_authorized(self):
        config = AuthorizationConfig(
            authorized_accounts=[
                AuthorizedAccount(
                    account_id="user1",
                    account_type="owner",
                    login="owner",
                )
            ],
        )
        assert ras.check_account_is_authorized(config, "user1")
        assert not ras.check_account_is_authorized(config, "user2")


class TestCheckAccountIsOwner:
    def test_owner(self):
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
        assert ras.check_account_is_owner(config, "user1")
        assert not ras.check_account_is_owner(config, "user2")
