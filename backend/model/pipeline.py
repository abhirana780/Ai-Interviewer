import os
try:
    from gpt4all import GPT4All
except Exception:
    GPT4All = None


class ModelPipeline:
    def __init__(self, model_dir):
        self.model = None
        self.backend = None

        # Load GPT4All model if available
        model_file = None
        if os.path.isdir(model_dir):
            for f in os.listdir(model_dir):
                if f.endswith(".bin") or f.endswith(".gguf"):
                    model_file = os.path.join(model_dir, f)
                    break

        loaded = False
        if GPT4All and model_file:
            try:
                model_name = os.path.basename(model_file)
                model_path = os.path.dirname(model_file)
                self.model = GPT4All(model_name, model_path=model_path)
                self.backend = "gpt4all"
                loaded = True
            except Exception:
                pass
        if not loaded:
            try:
                from transformers import pipeline, set_seed
                set_seed(42)
                self.model = pipeline("text-generation", model="distilgpt2")
                self.backend = "transformers"
                loaded = True
            except Exception:
                self.backend = "basic"

    def generate(self, prompt, max_length=120):
        if self.backend == "gpt4all" and isinstance(self.model, GPT4All):
            return self.model.generate(prompt, max_tokens=max_length)

        if self.backend == "transformers" and self.model:
            out = self.model(prompt, max_length=max_length, num_return_sequences=1)[0].get("generated_text", "")
            if out.startswith(prompt):
                out = out[len(prompt):]
            return out.strip()

        lower = (prompt or "").lower()
        if "follow-up" in lower or "ask" in lower:
            return "Can you elaborate on your approach and trade-offs?"
        return "Please provide more details."
