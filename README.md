# AiTA Demo 0.0.1

AiTA (Artificial Intelligence Tutoring Assistant) is an innovative online tutoring system designed for college students. This system leverages advanced AI technologies to offer personalized learning experiences and support.

## Features

- **Lecture Notes Digest**: Utilizes a language processing model to generate organized and easy-to-understand lecture notes digests.
- **Question Sheet Solutions**: Students can upload their question sheets to receive AI-generated step-by-step solutions and explanations.
- **Q&A Bot**: An interactive bot that provides instant answers to students' queries.

## Installation

To use AiTA, clone the repository and install the required dependencies.

```python
git clone xl631212/aita_new_version
cd xl631212/aita_new_version
pip install -r requirements.txt
```

## Usage

Run the Streamlit application locally:

```python
streamlit run app.py
```

## Key Components

- **Page Navigation**: Users can navigate between different functionalities like lecture materials digestion and question sheet solutions.
- **File Uploading**: Supports uploading of lecture notes and question sheets in PDF format.
- **Customizable Settings**: Allows users to select reading level, teaching style, language, and grade level for a personalized experience.
- **AI-Driven Analysis**: Employs OpenAI's GPT-4 model to process and generate educational content.

## Dependencies

- Streamlit
- OpenAI
- pdfplumber
- streamlit_chat

## Environment Variables

Set your OpenAI API key in the environment:

```python
export OPENAI_API_KEY='your_api_key'
```

## Contribution

Contributions to AiTA are welcome! Please read the contribution guidelines before submitting pull requests.


## Acknowledgments

Special thanks to [Contributors and Supporters].

---

Made with ❤️ by XuyingLi
