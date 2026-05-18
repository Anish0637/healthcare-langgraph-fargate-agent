from app.security import authorize


def test_rbac_denies_invalid_purpose():
    decision = authorize(
        role="billing",
        tenant_id="t1",
        purpose_of_use="treatment",
        attributes={"tenant_id": "t1", "env": "prod", "data_class": "restricted"},
        context={},
        patient_context={"consent": True},
    )
    assert decision.allow is False
