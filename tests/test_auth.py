from app.auth import merge_request_with_claims


def test_claim_mapping_overrides_identity_fields():
    payload = {
        "user_id": "body-user",
        "role": "billing",
        "tenant_id": "t-1",
        "purpose_of_use": "operations",
        "attributes": {"env": "dev"},
        "context": {},
        "patient_context": {},
    }
    claims = {
        "sub": "jwt-user",
        "role": "clinician",
        "tenant_id": "t-2",
        "purpose_of_use": "treatment",
        "attributes": {"env": "prod"},
    }
    merged = merge_request_with_claims(payload, claims)
    assert merged["user_id"] == "jwt-user"
    assert merged["role"] == "clinician"
    assert merged["tenant_id"] == "t-2"
    assert merged["purpose_of_use"] == "treatment"
    assert merged["attributes"]["env"] == "prod"
