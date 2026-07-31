import asyncio
import edge_tts

def create_voiceover(text, output_file="voice.mp3"):
    try:
        async def generate_voiceover_async():
            voice = "en-US-ChristopherNeural"
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(output_file)

        asyncio.run(generate_voiceover_async())
        return True, "Success"
    except Exception as e:
        print(f"Error generating AI voiceover: {e}")
        return False, str(e)
