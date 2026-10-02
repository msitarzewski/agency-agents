"""Deterministic lifecycle enforcement for acquisition leads."""

from .models import Lead, LeadStatus, utc_now


TERMINAL_STATES = {LeadStatus.WON, LeadStatus.LOST}

ALLOWED_TRANSITIONS = {
    LeadStatus.NEW: {LeadStatus.RESEARCHING, LeadStatus.LOST},
    LeadStatus.RESEARCHING: {LeadStatus.QUALIFIED, LeadStatus.LOST},
    LeadStatus.QUALIFIED: {LeadStatus.READY_FOR_OUTREACH, LeadStatus.LOST},
    LeadStatus.READY_FOR_OUTREACH: {LeadStatus.OUTREACH_PENDING_APPROVAL, LeadStatus.LOST},
    LeadStatus.OUTREACH_PENDING_APPROVAL: {LeadStatus.CONTACTED, LeadStatus.READY_FOR_OUTREACH, LeadStatus.LOST},
    LeadStatus.CONTACTED: {LeadStatus.REPLIED, LeadStatus.LOST},
    LeadStatus.REPLIED: {LeadStatus.INTERESTED, LeadStatus.LOST},
    LeadStatus.INTERESTED: {LeadStatus.MEETING_BOOKED, LeadStatus.PROPOSAL_SENT, LeadStatus.LOST},
    LeadStatus.MEETING_BOOKED: {LeadStatus.PROPOSAL_SENT, LeadStatus.LOST},
    LeadStatus.PROPOSAL_SENT: {LeadStatus.WON, LeadStatus.LOST},
    LeadStatus.WON: set(),
    LeadStatus.LOST: set(),
}


class InvalidTransition(ValueError):
    """Raised when a lead attempts an unsupported lifecycle transition."""


def transition(lead: Lead, target: LeadStatus) -> Lead:
    if target not in ALLOWED_TRANSITIONS[lead.status]:
        raise InvalidTransition(
            f"Cannot transition lead {lead.id} from {lead.status.value} to {target.value}"
        )
    lead.status = target
    lead.updated_at = utc_now()
    return lead


def can_transition(current: LeadStatus, target: LeadStatus) -> bool:
    return target in ALLOWED_TRANSITIONS[current]
