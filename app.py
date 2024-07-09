from flask import Flask, render_template, request
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel

app = Flask(__name__)

# Sample dataset with job roles, industries, descriptions, and skills
data = {
    'job_id': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    'job_role': [
        'Software Engineer', 'Data Scientist', 'Project Manager', 'Product Manager', 'Data Analyst',
        'Web Developer', 'Database Administrator', 'Network Engineer', 'UI/UX Designer', 'Business Analyst'
    ],
    'industry': [
        'IT', 'IT', 'Management', 'Management', 'IT',
        'IT', 'IT', 'IT', 'Design', 'Management'
    ],
    'description': [
        'Develop and maintain software applications.',
        'Analyze data to extract insights and build models.',
        'Oversee projects from initiation to completion.',
        'Manage product development and strategy.',
        'Analyze data to support business decisions.',
        'Design and develop websites and web applications.',
        'Design and maintain database systems.',
        'Design and manage computer networks.',
        'Create intuitive and engaging user interfaces and experiences.',
        'Analyze business processes and recommend improvements.'
    ],
    'skills': [
        'Python, Java', 'Python, SQL', 'Project Management', 'Product Management', 'SQL, Excel',
        'HTML, CSS, JavaScript', 'SQL, Database Management', 'Networking, Security', 'UI/UX Design', 'Business Analysis'
    ]
}

jobs_df = pd.DataFrame(data)

tfidf_vectorizer = TfidfVectorizer(stop_words='english')
tfidf_matrix = tfidf_vectorizer.fit_transform(jobs_df['description'] + " " + jobs_df['job_role'])

def recommend_jobs_based_on_skills(skills, n_recommendations=3):
    filtered_jobs = jobs_df[jobs_df['skills'].apply(lambda x: any(skill.strip().lower() in x.lower() for skill in skills))]
    
    if filtered_jobs.empty:
        return pd.DataFrame()
    
    # Calculate TF-IDF similarity for the filtered jobs
    tfidf_filtered = tfidf_vectorizer.transform(filtered_jobs['description'] + " " + filtered_jobs['job_role'])
    cosine_similarities = linear_kernel(tfidf_filtered, tfidf_matrix)
    
    # Get top similar jobs based on cosine similarity
    similar_indices = cosine_similarities.argsort(axis=1)[:, :-n_recommendations-2:-1]
    
    recommended_jobs = []
    for idx in range(len(filtered_jobs)):
        similar_jobs = jobs_df.iloc[similar_indices[idx]]
        similar_jobs = similar_jobs[~similar_jobs['job_id'].isin(filtered_jobs['job_id'].iloc[[idx]])]
        recommended_jobs.extend(similar_jobs.head(n_recommendations).to_dict(orient='records'))
    
    return pd.DataFrame(recommended_jobs)

def recommend_jobs_based_on_role(job_role, n_recommendations=3):
    job_indices = jobs_df.index[jobs_df['job_role'].str.lower() == job_role.lower()].tolist()
    if not job_indices:
        return pd.DataFrame()  # No job roles found
    
    cosine_similarities = linear_kernel(tfidf_matrix[job_indices[0]], tfidf_matrix).flatten()
    similar_indices = cosine_similarities.argsort()[:-n_recommendations-2:-1]
    similar_indices = [i for i in similar_indices if i not in job_indices]
    recommended_jobs = jobs_df.iloc[similar_indices].head(n_recommendations)
    
    return recommended_jobs

@app.route('/')
def home():
    return render_template('index.html', jobs=jobs_df['job_role'].unique())

@app.route('/recommend', methods=['POST'])
def recommend():
    selection_type = request.form.get('selection_type')
    if selection_type == 'skills':
        skills = request.form.get('skills').split(',')
        recommended_jobs = recommend_jobs_based_on_skills(skills)
    else:
        job_role = request.form.get('job_role')
        recommended_jobs = recommend_jobs_based_on_role(job_role)
    
    return render_template('results.html', jobs=recommended_jobs.to_dict(orient='records'))

if __name__ == '__main__':
    app.run(debug=True)
