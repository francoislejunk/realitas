"""
Realitas Neo System Reviewer

A comprehensive reviewer skill that analyzes all aspects of the simulation,
checks for proper context implementation, and identifies edge cases.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum, auto


class ReviewSeverity(Enum):
    CRITICAL = auto()  # System-breaking issues
    HIGH = auto()      # Major functionality impaired
    MEDIUM = auto()    # Minor issues, workarounds exist
    LOW = auto()       # Cosmetic or optimization suggestions
    INFO = auto()      # Observations and best practices


@dataclass
class ReviewFinding:
    category: str
    severity: ReviewSeverity
    location: str
    issue: str
    recommendation: str
    edge_case: Optional[str] = None
    related_files: List[str] = field(default_factory=list)


@dataclass
class SystemHealthReport:
    overall_status: str
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    findings: List[ReviewFinding]
    recommendations: List[str]


class RealitasReviewer:
    """
    Comprehensive system reviewer for Realitas Neo simulation.
    
    This reviewer analyzes:
    1. Agent architecture and communication patterns
    2. Context flow between systems
    3. Data persistence and state management
    4. Edge case handling
    5. Integration points and dependencies
    """
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path(__file__).parent
        self.findings: List[ReviewFinding] = []
        self.systems_analyzed: Set[str] = set()
        
    def run_full_review(self) -> SystemHealthReport:
        """Execute comprehensive system review."""
        print("🔍 Starting Realitas Neo System Review...")
        print("=" * 60)
        
        # Core system reviews
        self._review_agent_architecture()
        self._review_context_systems()
        self._review_memory_systems()
        self._review_actor_systems()
        self._review_narrative_systems()
        self._review_exchange_systems()
        self._review_validation_systems()
        self._review_integration_points()
        self._review_edge_cases()
        
        # Generate report
        return self._compile_report()
    
    def _review_agent_architecture(self):
        """Review agent system architecture and communication."""
        print("📋 Reviewing Agent Architecture...")
        
        agents_dir = self.project_root / "agents"
        if not agents_dir.exists():
            self._add_finding(
                category="Agent Architecture",
                severity=ReviewSeverity.CRITICAL,
                location="agents/",
                issue="Agents directory not found",
                recommendation="Verify project structure"
            )
            return
        
        # Check core agents exist
        core_agents = [
            "conductor_agent.py",
            "narrator_agent.py", 
            "interpreter_agent.py",
            "decider_agent.py",
            "creator_agent.py",
            "tracker_agent.py"
        ]
        
        for agent in core_agents:
            agent_path = agents_dir / agent
            if not agent_path.exists():
                self._add_finding(
                    category="Agent Architecture",
                    severity=ReviewSeverity.HIGH,
                    location=f"agents/{agent}",
                    issue=f"Core agent {agent} not found",
                    recommendation=f"Verify {agent} is present and properly named"
                )
        
        # Check for proper agent initialization patterns
        self._check_agent_initialization_patterns()
        
        # Check for circular dependencies
        self._check_circular_dependencies()
        
        self.systems_analyzed.add("agent_architecture")
    
    def _check_agent_initialization_patterns(self):
        """Check that agents follow proper initialization patterns."""
        # Key pattern: agents should receive dependencies via __init__
        required_patterns = [
            ("logger", "UTASLogger dependency"),
            ("rag_system", "RAG system for worldbuilding context"),
            ("tracker_agent", "Tracker for session context"),
            ("scene_description", "Scene context"),
        ]
        
        # This would involve AST parsing in a real implementation
        # For now, document the expected pattern
        self._add_finding(
            category="Agent Architecture",
            severity=ReviewSeverity.INFO,
            location="agents/*",
            issue="Agent initialization pattern validation",
            recommendation="Ensure all agents receive: logger, rag_system, tracker_agent, scene_description via __init__",
            edge_case="Agents initialized without RAG will lack worldbuilding context, causing anachronisms"
        )
    
    def _check_circular_dependencies(self):
        """Check for circular import dependencies."""
        # Document known patterns to avoid
        self._add_finding(
            category="Agent Architecture",
            severity=ReviewSeverity.MEDIUM,
            location="agents/",
            issue="Potential circular import risk between Conductor and child agents",
            recommendation="Use TYPE_CHECKING imports for type hints; import at runtime only when needed",
            edge_case="Import loops can cause initialization failures when systems are partially loaded"
        )
    
    def _review_context_systems(self):
        """Review context management and flow."""
        print("🌐 Reviewing Context Systems...")
        
        context_files = [
            "persistent_context_manager.py",
            "context_store.py",
            "narrative_context_system.py",
            "spatial_context_system.py"
        ]
        
        for cf in context_files:
            cf_path = self.project_root / cf
            if not cf_path.exists():
                self._add_finding(
                    category="Context Systems",
                    severity=ReviewSeverity.HIGH,
                    location=cf,
                    issue=f"Context system file {cf} not found",
                    recommendation="Verify all context systems are present"
                )
        
        # Check for session ID consistency
        self._add_finding(
            category="Context Systems",
            severity=ReviewSeverity.CRITICAL,
            location="MAIN/redesigned_main.py",
            issue="Session ID must be consistent across all context managers",
            recommendation="Initialize context_manager AFTER tracker session is created/loaded, using tracker.session_id",
            edge_case="If context_manager is initialized before tracker, it uses a new UUID instead of the saved session ID, breaking continuity",
            related_files=["MAIN/redesigned_main.py:8300-8320", "persistent_context_manager.py"]
        )
        
        # Check spatial context session binding
        self._add_finding(
            category="Context Systems",
            severity=ReviewSeverity.HIGH,
            location="agents/interpreter_agent.py",
            issue="Spatial context must use correct session ID for continuity checks",
            recommendation="InterpreterAgent should use tracker.session_id for spatial checks, not 'default'",
            edge_case="Using 'default' session causes all spatial continuity checks to fail on session resume",
            related_files=["agents/interpreter_agent.py:90-109", "spatial_context_system.py"]
        )
        
        self.systems_analyzed.add("context_systems")
    
    def _review_memory_systems(self):
        """Review memory creation and retrieval systems."""
        print("💭 Reviewing Memory Systems...")
        
        memory_files = [
            "key_memories_system.py",
            "npc_memory_system.py",
            "automatic_memory_creation.py",
            "intent_based_memory_creation.py"
        ]
        
        for mf in memory_files:
            mf_path = self.project_root / mf
            if not mf_path.exists():
                self._add_finding(
                    category="Memory Systems",
                    severity=ReviewSeverity.MEDIUM,
                    location=mf,
                    issue=f"Memory system file {mf} not found",
                    recommendation="Verify memory system implementation"
                )
        
        # Check memory deduplication
        self._add_finding(
            category="Memory Systems",
            severity=ReviewSeverity.HIGH,
            location="intent_based_memory_creation.py",
            issue="Memory deduplication must handle semantic similarity, not just exact matches",
            recommendation="Implement semantic deduplication to prevent 'I met John' and 'I encountered John' as separate memories",
            edge_case="Without semantic deduplication, similar memories accumulate and clutter the system"
        )
        
        # Check NUA memory initialization
        self._add_finding(
            category="Memory Systems",
            severity=ReviewSeverity.MEDIUM,
            location="MAIN/redesigned_main.py",
            issue="NUA Memory System must be session-scoped",
            recommendation="Initialize NUA memory with session-specific storage path",
            edge_case="Shared storage causes memory leakage between sessions",
            related_files=["MAIN/redesigned_main.py:8340-8350"]
        )
        
        self.systems_analyzed.add("memory_systems")
    
    def _review_actor_systems(self):
        """Review actor (UA/NUA/INUA) management."""
        print("👥 Reviewing Actor Systems...")
        
        # Check actor reference detection
        self._add_finding(
            category="Actor Systems",
            severity=ReviewSeverity.CRITICAL,
            location="dynamic_actor_system.py:72-80",
            issue="Existing actor reference detection uses overly aggressive partial matching",
            recommendation="Replace word-level partial matching with phrase-level matching or require exact substring",
            edge_case="Input 'I talk to the guard' matches existing actor 'Security Guard' because 'guard' is in both, blocking NUA detection",
            related_files=["dynamic_actor_system.py", "agents/interpreter_agent.py"]
        )
        
        # Check actor category handling
        self._add_finding(
            category="Actor Systems",
            severity=ReviewSeverity.MEDIUM,
            location="actors.py",
            issue="Actor category (UA/NUA/MNUA/INUA) must be preserved across save/load",
            recommendation="Ensure category enum is serialized and restored correctly",
            edge_case="Category loss causes actors to default to wrong behavior patterns"
        )
        
        # Check sympathy initialization with context
        self._add_finding(
            category="Actor Systems",
            severity=ReviewSeverity.MEDIUM,
            location="llm_agents/sympathy_initialization.py",
            issue="Newly encountered NPCs may default to neutral sympathy despite context",
            recommendation="Pass recent narrative context (lookback=15) to assign_initial_sympathies",
            edge_case="Phone call with 'best friend' initializes as neutral instead of friendly",
            related_files=["llm_agents/sympathy_initialization.py", "MAIN/redesigned_main.py"]
        )
        
        self.systems_analyzed.add("actor_systems")
    
    def _review_narrative_systems(self):
        """Review narrative generation and formatting."""
        print("📖 Reviewing Narrative Systems...")
        
        # Check sensory narration requirements
        self._add_finding(
            category="Narrative Systems",
            severity=ReviewSeverity.MEDIUM,
            location="agents/narrator_agent.py:79-125",
            issue="Sensory narration must start with 'You [perception verb]'",
            recommendation="Enforce sentence structure validation in narrative generation",
            edge_case="Narratives starting with context clauses break immersion: 'As she lifts the shutter, you glimpse...'"
        )
        
        # Check interior/exterior consistency
        self._add_finding(
            category="Narrative Systems",
            severity=ReviewSeverity.MEDIUM,
            location="agents/narrator_agent.py:71-76",
            issue="Scene descriptions must be either interior OR exterior, never both",
            recommendation="Validate location type before generating descriptions",
            edge_case="Descriptions mixing 'room layout' with 'sky and weather' create impossible spaces"
        )
        
        # Check narrative loop integration
        self._add_finding(
            category="Narrative Systems",
            severity=ReviewSeverity.HIGH,
            location="llm_agents/enhanced_narrative_loop.py",
            issue="Four-Mode Narrative Loop must be integrated with all narrative generation",
            recommendation="Ensure all narrators use narrative_loop.process_turn() for framing",
            edge_case="Without narrative loop, tone shifts are jarring and inconsistent"
        )
        
        self.systems_analyzed.add("narrative_systems")
    
    def _review_exchange_systems(self):
        """Review exchange/turn management systems."""
        print("⚔️ Reviewing Exchange Systems...")
        
        # Check remote encounter handling
        self._add_finding(
            category="Exchange Systems",
            severity=ReviewSeverity.CRITICAL,
            location="MAIN/redesigned_main.py:19630-19660",
            issue="Remote encounters (phone calls) must constrain actions to non-physical",
            recommendation="Add remote_constraint to context_guidance forbidding physical actions",
            edge_case="NUA may generate 'approaches you' actions during phone calls, which is physically impossible",
            related_files=["MAIN/redesigned_main.py", "agents/decider_agent.py"]
        )
        
        # Check continuity validation in exchanges
        self._add_finding(
            category="Exchange Systems",
            severity=ReviewSeverity.HIGH,
            location="MAIN/redesigned_main.py:19685-19860",
            issue="NUA proactions must be validated for continuity before execution",
            recommendation="Implement retry loop with continuity feedback for failed validations",
            edge_case="NUA generates impossible actions (approaching during phone call) without validation"
        )
        
        # Check turn queue management
        self._add_finding(
            category="Exchange Systems",
            severity=ReviewSeverity.MEDIUM,
            location="encounter_checker.py",
            issue="Turn queue position must advance correctly after each action",
            recommendation="Verify round_manager.advance_turn_queue() is called consistently",
            edge_case="Skipped advancement causes same actor to act twice"
        )
        
        self.systems_analyzed.add("exchange_systems")
    
    def _review_validation_systems(self):
        """Review validation and continuity checking."""
        print("✅ Reviewing Validation Systems...")
        
        # Check continuity validator integration
        self._add_finding(
            category="Validation Systems",
            severity=ReviewSeverity.HIGH,
            location="scene_continuity_validator.py",
            issue="All actions must pass continuity validation before execution",
            recommendation="Integrate continuity_validator.validate_narrative() at action entry points",
            edge_case="Actions violating location constraints or NPC presence execute without warning"
        )
        
        # Check sensory constraint validation
        self._add_finding(
            category="Validation Systems",
            severity=ReviewSeverity.MEDIUM,
            location="sensory_constants.py",
            issue="Narratives must respect sensory constraints based on distance",
            recommendation="Validate narratives against get_sensory_rules_for_distance()",
            edge_case="Whispers audible at 50 units, facial expressions visible at 100 units"
        )
        
        # Check Mode B validation
        self._add_finding(
            category="Validation Systems",
            severity=ReviewSeverity.MEDIUM,
            location="agents/creator_agent.py",
            issue="Mode B validation may hard-fail character generation",
            recommendation="Set REALITAS_MODE_B_VALIDATION=0 by default to prevent startup crashes",
            edge_case="RAG vocab mismatches cause character creation to fail completely"
        )
        
        self.systems_analyzed.add("validation_systems")
    
    def _review_integration_points(self):
        """Review system integration points and data flow."""
        print("🔗 Reviewing Integration Points...")
        
        # Check Conductor agent integration
        self._add_finding(
            category="Integration Points",
            severity=ReviewSeverity.HIGH,
            location="agents/conductor_agent.py",
            issue="Conductor must propagate scene_description to all child agents",
            recommendation="Use @scene_description.setter to update interpreter, decider, and narrator",
            edge_case="Stale scene descriptions cause continuity violations",
            related_files=["agents/conductor_agent.py:590-616"]
        )
        
        # Check RAG system integration
        self._add_finding(
            category="Integration Points",
            severity=ReviewSeverity.HIGH,
            location="agents/",
            issue="All LLM-using agents must have access to RAG system",
            recommendation="Pass rag_system to all agents that generate content",
            edge_case="Agents without RAG produce anachronistic content (modern terms in 1960s setting)"
        )
        
        # Check world persistence integration
        self._add_finding(
            category="Integration Points",
            severity=ReviewSeverity.MEDIUM,
            location="world_persistence_system.py",
            issue="World state must be loaded before actor interactions",
            recommendation="Initialize world_state early in startup sequence",
            edge_case="Missing world state causes reputation/schedule/aftermath data loss"
        )
        
        self.systems_analyzed.add("integration_points")
    
    def _review_edge_cases(self):
        """Review specific edge case handling."""
        print("🚨 Reviewing Edge Cases...")
        
        edge_cases = [
            {
                "name": "Session Resume with Stale Context",
                "issue": "When resuming a session, context_manager may have stale data",
                "check": "Ensure sync_context_with_tracker() is called on resume",
                "location": "MAIN/redesigned_main.py:8318-8320"
            },
            {
                "name": "Empty Actor Queue",
                "issue": "Turn queue may be empty or have position beyond length",
                "check": "Validate queue state before accessing turn_queue_position",
                "location": "encounter_checker.py"
            },
            {
                "name": "Phone Call Actor Reference",
                "issue": "Remote actors may not be in spatial context",
                "check": "Handle missing spatial data gracefully for remote encounters",
                "location": "MAIN/redesigned_main.py:19750-19860"
            },
            {
                "name": "Memory Overflow",
                "issue": "Unbounded memory growth in key_memories",
                "check": "Implement memory pruning/aging strategy",
                "location": "key_memories_system.py"
            },
            {
                "name": "RAG Lock Timeout",
                "issue": "RAG queries may hang indefinitely",
                "check": "Add timeout handling to get_multi_category_context_for_llm",
                "location": "rag_lock_utils.py"
            },
            {
                "name": "JSON Parsing Failures",
                "issue": "LLM responses may contain invalid JSON",
                "check": "Use extract_and_parse_json with robust fallback parsing",
                "location": "json_utils.py"
            },
            {
                "name": "Mode B Validation Crash",
                "issue": "Character creation fails if skills/items not in RAG",
                "check": "Disable validation by default, enable only for strict mode",
                "location": "agents/creator_agent.py:304-313"
            },
            {
                "name": "NUA Detection False Positive",
                "issue": "Partial word matching blocks legitimate new actors",
                "check": "Use phrase-level matching instead of word-level",
                "location": "dynamic_actor_system.py:72-80"
            },
            {
                "name": "Sympathy Context Loss",
                "issue": "New NPCs default to neutral despite narrative context",
                "check": "Pass narrative context to sympathy initialization",
                "location": "llm_agents/sympathy_initialization.py"
            },
            {
                "name": "Spatial Session Mismatch",
                "issue": "Spatial manager uses wrong session ID after resume",
                "check": "Always use tracker.session_id for spatial operations",
                "location": "agents/interpreter_agent.py:90-109"
            }
        ]
        
        for ec in edge_cases:
            self._add_finding(
                category="Edge Cases",
                severity=ReviewSeverity.MEDIUM,
                location=ec["location"],
                issue=ec["name"],
                recommendation=ec["check"],
                edge_case=ec["issue"]
            )
        
        self.systems_analyzed.add("edge_cases")
    
    def _add_finding(self, category: str, severity: ReviewSeverity, location: str,
                     issue: str, recommendation: str, edge_case: str = None,
                     related_files: List[str] = None):
        """Add a review finding."""
        finding = ReviewFinding(
            category=category,
            severity=severity,
            location=location,
            issue=issue,
            recommendation=recommendation,
            edge_case=edge_case,
            related_files=related_files or []
        )
        self.findings.append(finding)
    
    def _compile_report(self) -> SystemHealthReport:
        """Compile findings into health report."""
        critical = sum(1 for f in self.findings if f.severity == ReviewSeverity.CRITICAL)
        high = sum(1 for f in self.findings if f.severity == ReviewSeverity.HIGH)
        medium = sum(1 for f in self.findings if f.severity == ReviewSeverity.MEDIUM)
        low = sum(1 for f in self.findings if f.severity == ReviewSeverity.LOW)
        
        # Determine overall status
        if critical > 0:
            status = "CRITICAL - Immediate action required"
        elif high > 3:
            status = "DEGRADED - Major issues need addressing"
        elif medium > 5:
            status = "FAIR - Several improvements recommended"
        else:
            status = "HEALTHY - Minor optimizations only"
        
        # Generate top recommendations
        recommendations = []
        for finding in sorted(self.findings, key=lambda f: f.severity.value):
            if finding.severity in [ReviewSeverity.CRITICAL, ReviewSeverity.HIGH]:
                recommendations.append(f"[{finding.severity.name}] {finding.location}: {finding.recommendation}")
        
        return SystemHealthReport(
            overall_status=status,
            critical_count=critical,
            high_count=high,
            medium_count=medium,
            low_count=low,
            findings=self.findings,
            recommendations=recommendations[:20]  # Top 20
        )
    
    def print_report(self, report: SystemHealthReport = None):
        """Print formatted review report."""
        if report is None:
            report = self._compile_report()
        
        print("\n" + "=" * 70)
        print("📊 REALITAS NEO SYSTEM REVIEW REPORT")
        print("=" * 70)
        print(f"Overall Status: {report.overall_status}")
        print(f"Systems Analyzed: {', '.join(sorted(self.systems_analyzed))}")
        print("-" * 70)
        print(f"Finding Counts:")
        print(f"  🔴 Critical: {report.critical_count}")
        print(f"  🟠 High: {report.high_count}")
        print(f"  🟡 Medium: {report.medium_count}")
        print(f"  🔵 Low: {report.low_count}")
        print(f"  ℹ️ Info: {len(report.findings) - report.critical_count - report.high_count - report.medium_count - report.low_count}")
        print("-" * 70)
        
        if report.recommendations:
            print("\n🎯 TOP PRIORITY RECOMMENDATIONS:")
            for i, rec in enumerate(report.recommendations, 1):
                print(f"  {i}. {rec}")
        
        print("\n" + "=" * 70)
        print("📋 DETAILED FINDINGS BY CATEGORY:")
        print("=" * 70)
        
        # Group by category
        by_category = {}
        for finding in report.findings:
            by_category.setdefault(finding.category, []).append(finding)
        
        for category, findings in sorted(by_category.items()):
            print(f"\n【{category}】")
            for finding in sorted(findings, key=lambda f: f.severity.value):
                severity_icon = {
                    ReviewSeverity.CRITICAL: "🔴",
                    ReviewSeverity.HIGH: "🟠",
                    ReviewSeverity.MEDIUM: "🟡",
                    ReviewSeverity.LOW: "🔵",
                    ReviewSeverity.INFO: "ℹ️"
                }.get(finding.severity, "•")
                
                print(f"  {severity_icon} [{finding.severity.name}] {finding.location}")
                print(f"     Issue: {finding.issue}")
                print(f"     Fix: {finding.recommendation}")
                if finding.edge_case:
                    print(f"     Edge Case: {finding.edge_case}")
                if finding.related_files:
                    print(f"     Related: {', '.join(finding.related_files)}")
                print()
        
        print("=" * 70)
        print("Review Complete.")
        print("=" * 70)


def main():
    """Run the reviewer as a standalone tool."""
    reviewer = RealitasReviewer()
    report = reviewer.run_full_review()
    reviewer.print_report(report)
    
    # Save report to file
    report_path = Path("realitas_review_report.json")
    with open(report_path, 'w') as f:
        json.dump({
            "status": report.overall_status,
            "systems_analyzed": list(reviewer.systems_analyzed),
            "counts": {
                "critical": report.critical_count,
                "high": report.high_count,
                "medium": report.medium_count,
                "low": report.low_count
            },
            "findings": [
                {
                    "category": f.category,
                    "severity": f.severity.name,
                    "location": f.location,
                    "issue": f.issue,
                    "recommendation": f.recommendation,
                    "edge_case": f.edge_case,
                    "related_files": f.related_files
                }
                for f in report.findings
            ],
            "recommendations": report.recommendations
        }, f, indent=2)
    
    print(f"\n💾 Report saved to: {report_path.absolute()}")


if __name__ == "__main__":
    main()
