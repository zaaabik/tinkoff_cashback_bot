import sys

sys.path.append("..")

from tinkoff.cloud.stt.v1 import stt_pb2_grpc, stt_pb2
from speech_pack.auth import authorization_metadata
import os
import wave

endpoint = os.environ.get("VOICEKIT_ENDPOINT") or "tts.tinkoff.ru:443"
api_key = 'ZXZ4ZmZxbXhjZndkZXN4YnB4c3B1dnFrbWRla2ZxZWw=s.chekulaevatinkoff'  # os.environ["VOICEKIT_API_KEY"]
secret_key = 'YmNobHphZWZrb3dybHF1YnhxZmR5emtoZXZ3ZmlxcXI='  # os.environ["VOICEKIT_SECRET_KEY"]

sample_rate = 48000

import sys

sys.path.append("..")

import grpc


def build_request(binary_file):
    request = stt_pb2.RecognizeRequest()
    request.audio.content = binary_file
    request.config.encoding = stt_pb2.AudioEncoding.LINEAR16
    request.config.sample_rate_hertz = 48000  # Not stored at raw ".s16" file
    request.config.num_channels = 1  # Not stored at raw ".s16" file
    return request


def print_recognition_response(response):
    for result in response.results:
        print("Channel", result.channel)
        print("Phrase start:", result.start_time.ToTimedelta())
        print("Phrase end:  ", result.end_time.ToTimedelta())
        for alternative in result.alternatives:
            print('"' + alternative.transcript + '"')
        print("----------------------------")


import subprocess


def file_to_text(src_filename):
    src_filename = os.path.join(
        '..', 'voices',
        src_filename
    )

    file_name_without_ext = os.path.basename(src_filename).split('.')[0]
    dest_filename = os.path.join(
        '..', 'voices',
        f'{file_name_without_ext}.wav'
    )

    process = subprocess.run(['ffmpeg', '-i', src_filename, dest_filename, '-y'])
    if process.returncode != 0:
        raise Exception("Something went wrong")
    with open(dest_filename, 'rb') as wav_file:
        return speech2text(wav_file.read())


def speech2text(binary_file):
    stub = stt_pb2_grpc.SpeechToTextStub(grpc.secure_channel(endpoint, grpc.ssl_channel_credentials()))
    metadata = authorization_metadata(api_key, secret_key, "tinkoff.cloud.stt")
    response = stub.Recognize(build_request(binary_file), metadata=metadata)
    print_recognition_response(response)
    output = ''
    for result in response.results:
        for alternative in result.alternatives:
            output += str(alternative.transcript)
    return output


if __name__ == '__main__':
    c = ['ffmpeg', '-i', '../voices/voice255314293.ogg', '../voices/voice255314293.wav', '-y']
    process = subprocess.run(c)
