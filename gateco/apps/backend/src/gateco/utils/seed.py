"""Dev seed data — run via: python -m gateco.utils.seed

Creates realistic mock data matching MSW fixtures so FE can switch page-by-page.
"""

import asyncio
import datetime
import os
import uuid

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Ensure DATABASE_URL is set
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/gateco_db"
)


async def seed():
    engine = create_async_engine(DATABASE_URL)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Import models after engine setup
    from gateco.database.enums import (
        AuditEventType,
        BillingPeriod,
        Classification,
        ConnectorStatus,
        ConnectorType,
        EncryptionMode,
        IdentityProviderStatus,
        IdentityProviderType,
        InvoiceStatus,
        PipelineRunStatus,
        PipelineStatus,
        PlanTier,
        PolicyEffect,
        PolicyStatus,
        PolicyType,
        PrincipalStatus,
        ResourceType,
        Sensitivity,
        SubscriptionStatus,
        UserRole,
    )
    from gateco.database.models.audit_event import AuditEvent
    from gateco.database.models.connector import Connector
    from gateco.database.models.identity_provider import IdentityProvider
    from gateco.database.models.invoice import Invoice
    from gateco.database.models.organization import Organization
    from gateco.database.models.pipeline import Pipeline
    from gateco.database.models.pipeline_run import PipelineRun
    from gateco.database.models.policy import Policy
    from gateco.database.models.policy_rule import PolicyRule
    from gateco.database.models.principal import Principal
    from gateco.database.models.principal_group import PrincipalGroup
    from gateco.database.models.resource import GatedResource
    from gateco.database.models.resource_chunk import ResourceChunk
    from gateco.database.models.subscription import Subscription
    from gateco.database.models.usage import UsageLog
    from gateco.database.models.user import User
    from gateco.utils.security import hash_password

    now = datetime.datetime.now(datetime.timezone.utc)

    async with factory() as session:
        # Clean existing seed data (idempotent re-runs)
        from sqlalchemy import text
        for table in [
            "secured_retrievals", "pipeline_runs", "pipelines",
            "resource_chunks", "policy_rules", "policies",
            "audit_events", "usage_logs", "invoices", "payments",
            "subscriptions", "principals", "principal_groups",
            "gated_resources", "connectors", "identity_providers",
            "access_rules", "invites", "user_sessions", "oauth_accounts",
            "users", "organizations",
        ]:
            await session.execute(text(f"DELETE FROM {table}"))
        await session.flush()

        # Organization
        org_id = uuid.uuid4()
        org = Organization(id=org_id, name="Acme Corp", slug="acme-corp", plan=PlanTier.pro)
        session.add(org)

        # User
        user_id = uuid.uuid4()
        user = User(
            id=user_id,
            organization_id=org_id,
            email="admin@acmecorp.com",
            password_hash=hash_password("password123"),
            name="Sarah Chen",
            role=UserRole.org_admin,
        )
        session.add(user)
        await session.flush()  # Ensure org + user exist for FK constraints

        # Connectors
        conn1_id, conn2_id = uuid.uuid4(), uuid.uuid4()
        session.add(Connector(
            id=conn1_id, organization_id=org_id, name="Production PgVector",
            type=ConnectorType.pgvector, status=ConnectorStatus.connected,
            config={"host": "db.example.com", "port": 5432, "database": "vectors"},
            index_count=3, record_count=50000, last_sync=now,
        ))
        session.add(Connector(
            id=conn2_id, organization_id=org_id, name="Pinecone Staging",
            type=ConnectorType.pinecone, status=ConnectorStatus.error,
            config={"environment": "us-east-1", "index_name": "staging"},
            error_message="API key expired",
        ))

        # Identity Providers
        idp1_id, idp2_id = uuid.uuid4(), uuid.uuid4()
        session.add(IdentityProvider(
            id=idp1_id, organization_id=org_id, name="Azure Entra ID",
            type=IdentityProviderType.azure_entra_id, status=IdentityProviderStatus.connected,
            config={"tenant_id": "abc-123", "client_id": "def-456"},
            principal_count=6, group_count=2, last_sync=now,
        ))
        session.add(IdentityProvider(
            id=idp2_id, organization_id=org_id, name="Okta",
            type=IdentityProviderType.okta, status=IdentityProviderStatus.disconnected,
            config={"domain": "acme.okta.com"},
        ))

        # Principals
        principal_ids = []
        for i, (name, email, groups, dept) in enumerate([
            ("Alice Johnson", "alice@acme.com", ["engineering", "leads"], "engineering"),
            ("Bob Smith", "bob@acme.com", ["engineering"], "engineering"),
            ("Carol Williams", "carol@acme.com", ["engineering"], "engineering"),
            ("Dave Brown", "dave@acme.com", ["marketing"], "marketing"),
            ("Eve Davis", "eve@acme.com", ["marketing"], "marketing"),
            ("Frank Wilson", "frank@acme.com", ["finance"], "finance"),
        ]):
            pid = uuid.uuid4()
            principal_ids.append(pid)
            session.add(Principal(
                id=pid, organization_id=org_id, identity_provider_id=idp1_id,
                external_id=f"ext-{i}", display_name=name, email=email,
                groups=groups, roles=["viewer"], attributes={"department": dept},
                status=PrincipalStatus.active, last_seen=now,
            ))

        # Principal Groups
        session.add(PrincipalGroup(
            organization_id=org_id, identity_provider_id=idp1_id,
            external_id="grp-eng", name="engineering", member_count=3,
        ))
        session.add(PrincipalGroup(
            organization_id=org_id, identity_provider_id=idp1_id,
            external_id="grp-mkt", name="marketing", member_count=2,
        ))

        # Policies
        pol1_id, pol2_id, pol3_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
        session.add(Policy(
            id=pol1_id, organization_id=org_id, name="Engineering Data Access",
            description="Allow engineering team to access internal docs",
            type=PolicyType.rbac, status=PolicyStatus.active, effect=PolicyEffect.allow,
            resource_selectors=[{"field": "domain", "op": "eq", "value": "engineering"}],
            version=2, created_by=user_id,
        ))
        session.add(PolicyRule(
            policy_id=pol1_id, description="Engineers can read internal data",
            effect=PolicyEffect.allow,
            conditions=[
                {"field": "principal.groups", "operator": "contains", "value": ["engineering"]},
                {"field": "resource.classification", "operator": "lte", "value": "confidential"},
            ],
            priority=10,
        ))

        session.add(Policy(
            id=pol2_id, organization_id=org_id, name="Finance Restriction",
            description="Restrict access to financial data", type=PolicyType.abac,
            status=PolicyStatus.draft, effect=PolicyEffect.deny,
            resource_selectors=[{"field": "domain", "op": "eq", "value": "finance"}],
            version=1, created_by=user_id,
        ))
        session.add(PolicyRule(
            policy_id=pol2_id, description="Non-finance denied",
            effect=PolicyEffect.deny,
            conditions=[
                {"field": "principal.attributes.department", "operator": "ne", "value": "finance"},
            ],
            priority=10,
        ))

        session.add(Policy(
            id=pol3_id, organization_id=org_id, name="Legacy Access Policy",
            type=PolicyType.rebac, status=PolicyStatus.archived, effect=PolicyEffect.allow,
            version=3, created_by=user_id,
        ))

        # GatedResources with chunks
        resource_ids = []
        for i, (title, domain, clf, sens) in enumerate([
            ("Q4 Revenue Report", "finance", Classification.confidential, Sensitivity.high),
            ("Engineering Runbook", "engineering", Classification.internal, Sensitivity.medium),
            ("Marketing Plan 2026", "marketing", Classification.internal, Sensitivity.low),
            ("API Documentation", "engineering", Classification.public, Sensitivity.low),
            ("Customer PII Export", "compliance", Classification.restricted, Sensitivity.critical),
        ]):
            rid = uuid.uuid4()
            resource_ids.append(rid)
            session.add(GatedResource(
                id=rid, organization_id=org_id, type=ResourceType.file,
                title=title, description=f"Description for {title}",
                content_url=f"https://storage.example.com/{rid}",
                classification=clf, sensitivity=sens, domain=domain,
                labels=[domain, "2026"], encryption_mode=EncryptionMode.at_rest,
                source_connector_id=conn1_id, created_by=user_id,
            ))
            for j in range(3):
                session.add(ResourceChunk(
                    resource_id=rid, index=j,
                    preview=f"Chunk {j} of {title}: Lorem ipsum dolor sit amet...",
                    encrypted=False, vector_id=f"vec-{rid}-{j}",
                ))

        # Pipeline
        pipe_id = uuid.uuid4()
        session.add(Pipeline(
            id=pipe_id, organization_id=org_id, name="Daily Ingestion",
            source_connector_id=conn1_id, status=PipelineStatus.active,
            schedule="manual", records_processed=450, last_run=now,
        ))
        for status, ago_hours in [
            (PipelineRunStatus.completed, 2),
            (PipelineRunStatus.completed, 26),
            (PipelineRunStatus.failed, 50),
        ]:
            started = now - datetime.timedelta(hours=ago_hours)
            session.add(PipelineRun(
                pipeline_id=pipe_id, status=status,
                records_processed=150 if status == PipelineRunStatus.completed else 0,
                errors=1 if status == PipelineRunStatus.failed else 0,
                started_at=started,
                completed_at=started + datetime.timedelta(seconds=12),
                duration_ms=12000,
            ))

        # Audit Events
        audit_types = [
            AuditEventType.user_login, AuditEventType.connector_added,
            AuditEventType.idp_added, AuditEventType.policy_created,
            AuditEventType.policy_activated, AuditEventType.pipeline_run,
            AuditEventType.resource_updated, AuditEventType.settings_changed,
            AuditEventType.retrieval_allowed, AuditEventType.retrieval_denied,
        ]
        for i, et in enumerate(audit_types):
            session.add(AuditEvent(
                organization_id=org_id, event_type=et,
                actor_id=user_id, actor_name="Sarah Chen",
                details=f"Seed audit event: {et.value}",
                timestamp=now - datetime.timedelta(hours=i),
            ))

        # Subscription
        period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        next_month = (period_start.month % 12) + 1
        next_year = period_start.year + (1 if next_month == 1 else 0)
        period_end = period_start.replace(year=next_year, month=next_month)
        session.add(Subscription(
            organization_id=org_id, plan_tier=PlanTier.pro,
            status=SubscriptionStatus.active, billing_period=BillingPeriod.monthly,
            current_period_start=period_start, current_period_end=period_end,
        ))

        # Invoices
        session.add(Invoice(
            organization_id=org_id, amount_cents=4900, status=InvoiceStatus.paid,
            period_start=period_start - datetime.timedelta(days=30),
            period_end=period_start, paid_at=period_start,
        ))
        session.add(Invoice(
            organization_id=org_id, amount_cents=4900, status=InvoiceStatus.open,
            period_start=period_start, period_end=period_end,
        ))

        # Usage
        session.add(UsageLog(
            organization_id=org_id, period_start=period_start, period_end=period_end,
            secured_retrievals=4200, resources_created=5,
        ))

        await session.commit()
        print("Seed data created successfully!")
        print(f"  Organization: {org_id} (Acme Corp)")
        print("  User: admin@acmecorp.com / password123")
        print(f"  {len(resource_ids)} resources, {len(principal_ids)} principals")


if __name__ == "__main__":
    asyncio.run(seed())
