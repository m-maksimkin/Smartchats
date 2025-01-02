from llama_index.core.callbacks import LlamaDebugHandler, CBEventType


class CustomLlamaInfoHandler(LlamaDebugHandler):
    def on_event_end(self, event_type, payload, event_id, **kwargs):
        if event_type == CBEventType.LLM:
            prompts = payload.get("messages")
            if prompts:
                self.logger.info(f"LLM Prompt:\n{'\n'.join(str(i) for i in prompts)}")
        super().on_event_end(event_type, payload, event_id, **kwargs)

    def _print(self, print_str: str) -> None:
        if self.logger:
            self.logger.info(print_str)
        else:
            # This branch is to preserve existing behavior.
            print(print_str, flush=True)