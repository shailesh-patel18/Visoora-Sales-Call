-- Alembic Migration: Provision TCPA & GDPR Compliance Tables
-- Revision ID: c3c0217b_compliance_v1
-- Date: 2026-05-24

BEGIN;

-- 1. Tenant-Scoped Do Not Call (DNC) Registry Table
-- Mapped to TCPA 47 U.S.C. § 227 (Do Not Call Registry standards)
CREATE TABLE IF NOT EXISTS dnc_numbers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone_number VARCHAR(20) NOT NULL, -- Standard E.164 phone formats
    tenant_id VARCHAR(100) NOT NULL,    -- Multi-tenant separation boundary
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()) NOT NULL,
    CONSTRAINT uq_phone_tenant UNIQUE (phone_number, tenant_id)
);

CREATE INDEX IF NOT EXISTS idx_dnc_phone_tenant ON dnc_numbers (phone_number, tenant_id);

-- 2. Call Consents Table
-- Mapped to GDPR Article 7 (Conditions for Consent) and TCPA Prior Express Written Consent (PEWC)
CREATE TABLE IF NOT EXISTS call_consents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone_number VARCHAR(20) NOT NULL,
    consent_token UUID NOT NULL UNIQUE, -- Passed in /make-call header or payload
    granted_at TIMESTAMP WITH TIME ZONE NOT NULL,
    consent_type VARCHAR(20) NOT NULL CHECK (consent_type IN ('marketing', 'transactional')),
    granted_by_ip VARCHAR(45) NOT NULL,  -- IPv4 or IPv6 tracking
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL, -- FTC rules require expiry mapping (default 90 days)
    tenant_id VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_consents_token ON call_consents (consent_token);
CREATE INDEX IF NOT EXISTS idx_consents_lookup ON call_consents (phone_number, tenant_id);

-- 3. Tenant Compliance Settings Table
-- Mapped to FCC One-Party/Two-Party Recording Consent Laws and FTC/FTC AI Disclosures (FTC 16 CFR Part 310)
CREATE TABLE IF NOT EXISTS tenant_compliance_settings (
    tenant_id VARCHAR(100) PRIMARY KEY,
    recording_disclosure_enabled BOOLEAN DEFAULT TRUE NOT NULL,
    recording_disclosure_text TEXT DEFAULT 'This call may be recorded for quality and training purposes.' NOT NULL,
    ai_disclosure_enabled BOOLEAN DEFAULT TRUE NOT NULL,
    ai_disclosure_text TEXT DEFAULT 'You are speaking with an automated assistant.' NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()) NOT NULL
);

COMMIT;
