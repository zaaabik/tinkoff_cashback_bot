import sys

sys.path.append("..")

from tinkoff.cloud.tts.v1 import tts_pb2_grpc, tts_pb2
from speech_pack.auth import authorization_metadata
import grpc
import os
import wave

endpoint = os.environ.get("VOICEKIT_ENDPOINT") or "tts.tinkoff.ru:443"
api_key = 'ZXZ4ZmZxbXhjZndkZXN4YnB4c3B1dnFrbWRla2ZxZWw=s.chekulaevatinkoff'  # os.environ["VOICEKIT_API_KEY"]
secret_key = 'YmNobHphZWZrb3dybHF1YnhxZmR5emtoZXZ3ZmlxcXI='  # os.environ["VOICEKIT_SECRET_KEY"]

sample_rate = 48000


def build_request(text):
    full_text = f'{text}'
    print(full_text)
    return tts_pb2.SynthesizeSpeechRequest(
        input=tts_pb2.SynthesisInput(
            text=full_text),
        audio_config=tts_pb2.AudioConfig(
            audio_encoding=tts_pb2.LINEAR16,
            sample_rate_hertz=sample_rate,
        ),
    )


def generate(text, chat_id):
    with wave.open(f"synthesised{chat_id}.wav", "wb") as f:
        f.setframerate(sample_rate)
        f.setnchannels(1)
        f.setsampwidth(2)

        stub = tts_pb2_grpc.TextToSpeechStub(grpc.secure_channel(endpoint, grpc.ssl_channel_credentials()))
        request = build_request(text)
        metadata = authorization_metadata(api_key, secret_key, "tinkoff.cloud.tts")
        responses = stub.StreamingSynthesize(request, metadata=metadata)
        for key, value in responses.initial_metadata():
            if key == "x-audio-num-samples":
                print("Estimated audio duration is " + str(int(value) / sample_rate) + " seconds")
                break

        for stream_response in responses:
            f.writeframes(stream_response.audio_chunk)
