import heapq
import json
import os
import google.generativeai as genai
from dataclasses import dataclass, field
from typing import Tuple

# --- CONFIGURATION ---
# Replace this with your actual API key
API_KEY = "AIzaSyAh5xaEQR81mOmCf5SsyIFZpykQXfhQgGE"

# Configure the Gemini API
genai.configure(api_key=API_KEY)

# --- 1. The Data Structure ---
@dataclass(order=True)
class Complaint:
    sort_index: int = field(init=False, repr=False)
    severity: int
    complaint_id: str = field(compare=False)
    text: str = field(compare=False)
    reasoning: str = field(compare=False) # New: AI explains WHY it picked this score

    def __post_init__(self):
        # Sort by negative severity so higher numbers come first (Max-Heap)
        self.sort_index = -self.severity

# --- 2. The Gemini AI Module ---
class GeminiAnalyzer:
    def __init__(self):
        # We use Gemini 1.5 Flash because it is fast and cheap for this task
        self.model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            generation_config={"response_mime_type": "application/json"}
        )

    def analyze_complaint(self, text: str) -> Tuple[int, str]:
        """
        Sends text to Gemini and retrieves a severity score (1-10) and reasoning.
        """
        prompt = f"""
        You are an expert customer service manager. Analyze the following complaint.
        
        Complaint: "{text}"
        
        Task:
        1. Assign a "severity" score from 1 (Low priority) to 10 (Critical/Emergency).
        2. Provide a short "reasoning" (max 10 words).
        
        Rules for scoring:
        - 10: Life safety, fire, massive security breach, legal threat.
        - 7-9: System outage, financial loss, extreme anger/churn risk.
        - 4-6: Bug, annoyance, slow service.
        - 1-3: Feature request, cosmetic issue, mild feedback.
        
        Output JSON format: {{ "severity": int, "reasoning": "string" }}
        """
        
        try:
            response = self.model.generate_content(prompt)
            data = json.loads(response.text)
            return data["severity"], data["reasoning"]
        except Exception as e:
            print(f"[Error] Gemini API failed: {e}")
            return 5, "Manual review needed (AI Failed)"

# --- 3. The Central System ---
class SmartComplaintSystem:
    def __init__(self):
        self.queue = []
        self.ai = GeminiAnalyzer()
        self.counter = 1

    def receive_complaint(self, text: str):
        print(f"\n[System] Sending to Gemini API: '{text[:40]}...'")
        
        # Call Gemini
        severity, reasoning = self.ai.analyze_complaint(text)
        
        # Create Complaint Object
        comp_id = f"C-{self.counter:03d}"
        complaint = Complaint(severity=severity, complaint_id=comp_id, text=text, reasoning=reasoning)
        
        # Push to Queue
        heapq.heappush(self.queue, complaint)
        self.counter += 1
        
        print(f" -> AI Score: {severity}/10")
        print(f" -> Reason:   {reasoning}")

    def process_queue(self):
        if not self.queue:
            print("\n[System] No pending complaints.")
            return

        # Pop the most severe complaint
        current = heapq.heappop(self.queue)
        
        print(f"\n{'!'*5} HANDLING HIGH PRIORITY {'!'*5}")
        print(f"ID:       {current.complaint_id}")
        print(f"Severity: {current.severity}/10")
        print(f"Reason:   {current.reasoning}")
        print(f"Message:  {current.text}")
        print("-" * 40)
        
        input("Press Enter to mark as Resolved...")
        print("✅ Resolved.")

# --- 4. Main Execution ---
if __name__ == "__main__":
    # Safety check for API Key
    if API_KEY == "YOUR_GEMINI_API_KEY_HERE":
        print("❌ ERROR: Please paste your Gemini API Key in line 10 of the code!")
        exit()

    system = SmartComplaintSystem()

    # Process them in order of priority (AI decided)
    while True:
        cmd = input("\n[P]rocess Next | [A]dd New | [E]xit: ").lower()
        if cmd == 'p':
            system.process_queue()
        elif cmd == 'a':
            txt = input("Complaint text: ")
            system.receive_complaint(txt)
        elif cmd == 'e':
            break