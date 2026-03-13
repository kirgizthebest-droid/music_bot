def build_prompt(data):

    prompt = f"""
Create a Russian song.

Style: {data['style']}
Mood: {data['mood']}

Song for: {data['name']}
From: {data['from']}
Occasion: {data['occasion']}
Relationship: {data['target_type']}

Description:
{data['description']}

Make the lyrics emotional, personal and memorable.
"""

    return prompt
