import boto3
from pydub import AudioSegment
import os


class Polly:
    def __init__(self):
        self.client = boto3.client('polly')
        self.voices = self.list_available_voices()
    
    def synthesize_speech(self, dialogue, voice_id):
        try:
            # Call Polly to synthesize speech
            response = self.client.synthesize_speech(
                Text=dialogue,
                OutputFormat="mp3",
                VoiceId=voice_id,
                Engine='neural'  # Use neural engine for better quality
            )
            
            # Save audio stream to file
            if "AudioStream" in response:
                return response['AudioStream']
            else:
                raise Exception("No audio stream in Polly response")
                
        except Exception as e:
            print(f"  ✗ Polly error: {str(e)}")
            raise

    def list_available_voices(self):
        """
        Get list of available Polly voices.
        Useful for users to see what voices they can use.
        """
        response = self.client.describe_voices()
        
        voices = []
        for voice in response['Voices']:
            voices.append({
                'id': voice['Id'],
                'name': voice['Name'],
                'gender': voice['Gender'],
                'language': voice['LanguageCode']
            })
        
        return voices

class Podcast(Polly):
    def __init__(self, s3_bucket_arn, podcast_name):
        super().__init__()
        self.podcast_s3_bucket = s3_bucket_arn
        self.podcast_name = podcast_name
    
    def create_podcast(self, dialogue, dialogue_gap=.7):
        
        snippet_file_paths = []
        for i, dialogue_clip in enumerate(dialogue):
            if dialogue_clip['speaker'] == "host":
                voice_id = 'Ruth'
            elif dialogue_clip['speaker'] == "guest":
                #voice_id = 'Patrick'
                voice_id = 'Stephen'
            else:
                raise(Exception("An unknown speaker was present in the dialogue"))
            response_stream  = pod.synthesize_speech(dialogue_clip['text'], voice_id)
            file_path = f"/tmp/{self.podcast_name}-part{i}.mp3"
            snippet_file_paths.append(file_path)
            with open(file_path, "wb") as f:
                f.write(response_stream.read())

        

        final_audio = self.stitch_audio(snippet_file_paths)
        final_audio_file_path = f"/tmp/{self.podcast_name}"
        final_audio.export(final_audio_file_path, format="mp3")
        self.upload_to_s3(final_audio_file_path, self.podcast_s3_bucket, "podcasts", self.podcast_name)


    def stitch_audio(self, audio_file_paths, dialogue_gap = 1.5):
        final_audio = AudioSegment.silent(duration=.1)
        for audio_path in audio_file_paths:
            final_audio += AudioSegment.from_mp3(audio_path) + AudioSegment.silent(duration=(dialogue_gap * 100.00))
            os.remove(audio_path)

        return final_audio
    
    def upload_to_s3(self, file_path, bucket_name, object_path, object_name):
        try:
            s3 = boto3.client('s3')
            s3.upload_file(file_path, bucket_name, object_name)
            print(f"Uploaded {file_path} to s3://{bucket_name}/{object_path}/{object_name}")
        except Exception as e:
            print(f"Upload failed: {e}")
        


if __name__ == "__main__":
    pod = Podcast("mcp-claude-interview","test_podcast")
    #print(pod.voices)

    # response_stream  = pod.synthesize_speech("This is a test", "Olivia")
    # with open("temp.mp3", "wb") as f:
    #     f.write(response_stream.read())

    dialogue =  [
        {"speaker": "host", "text": "Welcome to the show!"},
        {"speaker": "guest", "text": "Thanks for having me!"}
    ]
    pod.create_podcast(dialogue)