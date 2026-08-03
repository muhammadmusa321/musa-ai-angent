import asyncio
import os
import edge_tts

VOICE = "en-US-ChristopherNeural"


def create_voiceover(text, output_file="voice.mp3", srt_file="voice.srt"):
    """
    Generates the AI voiceover (free, via edge-tts) and, when possible, a
    matching .srt caption file synced to the actual spoken word timings
    (also free -- edge-tts reports word-boundary timestamps natively).
    If caption generation fails for any reason, we still fall back to a
    plain voiceover so the pipeline never breaks.
    """
    try:
        async def with_captions():
            communicate = edge_tts.Communicate(text, VOICE)
            submaker = edge_tts.SubMaker()
            with open(output_file, "wb") as f:
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        f.write(chunk["data"])
                    elif chunk["type"] == "WordBoundary":
                        submaker.feed(chunk)
            srt_content = submaker.get_srt()
            with open(srt_file, "w", encoding="utf-8") as f:
                f.write(srt_content)

        async def without_captions():
            communicate = edge_tts.Communicate(text, VOICE)
            await communicate.save(output_file)

        try:
            asyncio.run(with_captions())
            print("Voiceover + synced captions generated successfully.")
        except Exception as caption_err:
            print(f"Caption-synced voiceover failed, falling back to plain voiceover: {caption_err}")
            if os.path.exists(srt_file):
                os.remove(srt_file)
            asyncio.run(without_captions())

        return True, "Success"
    except Exception as e:
        print(f"Error generating AI voiceover: {e}")
        return False, str(e)
