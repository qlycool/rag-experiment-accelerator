
import json
import re
import llm.prompts
from llm.prompt_execution import generate_response
import numpy as np
from sentence_transformers import CrossEncoder

def cross_encoder_rerank_documents(documents, user_prompt, output_prompt, model_name, k):
    model = CrossEncoder(model_name)
    cross_scores_ques = model.predict([[user_prompt, item] for item in documents],apply_softmax = True, convert_to_numpy = True )
                                    
    top_indices_ques = cross_scores_ques.argsort()[-k:][::-1]
    top_values_ques = cross_scores_ques[top_indices_ques]
    sub_context = []
    for idx in list(top_indices_ques):
        sub_context.append(documents[idx])

    return sub_context

def llm_rerank_documents(documents, question, deployment_name, temperature, rerank_threshold):
    rerank_context = ""
    for index, docs in enumerate(documents):
        rerank_context += "\ndocument " + str(index) + ":\n"
        rerank_context += docs + "\n"


    prompt = f"""
        Let's try this now:
        {rerank_context}
        Question: {question}
    """

    response = generate_response(llm.prompts.rerank_prompt_instruction,prompt, deployment_name, temperature)
    print(response)
    pattern = r'\{(?:[^{}]|(?:\{(?:[^{}]|(?:\{[^{}]*\}))*\}))*\}'
    try:
        matches = re.findall(pattern, response)[0]
        reranked = json.loads( matches )
        print(reranked)
        new_docs = []
        for key, value in reranked['documents'].items():
            key = key.replace('document_', '')
            numeric_data = re.findall(r'\d+\.\d+|\d+', key)
            if int(value) > rerank_threshold:
                new_docs.append(int(numeric_data[0]))
            result = [documents[i] for i in new_docs]
    except:
        print("ERROR: Unable to parse the rerank documents LLM response. Returning all documents.")
        result = documents
    return result