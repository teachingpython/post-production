import spacy

nlp = spacy.load("en_core_web_sm")
with open("test_transcript.txt") as infile:
    transcript = infile.read()

doc = nlp(transcript)
print(set(doc.ents))
