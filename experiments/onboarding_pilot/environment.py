"""Stateful simulated banking services. Task goals and grading live separately."""
import copy
import hashlib

from baseline.synthetic_environment import SyntheticSystemTools


class OnboardingEnvironment(SyntheticSystemTools):
    def __init__(self, fixture):
        self._fixture = copy.deepcopy(fixture)
        self._application = self._fixture["application"]
        self._documents = {d["file_id"]: d for d in self._fixture["documents"]}
        self._available = {name for name, d in self._documents.items() if d["availability"] == "initial"}
        self._extracted = set()
        self._verified = set()
        self._screened = {}
        self._risk = None
        self._followup_requested = False
        self._address_confirmed = not fixture["address_reconciliation_required"]
        self._db = {"customers": {}, "accounts": {}, "crm": {}, "communications": {}}

    def _id(self, prefix):
        token = hashlib.sha256(self._application["application_id"].encode()).hexdigest()[:10]
        return f"{prefix}-{token}"

    def _check_application(self, application_id):
        if application_id != self._application["application_id"]:
            raise ValueError("Application does not exist in this authenticated session")

    def _snapshot(self):
        return copy.deepcopy(self._db)

    def get_application(self, application_id: str) -> dict:
        """Read an already-submitted application from the authenticated secure portal.

        Returns customer profile, AML profile, beneficial owners, account type,
        contact channel, and available document filenames. Use these records
        rather than asking the customer to retype private document data.
        """
        self._check_application(application_id)
        profile = copy.deepcopy(self._fixture["customer"])
        if not self._address_confirmed:
            profile["address"] = next(d["address"] for d in self._documents.values() if d["id_number"])
        return {"application_id": application_id, "customer_type": self._application["customer_type"],
                "account_type": self._application["account_type"], "customer_profile": profile,
                "risk_profile": copy.deepcopy(self._fixture["risk_profile"]),
                "beneficial_owners": self._application.get("beneficial_owners", []),
                "available_documents": sorted(self._available),
                "followup_required": any(d["availability"] == "followup" for d in self._documents.values()),
                "address_reconciliation_required": self._fixture["address_reconciliation_required"],
                "contact_email": self._application["contact_email"],
                "preferred_channel": self._fixture["preferred_channel"]}

    def extract_kyc_documents(self, document_files: list[str]) -> dict:
        """Extract document facts from files actually available in the secure portal.

        Returns documents containing file_id, document_type, name, dob, address,
        id_type, id_number, and valid. Address-only documents are not identity IDs.
        """
        if not document_files or not set(document_files) <= self._available:
            raise ValueError("Requested documents are missing; request follow-up documents first")
        documents = [copy.deepcopy(self._documents[name]) for name in document_files]
        if not all(d["valid"] for d in documents):
            raise ValueError("An uploaded document is invalid")
        self._extracted.update(document_files)
        return {"documents": documents}

    def validate_identity(self, extracted_data: dict, id_type: str, id_number: str) -> dict:
        """Verify a person using an extracted identity document, not an agent claim.

        extracted_data must include the actual document's name and dob.
        id_type and id_number must match an extracted, valid identity document.
        Each beneficial owner must be verified for a business account.
        """
        match = next((d for name, d in self._documents.items() if name in self._extracted
                      and d["id_number"] == id_number and d["id_type"] == id_type
                      and d["name"] == extracted_data.get("name") and d["dob"] == extracted_data.get("dob")
                      and d["valid"] and d["id_number"]), None)
        if match is None:
            raise ValueError("Identity fields do not match an extracted identity document")
        self._verified.add(match["name"])
        return {"name": match["name"], "status": "verified", "fraud_flag": False}

    def screen_sanctions_lists(self, customer_data: dict) -> dict:
        """Screen the named customer/business and owners using the sanctions service.

        Supply name, business_name, and/or owner_names. Business and all owners
        must be screened; separate calls or a combined call are both valid.
        """
        names = {customer_data[k] for k in ("name", "business_name") if customer_data.get(k)}
        names.update(customer_data.get("owner_names") or [])
        if not names or not names <= set(self._fixture["sanctions"]):
            raise ValueError("Screening subjects do not match this application")
        results = {name: self._fixture["sanctions"][name] for name in sorted(names)}
        self._screened.update(results)
        return {"results": results, "match_status": "none" if all(v == "none" for v in results.values()) else "exact"}

    def calculate_aml_risk_score(self, profile_data: dict) -> dict:
        """Assess the submitted AML profile with the simulated bank risk service.

        Use risk_profile returned by get_application, including nationality,
        occupation, transaction_volume, geography, and business_type if present.
        The risk service is fixture-backed; it is not real-world AML advice.
        """
        if any(profile_data.get(k) != v for k, v in self._fixture["risk_profile"].items()):
            raise ValueError("Risk profile differs from the submitted application")
        self._risk = copy.deepcopy(self._fixture["risk_result"])
        return copy.deepcopy(self._risk)

    def request_missing_documents(self, application_id: str, reason: str) -> dict:
        """Request missing/supporting documents before customer creation.

        This does not need a customer ID. The simulated customer then uploads
        the available follow-up documents into the secure portal. Returns their
        filenames and the customer's address explanation if one was supplied.
        """
        self._check_application(application_id)
        followup = {name for name, d in self._documents.items() if d["availability"] == "followup"}
        if not followup:
            return {"status": "not_required", "available_documents": sorted(self._available)}
        self._followup_requested = True
        self._available.update(followup)
        self._db["communications"][self._id("DOCREQ")] = {
            "application_id": application_id, "type": "document_request", "status": "sent",
            "recipient": self._application["contact_email"]}
        return {"status": "customer_uploaded", "new_documents": sorted(followup),
                "address_explanation": self._application.get("address_explanation")}

    def confirm_current_address(self, application_id: str, evidence_files: list[str]) -> dict:
        """Resolve an address mismatch using received, extracted supporting documents.

        For a mismatch, request supporting documents first. Supply the returned
        follow-up evidence filenames after extracting them. Returns the verified
        current address to use when creating the customer.
        """
        self._check_application(application_id)
        if not self._fixture["address_reconciliation_required"]:
            return {"status": "not_required", "address": self._fixture["customer"]["address"]}
        followup = {name for name, d in self._documents.items() if d["availability"] == "followup"}
        if not self._followup_requested or not followup <= set(evidence_files) or not set(evidence_files) <= self._extracted:
            raise ValueError("Customer explanation and extracted follow-up evidence are required")
        address = self._fixture["customer"]["address"]
        if not all(self._documents[name]["address"] == address for name in evidence_files):
            raise ValueError("Address evidence is inconsistent")
        self._address_confirmed = True
        return {"status": "confirmed", "address": address}

    def create_core_banking_customer(self, customer_data: dict, account_type: str,
                                     authorized_signers: list[str] | None = None) -> dict:
        """Actually create the bank customer and account after required checks.

        customer_data needs name, dob (null is permitted for a business), address,
        kyc_status='verified', risk_level, and documents (filenames or objects with
        file_id). All required identities, sanctions, AML, and documents must be
        verified before creation; agent-supplied status claims cannot bypass them.
        Business authorized_signers must match the submitted beneficial owners.
        Repeating an identical valid creation is idempotent.
        """
        identities = {p["name"] for p in self._fixture["identities"]}
        subjects = set(self._fixture["sanctions"])
        required_documents = set(self._documents)
        if not identities <= self._verified or not subjects <= self._screened.keys():
            raise ValueError("Complete identity verification and sanctions screening first")
        if any(self._screened[n] != "none" for n in subjects) or self._risk is None or self._risk["risk_level"] not in ("low", "medium"):
            raise ValueError("AML assessment and clear sanctions are required")
        if not required_documents <= self._extracted or not self._address_confirmed:
            raise ValueError("Required documents or address confirmation are missing")
        if any(customer_data.get(k) != v for k, v in self._fixture["customer"].items()):
            raise ValueError("Customer identity/address differ from the verified records")
        if customer_data.get("kyc_status") != "verified" or customer_data.get("risk_level") != self._risk["risk_level"]:
            raise ValueError("Customer compliance fields do not match service results")
        supplied_documents = {d if isinstance(d, str) else d.get("file_id") for d in customer_data.get("documents", [])}
        if not required_documents <= supplied_documents or not supplied_documents <= self._extracted:
            raise ValueError("Attach the verified documents to the customer record")
        owners = set(self._application.get("beneficial_owners", []))
        if account_type != self._application["account_type"] or set(authorized_signers or []) != owners:
            raise ValueError("Account type or authorized owners differ from the application")
        customer_id, account_id = self._id("CUST"), self._id("ACC")
        evidence = {"identities": sorted(self._verified), "sanctions": copy.deepcopy(self._screened),
                    "risk": copy.deepcopy(self._risk), "documents": sorted(self._extracted),
                    "address_confirmed": self._address_confirmed,
                    "followup_requested": self._followup_requested}
        self._db["customers"][customer_id] = {**copy.deepcopy(customer_data), "application_id": self._application["application_id"],
                                             "documents": sorted(supplied_documents)}
        self._db["accounts"][account_id] = {"customer_id": customer_id, "account_type": account_type,
                                          "authorized_signers": sorted(owners), "status": "active",
                                          "compliance_at_creation": evidence}
        return {"customer_id": customer_id, "account_id": account_id, "status": "created"}

    def create_crm_profile(self, customer_id: str, risk_level: str, kyc_documents: list,
                           relationship_data: dict | None = None) -> dict:
        """Persist a CRM profile linked to the created customer and verified KYC files."""
        if customer_id not in self._db["customers"] or self._risk is None or risk_level != self._risk["risk_level"]:
            raise ValueError("Use a real created customer and its assessed risk level")
        files = {d if isinstance(d, str) else d.get("file_id") for d in kyc_documents}
        if not set(self._documents) <= files or not files <= self._extracted:
            raise ValueError("CRM needs the verified document set")
        crm_id = self._id("CRM")
        self._db["crm"][crm_id] = {"customer_id": customer_id, "risk_level": risk_level, "documents": sorted(files)}
        return {"crm_id": crm_id, "status": "created"}

    def send_welcome_communication(self, customer_id: str, communication_type: str,
                                   content: str, delivery_method: str = "email") -> dict:
        """Send and record a welcome message after account and CRM creation.

        Use communication_type='welcome', nonempty content, and the application's
        preferred channel. Missing-document requests use request_missing_documents.
        The service determines the actual recipient from the application record.
        """
        if customer_id not in self._db["customers"] or not self._db["crm"]:
            raise ValueError("Create the account and CRM profile before sending a welcome")
        if communication_type != "welcome" or delivery_method != self._fixture["preferred_channel"] or not content.strip():
            raise ValueError("Use a welcome message and the preferred contact channel")
        message_id = self._id("WELCOME")
        self._db["communications"][message_id] = {"customer_id": customer_id, "account_id": self._id("ACC"),
            "recipient": self._application["contact_email"], "type": "welcome", "channel": delivery_method,
            "status": "sent", "content": content}
        return {"message_id": message_id, "delivery_status": "sent"}
