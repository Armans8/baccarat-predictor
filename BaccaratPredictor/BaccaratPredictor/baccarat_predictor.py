import numpy as np
import pandas as pd
from collections import Counter, deque

class BaccaratPredictor:
    """Class to handle baccarat prediction logic"""
    
    def __init__(self, history):
        self.history = history
        # Weights for prediction methods
        self.method_weights = {
            'pattern_recognition': 0.4,
            'frequency_analysis': 0.3,
            'streak_analysis': 0.3
        }
        
    def predict_next(self):
        """
        Predicts the next outcome based on historical data
        
        Returns:
            tuple: (prediction, confidence percentage)
        """
        if len(self.history) < 4:
            # Not enough data, return a default prediction with low confidence
            return "B", 50
            
        # Combine multiple prediction methods for a more robust prediction
        predictions = {}
        
        # Method 1: Pattern Recognition
        pattern_pred, pattern_conf = self._pattern_recognition()
        predictions['pattern_recognition'] = (pattern_pred, pattern_conf)
        
        # Method 2: Frequency Analysis
        freq_pred, freq_conf = self._frequency_analysis()
        predictions['frequency_analysis'] = (freq_pred, freq_conf)
        
        # Method 3: Streak Analysis
        streak_pred, streak_conf = self._streak_analysis()
        predictions['streak_analysis'] = (streak_pred, streak_conf)
        
        # Weighted combination of predictions
        final_pred = self._combine_predictions(predictions)
        confidence = self._calculate_confidence(predictions, final_pred)
        
        return final_pred, confidence
        
    def _pattern_recognition(self):
        """
        Look for repeating patterns in the history
        
        Returns:
            tuple: (prediction, confidence)
        """
        if len(self.history) < 8:
            return "B", 40
            
        # Look for patterns of different lengths
        best_pattern = None
        best_confidence = 0
        
        # Look for patterns of length 2-5
        for pattern_len in range(2, 6):
            if len(self.history) < pattern_len * 2:
                continue
                
            # Get the most recent pattern
            recent_pattern = self.history[-pattern_len:]
            
            # Count how many times this pattern occurs
            pattern_occurrences = 0
            next_outcomes = []
            
            for i in range(len(self.history) - pattern_len):
                check_pattern = self.history[i:i+pattern_len]
                if check_pattern == recent_pattern:
                    pattern_occurrences += 1
                    if i + pattern_len < len(self.history):
                        next_outcomes.append(self.history[i + pattern_len])
            
            if pattern_occurrences >= 2 and next_outcomes:
                # Count the occurrences of each outcome after this pattern
                outcome_counts = Counter(next_outcomes)
                most_common = outcome_counts.most_common(1)[0]
                
                # Calculate confidence based on consistency of the pattern
                confidence = (most_common[1] / len(next_outcomes)) * 100
                
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_pattern = most_common[0]
        
        if best_pattern:
            return best_pattern, best_confidence
        else:
            return "B", 40  # Default if no pattern found
    
    def _frequency_analysis(self):
        """
        Analyze the frequency of outcomes
        
        Returns:
            tuple: (prediction, confidence)
        """
        if not self.history:
            return "B", 40
            
        # Count occurrences
        counts = {"B": 0, "P": 0, "T": 0}
        for outcome in self.history:
            counts[outcome] += 1
            
        # Calculate probabilities
        total = len(self.history)
        probabilities = {k: (v / total) * 100 for k, v in counts.items()}
        
        # Return the outcome with highest probability
        if probabilities["B"] >= probabilities["P"] and probabilities["B"] >= probabilities["T"]:
            pred = "B"
            conf = min(70, 40 + (probabilities["B"] - 33.3))
        elif probabilities["P"] >= probabilities["B"] and probabilities["P"] >= probabilities["T"]:
            pred = "P"
            conf = min(70, 40 + (probabilities["P"] - 33.3))
        else:
            pred = "T"
            conf = min(70, 40 + (probabilities["T"] - 33.3))
            
        return pred, conf
        
    def _streak_analysis(self):
        """
        Analyze streaks and alternating patterns
        
        Returns:
            tuple: (prediction, confidence)
        """
        if len(self.history) < 4:
            return "B", 40
            
        # Check for streaks (same outcome repeated)
        last_outcome = self.history[-1]
        streak_length = 1
        
        for i in range(len(self.history) - 2, -1, -1):
            if self.history[i] == last_outcome:
                streak_length += 1
            else:
                break
                
        # Check for alternating pattern
        alternating = True
        if len(self.history) >= 4:
            for i in range(len(self.history) - 3, len(self.history) - 1):
                if self.history[i] == self.history[i - 2]:
                    continue
                else:
                    alternating = False
                    break
        else:
            alternating = False
            
        # Make prediction based on streak or alternating pattern
        if streak_length >= 3:
            # After long streaks, often a change occurs
            opposite = {"B": "P", "P": "B", "T": "B"}
            return opposite[last_outcome], 60
        elif alternating and len(self.history) >= 4:
            # Predict next in alternating pattern
            return self.history[-2], 65
        else:
            # If no clear pattern, slightly favor continuing the last outcome
            return last_outcome, 55
            
    def _combine_predictions(self, predictions):
        """
        Combine predictions from different methods
        
        Args:
            predictions: Dictionary of prediction methods and their results
            
        Returns:
            str: Final prediction
        """
        # Count votes with weighting
        votes = {"B": 0, "P": 0, "T": 0}
        
        for method, (pred, conf) in predictions.items():
            weight = self.method_weights.get(method, 0.33)
            votes[pred] += weight * (conf / 100)
            
        # Return the outcome with highest weighted vote
        if votes["B"] >= votes["P"] and votes["B"] >= votes["T"]:
            return "B"
        elif votes["P"] >= votes["B"] and votes["P"] >= votes["T"]:
            return "P"
        else:
            return "T"
            
    def _calculate_confidence(self, predictions, final_pred):
        """
        Calculate overall confidence level for the final prediction
        
        Args:
            predictions: Dictionary of prediction methods and their results
            final_pred: The final prediction
            
        Returns:
            int: Confidence percentage (0-100)
        """
        total_confidence = 0
        total_weight = 0
        
        for method, (pred, conf) in predictions.items():
            weight = self.method_weights.get(method, 0.33)
            
            # If this method agrees with final prediction, use its confidence
            # Otherwise, use a reduced confidence
            if pred == final_pred:
                method_contribution = conf * weight
            else:
                method_contribution = (100 - conf) * weight
                
            total_confidence += method_contribution
            total_weight += weight
            
        # Calculate weighted average confidence
        overall_confidence = total_confidence / total_weight if total_weight > 0 else 50
        
        # Ensure confidence is between 50 and 90
        adjusted_confidence = min(max(overall_confidence, 50), 90)
        
        return int(adjusted_confidence)
