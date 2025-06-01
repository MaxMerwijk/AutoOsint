from openai import OpenAI
import time

class Openrouter:
    def __init__(self, config):
        self.config = config
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.config['OpenrouterKey']
        )
        self.models = {
            'fast': "google/gemini-2.0-flash-001",
            'balanced': "google/gemini-2.5-pro-preview-03-25",
            'powerful': "anthropic/claude-3-opus"
        }

    def get_completion(self, prompt, mode='balanced', retries=3, delay=2):
        model = self.models.get(mode, self.models['balanced'])
        
        for attempt in range(retries):
            try:
                completion = self.client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.4,
                    max_tokens=4096,
                    top_p=0.95,
                    frequency_penalty=0.1,
                    presence_penalty=0.1,
                    stop=None,
                    stream=False
                )
                return completion.choices[0].message.content
            except Exception as e:
                if attempt == retries - 1:
                    raise e
                time.sleep(delay * (attempt + 1))
                
    def get_streaming_completion(self, prompt, mode='balanced'):
        model = self.models.get(mode, self.models['balanced'])
        
        completion = self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.4,
            max_tokens=4096,
            top_p=0.95,
            frequency_penalty=0.1,
            presence_penalty=0.1,
            stop=None,
            stream=True
        )
        return completion