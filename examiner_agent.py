import os
from typing import List, Dict, Any, Optional
from openai import OpenAI
import json

class ExaminerAgent:
    def __init__(self, api_key: str, model: str = "llama-3.3-70b-versatile", base_url: str = None, temperature: float = 0.3):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self.temperature = temperature

    def generate_response(
        self, 
        messages: List[Dict[str, str]], 
        current_topic: Optional[str], 
        topics_remaining: List[str]
    ) -> Any:
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "transition_topic",
                    "description": "Call this to move to the next topic. Provide a score (number 0-10) and reasoning.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "topic_score": {
                                "type": "number", 
                                "description": "Score for the current topic (0 to 10). Must be a number, not a string."
                            },
                            "reasoning": {
                                "type": "string", 
                                "description": "Brief reasoning for the score."
                            },
                            "next_topic_name": {
                                "type": "string",
                                "description": "The name of the next topic."
                            }
                        },
                        "required": ["topic_score", "reasoning"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "finish_exam",
                    "description": "Call this when the exam is finished (no topics remaining).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "final_score": {
                                "type": "number", 
                                "description": "Overall score (0 to 10). Must be a number."
                            },
                            "feedback": {
                                "type": "string", 
                                "description": "Detailed feedback for the student."
                            }
                        },
                        "required": ["final_score", "feedback"]
                    }
                }
            }
        ]

        system_content = (
            "You are a professional technical interviewer AI. "
            f"You are examining a student.\n"
        )
        
        if current_topic:
            system_content += (
                f"The CURRENT TOPIC is: '{current_topic}'.\n"
                "Ask questions to probe the student's understanding. "
                "Start general, then drill down or give hints if needed.\n"
                "When satisfied, OR if the student gives up, YOU MUST call the 'transition_topic' tool immediately. "
                "Do not output text when you intend to call a tool."
            )
            if topics_remaining:
                system_content += f" Future topics: {', '.join(topics_remaining)}."
            else:
                system_content += " This is the last topic."
        else:
            system_content += "The exam is finished. Review the history and call 'finish_exam'."

        full_messages = [{"role": "system", "content": system_content}] + messages

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=full_messages,
                tools=tools,
                tool_choice="auto",
                temperature=self.temperature
            )
            return response.choices[0].message
        except Exception as e:
            return str(e)
