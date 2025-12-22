import os
import numpy as np
from typing import List, Tuple

try:
    from sentence_transformers import SentenceTransformer
    import torch
    MODEL_AVAILABLE = True
except ImportError:
    SentenceTransformer = None
    torch = None
    MODEL_AVAILABLE = False

# Try to import transformers for answer generation
try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False


class HuggingFaceAnswerMatcher:
    """
    A class to match answers using Hugging Face sentence transformers model.
    Uses sentence-transformers/all-MiniLM-L6-v2 for semantic similarity.
    """
    
    def __init__(self, hf_api_key: str = None):
        """
        Initialize the matcher with Hugging Face API key.
        
        Args:
            hf_api_key (str): Hugging Face API key for authentication
        """
        self.hf_api_key = hf_api_key or os.getenv("HF_API_KEY")
        self.model = None
        self.generator = None
        self._initialize_model()
        self._initialize_generator()
    
    def _initialize_model(self):
        """
        Initialize the sentence transformer model with Hugging Face authentication.
        """
        if not MODEL_AVAILABLE:
            print("Sentence Transformers not available")
            self.model = None
            return
            
        try:
            # Set the API token for Hugging Face
            if self.hf_api_key:
                try:
                    from huggingface_hub import login
                    login(token=self.hf_api_key)
                except ImportError:
                    print("huggingface_hub not available for login")
                except Exception as e:
                    print(f"Failed to login to Hugging Face: {e}")
            
            # Load the model
            self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        except Exception as e:
            print(f"Error initializing Hugging Face model: {e}")
            self.model = None
    
    def _initialize_generator(self):
        """
        Initialize the text generation model for answer generation.
        """
        if not TRANSFORMERS_AVAILABLE:
            print("Transformers not available for text generation")
            self.generator = None
            return
            
        try:
            # Initialize a text generation pipeline
            # Using a lightweight model suitable for answer generation
            self.generator = pipeline("text-generation", model="gpt2", max_new_tokens=100)
        except Exception as e:
            print(f"Error initializing text generation model: {e}")
            self.generator = None
    
    def generate_expected_answer(self, question: str) -> str:
        """
        Generate an expected answer for a given question using the model.
        
        Args:
            question (str): The interview question
            
        Returns:
            str: Generated expected answer
        """
        # If we have a generator model, use it to generate an answer
        if self.generator:
            try:
                prompt = f"Question: {question}\nAnswer:"
                generated = self.generator(prompt, max_new_tokens=150, num_return_sequences=1, truncation=True)
                answer = generated[0]['generated_text']
                
                # Extract just the answer part (remove the prompt)
                if "Answer:" in answer:
                    answer = answer.split("Answer:", 1)[1].strip()
                
                # Clean up the answer
                answer = answer.split("\n\n")[0].strip()  # Take first paragraph
                return answer
            except Exception as e:
                print(f"Error generating answer: {e}")
        
        # Fallback to a template approach
        return f"A comprehensive answer to the question '{question}' would include relevant technical details and demonstrate understanding of the concepts involved."
    
    def compute_similarity(self, text1: str, text2: str) -> float:
        """
        Compute semantic similarity between two texts using the model.
        
        Args:
            text1 (str): First text
            text2 (str): Second text
            
        Returns:
            float: Similarity score between 0 and 1
        """
        if not text1 or not text2 or not self.model:
            return 0.0
        
        try:
            # Encode both texts
            embeddings = self.model.encode([text1, text2], convert_to_tensor=True)
            
            # Compute cosine similarity
            similarity = torch.cosine_similarity(embeddings[0].unsqueeze(0), 
                                               embeddings[1].unsqueeze(0)).item()
            
            # Normalize to 0-1 range
            return max(0.0, min(1.0, (similarity + 1.0) / 2.0))
        except Exception as e:
            print(f"Error computing similarity: {e}")
            return 0.0
    
    def match_answer(self, question: str, candidate_answer: str, 
                     expected_answer: str = None) -> Tuple[float, str]:
        """
        Match a candidate's answer against an expected answer for a given question.
        
        Args:
            question (str): The interview question
            candidate_answer (str): The candidate's answer
            expected_answer (str): The expected answer (optional)
            
        Returns:
            Tuple[float, str]: Similarity score and feedback
        """
        if not candidate_answer:
            return 0.0, "No answer provided"
        
        # Generate expected answer if not provided
        if not expected_answer:
            expected_answer = self.generate_expected_answer(question)
        
        # Compute similarity between candidate answer and expected answer
        similarity = self.compute_similarity(candidate_answer, expected_answer)
        
        # Provide feedback based on similarity score
        if similarity >= 0.8:
            feedback = "Excellent answer match"
        elif similarity >= 0.6:
            feedback = "Good answer match"
        elif similarity >= 0.4:
            feedback = "Moderate answer match"
        elif similarity >= 0.2:
            feedback = "Low answer match"
        else:
            feedback = "Poor answer match"
        
        return similarity, feedback


# Example usage
if __name__ == "__main__":
    # Initialize with your Hugging Face API key
    matcher = HuggingFaceAnswerMatcher("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")
    
    # Test with sample data
    question = "What is the difference between lists and tuples in Python?"
    candidate_answer = "Lists are mutable while tuples are immutable. Lists use square brackets and tuples use parentheses."
    expected_answer = "Lists are mutable data structures that can be modified after creation, while tuples are immutable and cannot be changed once created. Lists are defined with square brackets [] and tuples with parentheses ()."
    
    score, feedback = matcher.match_answer(question, candidate_answer, expected_answer)
    print(f"Similarity Score: {score:.2f}")
    print(f"Feedback: {feedback}")