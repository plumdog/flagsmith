import json
import random

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from pytest_lazyfixture import lazy_fixture
from rest_framework import status

from audit.models import AuditLog
from audit.related_object_type import RelatedObjectType
from environments.models import Environment
from features.models import Feature
from segments.models import EQUAL, Condition, Segment, SegmentRule
from util.mappers import map_identity_to_identity_document

User = get_user_model()


@pytest.mark.parametrize(
    "client", [lazy_fixture("master_api_key_client"), lazy_fixture("admin_client")]
)
def test_can_filter_by_identity_to_get_only_matching_segments(
    project, client, environment, identity, trait, identity_matching_segment, segment
):
    # Given
    base_url = reverse("api-v1:projects:project-segments-list", args=[project.id])
    url = base_url + "?identity=%d" % identity.id

    # When
    res = client.get(url)

    # Then
    assert res.json().get("count") == 1


@pytest.mark.parametrize(
    "client", [lazy_fixture("master_api_key_client"), lazy_fixture("admin_client")]
)
def test_cannot_create_segments_without_rules(project, client):
    # Given
    url = reverse("api-v1:projects:project-segments-list", args=[project.id])
    data = {"name": "New segment name", "project": project.id, "rules": []}

    # When
    res = client.post(url, data=json.dumps(data), content_type="application/json")

    # Then
    assert res.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.parametrize(
    "client", [lazy_fixture("master_api_key_client"), lazy_fixture("admin_client")]
)
def test_can_create_segments_with_boolean_condition(project, client):
    # Given
    url = reverse("api-v1:projects:project-segments-list", args=[project.id])
    data = {
        "name": "New segment name",
        "project": project.id,
        "rules": [
            {
                "type": "ALL",
                "rules": [],
                "conditions": [
                    {"operator": EQUAL, "property": "test-property", "value": True}
                ],
            }
        ],
    }

    # When
    res = client.post(url, data=json.dumps(data), content_type="application/json")

    # Then
    assert res.status_code == status.HTTP_201_CREATED


@pytest.mark.parametrize(
    "client", [lazy_fixture("master_api_key_client"), lazy_fixture("admin_client")]
)
def test_can_create_segments_with_condition_that_has_null_value(project, client):
    # Given
    url = reverse("api-v1:projects:project-segments-list", args=[project.id])
    data = {
        "name": "New segment name",
        "project": project.id,
        "rules": [
            {
                "type": "ALL",
                "rules": [],
                "conditions": [{"operator": EQUAL, "property": "test-property"}],
            }
        ],
    }

    # When
    res = client.post(url, data=json.dumps(data), content_type="application/json")

    # Then
    assert res.status_code == status.HTTP_201_CREATED


@pytest.mark.parametrize(
    "client", [lazy_fixture("master_api_key_client"), lazy_fixture("admin_client")]
)
def test_audit_log_created_when_segment_updated(project, segment, client):
    # Given
    segment = Segment.objects.create(name="Test segment", project=project)
    url = reverse(
        "api-v1:projects:project-segments-detail",
        args=[project.id, segment.id],
    )
    data = {
        "name": "New segment name",
        "project": project.id,
        "rules": [{"type": "ALL", "rules": [], "conditions": []}],
    }

    # When
    res = client.put(url, data=json.dumps(data), content_type="application/json")

    # Then
    assert res.status_code == status.HTTP_200_OK
    assert (
        AuditLog.objects.filter(
            related_object_type=RelatedObjectType.SEGMENT.name
        ).count()
        == 1
    )


@pytest.mark.parametrize(
    "client", [lazy_fixture("master_api_key_client"), lazy_fixture("admin_client")]
)
def test_audit_log_created_when_segment_created(project, client):
    # Given
    url = reverse("api-v1:projects:project-segments-list", args=[project.id])
    data = {
        "name": "Test Segment",
        "project": project.id,
        "rules": [{"type": "ALL", "rules": [], "conditions": []}],
    }

    # When
    res = client.post(url, data=json.dumps(data), content_type="application/json")

    # Then
    assert res.status_code == status.HTTP_201_CREATED
    assert (
        AuditLog.objects.filter(
            related_object_type=RelatedObjectType.SEGMENT.name
        ).count()
        == 1
    )


@pytest.mark.parametrize(
    "client", [lazy_fixture("master_api_key_client"), lazy_fixture("admin_client")]
)
def test_can_filter_by_edge_identity_to_get_only_matching_segments(
    project,
    environment,
    identity,
    identity_matching_segment,
    edge_identity_dynamo_wrapper_mock,
    client,
):
    # Given
    Segment.objects.create(name="Non matching segment", project=project)
    expected_segment_ids = [identity_matching_segment.id]
    identity_document = map_identity_to_identity_document(identity)
    identity_uuid = identity_document["identity_uuid"]

    edge_identity_dynamo_wrapper_mock.get_segment_ids.return_value = (
        expected_segment_ids
    )

    base_url = reverse("api-v1:projects:project-segments-list", args=[project.id])
    url = f"{base_url}?identity={identity_uuid}"

    # When
    response = client.get(url)

    # Then
    assert response.json().get("count") == len(expected_segment_ids)
    assert response.json()["results"][0]["id"] == expected_segment_ids[0]
    edge_identity_dynamo_wrapper_mock.get_segment_ids.assert_called_with(identity_uuid)


@pytest.mark.parametrize(
    "client", [lazy_fixture("master_api_key_client"), lazy_fixture("admin_client")]
)
def test_associated_features_returns_all_the_associated_features(
    project, environment, feature, segment, segment_featurestate, client
):
    # Given
    # Firstly, let's create extra environment and feature to make sure we
    # have some features that are not associated with the segment
    Environment.objects.create(name="Another environment", project=project)
    Feature.objects.create(name="another feature", project=project)

    url = reverse(
        "api-v1:projects:project-segments-associated-features",
        args=[project.id, segment.id],
    )
    # When
    response = client.get(url)

    # Then
    assert response.json().get("count") == 1
    assert response.json()["results"][0]["id"] == segment_featurestate.id
    assert response.json()["results"][0]["feature"] == feature.id
    assert response.json()["results"][0]["environment"] == environment.id


@pytest.mark.parametrize(
    "client", [lazy_fixture("master_api_key_client"), lazy_fixture("admin_client")]
)
def test_can_create_feature_based_segment(project, client, feature):
    # Given
    url = reverse("api-v1:projects:project-segments-list", args=[project.id])
    data = {
        "name": "Test Segment",
        "project": project.id,
        "feature": feature.id,
        "rules": [{"type": "ALL", "rules": [], "conditions": []}],
    }

    # When
    res = client.post(url, data=json.dumps(data), content_type="application/json")

    # Then
    assert res.status_code == status.HTTP_201_CREATED
    assert res.json()["feature"] == feature.id


@pytest.mark.parametrize(
    "client", [lazy_fixture("master_api_key_client"), lazy_fixture("admin_client")]
)
def test_get_segment_by_uuid(client, project, segment):
    # Given
    url = reverse("api-v1:segments:get-segment-by-uuid", args=[segment.uuid])

    # When
    response = client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    assert response.json()["id"] == segment.id
    assert response.json()["uuid"] == str(segment.uuid)


@pytest.mark.parametrize(
    "client, num_queries",
    [(lazy_fixture("master_api_key_client"), 11), (lazy_fixture("admin_client"), 10)],
)
def test_list_segments(django_assert_num_queries, project, client, num_queries):
    # Given
    num_segments = 5
    segments = []
    for i in range(num_segments):
        segment = Segment.objects.create(project=project, name=f"segment {i}")
        all_rule = SegmentRule.objects.create(
            segment=segment, type=SegmentRule.ALL_RULE
        )
        any_rule = SegmentRule.objects.create(rule=all_rule, type=SegmentRule.ANY_RULE)
        Condition.objects.create(
            property="foo", value=str(random.randint(0, 10)), rule=any_rule
        )
        segments.append(segment)

    # When
    with django_assert_num_queries(num_queries):
        # TODO: improve this
        #  I've removed the N+1 issue using prefetch related but there is still an overlap on permission checks
        #  and we can probably use varying serializers for the segments since we only allow certain structures via
        #  the UI (but the serializers allow for infinite nesting)
        response = client.get(
            reverse("api-v1:projects:project-segments-list", args=[project.id])
        )

    # Then
    assert response.status_code == status.HTTP_200_OK

    response_json = response.json()
    assert response_json["count"] == num_segments


@pytest.mark.parametrize(
    "client", [lazy_fixture("master_api_key_client"), lazy_fixture("admin_client")]
)
def test_search_segments(django_assert_num_queries, project, client):
    # Given
    segments = []
    segment_names = ["segment one", "segment two"]

    for segment_name in segment_names:
        segment = Segment.objects.create(project=project, name=segment_name)
        all_rule = SegmentRule.objects.create(
            segment=segment, type=SegmentRule.ALL_RULE
        )
        any_rule = SegmentRule.objects.create(rule=all_rule, type=SegmentRule.ANY_RULE)
        Condition.objects.create(
            property="foo", value=str(random.randint(0, 10)), rule=any_rule
        )
        segments.append(segment)

    url = "%s?q=%s" % (
        reverse("api-v1:projects:project-segments-list", args=[project.id]),
        segment_names[0].split()[1],
    )

    # When
    response = client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    response_json = response.json()
    assert response_json["count"] == 1
    assert response_json["results"][0]["name"] == segment_names[0]


@pytest.mark.parametrize(
    "client", [lazy_fixture("master_api_key_client"), lazy_fixture("admin_client")]
)
def test_create_segments_with_description_condition(project, client):
    # Given
    url = reverse("api-v1:projects:project-segments-list", args=[project.id])
    data = {
        "name": "New segment name",
        "project": project.id,
        "rules": [
            {
                "type": "ALL",
                "rules": [],
                "conditions": [
                    {
                        "operator": EQUAL,
                        "property": "test-property",
                        "value": True,
                        "description": "test-description",
                    }
                ],
            }
        ],
    }

    # When
    response = client.post(url, data=json.dumps(data), content_type="application/json")

    # Then
    segment_condition_description_value = response.json()["rules"][0]["conditions"][0][
        "description"
    ]
    assert segment_condition_description_value == "test-description"


@pytest.mark.parametrize(
    "client", [lazy_fixture("master_api_key_client"), lazy_fixture("admin_client")]
)
def test_update_segment_add_new_condition(project, client, segment, segment_rule):
    # Given
    url = reverse(
        "api-v1:projects:project-segments-detail", args=[project.id, segment.id]
    )
    nested_rule = SegmentRule.objects.create(
        rule=segment_rule, type=SegmentRule.ANY_RULE
    )
    existing_condition = Condition.objects.create(
        rule=nested_rule, property="foo", operator=EQUAL, value="bar"
    )

    new_condition_property = "foo2"
    new_condition_value = "bar"
    data = {
        "name": segment.name,
        "project": project.id,
        "rules": [
            {
                "id": segment_rule.id,
                "type": segment_rule.type,
                "rules": [
                    {
                        "id": nested_rule.id,
                        "type": nested_rule.type,
                        "rules": [],
                        "conditions": [
                            # existing condition
                            {
                                "id": existing_condition.id,
                                "property": existing_condition.property,
                                "operator": existing_condition.operator,
                                "value": existing_condition.value,
                            },
                            # new condition
                            {
                                "property": new_condition_property,
                                "operator": EQUAL,
                                "value": new_condition_value,
                            },
                        ],
                    }
                ],
                "conditions": [],
            }
        ],
    }

    # When
    response = client.put(url, data=json.dumps(data), content_type="application/json")

    # Then
    assert response.status_code == status.HTTP_200_OK

    assert nested_rule.conditions.count() == 2
    assert (
        nested_rule.conditions.order_by("-id").first().property
        == new_condition_property
    )
    assert nested_rule.conditions.order_by("-id").first().value == new_condition_value


@pytest.mark.parametrize(
    "client", [lazy_fixture("master_api_key_client"), lazy_fixture("admin_client")]
)
def test_update_segment_delete_existing_condition(
    project, client, segment, segment_rule
):
    # Given
    url = reverse(
        "api-v1:projects:project-segments-detail", args=[project.id, segment.id]
    )
    nested_rule = SegmentRule.objects.create(
        rule=segment_rule, type=SegmentRule.ANY_RULE
    )
    existing_condition = Condition.objects.create(
        rule=nested_rule, property="foo", operator=EQUAL, value="bar"
    )

    data = {
        "name": segment.name,
        "project": project.id,
        "rules": [
            {
                "id": segment_rule.id,
                "type": segment_rule.type,
                "rules": [
                    {
                        "id": nested_rule.id,
                        "type": nested_rule.type,
                        "rules": [],
                        "conditions": [
                            {
                                "id": existing_condition.id,
                                "property": existing_condition.property,
                                "operator": existing_condition.operator,
                                "value": existing_condition.value,
                                "delete": True,
                            },
                        ],
                    }
                ],
                "conditions": [],
            }
        ],
    }

    # When
    response = client.put(url, data=json.dumps(data), content_type="application/json")

    # Then
    assert response.status_code == status.HTTP_200_OK

    assert nested_rule.conditions.count() == 0


@pytest.mark.parametrize(
    "client", [lazy_fixture("master_api_key_client"), lazy_fixture("admin_client")]
)
def test_update_segment_delete_existing_rule(project, client, segment, segment_rule):
    # Given
    url = reverse(
        "api-v1:projects:project-segments-detail", args=[project.id, segment.id]
    )
    nested_rule = SegmentRule.objects.create(
        rule=segment_rule, type=SegmentRule.ANY_RULE
    )

    data = {
        "name": segment.name,
        "project": project.id,
        "rules": [
            {
                "id": segment_rule.id,
                "type": segment_rule.type,
                "rules": [
                    {
                        "id": nested_rule.id,
                        "type": nested_rule.type,
                        "rules": [],
                        "conditions": [],
                    }
                ],
                "conditions": [],
                "delete": True,
            }
        ],
    }

    # When
    response = client.put(url, data=json.dumps(data), content_type="application/json")

    # Then
    assert response.status_code == status.HTTP_200_OK

    assert segment_rule.conditions.count() == 0
