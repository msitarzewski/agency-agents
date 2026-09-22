import sys
import unittest
from pathlib import Path

SOURCE_ROOT = Path(__file__).resolve().parents[1]
# sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(SOURCE_ROOT))

# from client_acquisition.orchestrator.models import Lead, LeadStatus
# from client_acquisition.orchestrator.registry import AGENT_REGISTRY, get_agent_path
# from client_acquisition.orchestrator.state_machine import InvalidTransition, can_transition, transition
from orchestrator.models import Lead, LeadStatus
from orchestrator.registry import AGENT_REGISTRY, get_agent_path
from orchestrator.state_machine import InvalidTransition, can_transition, transition

class FoundationTests(unittest.TestCase):
    def test_new_lead_can_enter_research(self):
        lead = Lead(company_name="Example Co")
        transition(lead, LeadStatus.RESEARCHING)
        self.assertIs(lead.status, LeadStatus.RESEARCHING)

    def test_invalid_transition_is_rejected(self):
        lead = Lead(company_name="Example Co")
        with self.assertRaises(InvalidTransition):
            transition(lead, LeadStatus.WON)

    def test_terminal_states_have_no_outgoing_transition(self):
        self.assertFalse(can_transition(LeadStatus.WON, LeadStatus.LOST))
        self.assertFalse(can_transition(LeadStatus.LOST, LeadStatus.NEW))

    def test_registry_points_to_existing_agents(self):
        self.assertGreaterEqual(len(AGENT_REGISTRY), 8)
        for capability in AGENT_REGISTRY:
            self.assertTrue(get_agent_path(capability).is_file())


if __name__ == "__main__":
    unittest.main()
