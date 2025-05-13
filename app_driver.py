from openai import OpenAI, AssistantEventHandler
import os
import pathlib
from dotenv import load_dotenv
from typing_extensions import override
import time

# Load environment variables
load_dotenv()  # This loads OPENAI_API_KEY and ASSISTANT_ID from .env

class AppDriver:
    def __init__(self):
        # Validate environment variables
        assert os.getenv("OPENAI_API_KEY"), "Add OPENAI_API_KEY to .env"
        assert os.getenv("ASSISTANT_ID"), "Add ASSISTANT_ID (asst_...) to .env"

        # Initialize the OpenAI client with the API key
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.assistant_id = os.getenv("ASSISTANT_ID")  # Load assistant ID from .env

        # Load the base prompt from prompt.txt
        prompt_file = pathlib.Path(__file__).parent / "prompt.txt"
        if (prompt_file.exists()):
            self.base_prompt = prompt_file.read_text(encoding="utf-8")  # Force UTF-8 encoding
        else:
            raise ValueError("prompt.txt not found – add your system prompt there.")

    def ask_llm(self, question: str, file_text: str = "", temperature: float = 0.7):
        # Construct the full prompt
        full_prompt = f"""{self.base_prompt}

        Uploaded file context:
        {file_text[:3000]}

        User question:
        {question}

        Respond clearly; always include: 'This is educational only and not investment advice.'
        """

        # Call the OpenAI API using the new v1.x syntax
        resp = self.client.chat.completions.create(
            model="gpt-4.1",  # Replace with "gpt-4o" or "gpt-4-turbo" as needed
            messages=[{"role": "user", "content": full_prompt}],
            temperature=temperature,
        )

        # Return the assistant's response
        return resp.choices[0].message.content

    def wait_for_run(self, thread_id, run_id, max_wait=60):
        """Polls the run until status=='completed' or error. Returns assistant text."""
        delay = 1.0
        start = time.time()

        while True:
            run = self.client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)

            if run.status == "completed":
                msgs = self.client.beta.threads.messages.list(thread_id=thread_id, limit=1)
                return msgs.data[0].content[0].text.value

            if run.status in ("failed", "cancelled", "expired"):
                raise RuntimeError(f"Run ended with status: {run.status}")

            if time.time() - start > max_wait:
                raise TimeoutError("Run polling timed out.")

            time.sleep(delay)
            delay = min(delay * 2, 10)  # exponential back-off, cap at 10 seconds

    def ask_with_assistant(self, user_question: str, file_text: str = "", temperature: float = 0.7):
        try:
            # 1. Create a thread
            thread = self.client.beta.threads.create()

            # 2. Add the user message
            content = user_question
            if file_text:
                content += f"\n\n[Context from uploaded file]\n{file_text[:3000]}"

            self.client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=content,
            )

            # 3. Run the assistant
            run = self.client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=self.assistant_id,
                temperature=temperature,
            )

            # 4. Wait for completion
            return self.wait_for_run(thread.id, run.id)

        except OpenAIError as e:
            return f"OpenAI API error: {e}"
        except Exception as exc:
            return f"Error: {exc}"
