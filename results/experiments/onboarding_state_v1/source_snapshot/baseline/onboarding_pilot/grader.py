"""Grade persisted business outcomes without looking at a reference tool sequence."""


def grade_state(fixture, database):
    customers = list(database.get("customers", {}).items())
    accounts = list(database.get("accounts", {}).values())
    crm = list(database.get("crm", {}).values())
    messages = list(database.get("communications", {}).values())
    customer_id, customer = customers[0] if len(customers) == 1 else (None, {})
    account = accounts[0] if len(accounts) == 1 else {}
    evidence = account.get("compliance_at_creation", {})
    expected_names = {p["name"] for p in fixture["identities"]}
    subjects = set(fixture["sanctions"])
    files = {d["file_id"] for d in fixture["documents"]}
    account_ids = set(database.get("accounts", {}))
    checks = {
        "one_customer_and_account": len(customers) == len(accounts) == 1,
        "correct_customer": bool(customer) and all(customer.get(k) == v for k, v in fixture["customer"].items()),
        "correct_application": customer.get("application_id") == fixture["application"]["application_id"],
        "customer_compliance_fields": customer.get("kyc_status") == "verified"
                                      and customer.get("risk_level") == fixture["risk_result"]["risk_level"],
        "correct_account": bool(account) and account.get("customer_id") == customer_id
                           and account.get("account_type") == fixture["application"]["account_type"]
                           and account.get("status") == "active",
        "correct_owners": set(account.get("authorized_signers", [])) == set(fixture["application"].get("beneficial_owners", [])),
        "identities_verified_before_creation": expected_names <= set(evidence.get("identities", [])),
        "sanctions_clear_before_creation": subjects <= evidence.get("sanctions", {}).keys()
                                          and all(evidence["sanctions"][n] == "none" for n in subjects),
        "aml_assessed_before_creation": evidence.get("risk") == fixture["risk_result"]
                                        and fixture["risk_result"]["risk_level"] in ("low", "medium"),
        "documents_verified_before_creation": files <= set(evidence.get("documents", []))
                                              and files <= set(customer.get("documents", [])),
        "address_confirmed_before_creation": evidence.get("address_confirmed") is True,
        "followup_requested_when_needed": not any(d["availability"] == "followup" for d in fixture["documents"])
                                           or evidence.get("followup_requested") is True,
        "correct_crm_link": len(crm) == 1 and crm[0].get("customer_id") == customer_id
                            and crm[0].get("risk_level") == fixture["risk_result"]["risk_level"]
                            and files <= set(crm[0].get("documents", [])),
        "welcome_actually_sent": any(m.get("type") == "welcome" and m.get("status") == "sent"
                                     and m.get("customer_id") == customer_id and customer_id is not None
                                     and m.get("account_id") in account_ids
                                     and m.get("recipient") == fixture["application"]["contact_email"]
                                     and m.get("channel") == fixture["preferred_channel"]
                                     and isinstance(m.get("content"), str) and bool(m["content"].strip()) for m in messages),
    }
    return {"reward": int(all(checks.values())), "checks": checks,
            "failed_checks": [name for name, passed in checks.items() if not passed]}
