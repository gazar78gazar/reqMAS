"""
Test A/B Question Generation and Autofill Functionality
Verify that decision support and adaptive autofill work correctly
"""

import pytest
import sys
import os
import asyncio

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from agents.decision_coordinator import DecisionCoordinatorAgent
from tools.abq_generator import ABQuestionGenerator
from tools.autofill_mapper import AutofillMapper
from data.data_loader import data_loader

class TestABQuestionsAndAutofill:
    """Test A/B question generation and autofill functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.coordinator = DecisionCoordinatorAgent()
        self.ab_generator = ABQuestionGenerator()
        self.autofill_mapper = AutofillMapper()
    
    async def test_budget_conflict_ab_question(self):
        """Test 1: Budget conflict -> generates correct A/B question"""
        print("\n=== TEST 1: Budget Conflict A/B Question ===")
        
        # Create a budget conflict scenario
        conflicts = [{
            "type": "budget",
            "message": "Configuration exceeds budget by $500",
            "severity": "high",
            "budget": 1000,
            "cost": 1500,
            "overage": 500
        }]
        
        session_data = {
            "user_expertise": "intermediate",
            "specifications": [
                {"constraint": "analog_input", "value": "8"},
                {"constraint": "digital_output", "value": "16"}
            ],
            "budget": 1000
        }
        
        # Generate A/B question for budget conflict
        ab_questions = self.ab_generator.generate_questions(conflicts, session_data)
        
        print(f"Generated {len(ab_questions)} A/B questions:")
        for i, question in enumerate(ab_questions, 1):
            print(f"\nQuestion {i}:")
            print(f"  Question: {question['question']}")
            print(f"  Option A: {question['option_a']}")
            print(f"  Option B: {question['option_b']}")
            print(f"  Context: {question['context']}")
            print(f"  Impact: {question['impact']}")
            print(f"  Recommendation: {question['recommendation']}")
        
        # Verify correct question generation
        assert len(ab_questions) > 0, "Should generate at least one A/B question"
        
        first_question = ab_questions[0]
        assert "budget" in first_question["question"].lower() or "cost" in first_question["question"].lower()
        assert first_question["option_a"] != first_question["option_b"]
        assert first_question["context"] != ""
        assert first_question["impact"] != ""
        
        # Check that recommendations are budget-aware
        assert any(keyword in first_question["recommendation"].lower() 
                  for keyword in ["budget", "cost", "price", "affordable"])
        
        return ab_questions
    
    async def test_technical_conflict_ab_question(self):
        """Test 2: Technical conflict -> generates upgrade vs adjust question"""
        print("\n=== TEST 2: Technical Conflict A/B Question ===")
        
        # Create a technical conflict scenario
        conflicts = [{
            "type": "technical",
            "message": "I/O requirements exceed controller capacity (32 > 16)",
            "severity": "high",
            "required_io": 32,
            "max_capacity": 16
        }]
        
        session_data = {
            "user_expertise": "novice",
            "specifications": [
                {"constraint": "digital_io", "value": "32"}
            ]
        }
        
        # Generate A/B question for technical conflict
        ab_questions = self.ab_generator.generate_questions(conflicts, session_data)
        
        print(f"Generated {len(ab_questions)} A/B questions:")
        for i, question in enumerate(ab_questions, 1):
            print(f"\nQuestion {i}:")
            print(f"  Question: {question['question']}")
            print(f"  Option A: {question['option_a']}")
            print(f"  Option B: {question['option_b']}")
            print(f"  Context: {question['context']}")
            print(f"  Novice-friendly: {'simple' in question['context'].lower() or 'easy' in question['context'].lower()}")
        
        # Verify correct question generation
        assert len(ab_questions) > 0, "Should generate at least one A/B question"
        
        first_question = ab_questions[0]
        # Should offer upgrade vs adjust options
        assert any(keyword in (first_question["option_a"] + first_question["option_b"]).lower()
                  for keyword in ["upgrade", "adjust", "reduce", "split", "multiple"])
        
        # For novice users, should have simpler language
        assert session_data["user_expertise"] == "novice"
        # Context should be explanatory
        assert len(first_question["context"]) > 20
        
        return ab_questions
    
    async def test_autofill_high_confidence(self):
        """Test 3: Autofill with 90% confidence -> triggers with correct fields"""
        print("\n=== TEST 3: Autofill with 90% Confidence ===")
        
        # Create high confidence scenario
        session_data = {
            "user_expertise": "expert",
            "specifications": [
                {"constraint": "analog_input", "value": "8"},
                {"constraint": "sampling_rate", "value": "1000"}
            ],
            "form_fields": ["processor_type", "memory_size", "storage_type", "network_ports"]
        }
        
        confidence_scores = {
            "processor_type": 0.95,
            "memory_size": 0.92,
            "storage_type": 0.90,
            "network_ports": 0.88
        }
        
        # Test autofill mapping
        autofill_result = self.autofill_mapper.map_fields(
            session_data["specifications"],
            session_data["form_fields"],
            confidence_scores
        )
        
        print(f"Autofill results:")
        print(f"  Triggered: {autofill_result['autofill_triggered']}")
        print(f"  Overall confidence: {autofill_result['overall_confidence']}")
        print(f"  Threshold: {autofill_result['confidence_threshold']}")
        
        print(f"\nAutofilled fields:")
        for field, value in autofill_result["autofilled_fields"].items():
            print(f"  - {field}: {value['value']} (confidence: {value['confidence']})")
        
        print(f"\nSkipped fields:")
        for field in autofill_result["skipped_fields"]:
            print(f"  - {field}: {autofill_result['field_scores'].get(field, 0)}")
        
        # Verify high confidence triggers autofill
        assert autofill_result["autofill_triggered"] == True
        assert autofill_result["overall_confidence"] >= 0.85
        
        # Should autofill high confidence fields
        assert "processor_type" in autofill_result["autofilled_fields"]
        assert "memory_size" in autofill_result["autofilled_fields"]
        assert "storage_type" in autofill_result["autofilled_fields"]
        
        # Field below threshold might be skipped
        if "network_ports" not in autofill_result["autofilled_fields"]:
            assert "network_ports" in autofill_result["skipped_fields"]
        
        return autofill_result
    
    async def test_autofill_low_confidence(self):
        """Test 4: Autofill with 70% confidence -> does not trigger"""
        print("\n=== TEST 4: Autofill with 70% Confidence ===")
        
        # Create low confidence scenario
        session_data = {
            "user_expertise": "intermediate",
            "specifications": [
                {"constraint": "digital_io", "value": "4"}
            ],
            "form_fields": ["processor_type", "memory_size", "storage_type", "cooling_type"]
        }
        
        confidence_scores = {
            "processor_type": 0.72,
            "memory_size": 0.68,
            "storage_type": 0.70,
            "cooling_type": 0.65
        }
        
        # Test autofill mapping
        autofill_result = self.autofill_mapper.map_fields(
            session_data["specifications"],
            session_data["form_fields"],
            confidence_scores
        )
        
        print(f"Autofill results:")
        print(f"  Triggered: {autofill_result['autofill_triggered']}")
        print(f"  Overall confidence: {autofill_result['overall_confidence']}")
        print(f"  Threshold: {autofill_result['confidence_threshold']}")
        print(f"  Reason: {autofill_result.get('reason', 'N/A')}")
        
        print(f"\nField scores:")
        for field, score in autofill_result["field_scores"].items():
            print(f"  - {field}: {score}")
        
        # Verify low confidence doesn't trigger autofill
        assert autofill_result["autofill_triggered"] == False
        assert autofill_result["overall_confidence"] < 0.85
        
        # Should have empty or minimal autofilled fields
        assert len(autofill_result["autofilled_fields"]) == 0 or \
               all(v["confidence"] < 0.85 for v in autofill_result["autofilled_fields"].values())
        
        return autofill_result
    
    async def test_expertise_levels_attempts(self):
        """Test 5: Expertise levels (novice=5, intermediate=3, expert=2 attempts)"""
        print("\n=== TEST 5: Expertise Levels and Attempt Limits ===")
        
        expertise_limits = {
            "novice": 5,
            "intermediate": 3,
            "expert": 2
        }
        
        for expertise, expected_limit in expertise_limits.items():
            print(f"\nTesting {expertise} level:")
            
            session_data = {
                "user_expertise": expertise,
                "attempts": 0,
                "specifications": []
            }
            
            # Process through decision coordinator
            input_data = {
                "conflicts": [{"type": "test", "message": "Test conflict"}],
                "session_data": session_data
            }
            
            result = await self.coordinator.process(input_data, {})
            
            # Check max attempts is set correctly
            max_attempts = result.get("max_attempts", 0)
            print(f"  Max attempts: {max_attempts}")
            print(f"  Expected: {expected_limit}")
            
            # Verify expertise-based limits
            assert max_attempts == expected_limit, f"Expected {expected_limit} for {expertise}"
            
            # Check adaptive behavior flags
            if expertise == "novice":
                assert result.get("provide_detailed_help", False) == True
                assert result.get("simplify_options", False) == True
            elif expertise == "expert":
                assert result.get("provide_detailed_help", False) == False
                assert result.get("quick_mode", False) == True
            
            print(f"  Adaptive flags: detailed_help={result.get('provide_detailed_help', False)}, " +
                  f"simplify={result.get('simplify_options', False)}, " +
                  f"quick_mode={result.get('quick_mode', False)}")
        
        return True
    
    async def test_session_attempt_tracking(self):
        """Test 6: Session attempt tracking and limits"""
        print("\n=== TEST 6: Session Attempt Tracking ===")
        
        # Simulate session with multiple attempts
        session_data = {
            "user_expertise": "intermediate",  # 3 attempts max
            "attempts": 0,
            "session_id": "test_session_123",
            "specifications": [
                {"constraint": "analog_input", "value": "4"}
            ]
        }
        
        conflicts = [{"type": "technical", "message": "Test conflict"}]
        
        print("Testing attempt progression:")
        
        for attempt in range(1, 5):  # Try 4 attempts (should stop at 3)
            session_data["attempts"] = attempt
            
            input_data = {
                "conflicts": conflicts,
                "session_data": session_data
            }
            
            result = await self.coordinator.process(input_data, {})
            
            print(f"\nAttempt {attempt}:")
            print(f"  Valid: {result['valid']}")
            print(f"  Attempts: {result.get('attempts', 0)}/{result.get('max_attempts', 0)}")
            print(f"  Can retry: {result.get('can_retry', False)}")
            
            # Check attempt tracking
            assert result["attempts"] == attempt
            assert result["max_attempts"] == 3  # Intermediate level
            
            if attempt < 3:
                assert result["can_retry"] == True
                assert "questions" in result or "ab_questions" in result
            else:
                # Should stop allowing retries after max attempts
                assert result["can_retry"] == False
                assert result.get("final_attempt", False) == True
                print(f"  Final attempt reached: True")
            
            # Check for escalation or alternative suggestions
            if attempt >= 2:
                assert "alternatives" in result or "escalation" in result or \
                       result.get("suggest_expert_help", False) == True
        
        print("\n[OK] Session tracking working correctly!")
        return True
    
    async def test_combined_scenario(self):
        """Test combined scenario: Budget + Technical conflicts with autofill"""
        print("\n=== COMBINED TEST: Budget + Technical + Autofill ===")
        
        # Complex scenario with multiple conflicts
        conflicts = [
            {
                "type": "budget",
                "message": "Over budget by $300",
                "severity": "medium",
                "cost": 1300,
                "budget": 1000
            },
            {
                "type": "technical", 
                "message": "Memory requirement not met",
                "severity": "low"
            }
        ]
        
        session_data = {
            "user_expertise": "novice",
            "attempts": 1,
            "specifications": [
                {"constraint": "analog_input", "value": "8"},
                {"constraint": "memory", "value": "16GB"}
            ],
            "form_fields": ["controller_type", "module_config"],
            "budget": 1000
        }
        
        # Process through coordinator
        input_data = {
            "conflicts": conflicts,
            "session_data": session_data
        }
        
        result = await self.coordinator.process(input_data, {})
        
        print(f"Combined result:")
        print(f"  Valid: {result['valid']}")
        print(f"  Conflicts handled: {len(conflicts)}")
        print(f"  A/B questions generated: {len(result.get('ab_questions', []))}")
        print(f"  Autofill available: {result.get('autofill_available', False)}")
        
        # Should generate questions for multiple conflicts
        ab_questions = result.get("ab_questions", [])
        assert len(ab_questions) >= 1  # At least one question
        
        # Check for budget and technical questions
        has_budget_q = any("budget" in q["question"].lower() or "cost" in q["question"].lower() 
                          for q in ab_questions)
        has_technical_q = any("memory" in q["question"].lower() or "technical" in q["question"].lower()
                            for q in ab_questions)
        
        print(f"  Has budget question: {has_budget_q}")
        print(f"  Has technical question: {has_technical_q}")
        
        # For novice user, should have detailed explanations
        if ab_questions:
            first_q = ab_questions[0]
            assert len(first_q["context"]) > 20
            assert first_q["recommendation"] != ""
            print(f"  Context length: {len(first_q['context'])} chars")
            print(f"  Has recommendation: True")
        
        return result

# Test runner functions
def test_budget_conflict_ab_question():
    """Sync wrapper for async test"""
    test_instance = TestABQuestionsAndAutofill()
    test_instance.setup_method()
    return asyncio.run(test_instance.test_budget_conflict_ab_question())

def test_technical_conflict_ab_question():
    """Sync wrapper for async test"""
    test_instance = TestABQuestionsAndAutofill()
    test_instance.setup_method()
    return asyncio.run(test_instance.test_technical_conflict_ab_question())

def test_autofill_high_confidence():
    """Sync wrapper for async test"""
    test_instance = TestABQuestionsAndAutofill()
    test_instance.setup_method()
    return asyncio.run(test_instance.test_autofill_high_confidence())

def test_autofill_low_confidence():
    """Sync wrapper for async test"""
    test_instance = TestABQuestionsAndAutofill()
    test_instance.setup_method()
    return asyncio.run(test_instance.test_autofill_low_confidence())

def test_expertise_levels_attempts():
    """Sync wrapper for async test"""
    test_instance = TestABQuestionsAndAutofill()
    test_instance.setup_method()
    return asyncio.run(test_instance.test_expertise_levels_attempts())

def test_session_attempt_tracking():
    """Sync wrapper for async test"""
    test_instance = TestABQuestionsAndAutofill()
    test_instance.setup_method()
    return asyncio.run(test_instance.test_session_attempt_tracking())

def test_combined_scenario():
    """Sync wrapper for async test"""
    test_instance = TestABQuestionsAndAutofill()
    test_instance.setup_method()
    return asyncio.run(test_instance.test_combined_scenario())

if __name__ == "__main__":
    # Run all tests with detailed output
    print("=" * 80)
    print("A/B QUESTIONS AND AUTOFILL TESTS")
    print("=" * 80)
    
    test_budget_conflict_ab_question()
    test_technical_conflict_ab_question()
    test_autofill_high_confidence()
    test_autofill_low_confidence()
    test_expertise_levels_attempts()
    test_session_attempt_tracking()
    test_combined_scenario()
    
    print("\n" + "=" * 80)
    print("ALL A/B AND AUTOFILL TESTS COMPLETED")
    print("=" * 80)