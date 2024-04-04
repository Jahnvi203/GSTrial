import os
from openai import OpenAI
import pandas as pd
import re
import streamlit as st
import traceback

# client = OpenAI(api_key = st.secrets("api_key"))
client = OpenAI(api_key = st.secrets("api_key"))

guidelines = [
    "The Genuine Student (GS) requirement in Australia requires all applicants for a student visa to be a genuine applicant for entry.",
    "They must stay as a student and be able to show an understanding that studying in Australia is the primary reason of their student visa. The GS requirement is intended to include students who, after studying in Australia, develop skills Australia needs and who then go on to apply for permanent residence.",
    "To be granted a student visa, all applicants must demonstrate they satisfy the genuine student criterion or the genuine student dependent criterion.",
    "The GS criterion focuses on the assessment of the student’s intention to genuinely study in Australia.",
    "It considers factors including the applicant's circumstances, immigration history, compliance with visa conditions and any other relevant matter.",
    "For each question, the criteria is given.",
    "For each question, using only the criteria for that question, give a score to each answer out of 25.",
    "Be very strict in your scoring and feedback. Scoring Guide for Each Question: 20-25 for a highly genuine student; 15-24 for a generally genuine student with a few areas needing clarification; below 15 suggests a more in-depth review of the student's intentions and information.",
    "Provide feedback for each question, from a second person perspective, specifically for this student based on their answer on where they need to improve their answer.",
    "The output should be in the form: Question 1 Score = .../25, Question 1 Feedback: ..., Question 2 Score: .../25. Question 2 Feedback: ..., etc."
]

prompts = {
    1: {
        "question": "Give details of the applicant’s current circumstances. This includes ties to family, community, employment and economic circumstances.",
        "prompt": [
            "Question 1 in the GS requirement in Australia is - 'Give details of the applicant’s current circumstances. This includes ties to family, community, employment and economic circumstances.'",
            "For question 1 alone, the criteria to assess the answer is - (1) reason for not studying in their home country or region if a similar course is available there; (2) the nature of the applicant’s personal ties to their home country; (3) economic circumstances; (4) military service commitments political and civil unrest in their home country."            
        ]
    },
    2: {
        "question": "Explain why the applicant wishes to study this course in Australia with this particular education provider. This must also explain their understanding of the requirements of the intended course and studying and living in Australia.",
        "prompt": [
            "Question 2 in the GS requirement in Australia is - 'Explain why the applicant wishes to study this course in Australia with this particular education provider. This must also explain their understanding of the requirements of the intended course and studying and living in Australia.'",
            "For question 2 alone, the criteria to assess the answer is - (1) level of knowledge of the proposed course and education provider; (2) previous study and qualifications; (3) planned living arrangements; (4) financial stability."
        ]
    },
    3: {
        "question": "Explain how completing the course will be of benefit to the applicant.",
        "prompt": [
            "Question 3 in the GS requirement in Australia is - 'Explain how completing the course will be of benefit to the applicant.'",
            "For question 3 alone, the criteria to assess the answer is - (1) if the course is consistent with their current level of education and if the course will assist them to obtain employment or improve employment prospect in their home country or another country; (2) if the course is relevant to past or proposed future employment in their home country or another country; (3) expected salary and other benefits in their home country or another country obtained with the applicant’s qualifications from the proposed course of study."
        ]
    },
    4: {
        "question": "Give details of any other relevant information the applicant would like to include.",
        "prompt": [
            "Question 4 in the GS requirement in Australia is - 'Give details of any other relevant information the applicant would like to include.'",
            "For question 4 alone, the criteria to assess the answer is - (1) visa and travel history for Australia and other countries; (2) previous visa applications for Australia or other countries; (3) visa refusals or cancellations; (4) any other relevant information such as about previously holding student visa in Australia or lodging an application in Australia from a non-student visa, English language proficiency or improvement plans, details of available support networks in Australia if any, long-term career or academic goals in Australia, efforts for cultural integration and future contributions to Australia."
        ]
    }
}

total_score = 0
word_limit = 150
error = False

with st.form("GSTrial"):

    st.title("Assess Your Genuine Student (GS) Application SOP")
    st.write("Enter your response to each question below.")
    st.header("Question 1")
    answer_1 = st.text_area(prompts[1]["question"])
    st.header("Question 2")
    answer_2 = st.text_area(prompts[2]["question"])
    st.header("Question 3")
    answer_3 = st.text_area(prompts[3]["question"])
    st.header("Question 4")
    answer_4 = st.text_area(prompts[4]["question"])

    submitted = st.form_submit_button("Submit")

    if submitted:

        if len(answer_1.strip()) == 0 or len(answer_2.strip()) == 0 or len(answer_3.strip()) == 0 or len(answer_4.strip()) == 0:
            st.warning("Please enter a response for all questions.", icon = "⚠️")
        
        else:
            try:
                answers = [answer_1, answer_2, answer_3, answer_4]
                word_limits = []
                messages = [
                    {
                        "role": "system",
                        "content": " ".join(guidelines)
                    }
                ]

                for i in range(1, 5):
                    
                    if len(answers[i-1].split()) > 150:
                        answers[i-1] = ' '.join(answers[i-1].split()[:150])
                        word_limits.append(False)
                    
                    else:
                        word_limits.append(True)
                    
                    messages.append({
                        "role": "user",
                        "content": " ".join(prompts[i]["prompt"])
                    })

                    messages.append(
                        {
                            "role": "user",
                            "content": f"The answer for question {i} is - {answers[i-1]}"
                        },
                    )

                response = client.chat.completions.create(
                    model = "gpt-3.5-turbo",
                    messages = messages,
                    temperature =  1.5,
                    max_tokens = 2000,
                    top_p = 1,
                    frequency_penalty = 0,
                    presence_penalty = 0
                )

                output = response.__dict__["choices"][0].__dict__["message"].__dict__["content"]
                scores_feedbacks = []
                questions_output = output.split("\n\n")
                
                for question in questions_output:
                    print(question)
                    temp = question.split("\n")

                    
                    if re.match("Question\s\d+\sScore\s=\s\d+/25", question.split(", ")[0].strip()):
                        
                        if "/25, Question " in question:
                            score = question.split("/25, ")[0].strip().split(" = ")[1]
                            feedback = question.split("/25, ")[1].strip()
                            if re.match("Question\s\d+\sFeedback:\s.+", feedback):
                                feedback = feedback.split("Feedback: ")[1].strip()
                                scores_feedbacks.append([score, feedback])
                                total_score += int(score)
                            else:
                                error = True
                                print("Re mismatch (feedback) error")
                        elif "/25\n" in question:
                            score = question.split("/25\n")[0].strip().split(" = ")[1]
                            feedback = question.split("/25\n")[1].strip()
                            if re.match("Question\s\d+\sFeedback:\s.+", feedback):
                                feedback = feedback.split("Feedback: ")[1].strip()
                                scores_feedbacks.append([score, feedback])
                                total_score += int(score)
                            else:
                                error = True
                                print("Re mismatch (feedback) error")
                        elif r"/25,\n" in question:
                            score = question.split("/25,\n")[0].strip().split(" = ")[1]
                            feedback = question.split("/25,\n")[1].strip()
                            if re.match("Question\s\d+\sFeedback:\s.+", feedback):
                                feedback = feedback.split("Feedback: ")[1].strip()
                                scores_feedbacks.append([score, feedback])
                                total_score += int(score)
                            else:
                                error = True
                                print("Re mismatch (feedback) error")
                        elif r"/25, \n" in question:
                            score = question.split("/25, \n")[0].strip().split(" = ")[1]
                            feedback = question.split("/25, \n")[1].strip()
                            if re.match("Question\s\d+\sFeedback:\s.+", feedback):
                                feedback = feedback.split("Feedback: ")[1].strip()
                                scores_feedbacks.append([score, feedback])
                                total_score += int(score)
                            else:
                                error = True
                                print("Re mismatch (feedback) error")
                        else:
                            error = True
                            print("Unsupported score and feedback structure")
                    
                    else:
                        error = True
                        print("Re mismatch (score) error")
                
                if error == True:
                    st.warning("There was an error in assessing your SOP. Please try again.", icon = "⚠️")
                
                else:
                    st.header(f"Results: {total_score}/100")
                    st.subheader("Question 1")
                    st.write(scores_feedbacks[0][1])
                    st.subheader("Question 2")
                    st.write(scores_feedbacks[1][1])
                    st.subheader("Question 3")
                    st.write(scores_feedbacks[2][1])
                    st.subheader("Question 4")
                    st.write(scores_feedbacks[3][1])
            
            except Exception:
                print(traceback.format_exc())
                st.warning("There was an error in assessing your SOP. Please try again.", icon = "⚠️")