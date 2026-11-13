"""Unit tests for the retry authorization domain logic."""

from qnagym.contracts.retry_authorization import (
    AuthorizationConfig,
    AuthorizedAccount,
    FeedbackSource,
)
from qnagym.domain.retry_authorization import (
    can_account_trigger_retry,
    classify_feedback_source,
    is_account_authorized,
    is_account_owner,
    is_feedback_eligible,
    is_workflow_comment,
    parse_retry_request,
)


def _config(
    authorized_accounts=None,
    eligible_feedback_sources=None,
    require_owner_for_retry=False,
):
    return AuthorizationConfig(
        authorized_accounts=authorized_accounts or [],
        eligible_feedback_sources=(
            frozenset(eligible_feedback_sources) if eligible_feedback_sources else None
        ),
        require_owner_for_retry=require_owner_for_retry,
    )


class TestParseRetryRequest:
    def test_retry_request_with_reason(self):
        request = parse_retry_request("/retry fix the lint failure")
        assert request.is_retry_request
        assert request.reason == "fix the lint failure"
        assert request.raw_comment == "/retry fix the lint failure"

    def test_retry_request_without_reason(self):
        request = parse_retry_request("/retry")
        assert request.is_retry_request
        assert request.reason is None
        assert request.raw_comment == "/retry"

    def test_retry_request_with_extra_whitespace(self):
        request = parse_retry_request("  /retry   reason here  ")
        assert request.is_retry_request
        assert request.reason == "reason here"

    def test_not_a_retry_request(self):
        request = parse_retry_request("just a regular comment")
        assert not request.is_retry_request
        assert request.reason is None

    def test_empty_comment(self):
        request = parse_retry_request("")
        assert not request.is_retry_request
        assert request.reason is None


class TestIsWorkflowComment:
    def test_workflow_comment_detected(self):
        assert is_workflow_comment("<!-- qnagym-workflow --> some body")

    def test_regular_comment_not_workflow(self):
        assert not is_workflow_comment("just a regular comment")

    def test_empty_comment(self):
        assert not is_workflow_comment("")


class TestClassifyFeedbackSource:
    def test_classify_owner_comment(self):
        source = classify_feedback_source(
            "owner_comment",
            "user1",
            "owner",
            "c1",
            False,
        )
        assert source.source_type == "owner_comment"
        assert source.account_id == "user1"
        assert source.account_login == "owner"
        assert source.comment_id == "c1"
        assert not source.is_workflow_authored

    def test_classify_workflow_authored(self):
        source = classify_feedback_source(
            "owner_comment",
            "workflow",
            "workflow",
            "c2",
            True,
        )
        assert source.is_workflow_authored


class TestIsFeedbackEligible:
    def test_eligible_source(self):
        source = FeedbackSource(
            source_type="owner_comment",
            account_id="user1",
            account_login="owner",
            comment_id="c1",
            is_workflow_authored=False,
        )
        config = _config(
            eligible_feedback_sources=["owner_comment"],
        )
        assert is_feedback_eligible(source, config)

    def test_ineligible_source(self):
        source = FeedbackSource(
            source_type="automated_reviewer",
            account_id=None,
            account_login=None,
            comment_id="c2",
            is_workflow_authored=False,
        )
        config = _config(
            eligible_feedback_sources=["owner_comment"],
        )
        assert not is_feedback_eligible(source, config)

    def test_workflow_authored_not_eligible(self):
        source = FeedbackSource(
            source_type="owner_comment",
            account_id="user1",
            account_login="owner",
            comment_id="c1",
            is_workflow_authored=True,
        )
        config = _config(
            eligible_feedback_sources=["owner_comment"],
        )
        assert not is_feedback_eligible(source, config)


class TestCanAccountTriggerRetry:
    def test_authorized_account_can_trigger(self):
        config = AuthorizationConfig(
            authorized_accounts=[
                AuthorizedAccount(
                    account_id="user1",
                    account_type="owner",
                    login="owner",
                )
            ],
            require_owner_for_retry=False,
        )
        assert can_account_trigger_retry(config, "user1")

    def test_unauthorized_account_cannot_trigger(self):
        config = AuthorizationConfig(
            authorized_accounts=[
                AuthorizedAccount(
                    account_id="user1",
                    account_type="owner",
                    login="owner",
                )
            ],
        )
        assert not can_account_trigger_retry(config, "user2")

    def test_owner_only_mode_non_owner_cannot_trigger(self):
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
        assert can_account_trigger_retry(config, "user1")
        assert not can_account_trigger_retry(config, "user2")


class TestIsAccountAuthorized:
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
        assert is_account_authorized(config, "user1")
        assert not is_account_authorized(config, "user2")


class TestIsAccountOwner:
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
        assert is_account_owner(config, "user1")
        assert not is_account_owner(config, "user2")
