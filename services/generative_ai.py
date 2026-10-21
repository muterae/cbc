import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))



def predict_band():
    # fetch student profile
    # return AE, BE, ME or EE
    pass


def generate_quiz():
    # predicted_band = predict_band()
    # prompt model with predicted_band
    # return quiz
    pass
