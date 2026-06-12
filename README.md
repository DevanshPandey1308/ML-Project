````markdown
# Student Performance Prediction

An end-to-end Machine Learning application that predicts a student's **Math Score** using demographic and academic attributes such as gender, race/ethnicity, parental education, lunch type, test preparation course, reading score, and writing score.

## Features

- End-to-End Machine Learning Pipeline
- Automated Data Ingestion & Data Transformation
- Multiple Model Training & Evaluation
- Automatic Best Model Selection
- Prediction Pipeline using Serialized Models
- Flask Web Application
- AWS Elastic Beanstalk Deployment
- Production-Oriented Project Structure

## Tech Stack

### Languages & Libraries
- Python
- Pandas
- NumPy
- Scikit-Learn
- CatBoost
- XGBoost
- Matplotlib
- Seaborn

### Backend
- Flask

### Deployment
- AWS Elastic Beanstalk

### Version Control
- Git & GitHub

---

## Project Workflow

```text
Dataset
   │
   ▼
Data Ingestion
   │
   ▼
Data Transformation
   │
   ▼
Model Training
   │
   ▼
Model Evaluation
   │
   ▼
Best Model Selection
   │
   ▼
Model Serialization
   │
   ▼
Prediction Pipeline
   │
   ▼
Flask Application
   │
   ▼
AWS Deployment
````

---

## Project Structure

```text
ML_Project
│
├── artifacts
│   ├── model.pkl
│   ├── preprocessor.pkl
│   ├── raw.csv
│   ├── train.csv
│   └── test.csv
│
├── src
│   ├── components
│   │   ├── data_ingestion.py
│   │   ├── data_transformation.py
│   │   └── model_trainer.py
│   │
│   ├── pipeline
│   │   └── predict_pipeline.py
│   │
│   ├── exception.py
│   ├── logger.py
│   └── utils.py
│
├── templates
│   ├── home.html
│   └── index.html
│
├── static
├── application.py
├── requirements.txt
├── setup.py
└── README.md
```

---

## Models Evaluated

The following regression models were trained and compared:

* Linear Regression
* Decision Tree Regressor
* Random Forest Regressor
* Gradient Boosting Regressor
* AdaBoost Regressor
* XGBoost Regressor
* CatBoost Regressor

The best-performing model was automatically selected based on evaluation metrics and saved for prediction.

---

## Installation

### Clone Repository

```bash
git clone https://github.com/your-username/your-repository.git
```

### Move into Project Directory

```bash
cd ML_Project
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run Application

```bash
python application.py
```

The application will start on:

```text
http://localhost:5000
```

---

## Screenshots

### Home Page

*Add Screenshot Here*

### Prediction Form

*Add Screenshot Here*

### Prediction Output

*Add Screenshot Here*

---

## Key Learnings

Through this project, I gained hands-on experience in:

* End-to-End Machine Learning Pipelines
* Data Preprocessing & Feature Engineering
* Model Training & Evaluation
* Scikit-Learn Pipelines
* Flask Application Development
* Model Deployment on AWS
* Production-Level Project Structure
* Debugging Real-World Deployment Issues

---

## Future Improvements

* Docker Containerization
* CI/CD Pipeline
* MLflow Integration
* Model Monitoring
* Automated Retraining Pipeline
* Cloud Storage Integration

---

## Author

**Devansh Pandey**

* GitHub: https://github.com/DevanshPandey1308
* LinkedIn: https://linkedin.com/in/devansh-pandey

```
```
