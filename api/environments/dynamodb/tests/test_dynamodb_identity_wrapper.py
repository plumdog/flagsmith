import pytest
from boto3.dynamodb.conditions import Key
from django.core.exceptions import ObjectDoesNotExist
from flag_engine.identities.builders import build_identity_model
from rest_framework.exceptions import NotFound

from environments.dynamodb import DynamoIdentityWrapper
from environments.identities.models import Identity
from segments.models import Segment
from util.mappers import (
    map_environment_to_environment_document,
    map_identity_to_identity_document,
)


def test_get_item_from_uuid_calls_query_with_correct_argument(mocker):
    # Given
    dynamo_identity_wrapper = DynamoIdentityWrapper()
    mocked_dynamo_table = mocker.patch.object(dynamo_identity_wrapper, "_table")
    identity_uuid = "test_uuid"

    # When
    dynamo_identity_wrapper.get_item_from_uuid(identity_uuid)
    # Then
    mocked_dynamo_table.query.assert_called_with(
        IndexName="identity_uuid-index",
        Limit=1,
        KeyConditionExpression=Key("identity_uuid").eq(identity_uuid),
    )


def test_get_item_from_uuid_raises_object_does_not_exists_if_identity_is_not_returned(
    mocker,
):
    # Given
    dynamo_identity_wrapper = DynamoIdentityWrapper()
    mocked_dynamo_table = mocker.patch.object(dynamo_identity_wrapper, "_table")
    mocked_dynamo_table.query.return_value = {"Items": [], "Count": 0}
    # Then
    with pytest.raises(ObjectDoesNotExist):
        dynamo_identity_wrapper.get_item_from_uuid("identity_uuid")


def test_get_item_from_uuid_or_404_calls_get_item_from_uuid_with_correct_arguments(
    mocker,
):
    # Given
    dynamo_identity_wrapper = DynamoIdentityWrapper()
    expected_document = {"key": "value"}
    mocked_get_item_from_uuid = mocker.patch.object(
        dynamo_identity_wrapper, "get_item_from_uuid", return_value=expected_document
    )
    identity_uuid = "test_uuid"

    # When
    returned_document = dynamo_identity_wrapper.get_item_from_uuid_or_404(identity_uuid)

    # Then
    assert returned_document == expected_document
    mocked_get_item_from_uuid.assert_called_with(identity_uuid)


def test_get_item_from_uuid_or_404_calls_raises_not_found_if_internal_method_raises_object_does_not_exists(
    mocker,
):
    # Given
    dynamo_identity_wrapper = DynamoIdentityWrapper()
    mocker.patch.object(
        dynamo_identity_wrapper, "get_item_from_uuid", side_effect=ObjectDoesNotExist
    )
    identity_uuid = "test_uuid"

    # Then
    with pytest.raises(NotFound):
        dynamo_identity_wrapper.get_item_from_uuid_or_404(identity_uuid)


def test_delete_item_calls_dynamo_delete_item_with_correct_arguments(mocker):
    # Given
    dynamo_identity_wrapper = DynamoIdentityWrapper()
    composite_key = "test_key"
    mocked_dynamo_table = mocker.patch.object(dynamo_identity_wrapper, "_table")

    # When
    dynamo_identity_wrapper.delete_item(composite_key)

    # Then
    mocked_dynamo_table.delete_item.assert_called_with(
        Key={"composite_key": composite_key}
    )


def test_get_item_calls_dynamo_get_item_with_correct_arguments(mocker):
    # Given
    dynamo_identity_wrapper = DynamoIdentityWrapper()
    composite_key = "test_key"
    mocked_dynamo_table = mocker.patch.object(dynamo_identity_wrapper, "_table")

    # When
    dynamo_identity_wrapper.get_item(composite_key)

    # Then
    mocked_dynamo_table.get_item.assert_called_with(
        Key={"composite_key": composite_key}
    )


def test_get_all_items_without_start_key_calls_query_with_correct_arguments(mocker):
    # Given
    dynamo_identity_wrapper = DynamoIdentityWrapper()
    environment_key = "environment_key"
    mocked_dynamo_table = mocker.patch.object(dynamo_identity_wrapper, "_table")

    # When
    dynamo_identity_wrapper.get_all_items(environment_key, 999)

    # Then
    mocked_dynamo_table.query.assert_called_with(
        IndexName="environment_api_key-identifier-index",
        Limit=999,
        KeyConditionExpression=Key("environment_api_key").eq(environment_key),
    )


def test_get_all_items_with_start_key_calls_query_with_correct_arguments(mocker):
    # Given
    dynamo_identity_wrapper = DynamoIdentityWrapper()

    environment_key = "environment_key"
    mocked_dynamo_table = mocker.patch.object(dynamo_identity_wrapper, "_table")
    start_key = {"key": "value"}

    # When
    dynamo_identity_wrapper.get_all_items(environment_key, 999, start_key)

    # Then
    mocked_dynamo_table.query.assert_called_with(
        IndexName="environment_api_key-identifier-index",
        Limit=999,
        KeyConditionExpression=Key("environment_api_key").eq(environment_key),
        ExclusiveStartKey=start_key,
    )


def test_search_items_with_identifier_calls_query_with_correct_arguments(mocker):
    dynamo_identity_wrapper = DynamoIdentityWrapper()
    environment_key = "environment_key"
    identifier = "test_user"
    mocked_dynamo_table = mocker.patch.object(dynamo_identity_wrapper, "_table")
    start_key = {"key": "value"}
    search_function = lambda x: Key("identifier").eq(x)  # noqa: E731

    # When
    dynamo_identity_wrapper.search_items_with_identifier(
        environment_key, identifier, search_function, 999, start_key
    )

    # Then
    mocked_dynamo_table.query.assert_called_with(
        IndexName="environment_api_key-identifier-index",
        Limit=999,
        KeyConditionExpression=Key("environment_api_key").eq(environment_key)
        & search_function(identifier),
        ExclusiveStartKey=start_key,
    )


def test_write_identities_calls_internal_methods_with_correct_arguments(
    mocker, project, identity
):
    # Given
    dynamo_identity_wrapper = DynamoIdentityWrapper()
    mocked_dynamo_table = mocker.patch.object(dynamo_identity_wrapper, "_table")

    expected_identity_document = map_identity_to_identity_document(identity)
    identities = Identity.objects.filter(id=identity.id)

    # When
    dynamo_identity_wrapper.write_identities(identities)

    # Then
    mocked_dynamo_table.batch_writer.assert_called_with()

    mocked_put_item = (
        mocked_dynamo_table.batch_writer.return_value.__enter__.return_value.put_item
    )
    _, kwargs = mocked_put_item.call_args
    actual_identity_document = kwargs["Item"]

    # Remove identity_uuid from the document since it will be different
    actual_identity_document.pop("identity_uuid")
    expected_identity_document.pop("identity_uuid")

    assert actual_identity_document == expected_identity_document


def test_write_identities_skips_identity_if_identifier_is_too_large(
    mocker, project, identity
):
    # Given
    dynamo_identity_wrapper = DynamoIdentityWrapper()
    mocked_dynamo_table = mocker.patch.object(dynamo_identity_wrapper, "_table")

    # Let's make the identifier too long
    identity.identifier = "a" * 1025
    identity.save()

    identities = Identity.objects.filter(id=identity.id)

    # When
    dynamo_identity_wrapper.write_identities(identities)

    # Then
    mocked_dynamo_table.batch_writer.assert_called_with()
    mocked_dynamo_table.batch_writer.return_value.__enter__.return_value.put_item.assert_not_called()


def test_is_enabled_is_false_if_dynamo_table_name_is_not_set(settings, mocker):
    # Given
    mocker.patch(
        "environments.dynamodb.dynamodb_wrapper.DynamoIdentityWrapper.table_name",
        None,
    )

    mocked_boto3 = mocker.patch("environments.dynamodb.dynamodb_wrapper.boto3")
    # When
    dynamo_identity_wrapper = DynamoIdentityWrapper()

    # Then
    assert dynamo_identity_wrapper.is_enabled is False
    mocked_boto3.resource.assert_not_called()
    mocked_boto3.resource.return_value.Table.assert_not_called()


def test_is_enabled_is_true_if_dynamo_table_name_is_set(settings, mocker):
    # Given
    table_name = "random_table_name"
    mocker.patch(
        "environments.dynamodb.dynamodb_wrapper.DynamoIdentityWrapper.table_name",
        table_name,
    )
    mocked_boto3 = mocker.patch("environments.dynamodb.dynamodb_wrapper.boto3")

    # When
    dynamo_identity_wrapper = DynamoIdentityWrapper()
    # Then

    assert dynamo_identity_wrapper.is_enabled is True
    mocked_boto3.resource.assert_called_with("dynamodb")
    mocked_boto3.resource.return_value.Table.assert_called_with(table_name)


def test_get_segment_ids_returns_correct_segment_ids(
    project, environment, identity, identity_matching_segment, mocker
):
    # Given - two segments (one that matches the identity and one that does not)
    Segment.objects.create(name="Non matching segment", project=project)

    identity_document = map_identity_to_identity_document(identity)
    dynamo_identity_wrapper = DynamoIdentityWrapper()
    mocked_get_item_from_uuid = mocker.patch.object(
        dynamo_identity_wrapper, "get_item_from_uuid", return_value=identity_document
    )
    identity_uuid = identity_document["identity_uuid"]

    environment_document = map_environment_to_environment_document(environment)
    mocked_environment_wrapper = mocker.patch(
        "environments.dynamodb.dynamodb_wrapper.DynamoEnvironmentWrapper"
    )
    mocked_environment_wrapper.return_value.get_item.return_value = environment_document

    # When
    segment_ids = dynamo_identity_wrapper.get_segment_ids(identity_uuid)

    # Then
    assert segment_ids == [identity_matching_segment.id]
    mocked_get_item_from_uuid.assert_called_with(identity_uuid)
    mocked_environment_wrapper.return_value.get_item.assert_called_with(
        environment.api_key
    )


def test_get_segment_ids_returns_empty_list_if_identity_does_not_exists(
    project, environment, identity, mocker
):
    # Given
    identity_document = map_identity_to_identity_document(identity)
    dynamo_identity_wrapper = DynamoIdentityWrapper()
    mocker.patch.object(
        dynamo_identity_wrapper, "get_item_from_uuid", side_effect=ObjectDoesNotExist
    )
    identity_uuid = identity_document["identity_uuid"]

    # Then
    segment_ids = dynamo_identity_wrapper.get_segment_ids(identity_uuid)

    # Then
    assert segment_ids == []


def test_get_segment_ids_throws_value_error_if_no_arguments():
    # Given
    dynamo_identity_wrapper = DynamoIdentityWrapper()

    # When
    with pytest.raises(ValueError):
        dynamo_identity_wrapper.get_segment_ids()

    # Then
    # exception raised


def test_get_segment_ids_throws_value_error_if_arguments_not_valid():
    # Given
    dynamo_identity_wrapper = DynamoIdentityWrapper()

    # When
    with pytest.raises(ValueError):
        dynamo_identity_wrapper.get_segment_ids(None)

    # Then
    # exception raised


def test_get_segment_ids_with_identity_model(identity, environment, mocker):
    # Given
    dynamo_identity_wrapper = DynamoIdentityWrapper()
    identity_document = map_identity_to_identity_document(identity)
    identity_model = build_identity_model(identity_document)

    mocker.patch.object(
        dynamo_identity_wrapper, "get_item_from_uuid", return_value=identity_document
    )

    environment_document = map_environment_to_environment_document(environment)
    mocked_environment_wrapper = mocker.patch(
        "environments.dynamodb.dynamodb_wrapper.DynamoEnvironmentWrapper"
    )
    mocked_environment_wrapper.return_value.get_item.return_value = environment_document

    # When
    segment_ids = dynamo_identity_wrapper.get_segment_ids(identity_model=identity_model)

    # Then
    assert segment_ids == []
