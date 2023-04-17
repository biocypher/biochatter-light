import openai

# read key from key.txt
key = open('key.txt', 'r').read()

openai.api_key = key

MODEL = "gpt-3.5-turbo"
response = openai.ChatCompletion.create(
    model=MODEL,
    messages=[
        {"role": "system", "content": "You are an assistant to a biomedical researcher."},
        {"role": "system", "content": "Your role is to contextualise the user's findings with biomedical background knowledge."},
        {"role": "system", "content": "The topic of the research is high grade serous ovarian cancer."},
        {"role": "system", "content": "You can ask the user to provide explanations and more background, for instance on the treatment the patient has received."},
        {"role": "system", "content": "The user has generated experimental results for a patient based on gene expression in the cancerous tissue."},
        {"role": "user", "content": "In the patient, I found PI3K and AKT to be highly active, while homologous recombination seems to be defective. What could this mean?"},
    ],
    temperature=0,
)

print(response)