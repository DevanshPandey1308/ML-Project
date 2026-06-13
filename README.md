# 🎓 Student Performance Prediction

An end-to-end Machine Learning application that predicts a student's **Math Score** using demographic and academic attributes such as gender, race/ethnicity, parental level of education, lunch type, test preparation course, reading score, and writing score.

The project follows a production-style machine learning workflow including data ingestion, transformation, model training, evaluation, prediction pipeline creation, Flask integration, and AWS deployment.

---

## 🚀 Key Features

* End-to-End Machine Learning Pipeline
* Automated Data Ingestion & Data Transformation
* Multiple Model Training & Evaluation
* Automatic Best Model Selection
* Reusable Prediction Pipeline
* Flask-based Web Application
* AWS Elastic Beanstalk Deployment
* Modular & Scalable Project Architecture
* Production-Oriented Code Structure

---

## 🛠️ Tech Stack

| Category         | Tools                           |
| ---------------- | ------------------------------- |
| Language         | Python                          |
| Data Handling    | Pandas, NumPy                   |
| Machine Learning | Scikit-Learn, XGBoost, CatBoost |
| Visualization    | Matplotlib, Seaborn             |
| Web Framework    | Flask                           |
| Deployment       | AWS Elastic Beanstalk           |
| Version Control  | Git, GitHub                     |

---

## 🏗️ Project Architecture / Workflow

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
```

### Models Evaluated

* Linear Regression
* Decision Tree Regressor
* Random Forest Regressor
* Gradient Boosting Regressor
* AdaBoost Regressor
* XGBoost Regressor
* CatBoost Regressor

The best-performing model is automatically selected based on evaluation metrics and serialized for inference.

---

## 📁 Project Structure

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
│   ├── logger.py
│   ├── exception.py
│   └── utils.py
│
├── templates
│   ├── home.html
│   └── index.html
│
├── static
│
├── application.py
├── requirements.txt
├── setup.py
└── README.md
```

---

## ⚙️ Installation & Setup

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/DevanshPandey1308/ML-Project.git
cd ML-Project
```

### 2️⃣ Create a Virtual Environment

```bash
python -m venv venv
```

### 3️⃣ Activate the Virtual Environment

#### Windows

```bash
venv\Scripts\activate
```

#### Linux / macOS

```bash
source venv/bin/activate
```

### 4️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 5️⃣ Run the Application

```bash
python application.py
```

### 6️⃣ Open in Browser

```text
StudentPerformancePredictor-env.eba-mrqxyj2a.ap-south-1.elasticbeanstalk.com
```

---

## 📸 Screenshots

### Home Page

<img width="746" height="448" alt="Screenshot 2026-06-13 221258" src="https://github.com/user-attachments/assets/cf2f0fa4-04f4-4a25-a968-43663bd5d6b0" />


### Prediction Output

<img width="746" height="445" alt="Screenshot 2026-06-13 221337" src="https://github.com/user-attachments/assets/4a3b3e97-1f6e-45e5-9248-a6dcc716de8a" />


### Exploratory Data Analysis

<img width="746" height="447" alt="Screenshot 2026-06-13 221354" src="https://github.com/user-attachments/assets/5efc4dd9-7934-46a4-89bf-e46dd369d96b" />


---

## 🎯 Key Learnings

Through this project, I gained hands-on experience in:

* End-to-End Machine Learning Pipelines
* Data Preprocessing & Feature Engineering
* Model Training & Evaluation
* Scikit-Learn Pipelines
* Object-Oriented Project Architecture
* Flask Application Development
* Model Deployment on AWS Elastic Beanstalk
* Production-Level Debugging & Troubleshooting

---

## 🔮 Future Improvements

* Docker Containerization
* CI/CD Pipeline using GitHub Actions
* MLflow Integration
* Hyperparameter Tuning
* Model Monitoring
* Automated Retraining Pipeline
* REST API Development

---

## 👤 Author

**Devansh Pandey**
**email : devanshp171@gmail.com**

* GitHub: https://github.com/DevanshPandey1308
* LinkedIn: https://www.linkedin.com/in/devanshp13/
* Project Live Demo: StudentPerformancePredictor-env.eba-mrqxyj2a.ap-south-1.elasticbeanstalk.com
* 
---

## ⭐ If you found this project useful, consider giving it a star!
