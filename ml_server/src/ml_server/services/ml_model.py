import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer


class Model:
    def __init__(self):
        model_name = "tabularisai/multilingual-sentiment-analysis"
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
        self.model.eval()

        for param in self.model.parameters():
            param.requires_grad_(False)

        # self.model = torch.compile(self.model)

    def predict(self, texts):
        inputs = self.tokenizer(
            texts, return_tensors="pt", truncation=True, padding=True, max_length=512
        )
        with torch.inference_mode():
            outputs = self.model(**inputs)
        probabilities = torch.nn.functional.softmax(outputs.logits, dim=-1)
        sentiment_map = {
            0: "Very Negative",
            1: "Negative",
            2: "Neutral",
            3: "Positive",
            4: "Very Positive",
        }
        return [sentiment_map[p] for p in torch.argmax(probabilities, dim=-1).tolist()]
