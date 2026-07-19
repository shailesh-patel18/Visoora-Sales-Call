from server.onboarding_api import (
    AnalyzeDomainResponse,
    EvidenceStringField,
    EvidenceObjectionField,
    EvidenceSegmentField
)

mock_onboarding_response = AnalyzeDomainResponse(
    company_name=EvidenceStringField(
        value="Stripe",
        confidence=100,
        snippet="<title>Stripe | Financial Infrastructure for the Internet</title>",
        source_url="https://stripe.com",
        source="schema.org"
    ),
    company_description=EvidenceStringField(
        value="Financial infrastructure platform for the internet. Millions of companies of all sizes use Stripe online and in person to accept payments, send payouts, automate financial processes, and ultimately grow revenue.",
        confidence=98,
        snippet="Millions of companies of all sizes...",
        source_url="https://stripe.com",
        source="meta_description"
    ),
    value_proposition=EvidenceStringField(
        value="The world's most powerful and easy-to-use APIs for internet commerce.",
        confidence=95,
        snippet="powerful and easy-to-use APIs",
        source_url="https://stripe.com",
        source="LLM"
    ),
    estimated_industries=[
        EvidenceStringField(value="Financial Services", confidence=100, snippet="Financial Infrastructure", source_url="https://stripe.com", source="keywords"),
        EvidenceStringField(value="Payments", confidence=100, snippet="accept payments", source_url="https://stripe.com", source="hero")
    ],
    estimated_regions=[
        EvidenceStringField(value="Global", confidence=90, snippet="Millions of companies... internet", source_url="https://stripe.com", source="LLM")
    ],
    estimated_decision_makers=[
        EvidenceStringField(value="CTO", confidence=85, snippet="APIs for internet commerce", source_url="https://stripe.com", source="LLM"),
        EvidenceStringField(value="VP of Finance", confidence=85, snippet="automate financial processes", source_url="https://stripe.com", source="LLM")
    ],
    potential_competitors=[
        EvidenceStringField(value="PayPal", confidence=90, snippet="N/A", source_url="N/A", source="LLM"),
        EvidenceStringField(value="Adyen", confidence=90, snippet="N/A", source_url="N/A", source="LLM")
    ],
    potential_objections=[
        EvidenceObjectionField(
            objection="Too expensive for small startups",
            rebuttal="Stripe Atlas helps startups incorporate easily, and the pay-as-you-go model means you only pay when you earn.",
            confidence=80,
            snippet="N/A",
            source_url="N/A",
            source="LLM"
        )
    ],
    suggested_segments=[
        EvidenceSegmentField(
            segment="SaaS Platforms",
            rationale="Stripe Connect is explicitly designed for multi-party payments and marketplaces.",
            confidence=95,
            snippet="Platform payments",
            source_url="https://stripe.com/connect",
            source="LLM"
        )
    ],
    brand_voice_tone=EvidenceStringField(
        value="Developer-centric, clear, and professional",
        confidence=90,
        snippet="APIs",
        source_url="https://stripe.com",
        source="LLM"
    )
)
