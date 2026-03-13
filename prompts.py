def build_prompt(data):

    prompt = f"""
Create a Russian song.

Style: {data['style']}
Mood: {data['mood']}

Song for: {data['name']}
From: {data['from']}
Occasion: {data['occasion']}

Description:
{data['description']}

Make lyrics emotional and personal.
"""

    return prompt
