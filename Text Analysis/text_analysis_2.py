import pandas as pd
import nltk
nltk.download('punkt')
from nltk.corpus import stopwords
from bs4 import BeautifulSoup
import requests
import re

import chardet

data = pd.read_excel('/content/sample_data/Data/Input.xlsx')

with open('/content/sample_data/Data/negative-words.txt', 'rb') as file:
    encoding = chardet.detect(file.read())['encoding']
    file.seek(0)
    positive_words = file.read().decode(encoding).splitlines()

with open('/content/sample_data/Data/positive-words.txt', 'rb') as file:
    encoding = chardet.detect(file.read())['encoding']
    file.seek(0)
    negative_words = file.read().decode(encoding).splitlines()

import nltk

nltk.download('stopwords')

def load_stopwords(file_path):
    with open(file_path, 'r', encoding='latin-1') as file:
        return set(word.strip() for word in file)

stop_words_auditor = load_stopwords('/content/sample_data/Data/StopWords_Auditor.txt')
stop_words_currencies = load_stopwords('/content/sample_data/Data/StopWords_Currencies.txt')
stop_words_dates_and_numbers = load_stopwords('/content/sample_data/Data/StopWords_DatesandNumbers.txt')
stop_words_generic = load_stopwords('/content/sample_data/Data/StopWords_Generic.txt')
stop_words_genericlong = load_stopwords('/content/sample_data/Data/StopWords_GenericLong.txt')
stop_words_geographic = load_stopwords('/content/sample_data/Data/StopWords_Geographic.txt')
stop_words_names = load_stopwords('/content/sample_data/Data/StopWords_Names.txt')

# Preprocessing function to clean text
def preprocess_text(text):
    # Remove HTML tags
    text = BeautifulSoup(text, 'html.parser').get_text()
    # Tokenize text
    tokens = nltk.word_tokenize(text)
    # Remove stopwords and punctuation
    clean_tokens = [word.lower() for word in tokens if word.lower() not in stop_words_auditor and word.isalnum()]
    return clean_tokens

# Function to extract text from websites
def extract_text(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    return soup.get_text()

# Function to calculate positive score
def calculate_positive_score(text):
    return sum(1 for word in text if word in positive_words)

# Function to calculate negative score
def calculate_negative_score(text):
    return sum(1 for word in text if word in negative_words)

# Function to count complex words
def count_complex_words(text):
    return sum(1 for word in text if syllable_count(word) > 2)

# Function to calculate syllable count for a word
def syllable_count(word):
    word = word.lower()
    vowels = "aeiouy"
    count = 0
    if word[0] in vowels:
        count += 1
    for index in range(1, len(word)):
        if word[index] in vowels and word[index - 1] not in vowels:
            count += 1
    if word.endswith("e"):
        count -= 1
    if word.endswith("le") and len(word) > 2 and word[-3] not in vowels:
        count += 1
    if count == 0:
        count += 1
    return count

# Function to calculate total syllable count for the entire text
def total_syllable_count(text):
    return sum(syllable_count(word) for word in text)

# Function to calculate metrics and scores
def calculate_metrics(text):
    positive_score = calculate_positive_score(text)
    negative_score = calculate_negative_score(text)
    polarity_score = (positive_score - negative_score) / ((positive_score + negative_score) + 0.000001)
    subjectivity_score = (positive_score + negative_score) / (len(text) + 0.000001)
    avg_sentence_length = len(text) / (text.count('.') + 1) if len(text) != 0 else 0
    percentage_complex_words = count_complex_words(text) / len(text) if len(text) != 0 else 0
    fog_index = 0.4 * (avg_sentence_length + percentage_complex_words)
    avg_words_per_sentence = len(text) / (text.count('.') + 1) if len(text) != 0 else 0
    complex_word_count = count_complex_words(text)
    word_count = len(text)
    personal_pronouns = sum(1 for word in text if word.lower() in ['i', 'we', 'my', 'ours', 'us'])
    avg_word_length = sum(len(word) for word in text) / len(text) if len(text) != 0 else 0
    syllable_count_total = total_syllable_count(text)
    return {
        'Positive_Score': positive_score,
        'Negative_Score': negative_score,
        'Polarity_Score': polarity_score,
        'Subjectivity_Score': subjectivity_score,
        'Avg_Sentence_Length': avg_sentence_length,
        'Percentage_of_Complex_Words': percentage_complex_words,
        'FOG_Index': fog_index,
        'Avg_Words_Per_Sentence': avg_words_per_sentence,
        'Complex_Word_Count': complex_word_count,
        'Word_Count': word_count,
        'Personal_Pronouns': personal_pronouns,
        'Avg_Word_Length': avg_word_length,
        'Syllable_Count': syllable_count_total
    }

# Process each URL in the dataset
for index, row in data.iterrows():
    text = extract_text(row['URL'])
    cleaned_text = preprocess_text(text)
    metrics = calculate_metrics(cleaned_text)

    for metric, value in metrics.items():
        data.at[index, metric] = value

# Save results to Excel
data.to_excel('output_file.xlsx', index=False)

